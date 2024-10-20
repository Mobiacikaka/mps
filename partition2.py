import itertools
import gurobipy as gp
from gurobipy import GRB
import numpy

class Graph:
	def __init__(self, n: int) -> None:
		self.n = n
		self.V, self.a, self.E = self.__createGraph__(self.n)
		print('weight:', self.weight())
		self.__printGraph__()
		# self.__sortEdge__()
		# self.__printGraph__()

	def __sortEdge__(self) -> None:
		EdgeName = [(i,j) for i in range(self.n-1) for j in range(i+1, self.n)]
		EdgeName = sorted(EdgeName, key=lambda x: self.E[x[0]][x[1]], reverse=True)
		self.EdgeValue = self.E
		for k in range(len(EdgeName)):
			i = EdgeName[k][0]
			j = EdgeName[k][1]
			self.E[i][j] = self.E[j][i] = 0.5**(k-20)

	def weight(self, subgraph: list=[]) -> int:
		if len(subgraph) == 0:
			subgraph = [1] * self.n
		return sum(
			[self.E[i][j] * subgraph[i] * subgraph[j]
			for i in range(self.n-1) for j in range(i+1, self.n)]
		)

	## Random create edges
	def __createGraph__(self, n: int):
		## vertex
		V = [i for i in range(n)]
		## vertex weight
		a = [1] * n
		## edges
		E = [ [ 0.0 for _ in range(n) ] for _ in range(n) ]
		for i in range(n-1):
			for j in range(i+1, n):
				E[i][j] = E[j][i] = float(numpy.random.randint(100) + 1)
		return V, a, E

	def __printGraph__(self):
		for edges in self.E:
			for edge in edges:
				print(str(edge), end='\t')
			print()
		print()

class PriceIP:
	def __init__(self, G: Graph, S: int) -> None:
		self.G = G
		self.S = S

	def create_model(self) -> None:
		self.model = gp.Model('sub model')
		self.y = self.model.addVars(self.G.n, lb=0, ub=1, vtype=GRB.INTEGER, name='y')
		self.model.addConstr( (gp.quicksum(self.G.a[i] * self.y[i] for i in range(self.G.n)) >= self.S) )

	def weight(self, subgraph):
		return gp.quicksum( (self.G.E[i][j] * subgraph[i] * subgraph[j]) for i in range(self.G.n-1) for j in range(i+1, self.G.n) )

	def set_objective(self, pi: list):
		self.model.setObjective(
			- gp.quicksum(pi[i] * self.y[i] for i in range(self.G.n))
			+ self.weight(self.y)
			, sense=GRB.MINIMIZE
		)

	def solve(self, flag=0):
		self.model.Params.OutputFlag = flag
		self.model.optimize()

	def get_solution(self):
		return [self.model.getVars()[i].x for i in range(self.G.n)]

	def get_reduced_cost(self):
		return self.model.ObjVal

	def write(self):
		self.model.write('sub_model.lp')

class Node:
	def __init__(self, model: gp.Model, upper_bound: float, lower_bound: float, candidate_vars: list) -> None:
		self.model = model
		self.upper_bound, self.lower_bound = upper_bound, lower_bound
		self.candidate_vars = candidate_vars ## candidate columns

	def optimize(self, solve):
		self.obj_values, self.solution = solve(self.model)
		if self.obj_values == None:
			return 'infeasible'
		return 'feasible'

	def update_upper_bound(self):
		self.upper_bound = self.obj_values
		assert(self.lower_bound <= self.upper_bound), 'upper bound is less than lower bound'

	def update_lower_bound(self):
		if self.lower_bound > self.obj_values:
			self.lower_bound = self.obj_values
			assert(self.lower_bound <= self.upper_bound), 'upper bound is less than lower bound'

	def is_integer(self):
		for var in self.solution:
			if 0 < var.x and var.x < 1:
				return False
		return True

	def is_child_problem(self):
		if self.candidate_vars:
			return True
		return False

	def generate_columns_with_gurobi(self, G, subprob: PriceIP):
		constrs = self.model.getConstrs()
		try:
			pi = [constrs[i].getAttr(GRB.Attr.Pi) for i in range(len(constrs))]
		except:
			self.model.write('error.lp')
			print('\nExit with error: Cannot acquire pi')
			exit(0)
		subprob.set_objective(pi)
		subprob.solve()
		y = subprob.get_solution()
		# reduced_cost = subprob.get_reduced_cost()
		subprob.write()
		column = None
		try:
			column = gp.Column(y, self.model.getConstrs())
		except:
			column = gp.Column(y+[0] * (len(self.model.getConstrs()) - len(y)), self.model.getConstrs())
		self.candidate_vars.append(self.candidate_vars[-1]+1)
		self.model.addVar(
			vtype=GRB.CONTINUOUS,
			obj=G.weight(y),
			name='x'+str(self.candidate_vars[-1]),
			column=column
		)
		print('generate_columns_with_gurobi: ', y)

	def get_child_problem(self):
		## TODO
		self.child_left, self.child_right = self.model.copy(), self.model.copy()
		branch_index, self.candidate_child_vars = self.choice_branch(self.candidate_vars)
		try:
			self.child_left.addConstr(self.child_left.getVars()[branch_index] == 0)
			self.child_left.write('child_left.lp')
			self.child_right.addConstr(self.child_right.getVars()[branch_index] == 1)
		except:
			print('candidate_vars', self.candidate_vars)
			print('branch_index', branch_index)
			print('getVars', self.child_left.getVars())
			exit()
		node_left = Node(self.child_left, self.upper_bound, self.lower_bound, self.candidate_child_vars)
		node_right = Node(self.child_right, self.upper_bound, self.lower_bound, self.candidate_child_vars)
		return node_left, node_right

	def choice_branch(self, candidate_vars: list):
		## TODO
		self.candidate_child_vars = candidate_vars.copy()
		branch_index = self.candidate_child_vars.pop(0)
		return branch_index, self.candidate_child_vars

	def write(self):
		self.model.write('model.lp')

def heuristic_solve(problem: gp.Model):
	problem.Params.OutputFlag = 0
	problem.optimize()
	if problem.Status == GRB.INFEASIBLE:
		return None, None
	return problem.ObjVal, problem.getVars()

def choice_node(candidate_node: list) -> tuple[Node, list]:
	node = candidate_node.pop(0)
	return node, candidate_node

def createIP(n, S, G):
	## TODO
	model = gp.Model('Clique Partition')
	n0 = 10 if n > 10 else n
	P0 = list(itertools.combinations(list(range(n0)), S))
	P1 = []
	for comb in P0:
		P = [0] * n
		for i in comb:
			P[i] = 1
		P1.append(P)
	x = []
	for i in range(len(P1)):
		x.append(model.addVar(vtype=GRB.BINARY, obj=G.weight(P1[i]), name='x'+str(i)))
		# x.append(model.addVar(lb=0, ub=1, obj=G.weight(P1[i]), vtype=GRB.CONTINUOUS, name='x'+str(i)))
	model.addConstrs(
		gp.quicksum(x[i] * P1[i][j] for i in range(len(x))) == 1 for j in range(n)
	)
	return model

def Main():
	n = 10
	S = 5
	gap = 1
	G = Graph(n)

	model = createIP(n, S, G)
	model.optimize()
	model.write('model_integer.lp')

	subprob = PriceIP(G, S)
	subprob.create_model()

	upper_bound, lower_bound = float('inf'), G.weight()
	model_relax = model.relax()
	root_node = Node(model=model_relax, upper_bound=upper_bound, lower_bound=lower_bound, candidate_vars=list(range(len(model.getVars()))))
	candidate_node = [root_node]
	current_optimum = None
	bestmodel = model_relax

	while candidate_node:
		node, candidate_node = choice_node(candidate_node)
		if node.upper_bound <= lower_bound:
			print('prune by bound')
			continue

		model_status = node.optimize(heuristic_solve)
		# print('LOG: generate_columns_with_gurobi')
		# node.generate_columns_with_gurobi(G, subprob)

		if model_status == 'infeasible':
			print('prune by infeasibility')
			continue

		print('LOG: update_lower_bound')
		node.update_lower_bound()
		if node.upper_bound <= lower_bound:
			print('prune by bound')
			continue
		if node.is_integer():
			node.update_upper_bound()
			if node.upper_bound < upper_bound:
				upper_bound = node.upper_bound
				current_optimum = node.solution
				bestmodel = node.model
			continue

		if node.is_child_problem():
			child_node1, child_node2 = node.get_child_problem()
			candidate_node.append(child_node1)
			candidate_node.append(child_node2)
	
	print('lower bound: ', lower_bound)
	print('optimum: ', current_optimum)
	bestx = bestmodel.getVars()
	for x in bestx:
		if x.X == 1.0:
			print(bestmodel.getCol(x))

if __name__ == '__main__':
	Main()
