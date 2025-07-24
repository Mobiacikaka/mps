from gurobipy import GRB
from src.graph import Graph
from src.node import Node
from utils.analyzer import UnfoldSolution

def BranchAndPrice(graph: Graph, S: int, verbose: bool=True):
	OriginalGraph = graph

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

	total_instances = 0
	solved_exactly = 0

	while candidate_node:
		node = candidate_node.pop(0)
		total_instances += 1
		node.create_model()

		if node.lower_bound >= upper_bound:
			if verbose:
				print('B&P::PRUNE BY BOUND')
			continue

		model_status = node.optimize()
		solved_exactly += 1
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

	print()
	print('Total instances: ', total_instances)
	print('Solved exactly: ', solved_exactly)
	print('Upper bound: ', upper_bound)
	print('Divided Nodes', optimum_divide_combo)
	print('Collapsed Nodes', optimum_collapse_combo)

	assert(optimum_mlp != None)
	optimum_mlp.to_int()
	optimum_mlp.model.optimize()
	sol = optimum_mlp.model.getVars()
	print('Accepted Columns:')
	solution = []
	for i in range(optimum_mlp.n_col):
		if sol[i].X != 0.0:
			print(sol[i].VarName, sol[i].X, optimum_mlp.columns[i])
			solution.append(optimum_mlp.columns[i])

	print()
	print('Total Columns Generated: ', optimum_mlp.n_col)
	print('Total Cutting Planes Generated: ', optimum_mlp.n_cup)

	return UnfoldSolution(solution, optimum_collapse_combo)
