from math import factorial

def CombinationCount(n: int, k: int) -> int:
	return int(factorial(n) / (factorial(n-k) * factorial(k)))

if __name__ == '__main__':
	S = 7
	c = 0
	for size in range(S, S*2):
		c += CombinationCount(S*2, size)
	print(c)
