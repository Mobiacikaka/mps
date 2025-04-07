#!/bin/python3
from os import system

if __name__ == '__main__':
	seed_list = list(range(0, 100))
	N_list = list(range(20, 51))
	S_list = [4, 7]

	for S in S_list:
		system(f'mkdir -p S{S}')
		for N in N_list:
			system(f'mkdir -p S{S}/N{N}')
			for seed in seed_list:
				folder = f'S{S}/N{N}/{seed}'
				system(f'mkdir -p {folder}')
				system(f'echo "{seed}\\n{N}\\n{S}\\n" | python ../src/BranchPriceCut.py > log.txt')
				system(f'mv Graph.txt    {folder}/')
				system(f'mv log.txt      {folder}/')
				system(f'mv master.lp    {folder}/')
				system(f'mv sub_model.lp {folder}/')
