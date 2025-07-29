import argparse
import math
import numpy as np
import xxhash


class OLH():
	def __init__(self) -> None:
		self.domain = 0
		self.epsilon = 0.0
		self.n = 0
		self.g = 0

		self.X = []
		self.Y = []

		self.REAL_DIST = []
		self.ESTIMATE_DIST = []

		self.p = 0.0
		self.q = 0.0


	def generate(self):
		# uniform distribution. one can also use other distributions
		x = np.random.randint(self.domain)
		return x


	def generate_dist(self):
		# global X, REAL_DIST
		self.X = np.zeros(args.n_user, dtype=np.int32)
		for i in range(args.n_user):
			self.X[i] = self.generate()
			self.REAL_DIST[self.X[i]] += 1


	def generate_auxiliary(self):
		# global ESTIMATE_DIST, REAL_DIST, n, p, q, epsilon, domain
		self.domain = args.domain
		self.epsilon = args.epsilon

		self.n = args.n_user

		self.REAL_DIST = np.zeros(self.domain)
		self.ESTIMATE_DIST = np.zeros(self.domain)

		self.p = math.exp(self.epsilon) / (math.exp(self.epsilon) + self.g - 1)
		self.q = 1.0 / (math.exp(self.epsilon) + self.g - 1)


	def perturb(self):
		self.Y = np.zeros(self.n)
		for i in range(self.n):
			v = self.X[i]
			x = (xxhash.xxh32(str(v), seed=i).intdigest() % self.g)
			y = x

			p_sample = np.random.random_sample()
			# the following two are equivalent
			# if p_sample > p:
			#     while not y == x:
			#         y = np.random.randint(0, g)
			if p_sample > self.p - self.q:
				# perturb
				y = np.random.randint(0, self.g)
			self.Y[i] = y


	def aggregate(self):
		# global ESTIMATE_DIST
		self.ESTIMATE_DIST = np.zeros(self.domain)
		for i in range(self.n):
			for v in range(self.domain):
				if self.Y[i] == (xxhash.xxh32(str(v), seed=i).intdigest() % self.g):
					self.ESTIMATE_DIST[v] += 1
		a = 1.0 * self.g / (self.p * self.g - 1)
		b = 1.0 * self.n / (self.p * self.g - 1)
		self.ESTIMATE_DIST = a * self.ESTIMATE_DIST - b


	def error_metric(self):
		abs_error = 0.0
		for x in range(self.domain):
			# print REAL_DIST[x], ESTIMATE_DIST[x]
			abs_error += np.abs(self.REAL_DIST[x] - self.ESTIMATE_DIST[x]) ** 2
		return abs_error / self.domain


	def main(self):
		self.generate_auxiliary()
		self.generate_dist()
		results = np.zeros(args.exp_round)
		for i in range(args.exp_round):
			self.perturb()
			self.aggregate()
			results[i] = self.error_metric()
		print(np.mean(results), np.std(results), )
		# print(results)


	def dispatcher(self):
		# global g
		# for e in np.arange(1.0, 1.1, 0.1):
		# 	print(e, end=' ')
		# 	args.epsilon = float(e)
		# 	# try other g
		# 	self.g = args.projection_range
		# 	# OLH
		# 	self.g = int(round(math.exp(args.epsilon))) + 1
		# 	print(self.g, end=' ')
		# 	self.main()

		for i in range(0, 7):
			args.n_user = int(2 ** i * 1000)
			print(args.n_user, end=' ')
			# OLH
			self.g = int(round(math.exp(args.epsilon))) + 1
			print(self.g, end=' ')
			self.main()


parser = argparse.ArgumentParser(description='Comparisor of different schemes.')
parser.add_argument('--domain', type=int, default=1024,
					help='specify the domain of the representation of domain')
parser.add_argument('--n_user', type=int, default=1000,
					help='specify the number of data point, default 10000')
parser.add_argument('--exp_round', type=int, default=10,
					help='specify the n_userations for the experiments, default 10')
parser.add_argument('--epsilon', type=float, default=1.0,
					help='specify the differential privacy parameter, epsilon')
parser.add_argument('--projection_range', type=int, default=2,
					help='specify the domain for projection')
args = parser.parse_args()
# dispatcher()

olh = OLH()
olh.dispatcher()
