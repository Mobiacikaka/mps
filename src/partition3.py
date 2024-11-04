import numpy
from graph import Graph
from masterlp import MLP
from priceip import PriceIP as SUB
import gurobipy as gp
from gurobipy import GRB

def heuristic_solve(problem: gp.Model):
	problem.Params.OutputFlag = 0
	problem.optimize()
	if problem.Status == GRB.INFEASIBLE:
		return None, None
	return problem.ObjVal, problem.getVars()

class Node:
	def __init__(self, model: gp.Model, lower_bound: float, upper_bound: float, candidate_vars: list, name='') -> None:
		self.model = model
		self.lower_bound = lower_bound
		self.upper_bound = upper_bound
		self.candidate_vars = candidate_vars
		self.name = name

	def optimize(self, solve):
		self.obj_values, self.solution = solve(self.model)
		if self.obj_values == None:
			return 'infeasible'
		return 'feasible'

	def update_upper_bound(self):
		self.upper_bound = self.obj_values
		assert(self.lower_bound <= self.upper_bound)

	def update_lower_bound(self):
		if self.lower_bound < self.obj_values:
			self.lower_bound = self.obj_values
			assert(self.lower_bound <= self.upper_bound)

	def is_integer(self):
		for var in self.solution:
			if var.x > 0 and var.x < 1:
				return False
		return True

	def is_child_problem(self):
		if self.candidate_vars:
			return True
		return False

	def get_child_problem(self):
		self.child_left, self.child_right = self.model.copy(), self.model.copy()
		branch_index, self.candidate_child_vars = self.choice_branch()
		self.child_left.addConstr(self.child_left.getVars()[branch_index] == 0)
		self.child_right.addConstr(self.child_right.getVars()[branch_index] == 1)
		node_left = Node(self.child_left, self.lower_bound, self.upper_bound, self.candidate_child_vars, self.name+'0')
		node_right = Node(self.child_right, self.lower_bound, self.upper_bound, self.candidate_child_vars, self.name+'1')
		return node_left, node_right

	def choice_branch(self):
		self.candidate_child_vars = self.candidate_vars.copy()
		branch_index = self.candidate_child_vars.pop(0)
		return branch_index, self.candidate_child_vars

	def write(self, filename='model.lp'):
		self.model.write(filename)

def choice_node(candidate_node: list) -> tuple[Node, list[Node]]:
	node = candidate_node.pop(0)
	return node, candidate_node

def ColumnGeneration() -> gp.Model:
	## 1. Initialize
	n = 21
	S = 5

	G = Graph(n)
	G.PrintGraph()

	master_problem = MLP(G, S)
	master_problem.create_model()

	sub_problem = SUB(G, S)
	sub_problem.create_model()

	## 2-8
	while True:
		## TODO
		## 2. Approximately solve the current LP relaxation
		master_problem.solve()
		master_problem.write()

		if master_problem.model.Status == GRB.INFEASIBLE:
			print('\nINFEASIBLE!\n')
			exit()

		## Generate columns using an IP solver
		pi, sigma = master_problem.get_dual_vars()
		sub_problem.set_objective(pi)
		sub_problem.solve()
		sub_problem.write()

		y = sub_problem.get_solution()
		print('Generate Column: ', y)
		reduced_cost = sub_problem.get_reduced_cost()

		if reduced_cost - sigma >= 0:
			break

		master_problem.update_contrs(column_coeff=y)

	master_problem.to_int()
	master_problem.solve(flag=1)
	master_problem.write()

	print()
	for x in master_problem.model.getVars():
		if x.X == 1.0:
			print(f'{x.VarName}={x.X}\t: {master_problem.model.getCol(x)}')
	print()
	return master_problem.model

def solve():
	# master_problem = ColumnGeneration()

	master_problem_int = gp.read('model_read.lp')
	master_problem = master_problem_int.relax()
	for x in master_problem.getVars():
		x.setAttr('ub', float('inf'))

	## Branching
	upper_bound, lower_bound = float('inf'), 0
	root_node = Node(
		model=master_problem,
		upper_bound=upper_bound,
		lower_bound=lower_bound,
		candidate_vars=list(range(len(master_problem.getVars())))
	)
	candidate_node = [root_node]
	current_optimun = None

	node_num = 0

	while candidate_node:
		node, candidate_node = choice_node(candidate_node)
		print('node', node.name)
		# node.write(f'Node{node_num}.lp')
		node_num += 1

		if node.lower_bound >= upper_bound:
			print('prune by bound')
			continue

		model_status = node.optimize(heuristic_solve)
		if model_status == 'infeasible':
			print('prune by infeasibility')
			continue

		# print(node.candidate_vars)
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
			child_node1, child_node2 = node.get_child_problem()
			candidate_node.append(child_node1)
			candidate_node.append(child_node2)

	print('upper_bound: ', upper_bound)
	print('optimum: ', current_optimun)
	for var in current_optimun:
		if var.X == 1.0:
			print(var.VarName)

if __name__ == '__main__':
	numpy.random.seed(60)
	solve()
