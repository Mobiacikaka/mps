# Protocl Details

**butterfly tournament**
The butterfly tournament has the property that when two players meet in the i-th round, they have achieved the same sequence of outcomes in two independent butterfly tournaments T_0 and T_1 of order i - 1.

## Probabilistic Sorting Network

1. If $l < \epsilon\sqrt{k}$: Apply bitonic sort to blocks of size $2^l$ followed by two sets of bitonic merges between adjacent blocks.

## Setting

1. There are $N$ edges.
2. For edge $Edge_i$, there are $m_i$ users, input denoted as $\{x_{i,1}, \ldots, x_{i, m_i}\}$.
3. The output is $\{ x_{\pi(1)}, x_{\pi(2)}, \ldots, x_{\pi(n)} \}$. $n = \sum\limits_{i=1}^N m_i$

## Protocol

1. packing
	- share a packing length $K$
	- padding
	- generate a random value for every pack
2. sharing
	- number each edge node
	- create a new shared array in every edge node
	- shared every pack of edge node according to the order of edge node's number
3. create sorting network
	- create probabilistic sorting network
		-  based on "A (fairly) simple circuit that (usually) sorts"
	- use a NxM two-dimentional array to indicate the comparison target
4. run sorting network
    - all party generate two edaBits r1, r2 for comparator
    - if the comparator output 0, do nothing
    - if the comparator output 1, exchange the share in the shared array
    - the comparator is build by two components
        - one is $Π^{LTBits}$, another is $Π^{LTS}$
        - by "Rabbit: Efficient Comparison for Secure Multi-Party Computation"
5. submitting
    - each node submit their shares separtely to the center analyzer
