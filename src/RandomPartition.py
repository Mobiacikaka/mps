#!/bin/python3

from src.graph import Graph
import numpy

def RandomPartition(graph: Graph, S: int):
	n = graph.n
	vertices = list(range(n))
	clique_list: list[list] = []
	while len(vertices) >= S:
		clique = numpy.random.choice(vertices, size=S, replace=False).tolist()
		clique_list.append(clique)
		for v in clique:
			vertices.remove(v)

	while len(vertices) > 0:
		clique: list = clique_list[numpy.random.randint(low=0, high=len(clique_list))]
		clique.append(vertices[0])
		vertices.pop(0)

	solution = []
	for clique in clique_list:
		clique_one_hot = [0] * n
		for v in clique:
			clique_one_hot[v] = 1
		solution.append(clique_one_hot)
	return solution
