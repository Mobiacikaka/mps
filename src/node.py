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
		self.mlp = heuristic.SolveNode(self.G, self.S)
		self.mlp.solve()
		self.obj_values = self.mlp.model.ObjVal
		self.solution = self.mlp.model.getVars()
		return self.mlp.model.Status

	def update_lower_bound(self):
		if self.lower_bound < self.obj_values:
			self.lower_bound = self.obj_values
			# assert(self.lower_bound <= self.upper_bound)

	def update_upper_bound(self):
		self.upper_bound = self.obj_values
		# assert(self.lower_bound <= self.upper_bound)

	def is_integer(self):
		assert(self.mlp != None)
		for var in self.mlp.model.getVars():
			if var.X > 0 and var.X < 1:
				return False
		return True

	def is_child_problem(self) -> bool:
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
					if self.vi > self.vj:
						self.vi, self.vj = self.vj, self.vi
					return True
		return False

	def get_child_problem(self):
		G_Div, G_Cop = copy.deepcopy(self.G), copy.deepcopy(self.G)
		G_Div.Divide(self.vi, self.vj)
		G_Cop.Collapse(self.vi, self.vj)
		Node_Div = Node(G_Div, self.S, self.upper_bound, self.lower_bound)
		Node_Cop = Node(G_Cop, self.S, self.upper_bound, self.lower_bound)
		Node_Cop.collapse_comb = self.collapse_comb.copy() + [(self.vi, self.vj)]
		return Node_Div, Node_Cop
