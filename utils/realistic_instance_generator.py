import numpy, math, os, pandas

def euclidean_distance(lat1, lon1, lat2, lon2):
	# 将经纬度从度数转换为弧度
	lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

	# 地球半径（单位：米）
	R = 6371000

	# 计算横纵坐标差值
	x = (lon2 - lon1) * math.cos((lat1 + lat2) / 2)
	y = lat2 - lat1

	# 计算欧式距离
	distance = R * math.sqrt(x**2 + y**2)
	return distance

def ReadExcel(index: int):
	home_dir = os.getcwd()
	dataset_dir: str = 'datasets/Topology Bench/csv_data/small_synthetic_networks'
	filename = f'{home_dir}/{dataset_dir}/TOP_{index}.xlsx'
	df = pandas.read_excel(filename, sheet_name=f'Nodes_TOP{index}')
	n = len(df)
	longitude = df['Longitude'].tolist()
	latitude = df['Latitude'].tolist()
	VerticesPositionList = [
		(latitude[i], longitude[i])
		for i in range(n)
	]
	Edges = [
		[0.0 for _ in range(n)] for _ in range(n)
	]
	for i in range(n-1):
		for j in range(i+1, n):
			Edges[i][j] = Edges[j][i] = euclidean_distance(VerticesPositionList[i][0], VerticesPositionList[i][1], VerticesPositionList[j][0], VerticesPositionList[j][1])

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
	home_dir = os.getcwd()
	test_dir = 'test/TopologyBench'
	S_list = [4, 5, 6, 7, 8]

	for index in range(50):
		Edges = ReadExcel(index)
		for S in S_list:
			folder_name = f'{home_dir}/{test_dir}/TEST{index}/S_{S}'
			print(folder_name, S)
			PrintGraph(Edges, folder_name)
			PrintInput(S, folder_name)
	return

if __name__ == '__main__':
	main()
