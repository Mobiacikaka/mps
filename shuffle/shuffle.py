from io import TextIOWrapper
import numpy, subprocess, os, sys, socket, time, traceback, json

## WARNING: the script has to run in the repository root
root_dir = os.getcwd()
sys.path.append(root_dir)
from utils.random_instance_analyzer import ReadRandom

def SudoCommand(
	command: str,
	cwd: str=f'{root_dir}/shuffle',
	stdout: None|TextIOWrapper=None,
	stderr: None|TextIOWrapper=None,
):
	if verbose:
		print('SYSTEM COMMAND:', command)
	subprocess.run(
		command,
		cwd=cwd,
		shell=True,
		stdout=stdout,
		stderr=stderr,
	)

def changeN(n: int):
	mpcfile = open('./shuffle/shuffle.mpc', 'r')
	filecontent = mpcfile.readlines()
	mpcfile.close()

	mpcfile = open('./shuffle/shuffle.mpc', 'w')
	for line in filecontent:
		if 'n = ' in line:
			line = f'n = {n}\n'
		mpcfile.write(line)
	mpcfile.close()

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
		## A share is combined with two parts
		## The first part is a share of the random integer
		## The second part is a share of the original data

		## Share list that will be sent to other users
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
		## Share list that is received from other users
		self.shares.append(share)

	def SwapShare(self, index_i: int, index_j: int) -> None:
		self.shares[index_i], self.shares[index_j] \
			= self.shares[index_j], self.shares[index_i]

	def WriteData(self, index_i: int, index_j: int) -> None:
		os.system('mkdir -p shuffle/Player-Data')
		f = open(f'shuffle/Player-Data/Input-P{self.id}-0', 'w')
		D = self.shares[index_i][0] - self.shares[index_j][0]
		r = random()
		f.write(str(D) + '\n')
		f.write(str(r) + '\n')
		f.close()

def SecureCompare(
	users_list: list[User],
	index_i: int,
	index_j: int,
	sockets: list[socket.socket],
	free_ports: list[int],
) -> bool:
	for user in users_list:
		user.WriteData(index_i, index_j)
	### Use SPDZ to compare the value
	n = len(users_list)
	binary : str = f'{root_dir}/MP-SPDZ/semi-party.x'
	## TODO: ip_file is somehow not working, so we choose to use --hostname and --my-port
	# ip_file: str = f'{root_dir}/shuffle/ip_file'
	cwd    : str = f'{root_dir}/shuffle'

	for i in range(n-1):
		logfile = open(f'{cwd}/logs/user{i}.log', 'w')
		SudoCommand(
			f'{binary} shuffle -N {n} -p {i} --hostname 127.0.0.{11+i} --my-port {free_ports[i]} -v &',
			cwd   = cwd,
			stdout= logfile,
			stderr= logfile,
		)
		logfile.close()
	logfile = open(f'{cwd}/logs/user{n-1}.log', 'w')
	SudoCommand(
		f'{binary} shuffle -N {n} -p {n-1} --hostname 127.0.0.{11+n-1} --my-port {free_ports[n-1]} -v',
		cwd   = cwd,
		stdout= logfile,
		stderr= logfile,
	)
	logfile.close()

	user0log = open(f'{cwd}/logs/user0.log', 'r')
	lines = user0log.readlines()
	for line in lines:
		if 'rD: ' in line:
			rD: int = int(line.strip('rD: '))
			if rD > 0:
				return True
			else:
				return False

	if verbose:
		print()
	assert(0) ## There is no rD output in user0.log
	return False

def Shuffle(n: int, sockets: list[socket.socket], free_ports: list[int]) -> None:
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
			if SecureCompare(users_list, i, j, sockets, free_ports):
				for user in users_list:
					user.SwapShare(i, j)

	return

def find_free_ports(count: int):
	free_ports: list[int] = []
	sockets: list[socket.socket] = []
	try:
		for _ in range(count):
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.bind(('127.0.0.1', 0))
			port = s.getsockname()[1]
			free_ports.append(port)
			sockets.append(s)
	finally:
		pass

	ip_file = open(f'{root_dir}/shuffle/ip_file', 'w')
	host: int = 11
	for port in free_ports:
		ip_file.write(f'127.0.0.{host}:{port}\n')
		host += 1
	return free_ports, sockets

def SetLatency(latency: list, free_ports: list):
	n: int = len(latency)
	assert(n == len(free_ports))

	# latency = [[0 for _ in range(n)] for _ in range(n)]

	# 0. First add virtual ip
	for i in range(n):
		SudoCommand(f'sudo ip addr add 127.0.0.{11+i}/8 dev lo')

	## 1.1 Delete any existing qdisc on lo
	SudoCommand('sudo tc qdisc del dev lo root 2> /dev/null || true')

	## 2.1 Add root HTB handle “1:” on loopback
	SudoCommand('sudo tc qdisc add dev lo root handle 1: htb default 1')

	## 2.2 Create Class 1:1 → “no extra delay” (this is the default fallback)
	SudoCommand('sudo tc class add dev lo parent 1: classid 1:1 htb rate 1000mbit')

	## 3.1 create delay class with netem
	k: int = 2
	for i in range(n-1):
		for j in range(i+1, n):
			SudoCommand(f'sudo tc class add dev lo parent 1: classid 1:{k} htb rate 1000mbit')
			SudoCommand(f'sudo tc qdisc add dev lo parent 1:{k} handle {k}: netem delay {latency[i][j]}ms')
			k += 1

	k: int = 2
	for i in range(n-1):
		for j in range(i+1, n):
			SudoCommand(f'sudo tc filter add dev lo protocol ip parent 1: prio 1 u32 match ip src 127.0.0.{11+i}/8 match ip dst 127.0.0.{11+j}/8 flowid 1:{k}')
			SudoCommand(f'sudo tc filter add dev lo protocol ip parent 1: prio 1 u32 match ip src 127.0.0.{11+j}/8 match ip dst 127.0.0.{11+i}/8 flowid 1:{k}')
			k += 1
	return

def RemoveLatency(n: int):
	for i in range(n):
		SudoCommand(f'sudo ip addr delete 127.0.0.{11+i}/8 dev lo')
	SudoCommand('sudo tc qdisc del dev lo root')

def CompileMPC():
	SudoCommand(f'{root_dir}/MP-SPDZ/compile.py {root_dir}/shuffle/shuffle.mpc')

def main():
	AttributeList: list = ReadRandom()
	for attribute in AttributeList:
		if verbose:
			print('\nN\t', attribute['N'], '\nS\t', attribute['S'], '\nseed\t', attribute['seed'])

		## Each attribute is a setting of Clique Partition
		solution: list = attribute['solution']
		edges_G: list = attribute['edges'] ## Edges of Global Graph
		attribute['runtime'] = time_used = []
		for column in solution:
			## Acquire the vertice index list and the clique's edges list
			vertice, edges_C = GetVertice(edges_G, column) ## Edges in Clique
			## Acquire Clique size
			n = len(vertice)
			## rewrite shuffle.mpc to change its n
			changeN(n)
			CompileMPC()

			loopFlag = True
			while loopFlag:
				try:
					## Get the system's free ports for shuffling
					free_ports, sockets = find_free_ports(n)
					assert(len(free_ports) == n)

					## Set the latency between ports according to edges in clique
					SetLatency(edges_C, free_ports)

					for s in sockets:
						s.close()

					time_begin = time.time()
					Shuffle(n, sockets, free_ports)
					time_end = time.time()

					## Remove all latency after shuffling
					RemoveLatency(n)
					time_used.append(time_end - time_begin)
					loopFlag = False
				except:
					traceback.print_exc()
					print()

	if verbose:
		for attribute in AttributeList:
			print(attribute['N'], attribute['S'], attribute['seed'], attribute['runtime'])
			# json.dumps(attribute, indent=4)

	SudoCommand('mkdir -p DATA')
	for attribute in AttributeList:
		folder:str = f'DATA/N{attribute['N']}/S{attribute['S']}/seed{attribute['seed']}'
		SudoCommand(f'mkdir -p {folder}')
		datafile = open(f'shuffle/{folder}/log.json', 'w')
		datafile.write(json.dumps(attribute, indent=4))

def BuildMPSPDZ():
	SudoCommand('make -j8 semi-party.x > /dev/null 2>&1', cwd=f'{root_dir}/MP-SPDZ')

if __name__ == '__main__':
	verbose = True
	BuildMPSPDZ()
	main()
