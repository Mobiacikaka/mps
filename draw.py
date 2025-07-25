#!/bin/python3

import matplotlib.pyplot as plt
from src.RandomPartition import RandomPartition
from src.GreedyPartition import GreedyPartition
from src.graph import Graph
from utils.GraphGenerator import HotspotRandomGenerator as HRG
from utils.GraphGenerator import UniformRandomGenerator as URG
from utils.GraphGenerator import GetEdgesFromNodes as GEN
import utils.analyzer as al
import json
import numpy
import traceback
import contextlib
from utils.compare import ReadBPCFolder
from utils.analyzer import MaxEdgeRank as Scoring
from utils.analyzer import UnfoldSolution
from src.BranchPriceCut import BranchAndPrice as BPC
import os
import ast

def ReadGraph(filename: str='graph.csv'):
	file = open(filename, 'r')
	lines: list[str] = [line.strip(',\n') for line in file.readlines()]
	edges: list[list[float]] = []
	for line in lines:
		edges.append([float(edge) for edge in line.split(',')])
	return edges

def ReadLogFile(filename: str) -> dict | None:
	logfile = open(filename, 'r')

	## Read Log
	lines: list = logfile.readlines()
	attribute: dict = {}
	solution : list = [] ## solution lines
	for line in lines:
		if 'Total instances' in line:
			attribute['total instance'] = int(line.split(':')[1])
			continue
		if 'Solved exactly' in line:
			attribute['solve instance'] = int(line.split(':')[1])
			continue
		if 'Total Columns Generated' in line:
			attribute['column num']     = int(line.split(':')[1])
			continue
		if 'Total Cutting Planes Generated' in line:
			attribute['c-plane num']    = int(line.split(':')[1])
			continue
		if 'Upper bound' in line:
			attribute['upper bound']    = float(line.split(':')[1])
			continue
		if 'Total Time' in line:
			attribute['time']           = float(line.split(':')[1])
			continue
		if 'Divided Nodes' in line:
			attribute['divided'] = ast.literal_eval(line.strip('Divided Nodes '))
			continue
		if 'Collapsed Nodes ' in line:
			attribute['collapsed'] = ast.literal_eval(line.strip('Collapsed Nodes '))
			continue
		if ' 1.0 ' in line:
			solution.append(ast.literal_eval(line.split(' 1.0 ')[1]))
			continue
	if solution == []:
		return None
	attribute['solution'] = solution
	UnfoldSolution(attribute['solution'], attribute['collapsed'])
	return attribute

## GG == Graph Generator
def GGUniRand(N: int, S: int, seed: int):
	# graph_filename = f'./test/RANDOM/graph__N_{N}__seed_{seed}.csv'
	# if os.path.exists(graph_filename):
	# 	edges = ReadGraph()
	# else:
	# 	nodes = URG(N, seed)
	# 	edges = GEN(nodes=nodes)
	# log_filename = f'./test/RANDOM/'
	data = ReadBPCFolder(f'./test/RANDOM/S_{S}/N_{N}/{seed}')
	assert(data != None)
	solution = data['solution']
	edges = data['edges']
	graph = Graph(edges=edges)
	return graph, solution

def GGHotSpot(N: int, S: int, seed: int):
	graph_filename = f'./test/HOTSPOT/graph/graph__N{N}__seed{seed}.csv'
	log_filename = f'./test/HOTSPOT/log/bpc__N{N}__S{S}__seed{seed}.log'

	## Check graph file existence
	if os.path.exists(graph_filename):
		edges = ReadGraph(graph_filename)
		graph = Graph(edges=edges)
	else:
		nodes = HRG(N, seed=seed)
		edges = GEN(nodes=nodes)
		graph = Graph(edges=edges)
		graph.PrintGraph(graph_filename)

	## Check log file existence
	if os.path.exists(log_filename):
		data = ReadLogFile(log_filename)
		assert(data != None)
		solution_bpc = data['solution']
	else:
		with open(log_filename, 'w') as fnull:
			with contextlib.redirect_stdout(fnull):
				solution_bpc = BPC(graph, S)
	return graph, solution_bpc

def DrawNS(N: int|list, S: int|list, GG: str='UniRand'):
	variable = None
	assert(type(N) != type(S))
	if type(N) == int:
		variable = 'S'
		title = f'N={N}'
	else:
		variable = 'N'
		title = f'S={S}'
	seed_list = list(range(0, 10))

	x_val = []
	if variable == 'S':
		x_val = S
	else:
		x_val = N
	assert(type(x_val) == list)

	## branch and price and cut value
	bpc_val = []
	## random partition value
	rp_val = []
	## greedy partition value
	gp_val = []
	for v in x_val:
		bpc_score_list = []
		rp_score_list = []
		gp_score_list = []
		if variable == 'S':
			S = v
		else:
			N = v
		assert(type(S) == int and type(N) == int)
		for seed in seed_list:
			try:
				graph, solution = None, None
				if GG == 'UniRand':
					graph, solution = GGUniRand(N, S, seed)
				elif GG == 'HotSpot':
					graph, solution = GGHotSpot(N, S, seed)
				assert(graph != None and solution != None)
				## branch and price and cut scoring
				score = Scoring(graph, partition=solution)
				bpc_score_list.append(score)
				## random partition scoring
				score = Scoring(graph, partition=RandomPartition(graph, S))
				rp_score_list.append(score)
				## greedy partition scoring
				score = Scoring(graph, partition=GreedyPartition(graph, S))
				gp_score_list.append(score)
			except:
				traceback.print_exc()
				print(f'N{N} S{S} seed{seed} NOT GOOD!')
		bpc_val.append(numpy.mean(bpc_score_list))
		rp_val.append(numpy.mean(rp_score_list))
		gp_val.append(numpy.mean(gp_score_list))

	plt.plot(x_val, rp_val, marker='s', linestyle='--', color='green', label='Random Partition')
	plt.plot(x_val, gp_val, marker='^', linestyle='-.', color='red', label='Greedy Partition')
	plt.plot(x_val, bpc_val, marker='o', linestyle='-', color='blue', label='Branch-and-Price-and-Cut')
	plt.xlabel(variable)
	plt.ylabel('Mean Rank')
	plt.title(title)
	plt.legend()
	plt.grid()
	plt.savefig(f'figs/MEAN_RANK__{GG}__{title}.svg')
	# plt.show()

if __name__ == '__main__':
	S_list = [4, 5, 6, 7, 8]
	N_list = list(range(20, 50))
	for N in N_list:
		DrawNS(N=N, S=S_list, GG='UniRand')
	for S in S_list:
		DrawNS(N=N_list, S=S, GG='UniRand')
	# DrawNS(48, [4, 5, 6, 7, 8], GG='UniRand')
	# DrawNS([20, 25, 30, 35, 40, 45], 6, GG='UniRand')
	# DrawNS(48, [4, 5, 6, 7, 8], GG='HotSpot')
