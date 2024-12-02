import gurobipy, heapq, colorama, time, itertools
from typing import List
from gurobipy import GRB

from masterlp import MLP
from priceip import PriceIP as SUB
from graph import Graph

class CompareClass(tuple):
	def __lt__(self, other):
		return self[1] < other[1]

def PrintVarX(xlp: list[gurobipy.Var], columns):
	for i in range(len(xlp)):
		var = xlp[i]
		if var.X != 0.0:
			print(f'{var.VarName}\t= {var.X}\t{columns[i]}', end='\n')
	print()

## A subset of B
def subset(A: list, B: list) -> bool:
	assert(len(A) == len(B))
	for i in range(len(A)):
		if A[i] == 1 and B[i] == 0:
			return False
	return True

def GetSumofQ(xlp: List[gurobipy.Var], clusters: List[list], Q: list) -> float:
	s = 0.0
	for p in range(len(clusters)):
		P = clusters[p]
		if subset(P, Q) == True:
			s += xlp[p].X
	return s

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
				if subset(mlp.columns[float_xlp[k]], Q):
					sum_xp += xlp[float_xlp[k]].X
			if sum_xp - q_minus > 1e-6:
				QSet.append(Q)
	if verbose:
		for Q in QSet:
			print(
				f'{colorama.Fore.LIGHTBLUE_EX}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
				'LOG::GenerateQSET: Generated Cutting Planes', Q
			)
	return QSet

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

	if reduced_cost - sigma >= -1e-6:
		return False

	masterproblem.update_contrs(y)
	return True

def PriceColumn(column: list, pi: list, sigma: float, sigma_list: list, Q: list):
	assert(len(column) == len(pi))
	pi_sum = 0.0
	for i in range(len(column)):
		pi_sum += column[i] * pi[i]

	assert(len(sigma_list) == len(Q))
	sigma_sum = 0.0
	for i in range(len(sigma_list)):
		sigma_sum += int(subset(column, Q[i])) * sigma_list[i]

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

def LocalSearch(column: list, column_pool: list, mlp: MLP):
	pi, sigma, sigma_list = mlp.get_dual_vars()

	## search local by removing a vertex
	cluster = [i for i in range(mlp.G.n) if column[i] == 1]
	for i in range(len(cluster)):
		column_neighbor = column.copy()
		column_neighbor[cluster[i]] = 0
		if sum(column_neighbor) < mlp.S:
			break
		price = PriceColumn(column_neighbor, pi, sigma, sigma_list, mlp.cutting_planes)
		wP = mlp.G.Weight(column_neighbor)
		if price - wP > 1e-6:
			MaintainPool(column_pool, column_neighbor, price-wP)

	## search local by adding a vertex
	cluster = [i for i in range(mlp.G.n) if column[i] == 0]
	for i in range(len(cluster)):
		column_neighbor = column.copy()
		column_neighbor[cluster[i]] = 1
		price = PriceColumn(column_neighbor, pi, sigma, sigma_list, mlp.cutting_planes)
		wP = mlp.G.Weight(column_neighbor)
		if price - wP > 1e-6:
			MaintainPool(column_pool, column_neighbor, price-wP)

	## search local by switching a vertex
	for i in range(mlp.G.n - 1):
		for j in range(i+1, mlp.G.n):
			if column[i] + column[j] != 1:
				continue
			column_neighbor = column.copy()
			column_neighbor[i], column_neighbor[j] = column_neighbor[j], column_neighbor[i]
			price = PriceColumn(column_neighbor, pi, sigma, sigma_list, mlp.cutting_planes)
			wP = mlp.G.Weight(column_neighbor)
			if price - wP > 1e-6:
				MaintainPool(column_pool, column_neighbor, price-wP)

	## end
	pass

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
			bestCost = float('inf')
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
		CLIQ = sorted(CLIQ)
		column = [int(x in CLIQ) for x in range(mlp.G.n)]
		price = PriceColumn(column, pi, sigma, sigma_list, mlp.cutting_planes)
		wP = mlp.G.Weight(column)
		if price - wP > 1e-6:
			MaintainPool(column_pool, column, price-wP)
		# print(CLIQ)
		LocalSearch(column, column_pool, mlp)

	if len(column_pool) == 0:
		return False

	for column, price in column_pool:
		if verbose:
			print(
				f'{colorama.Fore.MAGENTA}[{time.strftime('%H:%M:%S')}]{colorama.Style.RESET_ALL}',
				'LOG::HEURISTICIII: Generated Column', column, price
			)
		mlp.update_contrs(column)
	return True

def solve(n: int, S: int):
	G = Graph(n)
	G.PrintGraph()

	cppmin = MLP(G, S)
	cppmin.create_model()
	sub_prob = SUB(G, S)
	sub_prob.create_model()

	while True:
		## 2: Approximately solve the current LP relaxation using CPLEX
		cppmin.solve()
		cppmin.write('mlp.lp')
		if cppmin.model.Status == GRB.INFEASIBLE:
			print('INFEASIBLE')
			exit()

		## Generate Q set
		# QSet = heuristic.GenerateQSET(cppmin, n, S)

		## 3: Generate columns using heuristic algorithms, if new columns are found goto 2.
		# if heuristic.HeuristicI(G, S, cppmin)   == True:
		# 	continue

		## 5: Generate columns using an IP solver, if new columns are found goto 2.
		if IPSolver(cppmin, sub_prob, True) == True: ## There is new column generated
			continue

		## 6: If the gap between the value of the LP relaxation
		##    and the value of the incumbent integer solution is sufficiently small,
		##    STOP with optimality
		break

	print()
	for x in cppmin.model.getVars():
		if x.X != 0.0:
			print(f'{x.VarName}={x.X}\t: {cppmin.model.getCol(x)}')

	if not cppmin.is_integer():
		print('WARNING::There is only fractional solution!')
		exit()

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

		# Q = GenerateQSET(mlp, G.n, S)
		# if len(Q) and verbose:
		# 	print(Q)

		# if HeuristicI(G, S, mlp, verbose) == True:
		# 	continue

		if IPSolver(mlp, pip, verbose) == True:
			continue

		break

	return mlp
