import numpy, time, heapq, functools, gurobipy
from gurobipy import GRB

import heuristic
from graph import Graph
from masterlp import MLP
from priceip import PriceIP as SUB

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
		cppmin.solve()
		cppmin.write('model_linear.lp')
		if cppmin.model.Status == GRB.INFEASIBLE:
			print('INFEASIBLE')
			exit()

		## Generate Q set
		QSet = heuristic.GenerateQSET(cppmin, n, S)

		## 5: Generate columns using an IP solver, if new columns are found goto 2
		if heuristic.IPSolver(cppmin, sub_prob) == True: ## There is new column generated
			continue

		## 6: If the gap between the value of the LP relaxation
		##    and the value of the incumbent integer solution is sufficiently small,
		##    STOP with optimality
		break

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
