import numpy

class Graph:
	def __init__(self, n: int) -> None:
		self.n = n
		self.V = []
		self.a = []
		self.E = []
		self.CreateGraph()

	## Random create edges
	def CreateGraph(self):
		## vertex
		self.V = [i for i in range(self.n)]
		## vertex weight
		self.a = [1] * self.n
		## edges
		self.E = [ [ 0.0 for _ in range(self.n) ] for _ in range(self.n) ]
		for i in range(self.n-1):
			for j in range(i+1, self.n):
				self.E[i][j] = self.E[j][i] = float(numpy.random.randint(100) + 1)
		self.InnerEdge = [0.0 for _ in range(self.n)]
		return

	def SortEdge(self) -> None:
		EdgeName = [(i,j) for i in range(self.n-1) for j in range(i+1, self.n)]
		EdgeName = sorted(EdgeName, key=lambda x: self.E[x[0]][x[1]], reverse=True)
		self.EdgeValue = self.E
		for k in range(len(EdgeName)):
			i = EdgeName[k][0]
			j = EdgeName[k][1]
			self.E[i][j] = self.E[j][i] = 0.5**(k-20)

	## subgraph consist of only 0 and 1
	def Weight(self, subgraph: list=[]) -> float:
		if len(subgraph) == 0:
			subgraph = [1] * self.n
		cluster = [i for i in range(self.n) if subgraph[i]]
		return self.weight(cluster)

	## subgraph consist of number less than n
	def weight(self, subgraph: list) -> float:
		length = len(subgraph)
		s = 0
		for i in range(length-1):
			for j in range(i+1, length):
				vi = subgraph[i]
				vj = subgraph[j]
				s += self.E[vi][vj]
		for v in subgraph:
			s += self.InnerEdge[v]
		return s

	def PrintGraph(self, filename: str='Graph.txt'):
		f = open(filename, 'w')
		for edges in self.E:
			for edge in edges:
				f.write(str(edge)+' \t')
			f.write('\n')

	def Divide(self, i: int, j: int):
		assert(i <= self.n and j <= self.n)
		self.E[i][j] = self.E[j][i] = 2**20

	def Collapse(self, i: int, j: int):
		assert(i < j)

		## add the weight of two vertex
		self.a[i] += self.a[j]
		self.a.pop(j)

		## set Vij's inner edge value to insure correctness of cluster's weight
		self.InnerEdge[i] += self.InnerEdge[j] + self.E[i][j]
		self.InnerEdge.pop(j)

		## remove edges
		for k in range(self.n):
			if k == i or k == j:
				continue
			self.E[k][i] = self.E[i][k] = self.E[i][k] + self.E[j][k]
		for k in range(self.n):
			self.E[k].pop(j)
		self.E.pop(j)

		## remove vertex
		self.n -= 1
		self.V = list(range(self.n))
