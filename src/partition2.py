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

class Node:
	def __init__(self, G: Graph, S: int, upper_bound: float, lower_bound: float) -> None:
		self.G = G
		self.S = S
		self.upper_bound = upper_bound
		self.lower_bound = lower_bound

	def optimize(self):
		## Create Model
		self.mlp = MLP(self.G, self.S)
		self.mlp.create_model()
		self.pip = SUB(self.G, self.S)
		self.pip.create_model()

		## Solve
		while True:
			self.mlp.solve()
			self.mlp.write('mlp.lp')
			if self.mlp.model.Status == GRB.INFEASIBLE:
				print(f'{colorama.Fore.RED}ERROR::INFEASIBLE!{colorama.Style.RESET_ALL}')
				exit()

			if heuristic.IPSolver(self.mlp, self.pip) == True:
				continue

			break

		self.mlp.solve()
		self.obj_values = self.mlp.model.ObjVal
		return self.mlp.model.Status

	def update_lower_bound(self):
		if self.lower_bound < self.obj_values:
			self.lower_bound = self.obj_values
			assert(self.lower_bound <= self.upper_bound)

	def update_upper_bound(self):
		self.upper_bound = self.obj_values
		assert(self.lower_bound <= self.upper_bound)

	def is_integer(self):
		for var in self.mlp.model.getVars():
			if var.X > 0 and var.X < 1:
				return False
		return True

def BranchAndPrice(n: int, S: int):
	OriginalGraph = Graph(n)
	OriginalGraph.PrintGraph()

	upper_bound, lower_bound = float('inf'), 0
	root_node = Node(
		G=OriginalGraph,
		S=S,
		upper_bound=upper_bound,
		lower_bound=lower_bound,
	)
	candidate_node = [root_node]
	current_optimun = None

	while candidate_node:
		node = candidate_node.pop(0)

		if node.lower_bound >= upper_bound:
			print('prune by bound')
			continue

		model_status = node.optimize()
		if model_status == GRB.INFEASIBLE:
			print('prune by infeasibility')
			continue

		node.update_lower_bound()
		if node.lower_bound >= upper_bound:
			print('prune by bound')
			continue

if __name__ == '__main__':
	numpy.random.seed(50)
	solve()
