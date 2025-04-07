#!/bin/python3
import subprocess

if __name__ == '__main__':
	seed_list = list(range(0, 1))
	N_list = [20, 21, 22, 23]
	S_list = [4]

	for seed in seed_list:
		for N in N_list:
			for S in S_list:
				subprocess.run(
					[
						'echo', f'\"{seed}\n{}\"', '|',
	  					'python', './src/BranchPriceCut.py',
						'>', 'log.txt',
					]
				)
