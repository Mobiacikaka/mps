import gurobipy
import numpy, time
from gurobipy import GRB

from graph import Graph
from node import Node

def PrintSolution(sol: list[gurobipy.Var]):
	for var in sol:
		if var.X == 1.0:
			print(var.VarName)

def BranchAndPrice(n: int, S: int):
	OriginalGraph = Graph(n)

	node_count = 0
	upper_bound, lower_bound = float('inf'), 0
	root_node = Node(
		G=OriginalGraph,
		S=S,
		upper_bound=upper_bound,
		lower_bound=lower_bound,
	)
	root_node.ROOT_FLAG = True
	candidate_node = [root_node]

	optimum_mlp = None
	optimum_divide_combo = []
	optimum_collapse_combo = []

	while candidate_node:
		node = candidate_node.pop(0)
		node.create_model()
		node.G.PrintGraph(f'Graph_{node_count}.txt')

		if node.lower_bound >= upper_bound:
			print('LOG::PRUNE BY BOUND')
			continue

		model_status = node.optimize()
		node_count += 1
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
				optimum_mlp = node.mlp
				optimum_divide_combo = node.divide_comb
				optimum_collapse_combo = node.collapse_comb
			continue
		else:
			pass

		if node.is_child_problem():
			print('LOG::Branching, branched by', node.vi, node.vj)
			Node_Div, Node_Cop = node.get_child_problem()
			candidate_node.append(Node_Div)
			candidate_node.append(Node_Cop)

	print('upper_bound: ', upper_bound)
	print('Divided Nodes', optimum_divide_combo)
	print('Collapsed Nodes', optimum_collapse_combo)

	assert(optimum_mlp != None)
	optimum_mlp.model.optimize()
	sol = optimum_mlp.model.getVars()
	for i in range(optimum_mlp.n_col):
		if sol[i].X == 1.0:
			print(sol[i].VarName, optimum_mlp.columns[i])

if __name__ == '__main__':
	time_start = time.time()

	# numpy.random.seed(60)
	# BranchAndPrice(50, 7)
	numpy.random.seed(11)
	BranchAndPrice(29, 7)
	# numpy.random.seed(5)
	# BranchAndPrice(15, 4)
	# numpy.random.seed(0)
	# BranchAndPrice(21, 5)

	time_end = time.time()
	print('Total Time: ', time_end - time_start)
