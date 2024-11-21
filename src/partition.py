import numpy, time, math, colorama
from gurobipy import GRB
from graph import Graph
from itertools import combinations
import gurobipy
import heuristic

class MLP:
	def __init__(self, G: Graph, S: int) -> None:
		self.G = G
		self.S = S
		self.n_col = 0 ##
		self.n_dim = 0 ## 变量数量
		self.cutting_planes = []

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
		dual_values = [constr.getAttr(GRB.Attr.Pi) for constr in self.model.getConstrs()]
		pi = dual_values[:self.G.n]
		sigma = dual_values[self.G.n]
		sigma_list = []
		if len(dual_values) > self.G.n+1:
			sigma_list = dual_values[self.G.n+1:]
		return pi, sigma, sigma_list

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

		_column_coeff = column_coeff
		column_coeff = _column_coeff.copy()
		column_coeff.append(1)
		for i in range(len(self.cutting_planes)):
			column_coeff.append(
				int(
					heuristic.subset(_column_coeff, self.cutting_planes[i])
				)
			)
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

	def AddCuttingPlanesMLP(self, Q: list):
		xlp = self.model.getVars()
		for Qi in Q:
			xps: list[gurobipy.Var] = []
			for i in range(len(xlp)):
				if heuristic.subset(self.columns[i], Qi):
					xps.append(xlp[i])
			self.model.addConstr(
				gurobipy.quicksum( xp for xp in xps ) <= ((sum(Qi) // S) * 1.0)
			)

		for Qi in Q:
			assert(len(Qi) == self.G.n)
			self.cutting_planes.append(Qi)

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

	def AddCuttingPlanesSUB(self, Q: list):
		y = self.model.getVars()
		for Qi in Q:
			for i in range(n):
				if Qi[i]:
					continue
				self.model.addConstr(y[i] >= 1)

def PrintVarX(xlp: list[gurobipy.Var]):
	for var in xlp:
		if var.X != 0.0:
			print(f'{var.VarName}={var.X}', end='\n')
	print()

def GenerateQSET(mlp: MLP, n, S, verbose: bool):
	xlp = mlp.model.getVars()
	columns = mlp.columns

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
				if verbose:
					print('LOG::GenerateQSET: Generated Cutting Planes', Q)
	return QSet

def PriceColumn(column: list, pi: list, sigma: float, sigma_list: list, G: Graph, Q: list):
	wP = G.Weight(column)

	assert(len(column) == len(pi))
	pi_sum = 0.0
	for i in range(len(column)):
		pi_sum += column[i] * pi[i]

	assert(len(sigma_list) == len(Q))
	sigma_sum = 0.0
	for i in range(len(sigma_list)):
		sigma_sum += int(heuristic.subset(column, Q[i])) * sigma_list[i]

	return pi_sum + sigma + sigma_sum - wP

def HeuristicI (mlp: MLP, verbose: bool):
	if verbose:
		print('LOG::HEURISTICI')
	maxsize = 2 * mlp.S - 1
	pi, sigma, sigma_list = mlp.get_dual_vars()
	column_pool = []
	if maxsize > mlp.G.n:
		maxsize = mlp.G.n
	for i in range(mlp.G.n):
		cloest_i = sorted(mlp.G.V, key=lambda x: mlp.G.E[i][x])[:maxsize]
		for size in range(mlp.S, maxsize):
			for cluster in combinations(cloest_i, size):
				column = [int(v in cluster) for v in mlp.G.V]
				price = PriceColumn(column, pi, sigma, sigma_list, G, mlp.cutting_planes)
				if price > 0:
					column_pool.append( (column, price) )

	## Add the 10 most violating columns from the column pool
	## with no more than 10 columns on the same vertex added.
	if len(column_pool) == 0:
		return False

	column_pool = sorted(column_pool, key=lambda x: x[1], reverse=True)[:10]
	for column_coeff, price in column_pool:
		if verbose:
			print('LOG::HEURISTICI: Generated Column', column_coeff)
		mlp.update_contrs(column_coeff)
	return True

def HeuristicII(mlp: MLP, verbose: bool):
	if verbose:
		print('LOG::HEURISTICII')
	pi, sigma, sigma_list = mlp.get_dual_vars()
	column_pool = []
	for Qi in mlp.cutting_planes:
		index = []
		for i in range(mlp.G.n):
			if Qi[i] == 1:
				index.append(i)

		assert(len(index) > mlp.S)
		minsize = mlp.S
		maxsize = mlp.S * 2 - 1
		if maxsize > len(index):
			maxsize = len(index)
		for size in range(minsize, maxsize+1):
			for cluster in combinations(index, size):
				column = [int(x in cluster) for x in range(mlp.G.n)]
				price = PriceColumn(column, pi, sigma, sigma_list, G, mlp.cutting_planes)
				if price > 0:
					column_pool.append( (column, price) )

	if len(column_pool) == 0:
		return False

	column_pool = sorted(column_pool, key=lambda x: x[1], reverse=True)[:10]
	for column_coeff, price in column_pool:
		if verbose:
			print('LOG::HEURISTICII: Generated Column', column_coeff)
		mlp.update_contrs(column_coeff)
	return True

def IPSolver(masterproblem: MLP, subproblem: SUB, verbose: bool):
	pi, sigma, sigma_list = masterproblem.get_dual_vars()
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

		if HeuristicI (mlp, verbose) == True:
			continue

		if HeuristicII(mlp, verbose) == True:
			continue

		Q = GenerateQSET(mlp, G.n, S, verbose)
		if len(Q):
			mlp.AddCuttingPlanesMLP(Q)
			pip.AddCuttingPlanesSUB(Q)
			continue

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
		pi, sigma, sigma_list = cppmin.get_dual_vars()
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
	mlp = SolveNode(G, S, verbose=True)
	print(mlp.model.ObjVal)

	PrintVarX(mlp.model.getVars())
