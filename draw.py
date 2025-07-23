#!/bin/python3

from src.RandomPartition import RandomPartition
from src.graph import Graph
import json

def main():
	N_list = list(range(20, 50))
	S_list = [4,5,6,7,8]
	seed_list = list(range(0, 10))

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
			print(f'N {N} S {S} seed {seed} file not exist')

	for arg in args:
		N, S, seed = arg
		data = data_dict[arg]
		Edges = data['edges']
		graph = Graph(Edges=Edges)
		trial_number = 10
		for _ in range(trial_number):
			solution = RandomPartition(graph, S)


if __name__ == '__main__':
	main()
