import gurobipy, math, itertools, copy
from gurobipy import GRB
from graph import Graph
import heuristic

class MLP:
	def __init__(
		self,
		G: Graph,
		S: int,
		columns: list=[],
		cutting_planes: list=[],
		candidate_columns: list=[],
	) -> None:
		self.G = G
		self.S = S

		## columns
		self.columns = copy.deepcopy(columns)
		self.n_col = 0

		## cutting planes
		self.cutting_planes = copy.deepcopy(cutting_planes)
		self.n_cup = len(self.cutting_planes)
		self.candidate_columns_cp = []

		## candidate columns
		self.candidate_columns = candidate_columns

	def __set_vars(self) -> None:
		if len(self.columns) > 0:
			return
		column = [1 for _ in range(self.G.n)]
		self.columns.append(column)
		self.x.append(
			self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
		)
		self.n_col += 1

	def __set_vars2(self) -> None:
		## Add the parent node's columns
		for column in self.columns:
			self.x.append(
				self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
			)
			self.n_col += 1

		## Add the whole vertex set
		if True:
			column = [1 for _ in range(self.G.n)]
			if column not in self.columns:
				self.columns.append(column)
				self.x.append(
					self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
				)
				self.n_col += 1

		## Add the Heuristic Algorithm from [14]
		clusters = heuristic.SolveGraphByHeuristic(self.G, self.S)
		for cluster in clusters:
			column = [int(i in cluster) for i in range(self.G.n)]
			if column in self.columns:
				continue
			self.columns.append(column)
			self.x.append(
				self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
			)
			self.n_col += 1

		closest_vertex = [
			sorted(self.G.V, key=lambda x: self.G.E[i][x])
			for i in range(self.G.n)
		]

		## include the clusters composed of the closest S and S+1 vertices to each vertex in the initial formulation
		for i in range(self.G.n):
			cluster = closest_vertex[i][:self.S]
			column = [int(j in cluster) for j in range(self.G.n)]
			if column in self.columns:
				continue
			self.x.append(
				self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
			)
			self.n_col += 1
			self.columns.append(column)

		for i in range(self.G.n):
			cluster = closest_vertex[i][:self.S+1]
			column = [int(j in cluster) for j in range(self.G.n)]
			if column in self.columns:
				continue
			self.x.append(
				self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
			)
			self.n_col += 1
			self.columns.append(column)

		pass

	def __set_contrs(self) -> None:
		## n vertexes
		assert(len(self.x) == len(self.columns) == self.n_col), \
		f'size(x)={len(self.x)}, size(columns)={len(self.columns)}, n_col={self.n_col}'
		self.model.addConstrs(
			gurobipy.quicksum(
				self.x[i] * self.columns[i][j] for i in range(self.n_col)
			) == 1 for j in range(self.G.n)
		)

		## sum(x_P) <= k
		self.model.addConstr(
			gurobipy.quicksum(
				self.x[i] for i in range(len(self.x))
			) <= math.floor(self.G.n / self.S)
		)

		## cutting planes
		for Qi in self.cutting_planes:
			k = 0
			for i in range(self.G.n):
				k += Qi[i] * self.G.a[i]
			k = k // self.S + 1
			self.model.addConstr(
				gurobipy.quicksum(
					self.x[i] * int(heuristic.subset(self.columns[i], Qi))
					for i in range(self.n_col)
				) <= k - 1
			)

	def __generate_candidate_columns(self):
		if len(self.candidate_columns) > 0:
			return
		## TODO: consider G.a
		closest_vertex = [
			sorted(self.G.V, key=lambda x: self.G.E[i][x])
			for i in range(self.G.n)
		]
		for i in range(self.G.n):
			indexes = closest_vertex[i][:2*self.S]
			for size in range(self.S, self.S * 2):
				for cluster in itertools.combinations(indexes, size):
					column = [int(i in cluster) for i in range(self.G.n)]
					weight = self.G.Weight(column)
					self.candidate_columns.append( (column, weight) )
		## cutting planes candidate columns

	def create_model(self):
		self.x = []
		self.model = gurobipy.Model('Master')
		self.__generate_candidate_columns()
		self.__set_vars2()
		self.__set_contrs()

		## generate cutting planes' candidate column
		for Qi in self.cutting_planes:
			assert(len(Qi) == self.G.n)
			Qi_indexes = [i for i in range(self.G.n) if Qi[i]]
			for size in range(self.S, self.S * 2):
				for cluster in itertools.combinations(Qi_indexes, size):
					column = [int(x in cluster) for x in range(self.G.n)]
					weight = self.G.Weight(column)
					self.candidate_columns_cp.append( (column, weight) )

		return

	def solve(self, flag = 0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()
		return self.model.getVars()

	def get_dual_vars(self):
		dual_values = [constr.getAttr(GRB.Attr.Pi) for constr in self.model.getConstrs()]
		pi = dual_values[:self.G.n]
		sigma = dual_values[self.G.n]
		sigma_list = []
		if len(dual_values) > self.G.n+1:
			sigma_list = dual_values[self.G.n+1:]
		return pi, sigma, sigma_list

	def update_contrs(self, column_coeff: list):
		## same column assertion
		# assert(sum([column_coeff[i] * self.G.a[i] for i in range(self.G.n)]) >= self.S)
		assert(column_coeff not in self.columns), f'Generated a same column {column_coeff}'
		self.columns.append(column_coeff)

		_column_coeff = column_coeff
		column_coeff = _column_coeff.copy()
		column_coeff.append(1)
		for i in range(len(self.cutting_planes)):
			column_coeff.append(
				int(
					heuristic.subset(_column_coeff, self.cutting_planes[i])
				)
			)
		column = gurobipy.Column(column_coeff, self.model.getConstrs())

		self.model.addVar(
			obj=self.G.Weight(column_coeff),
			lb=0,
			vtype=GRB.CONTINUOUS,
			name='x'+str(self.n_col),
			column=column
		)
		self.n_col += 1

	def print_status(self):
		print('master objective value: {}'.format(self.model.ObjVal))

	def to_int(self):
		for x in self.model.getVars():
			x.setAttr('VType', GRB.BINARY)

	def is_integer(self):
		for x in self.model.getVars():
			if x.X > 0 and x.X < 1:
				return False
		return True

	def write(self, filename='model.lp'):
		self.model.write(filename)

	def AddCuttingPlanesMLP(self, Q: list):
		xlp = self.model.getVars()
		for Qi in Q:
			self.model.addConstr(
				gurobipy.quicksum(
					xlp[i] * int(heuristic.subset(self.columns[i], Qi))
					for i in range(len(xlp))
				) <= sum(Qi) // self.S
			)

		for Qi in Q:
			assert(len(Qi) == self.G.n)
			assert(Qi not in self.cutting_planes), f'Generated a duplicated cutting plane {Qi}'
			self.cutting_planes.append(Qi)

			Qi_indexes = [i for i in range(self.G.n) if Qi[i]]
			for size in range(self.S, self.S * 2):
				for cluster in itertools.combinations(Qi_indexes, size):
					column = [int(x in cluster) for x in range(self.G.n)]
					weight = self.G.Weight(column)
					self.candidate_columns_cp.append( (column, weight) )
		pass
