import numpy, time, math, colorama, heapq, itertools
from gurobipy import GRB
from graph import Graph
import gurobipy
from heuristic import HeuristicI, HeuristicII, HeuristicIII, IPSolver, GenerateQSET, PrintVarX
from masterlp import MLP
from priceip import PriceIP as SUB

def SolveNode(G: Graph, S: int, verbose: bool=False):
	mlp = MLP(G, S) ## Master Linear Problem
	mlp.create_model()
	pip = SUB(G, S) ## Price Integer Problem
	pip.create_model()

	TIME_ESTIMATION_FLAG = True
	runtime_MLP = 0.0
	runtime_SUB = 0.0
	runtime_H1 = 0.0
	runtime_H2 = 0.0
	runtime_H3 = 0.0
	runtime_CP = 0.0 ##.0 cutting planes time

	while True:
		stime = time.time()
		mlp.solve()
		etime = time.time()
		runtime_MLP += etime - stime
		mlp.write('master.lp')
		if mlp.model.Status == GRB.INFEASIBLE:
			print(f'{colorama.Fore.RED}ERROR::INFEASIBLE!{colorama.Style.RESET_ALL}')
			exit()
		else:
			print('Best Objective Value: ', mlp.model.ObjVal)
			pass

		## Generate Columns using HeuristicI
		stime = time.time()
		flag = HeuristicI(mlp, verbose)
		etime = time.time()
		runtime_H1 += etime - stime
		if flag == True:
			continue

		## Generate Columns using HeuristicII
		stime = time.time()
		flag = HeuristicII(mlp, verbose)
		etime = time.time()
		runtime_H2 += etime - stime
		if flag == True:
			continue

		## Generate Columns using HeuristicIII
		stime = time.time()
		flag = HeuristicIII(mlp, verbose=True)
		etime = time.time()
		runtime_H3 += etime - stime
		if flag == True:
			continue

		## Generate Cutting Planes
		stime = time.time()
		Q = GenerateQSET(mlp, verbose)
		if len(Q):
			mlp.AddCuttingPlanesMLP(Q)
			pip.AddCuttingPlanesSUB(Q)
		etime = time.time()
		runtime_CP += etime - stime
		if len(Q):
			continue

		## Column Generation using IPSolver
		stime = time.time()
		flag = IPSolver(mlp, pip, verbose)
		etime = time.time()
		runtime_SUB += etime - stime
		if flag == True:
			continue

		break

	if TIME_ESTIMATION_FLAG:
		print()
		print('RUNTIME Master Problem:\t', runtime_MLP)
		print('RUNTIME HeuristicI:\t', runtime_H1)
		print('RUNTIME HeuristicII:\t', runtime_H2)
		print('RUNTIME HeuristicIII:\t', runtime_H3)
		print('RUNTIME Cutting Planes:\t', runtime_CP)
		print('RUNTIME Sub Problem:\t', runtime_SUB)
		print()
	return mlp

def main():
	for seed in range(100):
		print('seed', seed)
		numpy.random.seed(11)

		S = 7
		n = 4*S+1

		G = Graph(n)
		G.PrintGraph()
		mlp = SolveNode(G, S, verbose=True)
		print('ObjVal', mlp.model.ObjVal, '\n')

		PrintVarX(mlp.model.getVars(), mlp.columns)
		break

if __name__ == '__main__':
	main()
