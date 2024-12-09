import numpy, colorama, copy
from gurobipy import GRB

import heuristic
from graph import Graph
from masterlp import MLP
from priceip import PriceIP as SUB

class Node:
	def __init__(
		self,
		G: Graph,
		S: int,
		upper_bound: float,
		lower_bound: float,
	) -> None:
		self.G = G
		self.S = S
		self.upper_bound = upper_bound
		self.lower_bound = lower_bound
		self.vi = -1
		self.vj = -1
		self.collapse_comb = []
		self.divide_comb = []
		self.columns = []
		self.cutting_planes = []
		self.candidate_columns = []
		self.ROOT_FLAG: bool = False

	def create_model(self):
		self.mlp = MLP(
			self.G,
			self.S,
			columns=self.columns,
			cutting_planes=self.cutting_planes,
			candidate_columns=self.candidate_columns,
		)
		self.mlp.create_model()
		self.pip = SUB(self.G, self.S)
		self.pip.create_model()

	def optimize(self):
		self.mlp = heuristic.SolveNode(
			mlp=self.mlp,
			pip=self.pip,
			TIME_ESTIMATION_FLAG=False,
			USE_HEURISTIC_FLAG=False,
			# USE_CUTTING_PLANES=self.ROOT_FLAG == True,
			USE_CUTTING_PLANES=False,
			verbose=False,
		)
		self.obj_values = self.mlp.model.ObjVal
		self.solution = self.mlp.model.getVars()
		return self.mlp.model.Status

	def update_lower_bound(self):
		if self.lower_bound < self.obj_values:
			self.lower_bound = self.obj_values
			# assert(self.lower_bound <= self.upper_bound), f'lower_bound={self.lower_bound}, upper_bound={self.upper_bound}'

	def update_upper_bound(self):
		self.upper_bound = self.obj_values
		# assert(self.lower_bound <= self.upper_bound), f'lower_bound={self.lower_bound}, upper_bound={self.upper_bound}'

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
		G_Div = copy.deepcopy(self.G)
		G_Div.Divide(self.vi, self.vj)
		Node_Div = Node(G_Div, self.S, self.upper_bound, self.lower_bound)
		for column in self.mlp.columns:
			if column[self.vi] == 1 and column[self.vj] == 1:
				continue
			Node_Div.columns.append(column)
		for cutting_plane in self.mlp.cutting_planes:
			Node_Div.cutting_planes.append(cutting_plane)
		for candidate_column, weight in self.mlp.candidate_columns:
			if candidate_column[self.vi] == 1 and candidate_column[self.vj] == 1:
				continue
			Node_Div.candidate_columns.append( (candidate_column, weight) )
		Node_Div.divide_comb = self.divide_comb.copy() + [(self.vi, self.vj)]
		Node_Div.collapse_comb = self.collapse_comb.copy()

		G_Cop = copy.deepcopy(self.G)
		G_Cop.Collapse(self.vi, self.vj)
		Node_Cop = Node(G_Cop, self.S, self.upper_bound, self.lower_bound)
		for column in self.mlp.columns:
			if column[self.vi] + column[self.vj] == 1:
				continue
			Node_Cop.columns.append(column)
		for cutting_plane in self.mlp.cutting_planes:
			if cutting_plane[self.vi] + cutting_plane[self.vj] == 1:
				continue
			Node_Cop.cutting_planes.append(cutting_plane)
		for candidate_column, weight in self.mlp.candidate_columns:
			if candidate_column[self.vi] + candidate_column[self.vj] == 1:
				continue
			Node_Cop.candidate_columns.append( (candidate_column, weight) )
		Node_Cop.divide_comb = self.divide_comb.copy()
		Node_Cop.collapse_comb = self.collapse_comb.copy() + [(self.vi, self.vj)]
		return Node_Div, Node_Cop
