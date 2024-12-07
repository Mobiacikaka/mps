import numpy
from graph import Graph
from heuristic import SolveNode, PrintVarX

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
