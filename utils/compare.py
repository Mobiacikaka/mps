#!/bin/python
import numpy
import matplotlib.pyplot as plt
import contextlib

from src.BranchPriceCut import BranchAndPrice as BPC
from src.RandomPartition import RandomPartition as RP
from src.GreedyPartition import GreedyPartition as GP
from src.graph import Graph
from utils.GraphGenerator import HotspotRandomGenerator as HRG
from utils.GraphGenerator import GetEdgesFromNodes
from utils.analyzer import MaxEdgeRank as MER
from utils.random_instance_analyzer import ReadFolder as ReadBPCFolder

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

def DrawPartition(points, solution):
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

## take graph and S as input, output the rank of the max edge
def Compare3Algorithms(
	graph      : Graph,
	S          : int,
	verbose    : bool=True,
):
	G = graph
	nodes = graph.nodes

	## no stdout output
	with open('/dev/null', 'w') as fnull:
		with contextlib.redirect_stdout(fnull):
			solution_rp = RP(G, S)
			solution_gp = GP(G, S)
			solution_bpc = BPC(G, S)

	# print(solution_rp, solution_gp, solution_bpc, sep='\n\n')
	if verbose:
		DrawPartition(nodes, solution_rp)
		DrawPartition(nodes, solution_gp)
		DrawPartition(nodes, solution_bpc)

	return MER(G, solution_rp), MER(G, solution_gp), MER(G, solution_bpc)
