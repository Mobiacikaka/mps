#!/bin/python3
# vim:ts=2:sw=2:noet
import itertools
import numpy, math
import gurobipy
from gurobipy import GRB
import colorama

############
## CPPMIN ##
############

class graph:
	def __init__(self, n: int) -> None:
		self.n = n
		self.V, self.a, self.E = self.__createGraph__(self.n)
		self.__printGraph__()
		# self.__sortEdge__()
		# self.__printGraph__()

	def __sortEdge__(self) -> None:
		EdgeName = [(i,j) for i in range(self.n-1) for j in range(i+1, self.n)]
		EdgeName = sorted(EdgeName, key=lambda x: self.E[x[0]][x[1]], reverse=True)
		self.EdgeValue = self.E
		for k in range(len(EdgeName)):
			i = EdgeName[k][0]
			j = EdgeName[k][1]
			self.E[i][j] = self.E[j][i] = 0.5**(k-20)

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
		E = [ [ 0.0 for _ in range(n) ] for _ in range(n) ]
		for i in range(n-1):
			for j in range(i+1, n):
				E[i][j] = E[j][i] = float(numpy.random.randint(100) + 1)
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

class SUB:
	def __init__(self, G: graph, S: int) -> None:
		self.G = G
		self.S = S

	def create_model(self) -> None:
		self.model = gurobipy.Model('sub model')
		self.y = self.model.addVars(self.G.n, vtype=GRB.BINARY, name='y')
		self.z = []
		for i in range(self.G.n-1):
			zz = []
			for j in range(i+1, self.G.n):
				zz.append(self.model.addVar(vtype=GRB.CONTINUOUS, lb=0, name=f'z{i},{j}'))
			self.z.append(zz)

		self.model.addConstr( (gurobipy.quicksum(self.G.a[i] * self.y[i] for i in range(self.G.n)) >= self.S) )
		for i in range(self.G.n-1):
			for j in range(i+1, self.G.n):
				self.model.addConstr(self.z[i][j-i-1] >= self.y[i] + self.y[j] - 1)

	def set_objective(self, pi: list):
		self.model.setObjective(
			- gurobipy.quicksum(pi[i] * self.y[i] for i in range(self.G.n))
			+ gurobipy.quicksum( (self.G.E[i][j] * self.z[i][j-i-1]) for i in range(self.G.n-1) for j in range(i+1, self.G.n) )
			, sense=GRB.MINIMIZE
		)

	def solve(self, flag=0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()

	def get_solution(self):
		return [int(self.model.getVars()[i].X) for i in range(self.G.n)]

	def get_reduced_cost(self):
		return self.model.ObjVal

	def write(self):
		self.model.write('sub_model.lp')

class MLP:
	def __init__(self, G: graph, S: int) -> None:
		self.G = G
		self.S = S
		self.n_col = 0 ##
		self.n_dim = 0 ## 变量数量

	def create_model(self):
		self.x = []
		self.model = gurobipy.Model('Master')
		self.__set_vars()
		self.__set_contrs()

	def solve(self, flag = 0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()

	def get_dual_vars(self):
		pi = [self.constrs[i].getAttr(GRB.Attr.Pi) for i in range(len(self.constrs))]
		sigma = self.constrs2.getAttr(GRB.Attr.Pi)
		return pi, sigma

	def __set_contrs(self) -> None:
		self.constrs = self.model.addConstrs(
			gurobipy.quicksum( self.x[i] for i in range(len(self.x)) ) == 1 for _ in range(self.G.n)
		)
		self.constrs2 = self.model.addConstr(
			gurobipy.quicksum( self.x[i] for i in range(len(self.x)) ) <= math.floor(self.G.n / self.S)
		)

	def __set_vars(self) -> None:
		self.x.append(self.model.addVar(obj=self.G.weight(), lb=0, vtype=GRB.CONTINUOUS, name='x0'))
		self.n_dim = 1
		self.n_col = 1
		self.columns = [[1] * self.G.n]

	def update_contrs(self, column_coeff: list):
		column_coeff.append(1)
		column = gurobipy.Column(column_coeff, self.model.getConstrs())

		## same column assertion
		assert(column_coeff not in self.columns), "Generated a same column"
		self.columns.append(column_coeff)

		self.model.addVar(
			obj=self.G.weight(column_coeff),
			lb=0,
			vtype=GRB.CONTINUOUS,
			name='x'+str(self.n_dim),
			column=column
		)
		self.n_dim += 1
		self.n_col += 1

	def print_status(self):
		print('master objective value: {}'.format(self.model.ObjVal))

	def to_int(self):
		for x in self.model.getVars():
			x.setAttr('VType', GRB.BINARY)

	def write(self, filename='model.lp'):
		self.model.write(filename)

def solve():
	## number of vertex
	n = 29
	## least number of cluster
	S = 7
	G = graph(n)

	cppmin = MLP(G, S)
	cppmin.create_model()
	sub_prob = SUB(G, S)
	sub_prob.create_model()
	PI = []

	while True:
		## 2: Approximately solve the current LP relaxation using CPLEX
		cppmin.solve()
		cppmin.write()
		if cppmin.model.Status == GRB.INFEASIBLE:
			print('INFEASIBLE')
			exit()

		## 5: Generate columns using an IP solver, if new columns are found goto 2
		pi, sigma = cppmin.get_dual_vars()
		# print('pi', pi, 'sigma', sigma)
		assert(pi not in PI), 'Generated a same pi'
		PI.append(pi)

		sub_prob.set_objective(pi)
		sub_prob.solve()
		sub_prob.write()

		## 6: If the gap between the value of the LP relaxation and the value of the incumbent integer solution is sufficiently small, STOP with optimality
		y = sub_prob.get_solution()
		print('Generate Column: ', y)
		reduced_cost = sub_prob.get_reduced_cost()
		print('reduced_cost-sigma: ', reduced_cost-sigma)

		# if reduced_cost >= sigma - 1e-6:
		if reduced_cost - sigma >= 0:
			break

		cppmin.update_contrs(column_coeff=y)

	cppmin.to_int()
	cppmin.solve(flag=1)
	cppmin.write()
	for x in cppmin.model.getVars():
		if x.X == 1.0:
			print(x.VarName, '\t:\t', cppmin.model.getCol(x))

if __name__ == '__main__':
	# numpy.random.seed(0)
	solve()
