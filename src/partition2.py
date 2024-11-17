import numpy, colorama, copy
from gurobipy import GRB

import heuristic
from graph import Graph
from masterlp import MLP
from priceip import PriceIP as SUB

class Node:
	def __init__(self, G: Graph, S: int, upper_bound: float, lower_bound: float) -> None:
		self.G = G
		self.S = S
		self.upper_bound = upper_bound
		self.lower_bound = lower_bound
		self.vi = -1
		self.vj = -1
		self.collapse_comb = []

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
		# print('LOG::is_integer')
		for var in self.mlp.model.getVars():
			if var.X > 0 and var.X < 1:
				return False
		return True

	def is_child_problem(self) -> bool:
		# print('LOG::is_child_problem')
		Vars = self.mlp.model.getVars()
		for xP1 in range(len(Vars)-1):
			self.vi = self.vj = -1
			if Vars[xP1].X == 0.0 or Vars[xP1].X == 1.0:
				continue
			for xP2 in range(xP1+1, len(Vars)):
				if Vars[xP2].X == 0.0 or Vars[xP2].X == 1.0:
					continue
				for vi in range(self.G.n): ## vi is the vertice that in both clusters
					if self.mlp.columns[xP1][vi] + self.mlp.columns[xP2][vi] == 2:
						self.vi = vi
						break
				for vj in range(self.G.n): ## vj is the vertice that covered by only one cluster
					if self.mlp.columns[xP1][vj] + self.mlp.columns[xP2][vj] == 1:
						self.vj = vj
						break
				if self.vi < self.G.n and self.vj < self.G.n and self.vi >= 0 and self.vj >= 0:
					assert(self.vi != self.vj)
					return True
		return False

	def get_child_problem(self):
		# print('LOG::get_child_problem')
		G_Div, G_Cop = copy.deepcopy(self.G), copy.deepcopy(self.G)
		G_Div.Divide(self.vi, self.vj)
		G_Cop.Collapse(self.vi, self.vj)
		Node_Div = Node(G_Div, self.S, self.upper_bound, self.lower_bound)
		Node_Cop = Node(G_Cop, self.S, self.upper_bound, self.lower_bound)
		Node_Cop.collapse_comb = self.collapse_comb.copy() + [(self.vi, self.vj)]
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
	optimum_columns = []
	node_collapse_seq = []

	while candidate_node:
		node = candidate_node.pop(0)

		if node.lower_bound >= upper_bound:
			print('LOG::PRUNE BY BOUND')
			continue

		model_status = node.optimize()
		if model_status == GRB.INFEASIBLE:
			print('LOG::PRUNE BY INFEASIBILITY')
			continue

		node.update_lower_bound()
		if node.lower_bound >= upper_bound:
			print('LOG::PRUNE BY BOUND')
			continue

		if node.is_integer():
			print('LOG::IS INTEGER')
			node.update_upper_bound()
			if node.upper_bound < upper_bound:
				print('LOG::IS OPTIMUM')
				upper_bound = node.upper_bound
				current_optimun = node.solution
				optimum_columns = []
				for index in range(len(current_optimun)):
					if current_optimun[index].X == 1.0:
						optimum_columns.append(node.mlp.columns[index])
				node_collapse_seq = node.collapse_comb.copy()
			continue
		else:
			pass

		if node.is_child_problem():
			Node_Div, Node_Cop = node.get_child_problem()
			candidate_node.append(Node_Div)
			candidate_node.append(Node_Cop)
			print('LOG::Branching')

	print('upper_bound: ', upper_bound)
	# print('optimum: ', current_optimun)
	i = 0
	print(node_collapse_seq)
	for var in current_optimun:
		if var.X == 1.0:
			print(var.VarName, optimum_columns[i])
			i += 1

if __name__ == '__main__':
	numpy.random.seed(60)
	BranchAndPrice(50, 7)
	# numpy.random.seed(60)
	# BranchAndPrice(29, 7)
	# numpy.random.seed(5)
	# BranchAndPrice(15, 4)
