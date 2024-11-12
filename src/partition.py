import numpy, time
from gurobipy import GRB
from graph import Graph
from masterlp import MLP
from priceip import PriceIP as SUB

def solve():
	## number of vertex
	n = 29
	## least number of cluster
	S = 7
	G = Graph(n)
	G.PrintGraph()

	cppmin = MLP(G, S)
	cppmin.create_model()
	sub_prob = SUB(G, S)
	sub_prob.create_model()
	PI = []

	time_master = 0.0
	time_subprob = 0.0

	while True:
		## 2: Approximately solve the current LP relaxation using CPLEX

		time_start = time.time()
		cppmin.solve()
		time_end = time.time()
		time_master += time_end - time_start

		cppmin.write('model_linear.lp')
		if cppmin.model.Status == GRB.INFEASIBLE:
			print('INFEASIBLE')
			exit()

		## 5: Generate columns using an IP solver, if new columns are found goto 2
		pi, sigma = cppmin.get_dual_vars()
		# print('pi', pi, 'sigma', sigma)
		assert(pi not in PI), 'Generated a same pi'
		PI.append(pi)

		sub_prob.set_objective(pi)

		time_start = time.time()
		sub_prob.solve()
		time_end = time.time()
		time_subprob += time_end - time_start

		sub_prob.write()

		## 6: If the gap between the value of the LP relaxation and the value of the incumbent integer solution is sufficiently small, STOP with optimality
		y = sub_prob.get_solution()
		print('Generate Column: ', y)
		reduced_cost = sub_prob.get_reduced_cost()
		print('reduced_cost-sigma: ', reduced_cost-sigma)

		if reduced_cost >= sigma - 1e-6:
		# if reduced_cost - sigma >= 0:
			break

		cppmin.update_contrs(column_coeff=y)
		# y = [1-x for x in y]
		# cppmin.update_contrs(column_coeff=y)

	print()
	for x in cppmin.model.getVars():
		if x.X != 0.0:
			print(f'{x.VarName}={x.X}\t: {cppmin.model.getCol(x)}')

	cppmin.to_int()
	cppmin.solve(flag=1)
	cppmin.write('model_int.lp')

	print()
	for x in cppmin.model.getVars():
		if x.X == 1.0:
			print(f'{x.VarName}={x.X}\t: {cppmin.model.getCol(x)}')

	print(time_master, time_subprob)

if __name__ == '__main__':
	numpy.random.seed(60)
	solve()
