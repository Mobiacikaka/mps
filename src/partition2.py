import numpy, time, heapq
from itertools import combinations
from gurobipy import GRB
from graph import Graph
from masterlp import MLP
from priceip import PriceIP as SUB
import gurobipy

## A subset of B
def subset(A: list, B: list) -> bool:
	assert(len(A) == len(B))
	for i in range(len(A)):
		if A[i] == 1 and B[i] == 0:
			return False
	return True

def CheckInequality(xlp: list[gurobipy.Var], clusters: list[list], Q: list, q: int) -> tuple[bool, float]:
	s = 0.0
	for p in range(len(clusters)):
		P = clusters[p]
		if subset(P, Q) == True:
			s += xlp[p].X
	if s <= q - 1:
		return True, s ## valid
	return False, s    ## invalid

def GenerateQSET(model: gurobipy.Model, n, S):
	xlp = model.getVars()
	constrs = model.getConstrs()
	column_coeff = [ [model.getCoeff(constr, x) for constr in constrs] for x in xlp]

	QSet = []
	for i in range(len(xlp)-1):
		if xlp[i].X == 0.0 or xlp[i].X == 1.0:
			continue
		Pi = column_coeff[i]

		for j in range(i+1, len(xlp)):
			if xlp[j].X == 0.0 or xlp[j].X == 1.0:
				continue
			Pj = column_coeff[j]

			Q = [Pi[i] or Pj[i] for i in range(n)]

			## check inequality
			q = sum(Q) // S + 1
			if CheckInequality(xlp, column_coeff, Q, q)[0] == False: ## violated
				QSet.append(Q)
	return QSet

def HeuristicI(G: Graph, S: int, model: gurobipy.Model):
	xlp = model.getVars()
	constrs = model.getConstrs()
	column_coeff = [ [model.getCoeff(constr, x) for constr in constrs] for x in xlp]

	for i in range(G.n):
		## Find the closest 2S − 1 vertices to vertex i.
		index = list(range(G.n))
		index = sorted(index, key=lambda x: G.E[i][x])[:2*S]
		## Enumerate all clusters of size S to 2S − 1 from these 2S vertices.
		column_pool = []
		for size in range(S, 2*S-1):
			for cluster in combinations(index, size):
				Q = [int(x in cluster) for x in range(G.n)]
				q = sum(Q) // S + 1
				flag, s = CheckInequality(xlp, column_coeff, Q, q)
				if flag == False:
					if len(column_pool) < 10:
						column_pool.append((Q, s))
					else:
						## TODO
						assert(0)

def solve():
	n = 21
	S = 5
	G = Graph(n)
	G.PrintGraph()

	cppmin = MLP(G, S)
	cppmin.create_model()
	sub_prob = SUB(G, S)
	sub_prob.create_model()

	while True:
		## 2: Approximately solve the current LP relaxation using CPLEX
		xlp = cppmin.solve()
		cppmin.write('model_linear.lp')
		if cppmin.model.Status == GRB.INFEASIBLE:
			print('INFEASIBLE')
			exit()

		## Generate Q set
		QSet = GenerateQSET(cppmin.model, n, S)

		## 5: Generate columns using an IP solver, if new columns are found goto 2
		pi, sigma = cppmin.get_dual_vars()
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

	print()
	for x in cppmin.model.getVars():
		if x.X != 0.0:
			print(f'{x.VarName}={x.X}\t: {cppmin.model.getCol(x)}')

	cppmin.to_int()
	cppmin.solve(flag=1)
	cppmin.write('model_int.lp')

if __name__ == '__main__':
	numpy.random.seed(60)
	solve()
