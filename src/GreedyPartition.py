#!/bin/python3

from src.graph import Graph
import numpy as np

def GreedyPartition(graph: Graph, S: int):
	G = graph.Edges
	n = len(G)
	K = n // S
	nodes = list(range(n))
	
	# 步骤 2: 找出最大边连接的两个点
	max_dist = -1
	vlist = []
	for i in range(n):
		for j in range(i + 1, n):
			if G[i][j] > max_dist:
				max_dist = G[i][j]
				vlist = [i, j]
	
	# 步骤 3: 扩展 vlist 到 K 个点
	remaining = set(nodes) - set(vlist)
	while len(vlist) < K:
		best_node = None
		best_score = -1
		for v in remaining:
			total = sum(G[v][u] for u in vlist)
			if total > best_score:
				best_score = total
				best_node = v
		assert(best_node != None)
		vlist.append(best_node)
		remaining.remove(best_node)

	# 步骤 4: 初始化 solution
	solution = [[v] for v in vlist]

	# 步骤 5: 将剩余点分配到最佳的 clique
	for v in remaining:
		best_max_edge = float('inf')
		best_index = -1

		minLen = n
		for idx in range(K):
			if minLen > len(solution[idx]):
				minLen = len(solution[idx])

		for idx in range(K):
			if len(solution[idx]) > minLen:
				continue
			temp_clique = solution[idx] + [v]
			# 找到当前 clique 中的最大边
			max_edge: float = max(G[i][j] for i in temp_clique for j in temp_clique if i != j)
			if max_edge < best_max_edge:
				best_max_edge = max_edge
				best_index = idx
		solution[best_index].append(v)

	clique_list = solution
	solution = []
	for clique in clique_list:
		clique_one_hot = [0] * n
		for v in clique:
			clique_one_hot[v] = 1
		solution.append(clique_one_hot)
	return solution

def GreedyPartition2(graph: Graph, S: int):
	edges = graph.Edges
	degree = [graph.n-1] * graph.n
	sortedEdge = graph.sortedEdgeName

	for i,j in sortedEdge:
		degree[i] -= 1
		degree[j] -= 1
		if degree[i] == S:
			break
		if degree[j] == S:
			break

"""
# 示例输入用法（你可以替换 G 为自己的数据）
if __name__ == "__main__":
	# 随机生成一个 10 节点的完全图示例（对称矩阵）
	np.random.seed(0)
	n = 49
	G = np.random.uniform(0, 100, size=(n, n))
	G = (G + G.T) / 2  # 保证对称
	np.fill_diagonal(G, 0)  # 对角线为 0

	solution = GreedyPartition(G.tolist(), K=8)
	print("Solution:")
	for group in solution:
		print(group)
"""
