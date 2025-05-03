#!/bin/python3
import os
import multiprocessing
import subprocess
import time

def Processing(seed: int, N: int, S: int):
	os.system(f'mkdir -p {home_dir}/{test_dir}/S_{S}')
	cwd: str = f'{home_dir}/{test_dir}/S_{S}/N_{N}/{seed}'
	os.system(f'mkdir -p {cwd}')
	command = f'echo "{seed}\\n{N}\\n{S}\\n" | python {home_dir}/src/BranchPriceCut.py'
	logfile = open(f'{cwd}/BranchAndPrice.log', 'w')

	os.system(f'echo [{time.strftime("%H:%M:%S")}]\tseed: {seed}\tN: {N}\tS: {S} >> {runlog}')
	subprocess.run(
		command,
		cwd=cwd,
		shell=True,
		stdout=logfile,
	)
	os.system(f'echo [{time.strftime("%H:%M:%S")}]\tseed: {seed}\tN: {N}\tS: {S} FINISHED >> {runlog}')

	return

def run():
	seed_min: int = int(input('MIN SEED: '))
	seed_max: int = int(input('MAX SEED: '))
	N_min: int = int(input('MIN N: '))
	N_max: int = int(input('MAX N: '))
	S_min: int = int(input('MIN S: '))
	S_max: int = int(input('MAX S: '))

	seed_list: list[int] = list(range(seed_min, seed_max+1))
	N_list: list[int] = list(range(N_min, N_max+1))
	S_list: list[int] = list(range(S_min, S_max+1))

	args = [
		(seed, N, S)
		for seed in seed_list
		for N in N_list
		for S in S_list
	]

	os.system(f'echo seed_list: {seed_list} > {runlog}')
	os.system(f'echo N_list: {N_list} >> {runlog}')
	os.system(f'echo S_list: {S_list} >> {runlog}')

	pool = multiprocessing.Pool(processes=8)
	pool.starmap(Processing, args)
	pool.close()
	pool.join()

if __name__ == '__main__':
	home_dir: str = os.getcwd()
	test_dir: str = 'test'
	runlog:   str = 'run.log'
	os.system(f'mkdir -p {home_dir}/{test_dir}')
	run()
