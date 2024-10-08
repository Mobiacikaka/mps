#!/bin/python3
# vim:ts=2:sw=2:noet
import itertools
import numpy
import gurobipy
from gurobipy import GRB, gurobi
import bisect

############
## CPPMIN ##
############

def subset(A: list, B: list) -> bool:
	a = set(A)
	b = set(B)
	return a.issubset(b)

def union(A: list, B: list) -> list:
	a = set(A)
	b = set(B)
	c = a.union(b)
	return list(c)

class graph:
	def __init__(self, n: int) -> None:
		self.n = n
		self.V, self.a, self.E = self.__createGraph__(self.n)
		self.__printGraph__()

	def weight(self, subgraph: list=[]) -> int:
		if len(subgraph) == 0:
			subgraph = [1] * self.n
		return sum(
			[self.E[i][j] * subgraph[i] * subgraph[j]
			for i in range(self.n-1) for j in range(i+1, self.n)]
		)

	## Random create edges
	def __createGraph__(self, n: int):
		## vertex
		V = [i for i in range(n)]
		## vertex weight
		a = [1] * n
		## edges
		E = [ [ 0 for _ in range(n) ] for _ in range(n) ]
		for i in range(n-1):
			for j in range(i+1, n):
				E[i][j] = numpy.random.randint(100) + 1
				E[j][i] = E[i][j]
		return V, a, E

	def __printGraph__(self):
		for v in self.V:
			print(str(v), end='\t')
		print('\nEdges:')
		for edges in self.E:
			for edge in edges:
				print(str(edge), end='\t')
			print()
		print()

class CPPMINSub:
	def __init__(self, G: graph, S: int) -> None:
		self.G = G
		self.S = S

	def create_model(self) -> None:
		self.model = gurobipy.Model("sub model")
		self.y = self.model.addVars(self.G.n, lb=0, ub=1, vtype=GRB.INTEGER, name='y')
		self.model.addConstr( (gurobipy.quicksum(self.G.a[i] * self.y[i] for i in range(self.G.n)) >= self.S) )

	def weight(self, subgraph):
		return gurobipy.quicksum( (self.G.E[i][j] * subgraph[i] * subgraph[j]) for i in range(self.G.n-1) for j in range(i+1, self.G.n) )

	def set_objective(self, pi: list):
		self.model.setObjective(
			- gurobipy.quicksum(pi[i] * self.y[i] for i in range(self.G.n))
			+ self.weight(self.y)
			, sense=GRB.MINIMIZE
		)

	def solve(self, flag=0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()

	def get_solution(self):
		return [self.model.getVars()[i].x for i in range(self.G.n)]

	def get_reduced_cost(self):
		return self.model.ObjVal

	def write(self):
		self.model.write('sub_model.lp')

class MLP:
	def __init__(self, G: graph, P: list, S: int) -> None:
		self.G = G
		self.S = S

	def create_model(self):
		self.x = []
		self.model = gurobipy.Model("Master")
		self.__set_vars()
		self.__set_contrs()

	def solve(self, flag = 0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()

	def get_dual_vars(self):
		pi = [self.constrs[i].getAttr(GRB.Attr.Pi) for i in range(len(self.constrs))]
		return pi

	def __set_contrs(self) -> None:
		self.constrs = self.model.addConstrs(
			gurobipy.quicksum( self.x[i] for i in range(len(self.x)) ) == 1 for _ in range(self.G.n)
		)

	def __set_vars(self) -> None:
		self.x.append(self.model.addVar(obj=self.G.weight(), lb=0, ub=1, vtype=GRB.CONTINUOUS, name='x0'))
		self.n_dim = len(self.x)
		self.n_col = 1

	def update_contrs(self, column_coeff):
		self.column = gurobipy.Column(column_coeff, self.model.getConstrs())
		self.model.addVar(
			vtype=GRB.CONTINUOUS, lb=0,
			obj=self.G.weight(column_coeff),
			name='x'+str(self.n_dim), column=self.column
		)
		self.n_dim += 1
		self.n_col += 1

	def print_status(self):
		print("master objective value: {}".format(self.model.ObjVal))

	def to_int(self):
		for x in self.model.getVars():
			x.setAttr("VType", GRB.INTEGER)

	def write(self):
		self.model.write("model.lp")

def solve():
	MAX_ITER_TIMES = 100

	n = 10 ## number of vertex
	S = 3  ## least number of cluster
	G = graph(n)
	P = []
	for i in range(S, n-S+1):
		P += list(itertools.combinations(G.V, i))
	P = [G.V] + P

	# cppmin = CPPMINMaster(len(P), S, P, w, G)
	cppmin = MLP(G, P, S)
	cppmin.create_model()
	sub_prob = CPPMINSub(S=S, G=G)
	sub_prob.create_model()

	for i in range(MAX_ITER_TIMES):
		cppmin.solve()
		pi = cppmin.get_dual_vars()
		cppmin.write()

		sub_prob.set_objective(pi)
		sub_prob.solve()
		y = sub_prob.get_solution()
		reduced_cost = sub_prob.get_reduced_cost()
		sub_prob.write()
		cppmin.update_contrs(column_coeff=y)
		if reduced_cost >= 0:
			break

	cppmin.to_int()
	cppmin.solve(flag=1)

if __name__ == '__main__':
	solve()
