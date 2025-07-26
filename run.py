#!/bin/python3
import os
import multiprocessing
import time
from utils.GraphGenerator import HotspotRandomGenerator as HRG
from utils.GraphGenerator import UniformRandomGenerator as URG
from utils.GraphGenerator import GetEdgesFromNodes
from src.graph import Graph
from src.BranchPriceCut import BranchAndPrice
import contextlib

def logging(content: str, logfile: str, append: bool=True):
	current_time = time.strftime("%H:%M:%S")
	if not append:
		os.system(f'echo [{current_time}]\t{content} > {logfile}')
	else:
		os.system(f'echo [{current_time}]\t{content} >> {logfile}')
	return

def RunBPC(N: int, S: int, c_nodes: int, seed: int):
	graph_filename = f'graph__N{N}__seed{seed}.csv'
	log_filename = f'bpc__N{N}__S{S}__seed{seed}.log'
	if os.path.exists(f'./test/{test_folder}/log/{log_filename}'):
		logging(f'LOG FILE EXIST IN N {N} S {S} seed {seed}', runlog)
		return

	nodes = test_GG(N=N, seed=seed)
	edges = GetEdgesFromNodes(nodes)
	graph = Graph(edges=edges)
	graph.PrintGraph(f'./test/{test_folder}/graph/{graph_filename}')

	logging(f'RUNNING N {N} S {S} seed {seed}', runlog)
	with open(f'./test/{test_folder}/log/{log_filename}', 'w') as flog:
		with contextlib.redirect_stdout(flog):
			BranchAndPrice(graph=graph, S=S, verbose=True)

def run():
	args = [
		(N, S, 4, seed)
		for N in range(20, 50)
		for S in range(4, 9)
		for seed in range(0, 10)
	]

	logging('TEST START', logfile=runlog, append=False)
	pool = multiprocessing.Pool(processes=multiprocessing.cpu_count()//2)
	pool.starmap(RunBPC, args)
	pool.close()
	pool.join()

if __name__ == '__main__':
	test_folder = 'RANDOM'
	test_GG = URG
	runlog : str = 'run.log'
	run()
