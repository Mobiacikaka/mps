import numpy


class Graph:
	def __init__(self, n: int) -> None:
		self.n = n
		self.V, self.a, self.E = self.__createGraph__(self.n)

	## Random create edges
	def __createGraph__(self, n: int):
		## vertex
		V = [i for i in range(n)]
		## vertex weight
		a = [1] * n
		## edges
		E = [ [ 0.0 for _ in range(n) ] for _ in range(n) ]
		for i in range(n-1):
			for j in range(i+1, n):
				E[i][j] = E[j][i] = float(numpy.random.randint(100) + 1)
		return V, a, E

	def SortEdge(self) -> None:
		EdgeName = [(i,j) for i in range(self.n-1) for j in range(i+1, self.n)]
		EdgeName = sorted(EdgeName, key=lambda x: self.E[x[0]][x[1]], reverse=True)
		self.EdgeValue = self.E
		for k in range(len(EdgeName)):
			i = EdgeName[k][0]
			j = EdgeName[k][1]
			self.E[i][j] = self.E[j][i] = 0.5**(k-20)

	def Weight(self, subgraph: list=[]) -> int:
		if len(subgraph) == 0:
			subgraph = [1] * self.n
		return sum(
			[self.E[i][j] * subgraph[i] * subgraph[j]
			for i in range(self.n-1) for j in range(i+1, self.n)]
		)

	def PrintGraph(self):
		for v in self.V:
			print(str(v), end='\t')
		print('\nEdges:')
		for edges in self.E:
			for edge in edges:
				print(str(edge), end='\t')
			print()
		print()

