from math import factorial
import itertools, time

def CombinationCount(n: int, k: int) -> int:
	return int(factorial(n) / (factorial(n-k) * factorial(k)))

def AAA(n=29, S=7):
	atime = time.time()
	lst = [i for i in range(2*S)]
	c = 0
	for i in range(n):
		for size in range(S, S*2):
			for cluster in itertools.combinations(lst, size):
				c += 1
	btime = time.time()
	print(c, btime-atime)

if __name__ == '__main__':
	# S = 7
	# c = 0
	# for size in range(S, S*2):
	# 	a = CombinationCount(S*2, size)
	# 	print(a)
	# 	c += a
	# print(c)
	AAA()
