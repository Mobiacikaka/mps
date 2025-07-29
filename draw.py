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
import math

plt.rcParams.update({
    # 'font.family': 'Times New Roman',  # 使用 Times 字体
    'font.size': 18,                   # 设置为 10pt（与正文一致）
    'axes.labelsize': 18,
    'axes.titlesize': 18,
    'xtick.labelsize': 14,
    'ytick.labelsize': 14,
    'legend.fontsize': 16,
    'figure.dpi': 300,                 # 高分辨率图适合打印和论文
    'savefig.dpi': 300,
    'pdf.fonttype': 42,                # 使 PDF 可嵌入文本字体（非路径）
    'ps.fonttype': 42
})

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
		assert(0) ## File not exists, do not run again
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
	print(f'Drawing figs/MEAN_RANK__{GG}__{title}.svg')

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

	plt.plot(x_val, rp_val, marker='s', linestyle='--', color='green', label='RP')
	plt.plot(x_val, gp_val, marker='^', linestyle='-.', color='red', label='GP')
	plt.plot(x_val, bpc_val, marker='o', linestyle='-', color='blue', label='BPC')
	# plt.ylim(120, 220)
	# plt.ylim(500, 1200)
	plt.ylim(100, 1200)
	plt.xlabel(variable)
	plt.ylabel('Average Rank')
	# plt.title(title)
	plt.legend(loc='lower right', ncol=3, fontsize=14)
	plt.grid()
	plt.savefig(f'figs/MEAN_RANK__{GG}__{title}.eps')
	# plt.show()
	plt.clf()

### HIST
def DrawRuntimeCount():
	N_list = list(range(20, 50))
	S_list = [4, 5, 6, 7, 8]
	seed_list = list(range(0, 10))
	runtime_list_unirand = []
	runtime_list_hotspot = []
	for N in N_list:
		for S in S_list:
			for seed in seed_list:
				try:
					log_filename = f'./test/RANDOM/S_{S}/N_{N}/{seed}/BranchAndPrice.log'
					data = ReadLogFile(log_filename)
					assert(data != None)
					runtime = data['time']
					runtime_list_unirand.append(runtime)
				except:
					traceback.print_exc()
					print(f'UNIFORM N{N} S{S} seed{seed} NOT GOOD!')
				try:
					log_filename = f'./test/HOTSPOT/log/bpc__N{N}__S{S}__seed{seed}.log'
					data = ReadLogFile(log_filename)
					assert(data != None)
					runtime = data['time']
					runtime_list_hotspot.append(runtime)
				except:
					traceback.print_exc()
					print(f'HOTSPOT N{N} S{S} seed{seed} NOT GOOD!')
	
	hist_length = 4
	hist_uni = [0] * hist_length
	hist_hot = [0] * hist_length
	for runtime in runtime_list_unirand:
		idx = math.floor(math.log10(runtime+1))
		assert(0 <= idx < 10)
		if idx >= hist_length:
			continue
		hist_uni[idx] += 1
	for runtime in runtime_list_hotspot:
		idx = math.floor(math.log10(runtime+1))
		assert(0 <= idx < 10)
		if idx >= hist_length:
			continue
		hist_hot[idx] += 1
	
	labels = ['0–1s', '1–10s', '10–100s', '100–1000s']
	x = numpy.arange(len(labels))
	width = 0.35

	fig, ax = plt.subplots()
	bar1 = ax.bar(x - width/2, hist_uni, width, label='Uniform', color='#1f77b4', hatch='/', edgecolor='black', linewidth=1.0)
	bar2 = ax.bar(x + width/2, hist_hot, width, label='Hotspot', color='#ff7f0e', hatch='\\', edgecolor='black', linewidth=1.0)
	ax.set_xlabel('Running Time Range')
	ax.set_ylabel('Count')
	# ax.set_title('Grouped Bar Chart Example')
	ax.set_xticks(x)
	ax.set_xticklabels(labels)
	ax.legend()
	plt.savefig(f'figs/RUNTIME_COUNT.eps', bbox_inches='tight')
	plt.show()
	plt.clf()

### PLOT
def DrawRuntimeN(N: int|list, S: int|list, GG: str):
	assert(type(N) != type(S))
	assert(GG == 'UniRand' or GG == 'HotSpot')

	N_list = list(range(20, 50))
	S_list = list(range(4, 9))
	seed_list = list(range(0, 10))

	runtime_list_unirand = [0] * len(N_list)
	runtime_list_unirand_count = [0] * len(N_list)
	runtime_list_hotspot = [0] * len(N_list)
	runtime_list_hotspot_count = [0] * len(N_list)
	for N in N_list:
		for S in S_list:
			for seed in seed_list:
				try:
					log_filename = f'./test/RANDOM/S_{S}/N_{N}/{seed}/BranchAndPrice.log'
					data = ReadLogFile(log_filename)
					assert(data != None)
					runtime = data['time']
					runtime_list_unirand[N-20] += runtime
					runtime_list_unirand_count[N-20] += 1
				except:
					traceback.print_exc()
					print(f'UNIFORM N{N} S{S} seed{seed} NOT GOOD!')
				try:
					log_filename = f'./test/HOTSPOT/log/bpc__N{N}__S{S}__seed{seed}.log'
					data = ReadLogFile(log_filename)
					assert(data != None)
					runtime = data['time']
					runtime_list_hotspot[N-20] += runtime
					runtime_list_hotspot_count[N-20] += 1
				except:
					traceback.print_exc()
					print(f'UNIFORM N{N} S{S} seed{seed} NOT GOOD!')

	x = list(range(20, 50))
	y1 = [runtime_list_unirand[i] / runtime_list_unirand_count[i] for i in range(30)]
	y2 = [runtime_list_hotspot[i] / runtime_list_hotspot_count[i] for i in range(30)]
	plt.plot(x, y1, marker='o', linestyle='-', color='#1f77b4', label='Uniform')
	plt.plot(x, y2, marker='s', linestyle='--', color='#ff7f0e', label='Hotspot')
	plt.xlabel('N')
	plt.ylabel('Runtime(s)')
	plt.grid()
	plt.legend()
	plt.tight_layout()
	plt.savefig('figs/RUNTIME__N.eps', bbox_inches='tight')
	plt.show()
	plt.clf()

### PLOT
def DrawRuntimeS(N: int|list, S: int|list, GG: str):
	assert(type(N) != type(S))
	assert(GG == 'UniRand' or GG == 'HotSpot')

	N_list = list(range(20, 50))
	S_list = list(range(4, 9))
	seed_list = list(range(0, 10))

	runtime_list_unirand = [0] * len(S_list)
	runtime_list_unirand_count = [0] * len(S_list)
	runtime_list_hotspot = [0] * len(S_list)
	runtime_list_hotspot_count = [0] * len(S_list)
	for S in S_list:
		for N in N_list:
			for seed in seed_list:
				try:
					log_filename = f'./test/RANDOM/S_{S}/N_{N}/{seed}/BranchAndPrice.log'
					data = ReadLogFile(log_filename)
					assert(data != None)
					runtime = data['time']
					runtime_list_unirand[S-4] += runtime
					runtime_list_unirand_count[S-4] += 1
				except:
					traceback.print_exc()
					print(f'UNIFORM N{N} S{S} seed{seed} NOT GOOD!')
				try:
					log_filename = f'./test/HOTSPOT/log/bpc__N{N}__S{S}__seed{seed}.log'
					data = ReadLogFile(log_filename)
					assert(data != None)
					runtime = data['time']
					runtime_list_hotspot[S-4] += runtime
					runtime_list_hotspot_count[S-4] += 1
				except:
					traceback.print_exc()
					print(f'UNIFORM N{N} S{S} seed{seed} NOT GOOD!')

	x = S_list
	y1 = [runtime_list_unirand[i] / runtime_list_unirand_count[i] for i in range(len(S_list))]
	y2 = [runtime_list_hotspot[i] / runtime_list_hotspot_count[i] for i in range(len(S_list))]
	plt.plot(x, y1, marker='o', linestyle='-', color='#1f77b4', label='Uniform')
	plt.plot(x, y2, marker='s', linestyle='--', color='#ff7f0e', label='Hotspot')
	plt.xlabel('S')
	plt.ylabel('Runtime(s)')
	plt.grid()
	plt.legend()
	plt.tight_layout()
	plt.savefig('figs/RUNTIME__S.eps', bbox_inches='tight')
	plt.show()
	plt.clf()

if __name__ == '__main__':
	S_list = [4, 5, 6, 7, 8]
	N_list = list(range(20, 50))
	# for N in N_list:
	# 	DrawNS(N=N, S=S_list, GG='UniRand')
	# for S in S_list:
	# 	DrawNS(N=N_list, S=S, GG='UniRand')

	# DrawNS(N=N_list, S=4, GG='UniRand')
	# DrawNS(N=N_list, S=4, GG='HotSpot')
	# DrawNS(N=N_list, S=8, GG='UniRand')
	# DrawNS(N=N_list, S=8, GG='HotSpot')

	DrawRuntimeCount()
	DrawRuntimeN(20, S_list, 'UniRand')
	DrawRuntimeS(20, S_list, 'UniRand')
