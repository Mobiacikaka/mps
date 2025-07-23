#!/bin/python3

from graph import Graph

def GreedyPartition():
	S = int(input())

	graph = Graph()

	## Find the largest edge
	max_i, max_j = 0, 0
	max_edge = 0
	for i in range(graph.n-1):
		for j in range(i, graph.n):
			if graph.E[i][j] > max_edge:
				max_i, max_j = i, j
				max_edge = graph.E[i][j]

if __name__ == '__main__':
	GreedyPartition()
