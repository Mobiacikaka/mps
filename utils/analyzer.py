#!/bin/python3

from src.graph import Graph

def UnfoldSolution(solution_list: list, collapsed_comb: list) -> list:
	for solution in solution_list:
		for i in range(len(collapsed_comb), 0, -1):
			x, y = collapsed_comb[i-1]
			solution.insert(y, solution[x])
	return solution_list

def MaxWeight(graph: Graph, partition: list):
	maxEdge = 0
	for clique in partition:
		vlist = []
		for v in range(graph.n):
			if clique[v]:
				vlist.append(v)
		clique_size = len(vlist)
		for i in range(clique_size - 1):
			for j in range(i, clique_size):
				if graph.Edges[vlist[i]][vlist[j]] > maxEdge:
					maxEdge = graph.Edges[vlist[i]][vlist[j]]
	return maxEdge

def MinimumPossibleRankInTheory(N: int, S: int):
	def numEdge(numV: int):
		return int(numV * (numV-1) // 2)

	K = N // S
	VnumList = [S] * K
	for i in range(N % S):
		lindex = i % len(VnumList)
		VnumList[lindex] += 1

	Enum = 0
	for numV in VnumList:
		Enum += numEdge(numV)
	return Enum

def EdgeInPartiton(partition: list, edge: tuple):
	for clique in partition:
		try:
			if clique[edge[0]] + clique[edge[1]] == 2:
				return True
			if clique[edge[0]] + clique[edge[1]] == 1:
				return False
		except:
			print(clique, edge)
			assert(0)
	## The two circumstances above is all, nothing else we can get
	assert(0)

def MaxEdgeRank(graph: Graph, partition: list):
	## Edge Name sorted from largest to smallest by weight
	sortedEdgeName = graph.sortedEdgeName
	rank = len(sortedEdgeName)
	for edge in sortedEdgeName:
		if EdgeInPartiton(partition, edge):
			break
		rank -= 1
	return rank
