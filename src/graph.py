import copy
from utils.GraphGenerator import GetEdgesFromNodes

class Graph:
	def __init__(self, edges: list=[], nodes: list=[],) -> None:
		self.nodes = nodes
		self.E = edges
		if len(edges) == 0:
			if len(nodes) != 0:
				self.E = GetEdgesFromNodes(self.nodes)
			else:
				self.E = self.ReadGraphFromFile()
		self.n = len(self.E)
		self.V = [i for i in range(self.n)]
		self.a = [1 for _ in range(self.n)]
		self.SortEdge()
		self.InnerEdge = [0.0 for _ in range(self.n)]

	## Read From File
	def CreateGraph(self):
		self.V = [i for i in range(self.n)]
		self.a = [1 for _ in range(self.n)]
		self.E = self.ReadGraphFromFile()
		self.SortEdge()
		self.InnerEdge = [0.0 for _ in range(self.n)]

	def ReadGraphFromFile(self, filename: str = 'graph.csv'):
		## graph.txt format
		## edge,edge,...,edge,
		## edge,edge,...,edge,
		## ....,....,...,....,
		## edge,edge,...,edge,
		file = open(filename, 'r')
		lines: list[str] = [line.strip(',\n') for line in file.readlines()]
		edges: list[list[float]] = []
		for line in lines:
			edges.append([float(edge) for edge in line.split(',')])
		return edges

	def SortEdge(self) -> None:
		EdgeName = [(i,j) for i in range(self.n-1) for j in range(i+1, self.n)]
		EdgeName = sorted(EdgeName, key=lambda x: self.E[x[0]][x[1]], reverse=True)
		self.sortedEdgeName = EdgeName
		## Edges with original values
		self.Edges= copy.deepcopy(self.E)
		for k in range(len(EdgeName)):
			i = EdgeName[k][0]
			j = EdgeName[k][1]
			self.E[i][j] = self.E[j][i] = 0.5**(k-20)

	def Size(self, subgraph: list=[]) -> int:
		assert(len(subgraph) == self.n)
		s = 0
		for i in range(self.n):
			if subgraph[i] == 1:
				s += self.a[i]
		return s

	## subgraph consist of only 0 and 1
	def Weight(self, subgraph: list=[]) -> float:
		if len(subgraph) == 0:
			subgraph = [1] * self.n
		cluster = [i for i in range(self.n) if subgraph[i]]
		return self.__weight(cluster)

	## subgraph consist of number less than n
	def __weight(self, subgraph: list) -> float:
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
		for edges in self.Edges:
			for edge in edges:
				f.write(str(edge)+',')
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
