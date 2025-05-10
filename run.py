#!/bin/python3
import os
import multiprocessing
import subprocess
import time

def logging(content: str, logfile: str, append: bool=True):
	current_time = time.strftime("%H:%M:%S")
	if not append:
		os.system(f'echo [{current_time}]\t{content} > {logfile}')
	else:
		os.system(f'echo [{current_time}]\t{content} >> {logfile}')
	return

def GenerateRandomGraph(seed: int, N: int):
	cwd = f'{home_dir}/{test_dir}/seed_{seed}/N_{N}'
	os.system(f'mkdir -p {cwd}')

	try:
		graphfile = open(f'{cwd}/graph.csv', 'w')
		command = f'echo "{seed}\\n{N}\\n" | python {home_dir}/utils/dataset_random_generator.py'
		subprocess.run(
			command,
			cwd=cwd,
			shell=True,
			stdout=graphfile,
		)
		graphfile.close()
		logging(f'Generate Random Graph Success: N{N}\tseed{seed}', runlog)
	except:
		logging(f'Generate Random Graph Failed : N{N}\tseed{seed}', runlog)

	return

def GenerateRealisticGraph():
	return

def Processing(cwd: str):
	try:
		logfile = open(f'{cwd}/BranchAndPrice.log', 'w')
		command = f'cat "{cwd}/input.txt" | python {home_dir}/src/BranchPriceCut.py'
		subprocess.run(
			command,
			cwd=cwd,
			shell=True,
			stdout=logfile,
		)
		logging(f'instance {cwd} Finished', runlog)
	except:
		logging(f'instance {cwd} Failed', runlog)

	return

def runRandom():
	seed_min: int = int(input('MIN SEED: '))
	seed_max: int = int(input('MAX SEED: '))
	N_min: int = int(input('MIN N: '))
	N_max: int = int(input('MAX N: '))
	S_min: int = int(input('MIN S: '))
	S_max: int = int(input('MAX S: '))

	seed_list: list[int] = list(range(seed_min, seed_max+1))
	N_list: list[int] = list(range(N_min, N_max+1))
	S_list: list[int] = list(range(S_min, S_max+1))

	for seed in seed_list:
		for N in N_list:
			GenerateRandomGraph(seed, N)

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

def run(test_folder_name: str):
	subfolder_list = [x[0] for x in os.walk(f'{home_dir}/{test_root}/{test_folder_name}')]
	instances_list = []
	for folder in subfolder_list:
		if 'TEST' in folder:
			instances_list.append(tuple([folder]))

	logging(f'RUNNING {test_folder_name}', runlog)

	pool = multiprocessing.Pool(processes=8)
	pool.starmap(Processing, instances_list)
	pool.close()
	pool.join()

if __name__ == '__main__':
	home_dir : str = os.getcwd()
	test_root: str = 'test'
	runlog   : str = 'run.log'
	TEST_FOLDER = ['RANDOM', 'REALISTIC']
	logging('TEST START', logfile=runlog, append=False)
	run(TEST_FOLDER[0])
