import numpy, subprocess, os, sys, socket

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

def GetVertice(edges_G: list[list[float]], column: list[int]) -> tuple[list, list]:
	vertice: list = []
	for i in range(len(column)):
		if column[i] == 1:
			vertice.append(i)
	n = len(vertice)
	edges_C: list = [[0 for _ in range(n)] for _ in range(n)]

	for i in range(n-1):
		for j in range(i+1, n):
			edges_C[i][j] = edges_C[j][i] = edges_G[vertice[i]][vertice[j]]

	return vertice, edges_C

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
	## rewrite shuffle.mpc to change its n
	changeN(n)

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

def find_free_ports(count: int, host='127.0.0.1'):
	free_ports = []
	sockets = []
	try:
		for _ in range(count):
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.bind((host, 0))
			port = s.getsockname()[1]
			free_ports.append(port)
			sockets.append(s)
	finally:
		for s in sockets:
			s.close()
	return free_ports

def SetLatency(latency: list, free_ports: list):
	n: int = len(latency)
	assert(n == len(free_ports))

	## 1.1 Delete any existing qdisc on lo
	os.system('sudo tc qdisc del dev lo root 2> /dev/null || true')

	## 2.1 Add root HTB handle “1:” on loopback
	os.system('sudo tc qdisc add dev lo root handle 1: htb')

	## 2.2 Create Class 1:1 → “no extra delay” (this is the default fallback)
	os.system('sudo tc class add dev lo parent 1: classid 1:1 htb rate 1000mbit')

	## 3.1 
	k: int = 2
	for i in range(n-1):
		for j in range(i+1, n):
			os.system(f'sudo tc class add dev lo parent 1: classid 1:{k} htb rate 1000mbit')
			os.system(f'sudo tc qdisc add dev lo parent 1:{k} handle {k}: netem delay {latency[i][j]}ms')
			k += 1

			os.system(f'sudo tc class add dev lo parent 1: classid 1:{k} htb rate 1000mbit')
			os.system(f'sudo tc qdisc add dev lo parent 1:{k} handle {k}: netem delay {latency[i][j]}ms')
			k += 1
	
	k: int = 2
	for i in range(n-1):
		for j in range(i+1, n):
			os.system(f'\
tc filter add dev lo protocol ip parent 1: prio 1 u32 \
    match ip src   127.0.0.1/32 \
    match ip dst   127.0.0.1/32 \
    match ip sport {free_ports[i]} 0xffff \
    match ip dport {free_ports[j]} 0xffff \
    flowid 1:{k}')
			k += 1
			os.system(f'\
tc filter add dev lo protocol ip parent 1: prio 1 u32 \
    match ip src   127.0.0.1/32 \
    match ip dst   127.0.0.1/32 \
    match ip sport {free_ports[j]} 0xffff \
    match ip dport {free_ports[i]} 0xffff \
    flowid 1:{k}')
			k += 1
	return

def RemoveLatency():
	os.system('sudo tc qdisc del dev lo root')
	return

def main():
	AttributeList: list = ReadRandom()
	for attribute in AttributeList:
		solution: list = attribute['solution']
		edges_G: list = attribute['edges'] ## Edges in Global Graph
		for column in solution:
			vertice, edges_C = GetVertice(edges_G, column) ## Edges in Clique
			n = len(vertice)
			free_ports: list = find_free_ports(n)
			assert(len(free_ports) == n)
			SetLatency(edges_C, free_ports)
			Shuffle(n)
			RemoveLatency()
	return

if __name__ == '__main__':
	main()
