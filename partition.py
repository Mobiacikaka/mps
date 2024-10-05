#!/bin/python3
# vim:ts=2:sw=2:noet
import itertools
import numpy
import gurobipy
from gurobipy import GRB
import bisect

############
## CPPMIN ##
############

class graph:
	def __init__(self, n: int) -> None:
		self.n = n
		self.V, self.a, self.E = self.__createGraph__(self.n)
		# self.__printGraph__()
		# assert(0)

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
		print()
		for edges in self.E:
			for edge in edges:
				print(str(edge), end='\t')
			print()
		print()

class CPPMINMaster:
	def __init__(self, N: int, S: int, P: list[list[int]], w: list[int], G) -> None:
		self.N = N # 变量数量 - 簇的总数量，即len(P)
		self.S = S # 簇最小要拥有S个结点
		self.w = w # 在目标函数中变量的权重，类型为数组，长度为N，每个值代表了簇中边的权值，即$w_P = \sum_{e\in E(P)} w_e$
		self.P = P # 簇列表
		self.M = len(self.P)
		self.G = G

	def __set_vars(self) -> None:
		for i in range(self.M):
			# obj: 指在目标函数中变量的权重
			self.x.append(self.model.addVar(obj=self.w[i], lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name='x'+str(i)))
		self.n_col = 1
		self.n_dim = self.N

	def __set_contrs(self):
		# self.constrs = []
		# for v in range(self.N):
		# 	self.constrs.append( (self.x[i] * int(v in self.P[i])) == 1 for i in range(self.M) )
		self.constrs = self.model.addConstrs((gurobipy.quicksum(self.x[p] * int(self.G.V[i] in self.P[p]) for p in range(self.N)) == 1) for i in range(self.G.n))

	def create_model(self):
		self.x = []
		self.model = gurobipy.Model("Master")
		self.__set_vars()
		self.__set_contrs()

	def set_objective(self):
		pass

	def solve(self, flag = 0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()

	def get_dual_vars(self):
		return [self.constrs[i].getAttr(gurobipy.GRB.Attr.Pi) for i in range(len(self.constrs))]

	def update_contrs(self, column_coeff):
		self.column = gurobipy.Column(column_coeff, self.model.getConstrs())
		self.model.addVar(vtype=gurobipy.GRB.CONTINUOUS, lb=0, obj=1, name='x'+str(self.n_dim), column=self.column)
		self.n_dim += 1
		self.n_col += 1

	def print_status(self):
		print("master objective value: {}".format(self.model.ObjVal))

	def to_int(self):
		for x in self.model.getVars():
			x.setAttr("VType", gurobipy.GRB.INTEGER)

	def write(self):
		self.model.write("model.lp")

class CPPMINSub:
	def __init__(self, S: int, G: graph, N: int) -> None:
		self.G = G
		self.S = S
		self.N = N

	def create_model(self) -> None:
		self.model = gurobipy.Model("sub model")
		self.y = self.model.addVars(self.G.n, lb=0, ub=1, vtype=GRB.INTEGER, name='y')
		self.z = self.model.addVars(self.G.n * (self.G.n - 1), lb=0, ub=GRB.INFINITY, vtype=GRB.INTEGER, name='z')
		self.model.addConstrs( (self.z[i*self.G.n+j] >= self.y[i] + self.y[j] - 1) for i in range(self.G.n-1) for j in range(i, self.G.n) )
		self.model.addConstr( (gurobipy.quicksum(self.G.a[i] * self.y[i] for i in range(self.G.n)) >= self.S) )

	def set_objective(self, pi: list):
		self.model.setObjective(-gurobipy.quicksum(pi[i] * self.y[i] for i in range(self.G.n)) +
													gurobipy.quicksum(self.G.E[i][j] * self.z[i*self.G.n+j] for i in range(self.G.n - 1) for j in range(i+1, self.G.n)), sense=GRB.MINIMIZE)

	def solve(self, flag=0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()

	def get_solution(self):
		return [self.model.getVars()[i].x for i in range(self.G.n)]

	def get_reduced_cost(self):
		return self.model.ObjVal

	def write(self):
		self.model.write('sub_model.lp')

def subset(A: list, B: list) -> bool:
	a = set(A)
	b = set(B)
	return a.issubset(b)

def union(A: list, B: list) -> list:
	a = set(A)
	b = set(B)
	c = a.union(b)
	return list(c)

class RMLP:
	def __init__(self, G: graph, P: list, w: list, S: int) -> None:
		## TODO
		self.G = G
		self.P = P
		self.w = w
		self.S = S
		self.N = len(self.P)
		self.k = len(self.G.V) // self.S + 1

	def create_model(self):
		self.x = []
		self.model = gurobipy.Model("Master")
		self.__set_vars()
		self.__set_contrs()

	def solve(self, flag = 0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()

	def get_dual_vars(self):
		pi = [self.constrs1[i].getAttr(GRB.Attr.Pi) for i in range(len(self.constrs1))]
		# sigma = self.constrs2.getAttr(GRB.Attr.Pi)
		# sigma_list = [self.constrs3[i].getAttr(GRB.Attr.Pi) for i in range(len(self.Q))]
		# return pi, sigma, sigma_list
		return pi, [], []

	def __set_contrs(self) -> None:
		self.constrs1 = self.model.addConstrs(
			gurobipy.quicksum(
				self.x[i] * int(v in self.P[i]) for i in range(self.N)
			) == 1
			for v in self.G.V
		)
		# self.constrs2 = self.model.addConstr(
		# 	gurobipy.quicksum(
		# 		self.x[i] for i in range(self.N)
		# 	) <= self.k
		# )
		# self.Q = self.alg1()
		# self.constrs3 = self.model.addConstrs(
		# 	gurobipy.quicksum(
		# 		self.x[p] * int(subset(self.P[p], self.Q[i])) for p in range(self.N)
		# 	) <= len(self.Q[i]) // self.S
		# 	for i in range(len(self.Q))
		# )

	def __set_vars(self) -> None:
		for i in range(self.N):
			self.x.append(self.model.addVar(obj=self.w[i], lb=0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name='x'+str(i)))
		self.n_dim = self.N
		self.n_col = 1

	def update_contrs(self, column_coeff):
		print(len(self.model.getConstrs()), len(column_coeff))
		self.column = gurobipy.Column(column_coeff, self.model.getConstrs())
		self.model.addVar(vtype=GRB.CONTINUOUS, lb=0, obj=1, name='x'+str(self.n_dim), column=self.column)
		self.n_dim += 1
		self.n_col += 1

	def print_status(self):
		print("master objective value: {}".format(self.model.ObjVal))

	def to_int(self):
		for x in self.model.getVars():
			x.setAttr("VType", GRB.INTEGER)

	def write(self):
		self.model.write("model.lp")

	def alg1(self):
		## TODO:
		Qset = []
		for i in range(self.N-1):
			for j in range(i+1, self.N):
				Q = union(self.P[i], self.P[j])
				q = len(Q) // self.S
				if bool(gurobipy.quicksum(self.x[p] for p in range(self.N) if subset(self.P[p], Q))) <= q-1:
					Qset.append(Q)
		return Qset

def solve():
	MAX_ITER_TIMES = 10

	n = 10 ## number of vertex
	S = 5	## least number of cluster
	G = graph(n)
	P = []
	for i in range(S, n-S+1):
		P += list(itertools.combinations(G.V, i))
	w = []
	for cluster in P:
		edges = list(itertools.combinations(cluster, 2))
		weight = 0
		for edge in edges:
			i, j = edge
			weight += G.E[i][j]
		w.append(weight)

	# cppmin = CPPMINMaster(len(P), S, P, w, G)
	cppmin = RMLP(G, P, w, S)
	cppmin.create_model()
	sub_prob = CPPMINSub(S=S, G=G, N=len(P))
	sub_prob.create_model()

	for i in range(MAX_ITER_TIMES):
		cppmin.solve()
		pi, _, _ = cppmin.get_dual_vars()
		cppmin.write()

		sub_prob.set_objective(pi)
		sub_prob.solve()
		y = sub_prob.get_solution()
		reduced_cost = sub_prob.get_reduced_cost()
		sub_prob.write()
		cppmin.update_contrs(column_coeff=y)
		if reduced_cost <= 1:
			break
	
	cppmin.to_int()
	cppmin.solve(flag=1)

if __name__ == '__main__':
	solve()
