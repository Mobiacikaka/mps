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

def run(test_folder_name: str):
	subfolder_list = [x[0] for x in os.walk(f'{home_dir}/{test_root}/{test_folder_name}')]
	instances_list = []
	for folder in subfolder_list:
		if 'TEST' in folder and 'S_' in folder:
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
	TEST_FOLDER = input()
	logging('TEST START', logfile=runlog, append=False)
	run(TEST_FOLDER)

"""
import sys
import contextlib

class Tee:
    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for f in self.files:
            f.write(data)

    def flush(self):
        for f in self.files:
            f.flush()

with open("log.txt", "w") as logfile:
    tee = Tee(sys.stdout, logfile)
    with contextlib.redirect_stdout(tee):
        result = noisy_function()

print("Return value:", result)
"""
