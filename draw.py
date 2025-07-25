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
from src.BranchPriceCut import BranchAndPrice as BPC
import os

def ReadGraph(filename: str='graph.csv'):
	file = open(filename, 'r')
	lines: list[str] = [line.strip(',\n') for line in file.readlines()]
	edges: list[list[float]] = []
	for line in lines:
		edges.append([float(edge) for edge in line.split(',')])
	return edges

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
	edges = data['solution']
	graph = Graph(edges=edges)
	return graph, solution

def GGHotSpot(N: int, S: int, seed: int):
	nodes = HRG(N, seed=seed)
	edges = GEN(nodes)
	graph = Graph(edges=edges)
	graph.PrintGraph(f'./test/HOTSPOT/bpc_N_{N}_S_{S}_seed_{seed}_graph.csv')
	assert(type(graph) == Graph)
	with open(f'./test/HOTSPOT/bpc_N_{N}_S_{S}_seed_{seed}.log', 'w') as fnull:
		with contextlib.redirect_stdout(fnull):
			solution_bpc = BPC(graph, S)
	return graph, solution_bpc

def DrawNS(N: int|list, S: int|list, GG: str='UniRand'):
	variable = None
	assert(type(N) != type(S))
	if type(N) == int:
		variable = 'S'
		plt.title(f'N={N}')
	else:
		variable = 'N'
		plt.title(f'S={S}')
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
	plt.legend()
	plt.grid()
	plt.savefig(f'figs/MEAN_RANK__{GG}__N_{N}__S_{S}.svg')
	plt.show()

if __name__ == '__main__':
	# for N in range(20, 50):
	# 	DrawN(N)
	DrawNS(21, [4, 5, 6, 7, 8])
	# DrawNS([20, 25, 30, 35, 40, 45], 6)
	# DrawNS(21, [4, 5, 6, 7, 8], GG='HotSpot')
