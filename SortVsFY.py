#!/bin/python3
import random as rnd
from itertools import chain
import numpy as npy

n = 10 #int(input())
m = 1000 #int(input())

def sn(n: int, m: int) -> list[list]:
	res = []
	for _ in range(n):
		res.append([0.0] * n)
	for _ in range(m):
		arr = []
		for i in range(n):
			arr.append((rnd.randint(0, 2**16), i))
		arr = sorted(arr, key=lambda x: x[0])
		for i in range(n):
			i2 = arr[i][1]
			res[i][i2] += 1
	return res

def fy(n: int, m: int) -> list[list]:
	res = []
	for _ in range(n):
		res.append([0.0] * n)
	for _ in range(m):
		arr = list(range(n))
		for i in range(n-1):
			j = i + rnd.randint(0, n-i-1)
			arr[i], arr[j] = arr[j], arr[i]
		for i in range(n):
			i2 = arr[i]
			res[i][i2] += 1
	return res

res = sn(n, m)
res = list(chain.from_iterable(res))
print(npy.var(res))

res = fy(n, m)
res = list(chain.from_iterable(res))
print(npy.var(res))
