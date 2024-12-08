import numpy
from graph import Graph
from heuristic import SolveNode, PrintVarX
from masterlp import MLP
from priceip import PriceIP as SUB

def main():
	for seed in range(100):
		print('seed', seed)
		numpy.random.seed(11)

		S = 7
		n = 4*S+1

		G = Graph(n)
		G.PrintGraph()

		mlp = MLP(G, S)
		mlp.create_model()
		pip = SUB(G, S)
		pip.create_model()

		mlp = SolveNode(mlp, pip, verbose=True)
		print('ObjVal', mlp.model.ObjVal, '\n')

		PrintVarX(mlp.model.getVars(), mlp.columns)
		break

if __name__ == '__main__':
	main()
