import itertools, math, numpy
import gurobipy as gp
from gurobipy import GRB
from graph import Graph
from priceip import PriceIP

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

	def generate_columns_with_gurobi(self, G: Graph, subprob: PriceIP):
		try:
			pi = [self.model.getConstrs()[i].getAttr(GRB.Attr.Pi) for i in range(G.n)]
			sigma = self.model.getConstrs()[-1].getAttr(GRB.Attr.Pi)
		except:
			self.model.write('error.lp')
			print('\nExit with error: Cannot acquire pi')
			exit(0)

		subprob.set_objective(pi)
		subprob.solve()
		subprob.write()

		y = subprob.get_solution()
		print('Generate Column: ', y)
		reduced_cost = subprob.get_reduced_cost()
		print('reduced_cost-sigma: ', reduced_cost-sigma)

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

def createIP(n: int, S: int, G: Graph):
	## TODO
	model = gp.Model('Clique Partition')
	# n0 = 10 if n > 10 else n
	# P0 = list(itertools.combinations(list(range(n0)), S))
	# P1 = []
	# for comb in P0:
	# 	P = [0] * n
	# 	for i in comb:
	# 		P[i] = 1
	# 	P1.append(P)
	# x = []
	# for i in range(len(P1)):
	# 	x.append(model.addVar(vtype=GRB.BINARY, obj=G.weight(P1[i]), name='x'+str(i)))
	# 	# x.append(model.addVar(lb=0, ub=1, obj=G.weight(P1[i]), vtype=GRB.CONTINUOUS, name='x'+str(i)))
	# model.addConstrs(
	# 	gp.quicksum(x[i] * P1[i][j] for i in range(len(x))) == 1 for j in range(n)
	# )
	x0 = model.addVar(vtype=GRB.BINARY, obj=G.weight(), name='x0')
	model.addConstrs(
		x0 == 1 for _ in range(n)
	)
	model.addConstr(
		x0 <= math.floor(n / S)
	)
	return model

def Main():
	n = 5
	S = 2
	G = Graph(n)

	model = createIP(n, S, G)
	model.optimize()
	model.write('model_integer.lp')

	subprob = PriceIP(G, S)
	subprob.create_model()

	upper_bound, lower_bound = float('inf'), G.weight()
	model_relax = model.relax()
	root_node = Node(model=model_relax, upper_bound=upper_bound, lower_bound=lower_bound, candidate_vars=[0])
	candidate_node = [root_node]
	current_optimum = None
	bestmodel = model_relax

	while candidate_node:
		node, candidate_node = choice_node(candidate_node)
		if node.lower_bound <= upper_bound:
			print('prune by bound')
			continue

		model_status = node.optimize(heuristic_solve)

		if model_status == 'infeasible':
			print('prune by infeasibility')
			continue

		print('LOG: update_lower_bound')
		node.update_lower_bound()
		if node.lower_bound <= upper_bound:
			print('prune by bound')
			continue
		if node.is_integer():
			node.update_upper_bound()
			if node.upper_bound < upper_bound:
				upper_bound = node.upper_bound
				current_optimum = node.solution
				bestmodel = node.model
			continue

		print('LOG: generate_columns_with_gurobi')
		node.generate_columns_with_gurobi(G, subprob)

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
	G.__printGraph__()

if __name__ == '__main__':
	Main()
