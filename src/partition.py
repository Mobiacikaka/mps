import math
import time

import colorama
import gurobipy
import numpy
from gurobipy import GRB
from numpy.random import f

import heuristic
from graph import Graph


class MLP:
	def __init__(self, G: Graph, S: int) -> None:
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
		return self.model.getVars()

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
		self.x.append(self.model.addVar(obj=self.G.Weight(), lb=0, vtype=GRB.CONTINUOUS, name='x0'))
		self.n_dim = 1
		self.n_col = 1
		self.columns = [[1] * self.G.n]
		self.constrsLen = [1] * self.G.n

	def update_contrs(self, column_coeff: list):
		## same column assertion
		assert(column_coeff not in self.columns), "Generated a same column"
		self.columns.append(column_coeff)
		for i in range(len(column_coeff)):
			self.constrsLen[i] += column_coeff[i]

		column_coeff = column_coeff.copy()
		column_coeff.append(1)
		column = gurobipy.Column(column_coeff, self.model.getConstrs())

		self.model.addVar(
			obj=self.G.Weight(column_coeff),
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

	def is_integer(self):
		for x in self.model.getVars():
			if x.X > 0 and x.X < 1:
				return False
		return True

	def write(self, filename='model.lp'):
		self.model.write(filename)

class SUB:
	def __init__(self, G: Graph, S: int) -> None:
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

def PrintVarX(xlp: list[gurobipy.Var]):
	for var in xlp:
		if var.X != 0.0:
			print(f'{var.VarName}={var.X}', end='\n')
	print()

def GenerateQSET(mlp: MLP, n, S):
	# print('\nLOG::GenerateQSET')
	xlp = mlp.model.getVars()
	columns = mlp.columns
	# if not mlp.is_integer():
	# 	PrintVarX(xlp)
	# 	for i in range(len(xlp)):
	# 		if xlp[i].X != 0.0 :
	# 			print(columns[i])

	QSet = []
	for i in range(len(xlp)-1):
		if xlp[i].X == 0.0 or xlp[i].X == 1.0:
			continue
		Pi = columns[i]

		for j in range(i+1, len(xlp)):
			if xlp[j].X == 0.0 or xlp[j].X == 1.0:
				continue
			Pj = columns[j]

			Q = [Pi[i] or Pj[i] for i in range(n)]

			## check inequality
			q = sum(Q) // S + 1
			if heuristic.GetSumofQ(xlp, columns, Q) > q - 1: ## violated
				QSet.append(Q)
	return QSet

def IPSolver(masterproblem: MLP, subproblem: SUB, verbose: bool):
	pi, sigma = masterproblem.get_dual_vars()
	subproblem.set_objective(pi)
	subproblem.solve()
	subproblem.write()

	y = subproblem.get_solution()
	reduced_cost = subproblem.get_reduced_cost()
	if verbose:
		print('IPSOLVER::Generated Column: ', y)
		print('reduced_cost-sigma: ', reduced_cost-sigma)

	if reduced_cost - sigma >= -1e-6:
		return False

	masterproblem.update_contrs(y)
	return True

def AddCuttingPlanesMLP(mlp: MLP, Q: list):
	columns = mlp.columns
	xlp = mlp.model.getVars()
	for Qi in Q:
		xps: list[gurobipy.Var] = []
		for i in range(len(xlp)):
			if heuristic.subset(columns[i], Qi):
				xps.append(xlp[i])
		mlp.model.addConstr(
			gurobipy.quicksum( xp for xp in xps ) <= ((sum(Qi) // S) * 1.0)
		)
	return mlp

def AddCuttingPlanesSUB(sub: SUB, Q: list):
	y = sub.model.getVars()
	for Qi in Q:
		for i in range(n):
			if Qi[i]:
				continue
			sub.model.addConstr(y[i] >= 1)
	return sub

def SolveNode(G: Graph, S: int, verbose: bool=False):
	mlp = MLP(G, S) ## Master Linear Problem
	mlp.create_model()
	pip = SUB(G, S) ## Price Integer Problem
	pip.create_model()

	while True:
		mlp.solve()
		mlp.write('master.lp')
		if mlp.model.Status == GRB.INFEASIBLE:
			print(f'{colorama.Fore.RED}ERROR::INFEASIBLE!{colorama.Style.RESET_ALL}')
			exit()

		Q = GenerateQSET(mlp, G.n, S)
		if len(Q):
			print(Q)
			mlp = AddCuttingPlanesMLP(mlp, Q)
			pip = AddCuttingPlanesSUB(pip, Q)

		if IPSolver(mlp, pip, verbose) == True:
			continue

		break

	return mlp

def TimeEstimate(n: int, S: int):
	G = Graph(n)
	G.PrintGraph()

	cppmin = MLP(G, S)
	cppmin.create_model()
	sub_prob = SUB(G, S)
	sub_prob.create_model()
	PI = []

	time_master = 0.0
	time_subprob = 0.0

	while True:
		time_start = time.time()

		cppmin.solve()
		cppmin.write('model_linear.lp')
		if cppmin.model.Status == GRB.INFEASIBLE:
			print('INFEASIBLE')
			exit()
		pi, sigma = cppmin.get_dual_vars()
		assert(pi not in PI), 'Generated a same pi'
		PI.append(pi)

		time_end = time.time()
		time_master += time_end - time_start

		time_start = time.time()

		sub_prob.set_objective(pi)
		sub_prob.solve()
		sub_prob.write()

		time_end = time.time()
		time_subprob += time_end - time_start

		## 6: If the gap between the value of the LP relaxation and the value of the incumbent integer solution is sufficiently small, STOP with optimality
		y = sub_prob.get_solution()
		print('Generate Column: ', y)
		reduced_cost = sub_prob.get_reduced_cost()
		print('reduced_cost-sigma: ', reduced_cost-sigma)

		if reduced_cost >= sigma - 1e-6:
		# if reduced_cost - sigma >= 0:
			break

		cppmin.update_contrs(column_coeff=y)
		# y = [1-x for x in y]
		# cppmin.update_contrs(column_coeff=y)

	print()
	PrintVarX(cppmin.model.getVars())

	cppmin.to_int()
	cppmin.solve(flag=1)
	cppmin.write('model_int.lp')

	print()
	PrintVarX(cppmin.model.getVars())

	print(time_master, time_subprob)

if __name__ == '__main__':
	numpy.random.seed(60)

	n = 29
	S = 7

	G = Graph(n)
	G.PrintGraph()
	mlp = SolveNode(G, S, verbose=False)
	print(mlp.model.ObjVal)

	PrintVarX(mlp.model.getVars())
