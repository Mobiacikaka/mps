#!/bin/python3
# vim:ts=2:sw=2:noet
import random
import copy
import math

MAXINT16 = 2**16

def randint():
	return random.randint(0, MAXINT16-1)

class Edge:
	def __init__(self, M: int) -> None:
		self.M = M
		# self.data = [int(a) for a in input().split(' ')]
		self.data = [randint() for _ in range(self.M)]
		assert(len(self.data) == self.M)
		self.packages = []
		self.K = 0
		self.shareddata = []

	def Pack(self, K: int) -> int:
		self.K = K
		packageslen = math.ceil(self.M / K)
		for i in range(packageslen):
			package = []
			for j in range(K):
				data = None
				if i * K + j < self.M:
					data = self.data[i*K+j]
				package.append(data)
			rnd = randint()
			self.packages.append([rnd, package])
		return packageslen
	
	def Share(self, N: int) -> list:
		sharedata = []
		packages = copy.deepcopy(self.packages)
		for i in range(N-1):
			sharepacks = []
			for j in range(len(self.packages)):
				sharepack = []
				for k in range(self.K):
					if packages[j][1][k] == None:
						sharepack.append(None)
						continue
					rnd = randint()
					sharepack.append(rnd)
					packages[j][1][k] = (packages[j][1][k] - rnd) % MAXINT16
				rnd = randint()
				sharepacks.append([rnd, sharepack])
				packages[j][0] = (packages[j][0] - rnd) % MAXINT16
			sharedata.append(sharepacks)
		for pack in packages:
			self.shareddata.append(pack)
		return sharedata

	def Shared(self, sharedata: list) -> None:
		for item in sharedata:
			self.shareddata.append(item)

	def SwapSharedData(self, i: int, j: int) -> None:
		self.shareddata[i], self.shareddata[j] = self.shareddata[j], self.shareddata[i]

	def SharedDataPadding(self, k: int) -> None:
		while(len(self.shareddata) < 2**k):
			self.shareddata.append([0, None])
	
	def Print(self) -> None:
		print("Edge")
		print(self.data)
		print(self.packages)
		print(self.shareddata)

class Shuffler:
	def __init__(self) -> None:
		# edges number
		self.N = int(input())
		# users number list
		self.Ms = [int(a) for a in input().split(' ')]
		self.TotalUsersCount = sum(self.Ms)
		self.TotalPackagesCount = 0
		assert(len(self.Ms) == self.N)
		self.K = int(input())
		self.Edges: list[Edge] = []

	def EdgesInit(self) -> None:
		for i in range(self.N):
			self.Edges.append(Edge(self.Ms[i]))
		
	def EdgesPacking(self) -> None:
		for i in range(self.N):
			length = self.Edges[i].Pack(self.K)
			self.TotalPackagesCount += length
	
	def EdgesSharing(self) -> None:
		for i in range(self.N):
			addi = 0
			sharedata = self.Edges[i].Share(self.N)
			for j in range(self.N):
				if i == j:
					addi = 1
				else:
					self.Edges[j].Shared(sharedata[j-addi])
	
	def SwapElementsInEdges(self, i, j) -> None:
		for Edge in self.Edges:
			Edge.SwapSharedData(i, j)
	
	def LessThan(self, i, j) -> bool:
		a = sum([Edge.shareddata[i][0] for Edge in self.Edges])
		b = sum([Edge.shareddata[j][0] for Edge in self.Edges])
		return a < b

	def EdgesShuffling(self) -> None:
		def FisherYates() -> None:
			for i in range(self.TotalUsersCount):
				## O(1) communication cost
				j = i + random.randint(0, self.TotalUsersCount - i - 1)
				self.SwapElementsInEdges(i, j)

		def BitonicSort(begin: int, end: int, reverse: bool=False) -> None:
			halflen = (end - begin) // 2
			if halflen < 1:
				return
			assert((end - begin) % 2 == 0)
			for i in range(halflen):
				## SecureCompare shareddata[i+begin] and shareddata[i+begin+halflen]
				flag = self.LessThan(i+begin, i+begin+halflen)
				if flag == reverse:
					self.SwapElementsInEdges(i+begin, i+begin+halflen)
			BitonicSort(begin, end-halflen, reverse=reverse)
			BitonicSort(begin+halflen, end, reverse=reverse)

		def BitonicMergeSort() -> None:
			## First Padding
			k = math.ceil(math.log2(self.TotalPackagesCount))
			for Edge in self.Edges:
				Edge.SharedDataPadding(k)
			## Second Create Bitonic Sequence
			reverse = False
			for i in range(1, k):
				for j in range(0, 2**k, 2**i):
					BitonicSort(j, j+2**i, reverse)
					reverse = not reverse
			## Sort The Bitonic Sequence
			BitonicSort(0, 2**k)

		BitonicMergeSort()

	def Print(self) -> None:
		for i in range(self.N):
			self.Edges[i].Print()

if __name__ == '__main__':
	shuffler = Shuffler()
	shuffler.EdgesInit()
	shuffler.EdgesPacking()
	shuffler.EdgesSharing()
	shuffler.Print()
	shuffler.EdgesShuffling()
	print()
	shuffler.Print()
