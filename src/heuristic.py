import gurobipy, heapq, colorama
from itertools import combinations

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

def GetSumofQ(xlp: list[gurobipy.Var], clusters: list[list], Q: list) -> float:
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

def IPSolver(masterproblem: MLP, subproblem: SUB):
	print('LOG::USING IPSOLVER')

	pi, sigma = masterproblem.get_dual_vars()
	subproblem.set_objective(pi)
	subproblem.solve()
	subproblem.write()

	y = subproblem.get_solution()
	print('Generate Column: ', y)
	reduced_cost = subproblem.get_reduced_cost()
	print('reduced_cost-sigma: ', reduced_cost-sigma)

	if reduced_cost - sigma >= 0:
		return False

	masterproblem.update_contrs(y)
	return True

def HeuristicI(G: Graph, S: int, masterproblem: MLP):
	print('LOG::USING HEURISTIC I')

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
			print(f'{colorama.Fore.RED}Generate Column: {y}{colorama.Style.RESET_ALL}')
			masterproblem.update_contrs(y)

	return True
