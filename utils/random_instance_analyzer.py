import os, ast
import matplotlib.pyplot as plt

def ReadFolder(folder_name: str) -> dict:
	logfile = None
	try:
		logfile = open(f'{folder_name}/BranchAndPrice.log', 'r')
	except:
		print(folder_name, 'ERROR')
	if logfile == None:
		return {}
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
	attribute['solution'] = solution

	return attribute

def UnfoldSolution(solution_list: list, collapsed_comb: list) -> list:
	for solution in solution_list:
		for i in range(len(collapsed_comb), 0, -1):
			x, y = collapsed_comb[i]
			solution.insert(y, solution[x])
	return solution_list

def main():
	home_dir = os.getcwd()
	test_dir: str = 'test/RANDOM_OLD'

	seed_list = list(range(0, 10))
	N_list = list(range(20, 50))
	S_list = [4, 5, 6, 7, 8]

	AttributeList = []
	for N in N_list:
		for S in S_list:
			for seed in seed_list:
				test_folder_name = f'{home_dir}/{test_dir}/N_{N}/S_{S}/{seed}'
				attr: dict = ReadFolder(test_folder_name)
				if attr == {}:
					continue
				attr['N'] = N
				attr['S'] = S
				attr['seed'] = seed
				AttributeList.append(attr)

	for attr in AttributeList:
		print(attr)
		UnfoldSolution(attr['solution'], attr['collapsed'])
		print(attr)
		print()

	# for attribute in AttributeList:
	# 	if attribute['N'] != 20:
	# 		continue

if __name__ == '__main__':
	main()
