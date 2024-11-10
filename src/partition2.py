import numpy, colorama
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
		# QSet = heuristic.GenerateQSET(cppmin, n, S)

		## 3: Generate columns using heuristic algorithms, if new columns are found goto 2.
		# if heuristic.HeuristicI(G, S, cppmin)   == True:
		# 	continue

		## 5: Generate columns using an IP solver, if new columns are found goto 2.
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

def SolveNode(G: Graph, S: int):
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

		if heuristic.IPSolver(mlp, pip) == True:
			continue

		break

	return mlp

def BranchAndPrice(n: int, S: int):
	OriginalGraph = Graph(n)
	OriginalGraph.PrintGraph()

	GraphQueue = [OriginalGraph]

	while len(GraphQueue):
		G = GraphQueue.pop(0)
		mlp = SolveNode(G, S)

		## TODO: Branching
		if mlp.is_int():
			assert(0)

if __name__ == '__main__':
	numpy.random.seed(50)
	solve()
