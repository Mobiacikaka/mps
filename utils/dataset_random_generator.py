import math, numpy, os

def EuclideanDistance(vi: tuple[int, int], vj: tuple[int, int]):
	return math.sqrt(
		(vi[0] - vj[0])**2 + (vi[1] - vj[1]) ** 2
	)

def GenerateTypeIGraph(n: int):
	maxLen = 100
	all_vertex = []
	for i in range(maxLen):
		for j in range(maxLen):
			all_vertex.append( (i, j) )

	Vertex_pos = numpy.random.choice(list(range(len(all_vertex))), n)

	Edges = [
		[
			0.0 for _ in range(n)
		]
		for _ in range(n)
	]
	for i in range(n-1):
		for j in range(i+1, n):
			Edges[i][j] = Edges[j][i] = EuclideanDistance(all_vertex[Vertex_pos[i]], all_vertex[Vertex_pos[j]])

	return Edges

def GenerateTypeIIGraph(n: int):
	Edges = [
		[
			0.0 for _ in range(n)
		]
		for _ in range(n)
	]
	for i in range(n-1):
		for j in range(i+1, n):
			Edges[i][j] = Edges[j][i] = float(numpy.random.randint(99)+1)
	return Edges

def PrintGraph(Edges: list[list[float]], cwd: str):
	os.system(f'mkdir -p {cwd}')
	file = open(f'{cwd}/graph.csv', 'w')
	for edgeline in Edges:
		for edge in edgeline:
			file.write(str(edge)+',')
		file.write('\n')
	file.close()
	return

def PrintInput(S: int, cwd: str):
	os.system(f'mkdir -p {cwd}')
	file = open(f'{cwd}/input.txt', 'w')
	file.write(str(S))
	file.close()
	return

def main():
	seed_list = list(range(0, 10))
	N_list = list(range(20, 50))
	S_list = [4, 5, 6, 7, 8]

	home_dir = os.getcwd()
	test_dir = 'test/RANDOM'

	for N in N_list:
		for S in S_list:
			for seed in seed_list:
				numpy.random.seed(seed)
				Edges = GenerateTypeIGraph(N)
				folder_name = f'{home_dir}/{test_dir}/N_{N}/S_{S}/TEST{seed}'
				PrintGraph(Edges, folder_name)
				PrintInput(S, folder_name)

if __name__ == '__main__':
	main()
