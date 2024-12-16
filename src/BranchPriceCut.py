import numpy, time
from gurobipy import GRB

from graph import Graph
from node import Node

def BranchAndPrice(n: int, S: int, verbose: bool=True):
	OriginalGraph = Graph(n)
	OriginalGraph.PrintGraph()

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

	lp_obj_value = float('inf')

	while candidate_node:
		node = candidate_node.pop(0)
		node.create_model()

		if node.lower_bound >= upper_bound:
			if verbose:
				print('B&P::PRUNE BY BOUND')
			continue

		model_status = node.optimize()
		node_count += 1
		if model_status == GRB.INFEASIBLE:
			if verbose:
				print('B&P::PRUNE BY INFEASIBILITY')
			continue
		else:
			if lp_obj_value > node.mlp.model.ObjVal:
				lp_obj_value = node.mlp.model.ObjVal
			if verbose:
				print('B&P::OPTIMUM', node.mlp.model.ObjVal)

		node.update_lower_bound()
		if node.lower_bound >= upper_bound:
			if verbose:
				print('B&P::PRUNE BY BOUND')
			continue

		if node.is_integer():
			if verbose:
				print('B&P::IS INTEGER')
			node.update_upper_bound()
			if node.upper_bound < upper_bound:
				if verbose:
					print('B&P::IS OPTIMUM')
				upper_bound = node.upper_bound
				optimum_mlp = node.mlp
				optimum_divide_combo = node.divide_comb
				optimum_collapse_combo = node.collapse_comb

				if node.upper_bound / lp_obj_value < 1.05:
					## exit the loop as optimum
					break
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
	optimum_mlp.to_int()
	optimum_mlp.model.optimize()
	sol = optimum_mlp.model.getVars()
	for i in range(optimum_mlp.n_col):
		if sol[i].X != 0.0:
			print(sol[i].VarName, sol[i].X, optimum_mlp.columns[i])

if __name__ == '__main__':
	time_start = time.time()

	# numpy.random.seed(0)
	# BranchAndPrice(50, 4)
	# numpy.random.seed(60)
	# BranchAndPrice(36, 7)
	numpy.random.seed(60)
	BranchAndPrice(29, 7)
	# numpy.random.seed(2)
	# BranchAndPrice(23, 4)
	# numpy.random.seed(5)
	# BranchAndPrice(15, 4)

	# for seed in range(0, 5):
	# 	print(f'\nseed={seed}')
	# 	numpy.random.seed(seed)
	# 	for n in [41, 42, 43]:
	# 		BranchAndPrice(n, 4, verbose=False)
	# 		print()

	time_end = time.time()
	print('Total Time: ', time_end - time_start)
