#!/bin/python3
import os
import multiprocessing
import time
from utils.GraphGenerator import HotspotRandomGenerator as HRG
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

def RunBPConHotSpot(N: int, S: int, c_nodes: int, seed: int):
	graph_filename = f'graph__N{N}__seed{seed}.csv'
	log_filename = f'bpc__N{N}__S{S}__seed{seed}.log'
	if os.path.exists(f'./test/HOTSPOT/log/{log_filename}'):
		logging(f'LOG FILE EXIST IN N {N} S {S} seed {seed}', runlog)
		return

	nodes = HRG(N=N, c_nodes=c_nodes, seed=seed)
	edges = GetEdgesFromNodes(nodes)
	graph = Graph(edges=edges)
	graph.PrintGraph(f'./test/HOTSPOT/graph/{graph_filename}')

	logging(f'RUNNING N {N} S {S} seed {seed}', runlog)
	with open(f'./test/HOTSPOT/log/{log_filename}', 'w') as flog:
		with contextlib.redirect_stdout(flog):
			BranchAndPrice(graph=graph, S=S, verbose=True)

def run():
	args = [
		(N, S, 4, seed)
		for N in range(20, 21)
		for S in range(4, 9)
		for seed in range(0, 10)
	]

	logging('TEST START', logfile=runlog, append=False)
	pool = multiprocessing.Pool(processes=8)
	pool.starmap(RunBPConHotSpot, args)
	pool.close()
	pool.join()

if __name__ == '__main__':
	runlog : str = 'run.log'
	run()
