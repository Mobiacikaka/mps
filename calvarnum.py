from math import factorial

def CombinationCount(n: int, k: int):
	return factorial(n) / (factorial(n-k) * factorial(k))

if __name__ == '__main__':
	N = 20
	S = 4
	a = 0
	for i in range(S, N-S+1):
		a += CombinationCount(N, i)
	print(a)
