import gurobipy as gp
from gurobipy import GRB

class Graph:
	def __init__(self, n: int) -> None:
		self.n = n
		self.V, self.a, self.E = self.__createGraph__(self.n)
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
		for v in self.V:
			print(str(v), end='\t')
		print('\nEdges:')
		for edges in self.E:
			for edge in edges:
				print(str(edge), end='\t')
			print()
		print()

class Node:
	def __init__(self, model: gp.Model, upper_bound: float, lower_bound: float, candidate_vars: list) -> None:
		self.model = model
		self.upper_bound, self.lower_bound = upper_bound, lower_bound
		self.candidate_vars = candidate_vars ## candidate columns

	def optimize(self, solve):
		self.obj_values, self.solution = solve(self.model)
		if self.obj_values == None:
			return "infeasible"
		return "feasible"

	def update_upper_bound(self):
		self.upper_bound = self.obj_values
		assert(self.lower_bound <= self.upper_bound), "upper bound is less than lower bound"

	def update_lower_bound(self):
		if self.lower_bound < self.obj_values:
			self.lower_bound = self.obj_values
			assert(self.lower_bound <= self.upper_bound), "upper bound is less than lower bound"

	def is_integer(self):
		for var in self.solution:
			if 0 < var.x and var.x < 1:
				return False
		return True

	def is_child_problem(self):
		if self.candidate_vars:
			return True
		return False

	def get_child_problem(self):
		## TODO
		self.child_left, self.child_right = self.model.copy(), self.model.copy()
		branch_index, self.candidate_child_vars = self.choice_branch(self.candidate_vars)
		self.child_left.addConstr(self.child_left.getVars()[branch_index] == 0)
		self.child_right.addConstr(self.child_right.getVars()[branch_index] == 1)
		node_left = Node(self.child_left, self.upper_bound, self.lower_bound, self.candidate_child_vars)
		node_right = Node(self.child_left, self.upper_bound, self.lower_bound, self.candidate_child_vars)
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

def Main():
	n = 10
	S = 3
	G = Graph(n)

	## TODO
	model = gp.Model('Clique Partition')
	x = model.addVars(1, name='x', vtype=GRB.BINARY, obj=G.weight())
	# model.setObjective()
	model.addConstrs(
		gp.quicksum(x[i] for i in range(len(x))) == 1 for _ in range(G.n)
	)
	model.optimize()
	model.write('model_integer.lp')

	upper_bound, lower_bound = float('inf'), 0.0
	model_relax = model.relax()
	root_node = Node(model=model_relax, upper_bound=upper_bound, lower_bound=lower_bound, candidate_vars=[0])
	candidate_node = [root_node]
	current_optimum = None

	while candidate_node:
		node, candidate_node = choice_node(candidate_node)
		if node.upper_bound <= lower_bound:
			print('prune by bound')
			continue
		model_status = node.optimize(heuristic_solve)
		if model_status == 'infeasible':
			print('prune by infeasibility')
			continue
		node.update_lower_bound()
		if node.lower_bound >= lower_bound:
			print('prune by bound')
			continue
		if node.is_integer():
			node.update_upper_bound()
			if node.upper_bound < upper_bound:
				upper_bound = node.upper_bound
				current_optimum = node.solution
			continue
		if node.is_child_problem():
			child_node1, child_node2 = node.get_child_problem()
			candidate_node.append(child_node1)
			candidate_node.append(child_node2)
	
	print('lower bound: ', lower_bound)
	print('optimum: ', current_optimum)

if __name__ == '__main__':
	Main()
