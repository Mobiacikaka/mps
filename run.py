#!/bin/python3
import os
import multiprocessing
import subprocess

def Processing(seed: int):
	N_list: list[int] = list(range(20, 50))
	S_list: list[int] = list(range( 4,  9))

	for S in S_list:
		os.system(f'mkdir -p {home_dir}/{test_dir}/S_{S}')
		for N in N_list:
			cwd: str = f'{home_dir}/{test_dir}/S_{S}/N_{N}/{seed}'
			os.system(f'mkdir -p {cwd}')
			command = f'echo "{seed}\\n{N}\\n{S}\\n" | python {home_dir}/src/BranchPriceCut.py'
			logfile = open(f'{cwd}/BranchAndPrice.log', 'w')

			subprocess.Popen(
				command,
				cwd=cwd,
				shell=True,
				stdout=logfile,
			)

	return

if __name__ == '__main__':
	home_dir: str = os.getcwd()
	test_dir: str = 'test'

	os.system(f'mkdir -p {home_dir}/{test_dir}')

	seed_list: list[list[int]] = [[i] for i in range(0, 10)]

	pool = multiprocessing.Pool(4)
	pool.starmap(Processing, seed_list)
	pool.close()
	pool.join()
