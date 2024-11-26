import gurobipy, math
from gurobipy import GRB
from graph import Graph

class MLP:
	def __init__(self, G: Graph, S: int) -> None:
		self.G = G
		self.S = S
		self.n_col = 0 ##
		self.n_dim = 0 ## 变量数量

	def create_model(self):
		self.x = []
		self.model = gurobipy.Model('Master')
		self.__set_vars()
		self.__set_contrs()

	def solve(self, flag = 0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()
		return self.model.getVars()

	def get_dual_vars(self):
		pi = [self.constrs[i].getAttr(GRB.Attr.Pi) for i in range(len(self.constrs))]
		sigma = self.constrs2.getAttr(GRB.Attr.Pi)
		return pi, sigma

	def __set_contrs(self) -> None:
		self.constrs = self.model.addConstrs(
			gurobipy.quicksum( self.x[i] for i in range(len(self.x)) ) == 1 for _ in range(self.G.n)
		)
		self.constrs2 = self.model.addConstr(
			gurobipy.quicksum( self.x[i] for i in range(len(self.x)) ) <= math.floor(self.G.n / self.S)
		)

	def __set_vars(self) -> None:
		self.x.append(self.model.addVar(obj=self.G.Weight(), lb=0, vtype=GRB.CONTINUOUS, name='x0'))
		self.n_dim = 1
		self.n_col = 1
		self.columns = [[1] * self.G.n]
		self.constrsLen = [1] * self.G.n

	def update_contrs(self, column_coeff: list):
		## same column assertion
		assert(column_coeff not in self.columns), "Generated a same column"
		self.columns.append(column_coeff)
		for i in range(len(column_coeff)):
			self.constrsLen[i] += column_coeff[i]

		column_coeff = column_coeff.copy()
		column_coeff.append(1)
		column = gurobipy.Column(column_coeff, self.model.getConstrs())

		self.model.addVar(
			obj=self.G.Weight(column_coeff),
			lb=0,
			vtype=GRB.CONTINUOUS,
			name='x'+str(self.n_dim),
			column=column
		)
		self.n_dim += 1
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


	# def __set_vars(self):
		# self.columns = [[0] * self.G.n for _ in range(self.G.n // self.S)]
		# for i in range(self.G.n):
		# 	self.columns[i % (self.G.n // self.S)][i] = 1
		# for column in self.columns:
		# 	self.x.append(
		# 		self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
		# 	)
		# 	self.n_col += 1
		# 	for i in range(self.G.n):
		# 		self.constrsLen[i] += column[i]

		# self.x.append(self.model.addVar(obj=self.G.Weight(), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}'))
		# self.columns = [[1] * self.G.n]
		# self.n_col += 1
		# column_pool = []
		# for i in range(self.G.n):
		# 	for cluster in itertools.combinations(self.G.closest_vertex[i][:self.S*2], self.S):
		# 		column = [int(i in cluster) for i in range(self.G.n)]
		# 		price = self.G.Weight(column)
		# 		MaintainPool(column_pool=column_pool, column=column, price=price, MaxLen=100)

		# for column, _ in column_pool:
		# 	self.x.append(
		# 		self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
		# 	)
		# 	self.n_col += 1
		# 	self.columns.append(column)

		# self.x.append(self.model.addVar(obj=self.G.Weight(), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}'))
		# self.columns = [[1] * self.G.n]
		# self.n_col = 1
		# for i in range(self.G.n):
		# 	for cluster in itertools.combinations(self.G.closest_vertex[i][:self.S*2], self.S):
		# 		column = [int(i in cluster) for i in range(self.G.n)]
		# 		self.columns.append(column)
		# 		self.candidate_columns.remove(column)
		# 		self.x.append(
		# 			self.model.addVar(obj=self.G.Weight(column), lb=0, vtype=GRB.CONTINUOUS, name=f'x{self.n_col}')
		# 		)
		# 		self.n_col += 1

