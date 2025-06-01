import numpy, subprocess, os, sys

sys.path.append('../')
from utils.random_instance_analyzer import ReadRandom

def changeN(n: int):
	mpcfile = open('./shuffle.mpc', 'r')
	filecontent = mpcfile.readlines()
	mpcfile.close()

	mpcfile = open('./shuffle.mpc', 'w')
	for line in filecontent:
		if 'n = ' in line:
			line = f'n = {n}'

	return

def GetVertice(edges, column) -> list:
	vertice: list = []
	for i in range(len(column)):
		if column[i] == 1:
			vertice.append(i)
	return vertice

def main2():
	AttributeList: list = ReadRandom()
	for attribute in AttributeList:
		solution: list = attribute['solution']
		edges: list = attribute['edges']
		for column in solution:
			vertice = GetVertice(edges, column)

def random(lb: int=0, ub: int=2**20):
	assert(lb < ub)
	return numpy.random.randint(lb, ub)

class User:
	def __init__(self, _id: int) -> None:
		self.id = _id
		## the original data of a user
		self.data = random()
		## each user generate a random integer for the sorting in the shuffling
		self.rint = random()
		self.shares: list[tuple[int, int]] = []

	def CreateShares(self, n: int) -> list[tuple[int, int]]:
		shares_list: list[tuple[int, int]] = []
		last_shared_rint = self.rint
		last_shared_data = self.data
		for _ in range(n-1):
			shared_rint = random()
			shared_data = random()
			shares_list.append((shared_rint, shared_data))
			last_shared_rint -= shared_rint
			last_shared_data -= shared_data
		shares_list.append((last_shared_rint, last_shared_data))
		return shares_list

	def UpdateShares(self, share) -> None:
		self.shares.append(share)

	def SwapShare(self, index_i: int, index_j: int) -> None:
		self.shares[index_i], self.shares[index_j] \
			= self.shares[index_j], self.shares[index_i]

	def WriteData(self, index_i: int, index_j: int) -> None:
		os.system('mkdir -p Player-Data')
		f = open(f'Player-Data/Input-P{self.id}-0', 'w')
		D = self.shares[index_i][0] - self.shares[index_j][0]
		r = random()
		f.write(str(D) + '\n')
		f.write(str(r) + '\n')
		f.close()

def SecureCompare(users_list: list[User], index_i: int, index_j: int) -> bool:
	for user in users_list:
		user.WriteData(index_i, index_j)
	### Use SPDZ to compare the value
	n = len(users_list)
	binary : str = '/home/justin/Documents/MP-SPDZ/semi-party.x'
	ip_file: str = '/home/justin/Documents/mps/MP-SPDZ/ip_file'
	cwd    : str = '/home/justin/Documents/mps/MP-SPDZ'
	for i in range(n-1):
		logfile = open(f'user{i}.log', 'w')
		subprocess.Popen(
			f'{binary} shuffle -N {n} -p {i} -ip {ip_file} -v 2>&1',
			cwd   = cwd,
			shell = True,
			stdout= logfile,
			stderr= logfile,
		)
		logfile.close()
	logfile = open(f'user{n-1}.log', 'w')
	subprocess.run(
		f'{binary} shuffle -N {n} -p {n-1} -ip {ip_file} -v',
		cwd   = cwd,
		shell = True,
		stdout= logfile,
		stderr= logfile,
	)
	logfile.close()

	user0log = open('user0.log', 'r')
	lines = user0log.readlines()
	for line in lines:
		if 'rD: ' in line:
			rD: int = int(line.strip('rD: '))
			if rD > 0:
				return True
			else:
				return False
	
	assert(0) ## There is no rD output in user0.log
	return True

def Shuffle(n: int) -> None:
	users_list: list[User] = []
	for i in range(n):
		users_list.append(User(i))

	for i in range(n):
		userA = users_list[i]
		shares_list = userA.CreateShares(n)
		for j in range(n):
			userB = users_list[j]
			userB.UpdateShares(shares_list[j])

	for i in range(n-1):
		for j in range(i+1, n):
			if SecureCompare(users_list, i, j):
				for user in users_list:
					user.SwapShare(i, j)

def main():
	Shuffle(4)

if __name__ == '__main__':
	main()
