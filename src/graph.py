import numpy
import itertools

class Graph:
	def __init__(self, n: int) -> None:
		self.n = n
		self.V, self.a, self.E = self.__createGraph__(self.n)
		self.closest_vertex = [
			sorted(self.V, key=lambda x: self.E[i][x])
			for i in range(self.n)
		]

	def GenerateCandidateColumns(self, S: int):
		self.candidate_columns = []
		for i in range(self.n):
			candidate_columns_i = []
			closest_vertex = sorted(self.V, key=lambda x: self.E[i][x])[:2*S]
			for size in range(S, S*2):
				for cluster in itertools.combinations(closest_vertex, size):
					column = [int(i in cluster) for i in range(self.n)]
					candidate_columns_i.append(column)
			self.candidate_columns.append(candidate_columns_i)

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

	def PrintGraph(self, filename: str='Graph.txt'):
		f = open(filename, 'w')
		for edges in self.E:
			for edge in edges:
				f.write(str(edge)+'\t')
			f.write('\n')

	def Divide(self, i: int, j: int):
		assert(i <= self.n and j <= self.n)
		self.E[i][j] = self.E[j][i] = 2**20

	def Collapse(self, i: int, j: int):
		## pop V[j]
		self.V.pop(j)
		## add the weight of two vertex
		self.a[i] += self.a[j]
		self.a.pop(j)
		## remove edges
		for k in range(self.n):
			self.E[i][k] = self.E[i][k] + self.E[i][j] + self.E[j][k]
			self.E[k][i] = self.E[i][k]
		for k in range(self.n):
			self.E[k].pop(j)
		self.E.pop(j)
		self.n -= 1
