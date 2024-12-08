import numpy, time
from gurobipy import GRB

from graph import Graph
from node import Node

def BranchAndPrice(n: int, S: int):
	OriginalGraph = Graph(n)
	OriginalGraph.PrintGraph()

	upper_bound, lower_bound = float('inf'), 0
	root_node = Node(
		G=OriginalGraph,
		S=S,
		upper_bound=upper_bound,
		lower_bound=lower_bound,
	)
	candidate_node = [root_node]
	current_optimun = []
	optimum_columns = []
	node_collapse_seq = []

	node_count = 0

	while candidate_node:
		node = candidate_node.pop(0)

		if node.lower_bound >= upper_bound:
			print('LOG::PRUNE BY BOUND')
			continue

		model_status = node.optimize()
		# if True:
		# 	file = open(f'columns_{node_count}.txt', 'w')
		# 	for column in node.mlp.columns:
		# 		file.write(f'{column}\n')
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
				current_optimun = node.solution
				optimum_columns = []
				for index in range(len(current_optimun)):
					if current_optimun[index].X == 1.0:
						optimum_columns.append(node.mlp.columns[index])
				node_collapse_seq = node.collapse_comb.copy()
			continue
		else:
			pass

		if node.is_child_problem():
			print('LOG::Branching, branched by', node.vi, node.vj)
			Node_Div, Node_Cop = node.get_child_problem()
			candidate_node.append(Node_Div)
			candidate_node.append(Node_Cop)

	print('upper_bound: ', upper_bound)
	# print('optimum: ', current_optimun)
	i = 0
	print('Collapsed Nodes', node_collapse_seq)
	for var in current_optimun:
		if var.X == 1.0:
			print(var.VarName, optimum_columns[i])
			i += 1

if __name__ == '__main__':
	time_start = time.time()

	# numpy.random.seed(60)
	# BranchAndPrice(50, 7)
	# numpy.random.seed(11)
	# BranchAndPrice(29, 7)
	numpy.random.seed(5)
	BranchAndPrice(15, 4)

	time_end = time.time()
	print('Total Time: ', time_end - time_start)
