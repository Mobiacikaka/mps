#!/bin/python3
import numpy, time
from BranchPriceCut import BranchAndPrice
from graph import Graph

if __name__ == '__main__':
	S = int(input())

	time_start = time.time()

	graph = Graph()
	BranchAndPrice(graph, S)

	time_end = time.time()
	print('Total Time: ', time_end - time_start)
