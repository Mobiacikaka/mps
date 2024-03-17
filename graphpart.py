#!/bin/python3
# vim:ts=2:sw=2:noet

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
