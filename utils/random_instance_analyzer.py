import os, ast
import matplotlib.pyplot as plt

def UnfoldSolution(solution_list: list, collapsed_comb: list) -> list:
	for solution in solution_list:
		for i in range(len(collapsed_comb), 0, -1):
			x, y = collapsed_comb[i-1]
			solution.insert(y, solution[x])
	return solution_list

def ReadFolder(folder_name: str) -> dict | None:
	logfile = None
	graphfile = None
	try:
		logfile = open(f'{folder_name}/BranchAndPrice.log', 'r')
		graphfile = open(f'{folder_name}/graph.csv', 'r')
	except:
		print(folder_name, 'ERROR')
	if logfile == None or graphfile == None:
		return None

	## Read Log
	lines: list = logfile.readlines()
	attribute: dict = {}
	solution : list = [] ## solution lines
	for line in lines:
		if 'Total instances' in line:
			attribute['total instance'] = int(line.split(':')[1])
			continue
		if 'Solved exactly' in line:
			attribute['solve instance'] = int(line.split(':')[1])
			continue
		if 'Total Columns Generated' in line:
			attribute['column num']     = int(line.split(':')[1])
			continue
		if 'Total Cutting Planes Generated' in line:
			attribute['c-plane num']    = int(line.split(':')[1])
			continue
		if 'Upper bound' in line:
			attribute['upper bound']    = float(line.split(':')[1])
			continue
		if 'Total Time' in line:
			attribute['time']           = float(line.split(':')[1])
			continue
		if 'Divided Nodes' in line:
			attribute['divided'] = ast.literal_eval(line.strip('Divided Nodes '))
			continue
		if 'Collapsed Nodes ' in line:
			attribute['collapsed'] = ast.literal_eval(line.strip('Collapsed Nodes '))
			continue
		if ' 1.0 ' in line:
			solution.append(ast.literal_eval(line.split(' 1.0 ')[1]))
			continue
	if solution == []:
		return None
	attribute['solution'] = solution
	UnfoldSolution(attribute['solution'], attribute['collapsed'])

	## Read Graph
	lines = graphfile.readlines()
	edges: list = []
	for line in lines:
		line = '[' + line + ']'
		edges.append(ast.literal_eval(line))
	attribute['edges'] = edges

	return attribute

def ReadRandom():
	home_dir = os.getcwd()
	test_dir: str = 'test/RANDOM_OLD'

	## REAL TEST
	seed_list = list(range(0, 10))
	N_list = list(range(20, 50))
	S_list = [4, 5, 6, 7, 8]
	## LOCAL TEST
	# N_list = [20]
	# S_list = [4]
	# seed_list = [3]

	AttributeList: list = []
	for N in N_list:
		for S in S_list:
			for seed in seed_list:
				test_folder_name = f'{home_dir}/{test_dir}/S_{S}/N_{N}/{seed}'
				# test_folder_name = f'{home_dir}/{test_dir}/N_{N}/S_{S}/TEST{seed}'
				attribute: dict | None = ReadFolder(test_folder_name)
				if attribute == None:
					continue
				attribute['N'] = N
				attribute['S'] = S
				attribute['seed'] = seed
				AttributeList.append(attribute)

	return AttributeList
