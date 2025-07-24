#!/bin/python3
##########################
## the output would be: ##
## e11 e12 ... e1n      ##
## e21 e22 ... e2n      ##
## ... ... ... ...      ##
## en1 en2 ... enn      ##
##########################

import numpy

def RandomGraphGenerator1():
	## generate complete uniform vertices
	pass

def RandomGraphGenerator2(N: int=100, c_nodes=5):
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
