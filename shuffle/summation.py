import math, random, numpy

def calculate_c_gamma_for_fixed_k(n, epsilon, delta, k_fixed):
	"""
	Calculates the required gamma and corresponding c value for a fixed k,
	to achieve a specific (epsilon, delta)-differential privacy.

	Args:
		n (int): Number of parties. Must be > 1.
		epsilon (float): Privacy parameter epsilon. Must be > 0.
		delta (float): Privacy parameter delta. Must be between 0 and 0.5.
		k_fixed (int): The chosen fixed precision parameter k. Must be >= 1.

	Returns:
		tuple: (gamma_required, c_calculated) - the minimum gamma needed for privacy,
				and the corresponding c value.
	Raises:
		ValueError: If input parameters are invalid or if the desired privacy
					level cannot be achieved with the given k and n.
	"""
	if not (isinstance(n, int) and n > 1):
		raise ValueError("Number of parties n must be an integer greater than 1.")
	if not (epsilon > 0):
		raise ValueError("Epsilon must be greater than 0.")
	if not (0 < delta < 0.5):
		raise ValueError("Delta must be between 0 and 0.5.")
	if not (isinstance(k_fixed, int) and k_fixed >= 1):
		raise ValueError("Fixed k must be an integer greater than or equal to 1.")

	# Step 1: Calculate gamma_required using Theorem 1's formula
	# This is the minimum gamma needed to guarantee (epsilon, delta)-DP for the given k.
	term1_privacy: float = (14 * k_fixed * math.log(2 / delta)) / ((n - 1) * epsilon**2)
	term2_privacy: float = (27 * k_fixed) / ((n - 1) * epsilon)

	gamma_required: float = max(term1_privacy, term2_privacy)

	# Step 2: Check if the calculated gamma is feasible (i.e., < 1)
	if gamma_required >= 1.0 - 1e-9: # Use a small tolerance for float comparison
		raise ValueError(
			f"Cannot achieve (epsilon={epsilon}, delta={delta})-DP with n={n} parties "
			f"and fixed k={k_fixed}. Calculated gamma ({gamma_required:.4f}) is >= 1. "
			"Consider increasing epsilon/delta or increasing n, or decreasing k."
		)

	# Step 3: Calculate c using the relationship from Algorithm 2: gamma = c * (k+1) / n
	# So, c = gamma * n / (k+1)
	c_calculated = gamma_required * n / (k_fixed + 1)

	return gamma_required, c_calculated

def Ber(p):
	"""
	Generates a Bernoulli random variable.
	Returns 1 with probability p, and 0 with probability 1-p.

	Args:
		p (float): The probability of returning 1 (0 <= p <= 1).

	Returns:
		int: 1 if a random number is less than p, otherwise 0.
	"""
	if not (0 <= p <= 1):
		raise ValueError("Probability p must be between 0 and 1.")
	return 1 if random.random() < p else 0

def LocalRandomizer(x, c, k, n):
	"""
	Algorithm 2: Local Randomizer R_c_k_n for Optimal Summation.
	This randomizer is used for computing the sum of real values x_i in [0, 1].

	Public Parameters:
		c (float): A parameter derived from privacy/accuracy trade-off.
		k (int): Precision parameter for fixed-point encoding (domain size {0, ..., k}).
		n (int): Number of parties (users).

	Input:
		x (float): The user's input, a real number in the range [0, 1].

	Output:
		y (int): The privatized message, an integer in the domain {0, ..., k}.
	"""
	if not (0 <= x <= 1):
		raise ValueError(f"Input x ({x}) must be within the range [0, 1].")
	if not (isinstance(k, int) and k >= 0):
		raise ValueError("Precision parameter k must be a non-negative integer.")
	if not (isinstance(n, int) and n > 0):
		raise ValueError("Number of parties n must be a positive integer.")
	if not (isinstance(c, (int, float)) and c >= 0):
		raise ValueError("Parameter c must be a non-negative number.")

	# Step 1: Encode x with precision k using randomized rounding.
	# The paper states: "Let x_bar <- floor(xk) + Ber(xk - floor(xk))"
	# This ensures E[x_bar/k] = E[x] (unbiased encoding).
	scaled_x = x * k
	floor_scaled_x = math.floor(scaled_x)
	bernoulli_prob = scaled_x - floor_scaled_x

	# Handle floating point precision for exact integers (e.g., if xk is exactly 5.0)
	if bernoulli_prob < 1e-9:
		x_bar = floor_scaled_x
	else:
		x_bar = floor_scaled_x + Ber(bernoulli_prob)

	# Ensure x_bar stays within the intended domain {0, ..., k}.
	# It's possible for x_bar to be k+1 if x=1 and Ber(0) returns 1, but x_bar should be k.
	x_bar = min(x_bar, k)

	# Step 2: Apply randomized response based on parameter c.
	# The probability gamma for this algorithm is c * (k+1) / n.
	# This is derived from the paper's analysis connecting Algorithm 1's gamma
	# to the parameters of Algorithm 2.
	gamma_prime = c * (k + 1) / n

	# Ensure gamma_prime is a valid probability (0 to 1).
	# If the calculated c, k, n lead to gamma_prime outside this range, it indicates
	# either a theoretical edge case or parameter choices that don't fit the model.
	if not (0 <= gamma_prime <= 1):
		# print(f"Warning: Calculated gamma_prime ({gamma_prime:.4f}) is outside [0, 1]. Capping to valid range.")
		gamma_prime = max(0.0, min(1.0, gamma_prime))

	b = Ber(gamma_prime)

	if b == 0:
		y = int(x_bar) # Ensure y is an integer
	else:
		y = random.randint(0, k) # Sample uniformly from {0, 1, ..., k}

	return y

def Analyzer(y_list: list, c: float, k: float):
	n: int = len(y_list)
	z: float = 1.0 * sum(y_list) / k
	def Debias(w) -> float:
		return (w - c * (k+1) / 2) / (1 - c * (k+1) / n)
	z = Debias(z)
	return z

def CalculatePrivitarizedSum(x_list: list):
	num_parties = len(x_list)
	assert(num_parties >= 1000)

	eps = 1.0
	delta = 1e-2
	k_val = 2

	# term1_privacy: float = (14 * k_val * math.log(2 / delta)) / ((num_parties - 1) * eps**2)
	# term2_privacy: float = (27 * k_val) / ((num_parties - 1) * eps)

	# gamma: float = max(term1_privacy, term2_privacy)
	# assert(1e-9 <= gamma <= 1-1e-9)

	# c_val = gamma * num_parties / (k_val + 1)

	gamma, c_val = calculate_c_gamma_for_fixed_k(num_parties, eps, delta, k_val)

	y_list: list = [LocalRandomizer(x=x, c=c_val, k=k_val, n=num_parties) for x in x_list]
	z: float = Analyzer(y_list=y_list, c=c_val, k=k_val)

	# print(sum(x_list))
	# print(z)
	return z

def RandomizedResponse(x, k, eps) -> int:
	p = math.exp(eps) / (math.exp(eps) + k - 1)
	x_bar = math.floor(x * k)
	if random.random() < p:
		return x_bar
	else:
		return numpy.random.randint(0, k)

def decode_freq(hist, k, eps0, n):
	p = math.exp(eps0) / (math.exp(eps0) + k - 1)
	q = (1 - p) / (k - 1)
	est = (hist/n - q) / (p - q)
	est = numpy.clip(est, 0, 1)
	return est * n

def grr(x_bucket, k, eps):
	p = math.exp(eps) / (math.exp(eps) + k - 1)
	if numpy.random.rand() < p:
		return x_bucket
	else:
		alt = numpy.random.randint(0, k - 1)
		return alt + (alt >= x_bucket)  # 避免重复

def decode_grr(counts, k, eps, n):
	p = math.exp(eps) / (math.exp(eps) + k - 1)
	q = (1 - p) / (k - 1)
	return (counts / n - q) / (p - q)

# 最后估计均值（假设每个桶中心代表该桶的真实值）
def estimate_mean(counts, k, eps, n):
	est_freqs = decode_grr(counts, k, eps, n)
	bucket_centers = numpy.linspace(0.5/k, 1 - 0.5/k, k)
	return numpy.sum(est_freqs * bucket_centers)

def quantize(x, k):
	# x ∈ [0,1]，划分成 k 个桶
	# 返回桶编号 ∈ {0, ..., k-1}
	bucket = int(x * k)
	return min(bucket, k - 1)  # 防止 x=1.0 时越界

def LDPMechanism(x_list, eps, delta, k=100):
	num_parties = len(x_list)
	privatized_y_list = [grr(quantize(x, k), k, eps) for x in x_list]
	hist = numpy.bincount(privatized_y_list, minlength=k)
	est_counts = estimate_mean(hist, k, eps, num_parties)
	return est_counts

def main(n_list: list=[]):
	num_trial = 1000
	squared_errors_of_multi_shufflers = []
	squared_errors_of_one_shuffler = []
	squared_errors_of_ldp = []

	x_list_list_of_multi_shuffler = [[random.random() for _ in range(n)] for n in n_list]
	x_list_of_one_shuffler = []
	for x_list in x_list_list_of_multi_shuffler:
		x_list_of_one_shuffler += x_list
	sum_of_x = sum(x_list_of_one_shuffler)
	num_parties = len(x_list_of_one_shuffler)

	for _ in range(num_trial):
		z_list_of_multi_shufflers = [CalculatePrivitarizedSum(x_list) for x_list in x_list_list_of_multi_shuffler]
		z_of_one_shuffler = CalculatePrivitarizedSum(x_list_of_one_shuffler)
		# z_of_ldp = sum([RandomizedResponse(x, k=10, eps=1.0) for x in x_list_of_one_shuffler])
		z_of_ldp: float = LDPMechanism(x_list_of_one_shuffler, eps=1.0, delta=0.01)

		# print(sum(x_list_of_one_shuffler), sum(z_list_of_multi_shufflers), z_of_one_shuffler)
		squared_errors_of_multi_shufflers.append( (sum_of_x/num_parties - sum(z_list_of_multi_shufflers)/num_parties) ** 2 )
		squared_errors_of_one_shuffler.append( (sum_of_x/num_parties - z_of_one_shuffler/num_parties) ** 2 )
		squared_errors_of_ldp.append( (sum_of_x/num_parties - z_of_ldp/num_parties) ** 2 )

	print(sum(squared_errors_of_multi_shufflers) / num_trial)
	print(sum(squared_errors_of_one_shuffler) / num_trial)
	print(sum(squared_errors_of_ldp) / num_trial)

if __name__ == '__main__':
	# print('Please n list:')
	n_list: list = [int(x) for x in input().split(' ')]
	main(n_list=n_list)
