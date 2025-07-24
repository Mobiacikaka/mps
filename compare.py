#!/bin/python
import math, numpy
import matplotlib.pyplot as plt
import contextlib

from src.BranchPriceCut import BranchAndPrice as BPC
from src.RandomPartition import RandomPartition as RP
from src.GreedyPartition import GreedyPartition as GP
from src.graph import Graph
from utils.RandomGraph import RandomGraphGenerator2 as RGG2
from utils.analyzer import MaxEdgeRank as MER

def EuclideanDistance(vi: tuple[int, int], vj: tuple[int, int]):
	return math.sqrt(
		(vi[0] - vj[0])**2 + (vi[1] - vj[1]) ** 2
	)

def PrintNodes2Graph(points):
	x_vals = [p[0] for p in points]
	y_vals = [p[1] for p in points]

	plt.scatter(x_vals, y_vals, color='blue', marker='o')
	plt.xlabel("X")
	plt.ylabel("Y")
	plt.title("Point Set Visualization")
	plt.grid(True)
	plt.axis("equal")
	plt.show()

def PrintPartition(points, solution):
	x_vals = [p[0] for p in points]
	y_vals = [p[1] for p in points]

	plt.scatter(x_vals, y_vals, color='blue', marker='o')

	for sol in solution:
		clique = []
		for v in range(len(sol)):
			if sol[v]:
				clique.append(v)
		for i in range(len(clique)-1):
			for j in range(i, len(clique)):
				x_val = [points[clique[i]][0], points[clique[j]][0]]
				y_val = [points[clique[i]][1], points[clique[j]][1]]
				plt.plot(x_val, y_val, color='gray', linewidth=1, zorder=1)

	plt.xlabel("X")
	plt.ylabel("Y")
	plt.title("Undirected Graph with 2D Coordinates")
	plt.axis("equal")
	plt.grid(True)
	plt.show()

## 
def Compare3Algorithms(n: int, c_nodes: int, S: int, seed: int, GraphGenerator=RGG2):
	numpy.random.seed(seed)
	nodes = GraphGenerator(N=n, c_nodes=c_nodes)
	# PrintNodes2Graph(nodes)

	edges = [[0.0 for _ in range(n)] for _ in range(n)]
	for i in range(n-1):
		for j in range(i+1, n):
			edges[i][j] = edges[j][i] = EuclideanDistance(nodes[i], nodes[j])

	G = Graph(edges)

	solution_rp = RP(G, S)
	solution_gp = GP(G, S)
	with open('/dev/null', 'w') as fnull:
		with contextlib.redirect_stdout(fnull):
			solution_bpc = BPC(G, S)

	# print(solution_rp, solution_gp, solution_bpc, sep='\n\n')
	PrintPartition(nodes, solution_rp)
	PrintPartition(nodes, solution_gp)
	PrintPartition(nodes, solution_bpc)

	return MER(G, solution_rp), MER(G, solution_gp), MER(G, solution_bpc)
