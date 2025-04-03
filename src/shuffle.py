import numpy, random

class User:
	def __init__(self, index: int) -> None:
		## data or secret
		self.id = index
		self.data = numpy.random.randint(low=0, high=2**10)
		self.alist = []
		self.shares = []

	def CreatePoly(self, t: int):
		self.alist = [self.data]
		for _ in range(t-1):
			self.alist.append(numpy.random.randint(low=1, high=2**10))

	def GetPolyValue(self, x_i) -> int:
		s = 0
		p = 0
		for ai in self.alist:
			s += ai * x_i ** p
			p += 1
		return s

	def GetShares(self, n) -> list:
		shares = []
		for x in range(n):
			shares.append( (x, self.GetPolyValue(x)) )
		return shares

	def AddShare(self, share):
		self.shares.append(share)

	def SwapShare(self, i, j):
		self.shares[i], self.shares[j] = self.shares[j], self.shares[i]

def RestoreSecret(shareA, shareB) -> int:
	idA, pValueA = shareA
	idB, pValueB = shareB
	M: numpy.ndarray = numpy.array([[1, idA], [1, idB]])
	invM = numpy.linalg.inv(M)
	a0 = int(invM[0][0]) * pValueA + int(invM[0][1]) * pValueB
	return a0

def SecureCompare(userA: User, userB: User):
	secretA = RestoreSecret(userA.shares[userA.id], userB.shares[userA.id])
	secretB = RestoreSecret(userA.shares[userB.id], userB.shares[userB.id])
	return secretA < secretB

def Shuffle(n: int, t: int) -> None:
	users: list[User] = []
	for i in range(n):
		users.append(User(index=i))

	for user in users:
		user.CreatePoly(t=t)
		shares = user.GetShares(n=n)
		for i in range(n):
			users[i].AddShare(shares[i])

	for i in range(n-1):
		for j in range(i+1, n):
			if SecureCompare(users[i], users[j]):
				for user in users:
					user.SwapShare(i, j)
