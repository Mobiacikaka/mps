import gurobipy, heapq, colorama
from itertools import combinations
from typing import List
from gurobipy import GRB

from masterlp import MLP
from priceip import PriceIP as SUB
from graph import Graph

class CompareClass(tuple):
	def __lt__(self, other):
		return self[1] < other[1]

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

def GenerateQSET(masterproblem: MLP, n, S):
	xlp = masterproblem.model.getVars()
	columns = masterproblem.columns

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
			if GetSumofQ(xlp, columns, Q) > q - 1: ## violated
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

def HeuristicI(G: Graph, S: int, masterproblem: MLP, verbose: bool):
	model = masterproblem.model
	xlp = model.getVars()
	columns = masterproblem.columns

	column_pool = []
	for i in range(G.n):
		## Find the closest 2S − 1 vertices to vertex i.
		index = list(range(G.n))
		index = sorted(index, key=lambda x: G.E[i][x])[:2*S]
		## Enumerate all clusters of size S to 2S − 1 from these 2S vertices.
		for size in range(S, 2*S-1):
			for cluster in combinations(index, size):
				Q = [int(x in cluster) for x in range(G.n)]
				q = sum(Q) // S + 1
				s = GetSumofQ(xlp, columns, Q)
				if s > q-1:
					if len(column_pool) < 10:
						column_pool.append(CompareClass((Q, s)))
					elif len(column_pool) == 10:
						heapq.heapify(column_pool)
					else:
						if s > column_pool[0][1]:
							heapq.heappushpop(column_pool, CompareClass((Q, s)))

	## Add the 10 most violating columns from the column pool
	## with no more than 10 columns on the same vertex added.
	if len(column_pool) == 0:
		return False

	for y, _ in column_pool:
		assert(len(y) == G.n)
		flag = True
		for i in range(G.n):
			if y[i] == 1 and masterproblem.constrsLen[i] >= 10:
				flag = False
		if flag:
			if verbose:
				print('HEURISTICI::Generated Column: ', y)
			# print(f'{colorama.Fore.RED}Generated Column: {y}{colorama.Style.RESET_ALL}')
			masterproblem.update_contrs(y)

	return True

def HeuristicII(G: Graph, S: int, mlp: MLP, verbose: bool):
	pass

def HeuristicIII(G: Graph, S: int, mlp: MLP, verbose: bool):
	pi, _ = mlp.get_dual_vars()
	for i in range(G.n):
		cliq = [0] * G.n
		cliq[i] = 1
		v = 0
		for j in range(G.n):
			if cliq[j]:
				continue

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
