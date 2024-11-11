import numpy, colorama, copy
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
		self.mlp = None

	def optimize(self):
		## Create Model
		if self.mlp == None:
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
		self.solution = self.mlp.model.getVars()
		return self.mlp.model.Status

	def update_lower_bound(self):
		if self.lower_bound < self.obj_values:
			self.lower_bound = self.obj_values
			assert(self.lower_bound <= self.upper_bound)

	def update_upper_bound(self):
		self.upper_bound = self.obj_values
		assert(self.lower_bound <= self.upper_bound)

	def is_integer(self):
		assert(self.mlp != None)
		for var in self.mlp.model.getVars():
			if var.X > 0 and var.X < 1:
				return False
		return True

	def is_child_problem(self) -> bool:
		## TODO
		self.vi = 0
		self.vj = 0
		for xP1 in range(self.G.n-1):
			if self.solution[xP1].X == 0.0 or self.solution[xP1].X == 1.0:
				continue
			for xP2 in range(xP1+1, self.G.n):
				if self.solution[xP2].X == 0.0 or self.solution[xP2].X == 1.0:
					continue
				for vi in range(self.G.n): ## vi is the vertice that in both clusters
					if self.mlp.columns[xP1][vi] & self.mlp.columns[xP2][vi] == 1:
						self.vi = vi
						break
				for vj in range(self.G.n): ## vj is the vertice that covered by only one cluster
					if self.mlp.columns[xP1][vj] ^ self.mlp.columns[xP2][vj] == 1:
						self.vj = vj
						break
				if self.vi < self.G.n and self.vj < self.G.n:
					assert(self.vi != self.vj)
					return True
		return False

	def get_child_problem(self):
		## TODO
		G_Div, G_Cop = copy.deepcopy(self.G), copy.deepcopy(self.G)
		G_Div.Divide(self.vi, self.vj)
		G_Cop.Collapse(self.vi, self.vj)
		Node_Div = Node(G_Div, self.S, self.upper_bound, self.lower_bound)
		Node_Cop = Node(G_Cop, self.S, self.upper_bound, self.lower_bound)
		return Node_Div, Node_Cop

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
	current_optimun = []

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

		if node.is_integer():
			node.update_upper_bound()
			if node.upper_bound < upper_bound:
				upper_bound = node.upper_bound
				current_optimun = node.solution
			continue

		if node.is_child_problem():
			Node_Div, Node_Cop = node.get_child_problem()
			candidate_node.append(Node_Div)
			candidate_node.append(Node_Cop)

	print('upper_bound: ', upper_bound)
	# print('optimum: ', current_optimun)
	for var in current_optimun:
		if var.X == 1.0:
			print(var.VarName)

if __name__ == '__main__':
	numpy.random.seed(50)
	BranchAndPrice(11, 5)
