#!/bin/python3
# vim:ts=2:sw=2:noet

import numpy
import itertools

class Graph2:
	def __init__(self) -> None:
		self.minEdge = 1
		self.maxEdge = 100
		self.N       = 100
		self.K       = 5
		self.Edges = []
		for i in range(self.N):
			for j in range(i, self.N):
				self.Edges.append(numpy.random.randint(self.minEdge, self.maxEdge))

	def GrabEdgeValue(self, i: int, j: int) -> int:
		assert(i != j)
		min_index = min(i, j)
		max_index = max(i, j)
		index = 0
		for _i in range(min_index):
			index += self.N - _i - 1
		index += max_index
		return self.Edges[index]

	def BruteForceCluster(self) -> list:
		division_list = []

		def dfs(vertex_division, index, max_division):
			if index == self.N:
				if max(vertex_division) != self.K:
					return
				division_list.append(vertex_division)
				return
			if max_division > self.K:
				return
			for division in range(1, max_division+1):
				vertex_division[index] = division
				if division == max_division:
					max_division += 1
				dfs(vertex_division, index + 1, max_division)

		dfs([0] * self.N, 0, 1)

		max_edge = self.maxEdge
		best_division = []
		for division in division_list:
			def searchmaxedge(division) -> int:
				vertex_set = []
				for i in range(self.K):
					vertex_set.append([])
				for i in range(self.N):
					vertex_set[division[i]-1].append(i)
				crit_edge = 0
				for s in vertex_set:
					for i in range(len(s) - 1):
						for j in range(i, len(s)):
							edge = self.GrabEdgeValue(i, j)
							if edge > crit_edge:
								crit_edge = edge
				return crit_edge
			division_crit_edge = searchmaxedge(division)
			if division_crit_edge < max_edge:
				max_edge = division_crit_edge
				best_division = division

		return best_division

	def GreedyCluster(self) -> None:
		vertex_list = list(range(self.N))
		max_circle_sum = 0
		max_circle = []
		for subset in itertools.permutations(vertex_list, self.K):
			subset = list(subset)
			edge_sum = 0
			for i in range(len(subset)):
				edge_sum += self.GrabEdgeValue(subset[i], subset[i+1])
				if edge_sum > max_circle_sum:
					max_circle = subset
					max_circle_sum = edge_sum

	def BranchPriceCut(self) -> None:
		def firstHeuristic():
			pass
		# 1. Initialize.
		# 2. Approximately solve the current LP relaxation using CPLEX.
		# 3. Generate columns using heuristic algorithms, if new columns are found goto 2.
		# 4. Check if any cutting planes can be generated, if yes, generate cutting planes and goto 2.
		# 5. Generate columns using an IP solver, if new columns are found goto 2.
		# 6. If the gap between the value of the LP relaxation and the value of the incumbent integer solution is sufficiently small, STOP with optimality.
		# 7. Try to improve the incumbent solution locally by switching vertices and move extra vertices around.
		# 8. Check if any cutting planes can be generated, if yes, generate cutting planes and goto 2.
		# 9. Branching.
		pass

class Graph:
	def __init__(self) -> None:
		self.N = int(input())
		self._K = int(input()) # related to the privacy protection and aggregation accuracy
		self.Graph = []
		for _ in range(self.N):
			self.Graph.append([0 for _ in range(self.N)])
		self.edgesum = 0
		for i in range(self.N):
			for j in range(self.N-i):
				edge = int(input())
				self.edgesum += edge
				self.Graph[i][j] = edge
				self.Graph[j][i] = edge

	def Cluster(self) -> None:
		blist = [False for _ in range(self.N)]
		clist = []
		for i in range(self.N):
			clist.append(set())
			clist[i].add(i)

		## clustering
		for i in range(self.N):
			if blist[i] == True:
				continue

			def ScoreIndex(v: int) -> int:
				ind = -1
				max_score = 0
				for i in range(len(clist)):
					clust = clist[i]
					score_a = len(clust) / self._K
					score_b = 0
					for neighbor in clust:
						score_b += self.Graph[v][neighbor]
					score_b /= self.edgesum
					if score_a * score_b > max_score:
						ind = i
						max_score = score_a * score_b
				return ind

if __name__ == '__main__':
	G = Graph()
