#!/bin/python3

import matplotlib.pyplot as plt
from src.RandomPartition import RandomPartition
from src.GreedyPartition import GreedyPartition
from src.graph import Graph
import utils.analyzer as al
import json
import numpy

def main():
	N = 49
	S_list = [4, 5, 6, 7, 8]
	seed_list = list(range(0, 10))

	x_val = S_list

def main2():
	# N_list = list(range(20, 30))
	S_list = [4,5,6,7,8]
	seed_list = list(range(0, 10))
	N_list = [49]
	# S_list = [4]
	# seed_list = [0]

	args = [
		(N, S, seed)
		for N in N_list
		for S in S_list
		for seed in seed_list
	]

	data_dict = {}

	for N, S, seed in args:
		data = None
		try:
			f = open(f'./DATA/N_{N}_S_{S}_seed_{seed}.json', 'r')
			data = json.load(f)
			data_dict[(N, S, seed)] = data
		except:
			data_dict[(N, S, seed)] = None
			print(f'N {N} S {S} seed {seed} file not exist')

	result_BEST = {}
	result_BRC = {}
	result_RANDOM = {}
	result_GREEDY= {}

	for arg in args:
		N, S, seed = arg
		data = data_dict.get(arg, None)
		if data == None:
			continue
		Edges = data['edges']
		graph = Graph(Edges=Edges)

		## Random Partition trials
		RP_trial_number = 100
		maxEdges = []
		solution = []
		for _ in range(RP_trial_number):
			solution = RandomPartition(graph, S)
			# print(solution)
			maxEdgeRank = al.MaxEdgeRank(graph, solution)
			# print(maxEdge)
			maxEdges.append(maxEdgeRank)
		
		print(arg)
		result_BEST[arg] = al.MinimumPossibleRankInTheory(N, S)
		result_BRC[arg] = al.MaxEdgeRank(graph, data['solution'])
		sol_Greedy = GreedyPartition(graph, S)
		result_GREEDY[arg] = al.MaxEdgeRank(graph, sol_Greedy)
		result_RANDOM[arg] = min(maxEdges)

		# print("GREEDY")
		# for sol in sol_Greedy:
		# 	print(sum(sol))
		# print("BPC")
		# for sol in data['solution']:
		# 	print(sum(sol))
		# return

	for N in N_list:
		for S in S_list:
			BRC = []
			RANDOM = []
			GREEDY = []
			for seed in seed_list:
				data = result_BRC.get((N, S, seed), None)
				if data == None:
					continue
				BRC.append(data)

				data = result_GREEDY.get((N, S, seed), None)
				if data == None:
					continue
				GREEDY.append(data)

				data = result_RANDOM.get((N, S, seed), None)
				if data == None:
					continue
				RANDOM.append(data)

			print(numpy.mean(BRC))
			print(numpy.mean(RANDOM))
			print(numpy.mean(GREEDY))
			print()

if __name__ == '__main__':
	main()
