import gurobipy, heapq, colorama, time, itertools
from typing import List
from gurobipy import GRB

from masterlp import MLP
from priceip import PriceIP as SUB
from graph import Graph

class CompareClass(tuple):
	def __lt__(self, other):
		return self[1] < other[1]

def PrintVarX(xlp: List[gurobipy.Var], columns):
	for i in range(len(xlp)):
		var = xlp[i]
		if var.X != 0.0:
			print(f'{var.VarName}\t= {var.X}\t{columns[i]}', end='\n')
	print()

def subset(A: list, B: list) -> bool:
	## A subset of B
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
		CLIQ_size = mlp.G.a[i]
		vLeft = [j for j in range(mlp.G.n)]
		vLeft.remove(i)
		while True:
			if CLIQ_size >= 2 * mlp.S - 1:
				break
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
			if CLIQ_size < mlp.S or bestCost > 0:
				CLIQ.append(bestV)
				CLIQ_size += mlp.G.a[bestV]
				vLeft.remove(bestV)
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

def SolveGraphByHeuristic(G: Graph, S: int) -> list:
	U = G.V.copy()
	clusters = []
	while len(U) >= 2*S:
		x_s, x_t = 0, 0
		for i in range(G.n-1):
			for j in range(i+1, G.n):
				if G.E[i][j] > G.E[x_s][x_t]:
					x_s, x_t = i, j
		closest_x_s = sorted(U, key=lambda x: G.E[x_s][x])[:S]
		clusters.append(closest_x_s)
		for v in closest_x_s:
			U.remove(v)
		closest_x_t = sorted(U, key=lambda x: G.E[x_t][x])[:S]
		clusters.append(closest_x_t)
		for v in closest_x_t:
			U.remove(v)
	if len(U) >= S:
		clusters.append(U)
	if len(U) < S:
		for v in U:
			closest_neighbor = -1
			closest_distance = float('inf')
			for u in G.V:
				if u == v:
					continue
				if G.E[u][v] < closest_distance:
					closest_neighbor = u
					closest_distance = G.E[u][v]
			for cluster in clusters:
				if closest_neighbor in cluster:
					cluster.append(v)
					break
	return clusters

def SolveNode(
	mlp: MLP,
	pip: SUB,
	TIME_ESTIMATION_FLAG: bool=True,
	USE_HEURISTIC_FLAG: bool=True,
	USE_CUTTING_PLANES: bool=True,
	verbose: bool=False,
) -> MLP:
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
			pass

		if USE_HEURISTIC_FLAG:
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

		if USE_CUTTING_PLANES and USE_HEURISTIC_FLAG:
			## Generate Cutting Planes
			stime = time.time()
			Q = GenerateQSET(mlp, verbose)
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
