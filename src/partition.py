import numpy, time, math, colorama, heapq, itertools
from gurobipy import GRB
from graph import Graph
import gurobipy
import heuristic

class CompareClass(tuple):
	def __lt__(self, other):
		return self[1] < other[1]

class MLP:
	def __init__(self, G: Graph, S: int) -> None:
		self.G = G
		self.S = S
		self.n_col = 0 ## 列数量
		self.cutting_planes = []

	def __set_vars(self) -> None:
		self.x.append(self.model.addVar(obj=self.G.Weight(), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}'))
		self.n_col += 1
		self.columns = [[1] * self.G.n]

		for i in range(self.G.n):
			## include the clusters composed of the closest S and S+1 vertices to each vertex in the initial formulation
			cluster = self.G.closest_vertex[i][:self.S]
			column = [int(j in cluster) for j in range(self.G.n)]
			self.x.append(
				self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
			)
			self.n_col += 1
			self.columns.append(column)

			cluster = self.G.closest_vertex[i][:self.S+1]
			column = [int(j in cluster) for j in range(self.G.n)]
			self.x.append(
				self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
			)
			self.n_col += 1
			self.columns.append(column)

		pass

	def __set_contrs(self) -> None:
		self.constrs = self.model.addConstrs(
			gurobipy.quicksum( self.x[i] * self.columns[i][j] for i in range(len(self.x)) ) == 1 for j in range(self.G.n)
		)
		self.constrs2 = self.model.addConstr(
			gurobipy.quicksum( self.x[i] for i in range(len(self.x)) ) <= math.floor(self.G.n / self.S)
		)

	def __generate_candidate_columns(self):
		self.candidate_columns = []
		for i in range(self.G.n):
			closest_vertex = self.G.closest_vertex[i][:2*self.S]
			for size in range(self.S, self.S * 2):
				for cluster in itertools.combinations(closest_vertex, size):
					column = [int(i in cluster) for i in range(self.G.n)]
					weight = self.G.Weight(column)
					self.candidate_columns.append( (column, weight) )
		## cutting planes candidate columns
		self.candidate_columns_cp = []

	def create_model(self):
		self.x = []
		self.model = gurobipy.Model('Master')
		self.__generate_candidate_columns()
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

	def update_contrs(self, column_coeff: list):
		## same column assertion
		assert(column_coeff not in self.columns), "Generated a same column"
		self.columns.append(column_coeff)

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
			name='x'+str(self.n_col),
			column=column
		)
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
			self.model.addConstr(
				gurobipy.quicksum(
					xlp[i] * int(heuristic.subset(self.columns[i], Qi))
					for i in range(len(xlp))
				) <= sum(Qi) // self.S
			)

		for Qi in Q:
			assert(len(Qi) == self.G.n)
			assert(Qi not in self.cutting_planes), f'Generated a duplicated cutting plane {Qi}'
			self.cutting_planes.append(Qi)

			Qi_indexes = [i for i in range(self.G.n) if Qi[i]]
			for size in range(self.S, self.S * 2):
				for cluster in itertools.combinations(Qi_indexes, size):
					column = [int(x in cluster) for x in range(self.G.n)]
					weight = self.G.Weight(column)
					self.candidate_columns_cp.append( (column, weight) )
		pass

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
		for Qi in Q:
			assert(len(Qi) == self.G.n)
			self.model.addConstr(
				gurobipy.quicksum(
					(1-Qi[i]) * self.y[i] for i in range(self.G.n)
				) >= 1
			)

def PrintVarX(xlp: list[gurobipy.Var], columns):
	for i in range(len(xlp)):
		var = xlp[i]
		if var.X != 0.0:
			print(f'{var.VarName}\t= {var.X}\t{columns[i]}', end='\n')
	print()

def GenerateQSET(mlp: MLP, verbose: bool):
	if verbose:
		print(
			f'{colorama.Fore.LIGHTBLUE_EX}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
			'LOG::GenerateQSET'
		)

	xlp = mlp.model.getVars()
	float_xlp = []
	for i in range(mlp.n_col):
		if xlp[i].X == 0.0 or xlp[i].X == 1.0:
			continue
		float_xlp.append(i)

	QSet = []
	for i in range(len(float_xlp)-1):
		Pi = mlp.columns[float_xlp[i]]
		for j in range(i+1, len(float_xlp)):
			Pj = mlp.columns[float_xlp[j]]
			Q = [int(Pi[k] or Pj[k]) for k in range(mlp.G.n)]
			# if Q in QSet or Q in mlp.cutting_planes:
			if Q in QSet:
				continue
			## violated (9)
			q_minus = sum(Q) // mlp.S
			sum_xp = 0.0
			for k in range(len(float_xlp)):
				if heuristic.subset(mlp.columns[float_xlp[k]], Q):
					sum_xp += xlp[float_xlp[k]].X
			if sum_xp - q_minus > 1e-6:
				print(sum_xp)
				QSet.append(Q)
	if verbose:
		for Q in QSet:
			print(
				f'{colorama.Fore.LIGHTBLUE_EX}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
				'LOG::GenerateQSET: Generated Cutting Planes', Q
			)
	return QSet

def PriceColumn(column: list, pi: list, sigma: float, sigma_list: list, Q: list):
	assert(len(column) == len(pi))
	pi_sum = 0.0
	for i in range(len(column)):
		pi_sum += column[i] * pi[i]

	assert(len(sigma_list) == len(Q))
	sigma_sum = 0.0
	for i in range(len(sigma_list)):
		sigma_sum += int(heuristic.subset(column, Q[i])) * sigma_list[i]

	return pi_sum + sigma + sigma_sum

def InPool(column_pool: list, columnA: list) -> bool:
	for columnB, _ in column_pool:
		if columnA == columnB:
			return True
	return False

def MaintainPool(column_pool: list, column: list, price: float, MaxLen=10):
	if InPool(column_pool, column):
		return
	if len(column_pool) < MaxLen:
		column_pool.append( CompareClass( (column, price) ) )
		if len(column_pool) == MaxLen:
			heapq.heapify(column_pool)
	elif len(column_pool) == MaxLen:
		if price > column_pool[0][1]:
			heapq.heappushpop(column_pool, CompareClass( (column, price) ))
	return

def HeuristicI  (mlp: MLP, verbose: bool):
	if verbose:
		print(
			f'{colorama.Fore.CYAN}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
			'LOG::HEURISTICI'
		)
	pi, sigma, sigma_list = mlp.get_dual_vars()
	column_pool = []
	for column, wP in mlp.candidate_columns:
		price = PriceColumn(column, pi, sigma, sigma_list, mlp.cutting_planes)
		if price-wP > 1e-6:
			MaintainPool(column_pool, column, price-wP)

	## Add the 10 most violating columns from the column pool
	## with no more than 10 columns on the same vertex added.
	if len(column_pool) == 0:
		return False

	for column, price in column_pool:
		if verbose:
			print(
				f'{colorama.Fore.CYAN}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
				'LOG::HEURISTICI: Generated Column', column
			)
			# print('LOG::HEURISTICI: price', price)
		mlp.update_contrs(column)
	return True

def HeuristicII (mlp: MLP, verbose: bool):
	if verbose:
		print(
			f'{colorama.Fore.BLUE}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
			'LOG::HEURISTICII'
		)
	pi, sigma, sigma_list = mlp.get_dual_vars()
	column_pool = []
	for column, wP in mlp.candidate_columns_cp:
		price = PriceColumn(column, pi, sigma, sigma_list, mlp.cutting_planes)
		if price - wP > 1e-6:
			MaintainPool(column_pool, column, price-wP)

	if len(column_pool) == 0:
		return False

	column_pool = sorted(column_pool, key=lambda x: x[1], reverse=True)[:10]
	for column_coeff, price in column_pool:
		if verbose:
			print(
				f'{colorama.Fore.BLUE}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
				'LOG::HEURISTICII: Generated Column', column_coeff
			)
			# print('LOG::HEURISTICII: price', price)
		mlp.update_contrs(column_coeff)
	return True

def HeuristicIII(mlp: MLP, verbose: bool):
	if verbose:
		print(
			f'{colorama.Fore.MAGENTA}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
			'LOG::HEURISTICIII'
		)

	pi, sigma, sigma_list = mlp.get_dual_vars()
	column_pool = []
	for i in range(mlp.G.n):
		CLIQ = [i]
		vLeft = [j for j in range(mlp.G.n) if j != i]
		while True:
			## find the best v
			bestV = -1
			bestCost = 1e9
			for v in vLeft:
				curCost = pi[v]
				for vInP in CLIQ:
					curCost -= mlp.G.E[v][vInP]
				if curCost < bestCost:
					bestCost = curCost
					bestV = v
			## judge to continue or break
			if len(CLIQ) < mlp.S or bestCost > 0:
				CLIQ.append(bestV)
				vLeft.remove(bestV)
				continue
			else:
				break
		column = [int(x in CLIQ) for x in range(mlp.G.n)]
		price = PriceColumn(column, pi, sigma, sigma_list, mlp.cutting_planes)
		wP = mlp.G.Weight(column)
		if price - wP > 1e-6:
			column_pool.append( (column, price-wP) )

	if len(column_pool) == 0:
		return False

	column_pool = sorted(column_pool, key=lambda x: x[1], reverse=True)[:10]
	for column_coeff, price in column_pool:
		if verbose:
			print(
				f'{colorama.Fore.MAGENTA}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
				'LOG::HEURISTICIII: Generated Column', column_coeff
			)
		mlp.update_contrs(column_coeff)
	return True

def LocalSearch(CLIQ: list, vLeft: list, E: list, pi: list, curCost: int):
	assert(0)

def IPSolver(masterproblem: MLP, subproblem: SUB, verbose: bool):
	if verbose:
		print(
			f'{colorama.Fore.YELLOW}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
			'LOG::IPSOLVER'
		)
	pi, sigma, sigma_list = masterproblem.get_dual_vars()
	subproblem.set_objective(pi)
	subproblem.solve()
	subproblem.write()

	y = subproblem.get_solution()
	reduced_cost = subproblem.get_reduced_cost()
	if verbose:
		print(
			f'{colorama.Fore.YELLOW}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
			'LOG::IPSOLVER::Generated Column: ', y
		)
		# print('LOG::IPSOLVER::price', sigma-reduced_cost)
		# print('LOG::IPSOLVER::price:', - masterproblem.G.Weight(y) + sum([y[i] * pi[i] for i in range(len(y))]) + sigma)

	if reduced_cost - sigma >= -1e-6:
		return False

	masterproblem.update_contrs(y)
	return True

def SolveNode(G: Graph, S: int, verbose: bool=False):
	mlp = MLP(G, S) ## Master Linear Problem
	mlp.create_model()
	pip = SUB(G, S) ## Price Integer Problem
	pip.create_model()

	TIME_ESTIMATION_FLAG = True
	runtime_MLP = 0.0
	runtime_SUB = 0.0
	runtime_H1 = 0.0
	runtime_H2 = 0.0
	runtime_H3 = 0.0
	runtime_CP = 0.0 ##.0 cutting planes time

	while True:
		stime = time.time()
		mlp.solve()
		etime = time.time()
		runtime_MLP += etime - stime
		mlp.write('master.lp')
		if mlp.model.Status == GRB.INFEASIBLE:
			print(f'{colorama.Fore.RED}ERROR::INFEASIBLE!{colorama.Style.RESET_ALL}')
			exit()
		else:
			print('Best Objective Value: ', mlp.model.ObjVal)

		## Generate Columns using HeuristicI
		stime = time.time()
		flag = HeuristicI(mlp, verbose)
		etime = time.time()
		runtime_H1 += etime - stime
		if flag == True:
			continue

		## Generate Columns using HeuristicII
		stime = time.time()
		flag = HeuristicII(mlp, verbose)
		etime = time.time()
		runtime_H2 += etime - stime
		if flag == True:
			continue

		## Generate Columns using HeuristicIII
		stime = time.time()
		flag = HeuristicIII(mlp, verbose)
		etime = time.time()
		runtime_H3 += etime - stime
		if flag == True:
			continue

		## Generate Cutting Planes
		stime = time.time()
		Q = GenerateQSET(mlp, verbose=True)
		if len(Q):
			mlp.AddCuttingPlanesMLP(Q)
			pip.AddCuttingPlanesSUB(Q)
		etime = time.time()
		runtime_CP += etime - stime
		if len(Q):
			continue

		## Column Generation using IPSolver
		stime = time.time()
		flag = IPSolver(mlp, pip, verbose)
		etime = time.time()
		runtime_SUB += etime - stime
		if flag == True:
			continue

		break

	if TIME_ESTIMATION_FLAG:
		print()
		print('RUNTIME Master Problem:\t', runtime_MLP)
		print('RUNTIME HeuristicI:\t', runtime_H1)
		print('RUNTIME HeuristicII:\t', runtime_H2)
		print('RUNTIME HeuristicIII:\t', runtime_H3)
		print('RUNTIME Cutting Planes:\t', runtime_CP)
		print('RUNTIME Sub Problem:\t', runtime_SUB)
		print()
	return mlp

def main():
	for seed in range(100):
		print('seed', seed)
		numpy.random.seed(11)

		S = 7
		n = 4*S+1

		G = Graph(n)
		G.PrintGraph()
		mlp = SolveNode(G, S, verbose=True)
		print('ObjVal', mlp.model.ObjVal)

		PrintVarX(mlp.model.getVars(), mlp.columns)
		break

if __name__ == '__main__':
	main()
