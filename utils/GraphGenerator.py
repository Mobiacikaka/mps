#!/bin/python3
##########################
## the output would be: ##
## e11 e12 ... e1n      ##
## e21 e22 ... e2n      ##
## ... ... ... ...      ##
## en1 en2 ... enn      ##
##########################

import numpy, math

def EuclideanDistance(vi: tuple[int, int], vj: tuple[int, int]):
	return math.sqrt(
		(vi[0] - vj[0])**2 + (vi[1] - vj[1]) ** 2
	)

def GetEdgesFromNodes(nodes: list) -> list[list[float]]:
	n = len(nodes)
	edges = [[0.0 for _ in range(n)] for _ in range(n)]
	for i in range(n-1):
		for j in range(i+1, n):
			edges[i][j] = edges[j][i] = EuclideanDistance(nodes[i], nodes[j])
	return edges

#################################
#################################
### Return nodes' corrdinates ###
#################################
#################################
def UniformRandomGenerator(N: int, ):
	## generate complete uniform vertices
	nodes = numpy.random.uniform(0, 100, size=(N, 2)).tolist()
	return nodes

def HotspotRandomGenerator(N: int=20, c_nodes=5):
	## generate 
	num_nodes = N
	num_central_nodes = c_nodes
	central_nodes = numpy.random.uniform(10, 90, size=(num_central_nodes, 2)).tolist()

	nodes = []
	for central_node in central_nodes:
		# nodes.append(central_node)

		relative_distance = numpy.random.uniform(-10, 10, size=(num_nodes//num_central_nodes, 2)).tolist()
		for relative_node in relative_distance:
			nodes.append([central_node[0]+relative_node[0], central_node[1]+relative_node[1]])

	return nodes
