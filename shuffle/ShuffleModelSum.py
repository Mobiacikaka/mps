
import random
import math
from scipy.optimize import fsolve # For numerical root finding

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

def R_c_k_n(x, c, k, n):
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

def calculate_optimal_c_k(n, epsilon, delta):
	"""
	Calculates the optimal parameters c and k based on the paper's formulas
	for a given number of parties (n), privacy budget (epsilon), and delta.

	The paper establishes a relationship where 'gamma' (the probability of randomizing)
	is determined by both privacy requirements (Theorem 1) and by the accuracy-optimizing
	choice of 'k' (Theorem 2's connection of c, k, n to gamma).
	We solve for 'k' such that these two expressions for 'gamma' are equal.

	Args:
		n (int): Number of parties (users). Must be > 1.
		epsilon (float): Privacy parameter epsilon. Must be > 0.
		delta (float): Privacy parameter delta. Must be between 0 and 0.5 (as per Theorem 3).

	Returns:
		tuple: (c, k) - the calculated optimal c and k values.
	"""
	if not (isinstance(n, int) and n > 1):
		raise ValueError("Number of parties n must be an integer greater than 1.")
	if not (epsilon > 0):
		raise ValueError("Epsilon must be greater than 0.")
	if not (0 < delta < 0.5): # Paper's Theorem 3 assumes delta < 1/2
		raise ValueError("Delta must be between 0 and 0.5.")

	# Define the function whose root we want to find for k.
	# We are looking for k such that:
	# gamma_from_accuracy_optimization = gamma_required_for_privacy
	# (k+1)/k^3 = max( (14k log(2/δ)) / ((n-1)ε^2), (27k) / ((n-1)ε) )
	def func_for_k_root(k_val):
		# Ensure k_val is positive to avoid math domain errors (e.g., k^3 in denominator)
		if k_val <= 0:
			return 1e10 # Return a large value to push the solver away from non-positive k

		# Term 1 from Theorem 1's gamma max (privacy requirement)
		term1_privacy = (14 * k_val * math.log(2 / delta)) / ((n - 1) * epsilon**2)
		# Term 2 from Theorem 1's gamma max (privacy requirement)
		term2_privacy = (27 * k_val) / ((n - 1) * epsilon)

		gamma_required_for_privacy = max(term1_privacy, term2_privacy)

		# Gamma from accuracy optimization (derived from k = (n/c)^(1/3) and gamma = c(k+1)/n)
		# This simplifies to gamma = (k+1)/k^3
		gamma_from_accuracy_optimization = (k_val + 1) / (k_val**3)

		# We want to find k where these two gamma expressions are equal.
		# The solver finds roots (where the function returns 0).
		return gamma_from_accuracy_optimization - gamma_required_for_privacy

	# Provide an initial guess for k.
	# A rough asymptotic estimate for k is (n * epsilon^2 / (14 * log(2/delta)))**(1/2)
	# This helps fsolve converge faster and more reliably.
	try:
		k_initial_guess = (n * epsilon**2 / (14 * math.log(2/delta)))**(1/2)
	except ValueError: # Handle cases where log(2/delta) might be non-positive or very small
		k_initial_guess = 1.0 # Fallback to a small positive value

	if k_initial_guess <= 0: # Ensure initial guess is positive
		k_initial_guess = 1.0

	# Solve for k numerically using fsolve. It returns an array, so take the first element.
	k_solution = fsolve(func_for_k_root, k_initial_guess)[0]

	# k must be an integer. The paper's analysis implies a theoretical k,
	# so we round it to the nearest integer, ensuring it's at least 1.
	# Using math.ceil ensures we err on the side of slightly higher precision/privacy if needed.
	k = max(1, math.ceil(k_solution))

	# Now that k is determined, calculate the gamma that satisfies the privacy bound for this k.
	gamma_calculated: float = max(
		(14 * k * math.log(2 / delta)) / ((n - 1) * epsilon**2),
		(27 * k) / ((n - 1) * epsilon)
	)

	# Finally, calculate c using the relationship: c = gamma * n / (k+1)
	c = gamma_calculated * n / (k + 1)

	# Basic sanity checks for calculated values
	if c < 0 or k < 1:
		print(f"Warning: Calculated c ({c:.4f}) or k ({k}) are problematic. Check input parameters.")

	return c, k

# --- Example Usage ---
if __name__ == "__main__":
	print("--- Testing Algorithm 2 with Calculated Optimal c and k ---")

	# Define desired privacy parameters and number of parties
	num_parties = 1000
	target_epsilon = 1.0
	target_delta = 1e-2
	num_trials = 1 # Number of times to simulate the entire n-party summation protocol

	print(f"Calculating optimal c and k for n={num_parties}, epsilon={target_epsilon}, delta={target_delta}")
	try:
		# optimal_c, optimal_k = calculate_optimal_c_k(num_parties, target_epsilon, target_delta)
		k_val = 2
		gamma_val, c_val = calculate_c_gamma_for_fixed_k(
			num_parties, target_epsilon, target_delta, k_val
		)
		assert(0 <= gamma_val <= 1)
		print(f"Optimal c: {c_val:.4f}")
		print(f"Optimal k: {k_val}")

		# Now use these calculated values in the local randomizer
		# For simplicity, let's assume all users have the same input in this simulation.
		# In a real scenario, users would have different inputs.
		common_input_x = 0.75
		true_sum_of_inputs = common_input_x * num_parties

		simulated_sums = []
		squared_errors = []

		print(f"\nSimulating {num_trials} trials of the {num_parties}-party summation protocol...")
		for trial in range(num_trials):
			current_trial_sum_privatized_y = 0
			privatized_y_list = []
			for _ in range(num_parties): # Each party contributes one privatized value
				privatized_y = R_c_k_n(common_input_x, c_val, k_val, num_parties)
				current_trial_sum_privatized_y += privatized_y
				privatized_y_list.append(privatized_y)

			# The analyzer (Algorithm 3, not fully implemented here but described in paper)
			# would take this sum of privatized messages and debias it.
			# The paper states: DeBias(w) = (w - c(k+1)/2) / (1 - c(k+1)/n)
			# Here, w is current_trial_sum_privatized_y
			# Note: The paper's DeBias formula applies to the *average* (sum/n) of messages,
			# so we'll adjust it for the total sum.
			# If sum_y_i is the sum of privatized messages, and E[y_i/k] = x_i, then
			# E[sum_y_i / k] = sum_x_i.
			# The debiasing for the sum would be:
			# debiased_sum = (current_trial_sum_privatized_y - num_parties * optimal_c * (optimal_k + 1) / 2) / (1 - optimal_c * (optimal_k + 1) / num_parties)
			# However, for MSE calculation related to the paper's O(n^(1/3)) noise,
			# we often compare the sum of *encoded* values.
			# Let's use the simplest interpretation for MSE: (estimated_sum - true_sum)^2

			# The paper's analyzer (Algorithm 3) computes:
			# z_hat = (1/k) * sum(y_i)
			# z = DeBias(z_hat) where DeBias(w) = (w - c(k+1)/2) / (1 - c(k+1)/n)
			# So, the final estimated sum would be:
			# estimated_sum = k * DeBias(current_trial_sum_privatized_y / k)
			# estimated_sum = k * ( (current_trial_sum_privatized_y / k) - optimal_c * (optimal_k + 1) / 2 ) / (1 - optimal_c * (optimal_k + 1) / num_parties)
			# estimated_sum = (current_trial_sum_privatized_y - k * optimal_c * (optimal_k + 1) / 2) / (1 - optimal_c * (optimal_k + 1) / num_parties)

			# Let's use the unbiased property E[y_i/k] = x_i directly for MSE calculation,
			# assuming the analyzer effectively recovers sum(x_i).
			# The MSE is defined as E[(P(x) - f(x))^2]. Here f(x) is sum(x_i).
			# P(x) is the output of the analyzer.
			# For simplicity in this simulation, let's consider the sum of y_i/k as the estimate
			# and compare it to the sum of x_i. The debiasing corrects for the bias introduced by the randomizer.
			# The paper states that the estimator is unbiased, so E[estimated_sum] = true_sum.
			# Thus, MSE = Variance. We'll directly calculate (estimated_sum - true_sum)^2.

			# Re-implementing the debiasing step from Algorithm 3:
			gamma_prime_used = c_val * (k_val + 1) / num_parties
			if abs(1 - gamma_prime_used) < 1e-9: # Avoid division by zero if gamma_prime_used is ~1
				estimated_sum = 0 # Or handle as error/infinity
			else:
				# The paper's debiasing is for the average (z_hat = sum(y_i)/k/n),
				# and then z = DeBias(z_hat).
				# The actual sum of original inputs is sum(x_i).
				# The expected value of y_i is (1-gamma_prime) * x_bar_i + gamma_prime * (k/2)
				# E[y_i] = (1-gamma_prime) * k * x_i + gamma_prime * k/2 (approx, if x_bar is k*x)
				# E[sum(y_i)] = (1-gamma_prime) * k * sum(x_i) + num_parties * gamma_prime * k/2
				# So, sum(x_i) = (E[sum(y_i)] - num_parties * gamma_prime * k/2) / (k * (1-gamma_prime))
				# Let's use the formula from Algorithm 3's DeBias, applied to the sum directly.
				# The paper states: E[x_bar/k] = E[x]
				# And the analyzer's estimator is unbiased: E[DeBias(sum(y_i)/k)] = sum(x_i).
				# So, the estimated sum is:
				estimated_sum = (current_trial_sum_privatized_y - num_parties * c_val * (k_val + 1) / 2) / (1 - c_val * (k_val + 1) / num_parties)
				# This formula is derived by scaling the debiasing of the average back to the sum.
				# The denominator (1 - optimal_c * (optimal_k + 1) / num_parties) is (1 - gamma_prime_used).
				# The numerator is current_trial_sum_privatized_y - E[noise_from_blanket_sum]

			simulated_sums.append(estimated_sum)
			squared_error = (estimated_sum - true_sum_of_inputs)**2
			squared_errors.append(squared_error)

			# print(sum(privatized_y_list)/k_val/num_parties)
			z_hat = 1.0 * sum(privatized_y_list) / k_val
			z: float = (z_hat - c_val * (k_val + 1) / 2) / (1 - c_val * (k_val + 1)/num_parties)
			print(z / num_parties)

		empirical_mse = sum(squared_errors) / num_trials
		print(f"True sum of inputs (common_input_x * num_parties): {true_sum_of_inputs:.4f}")
		print(f"Empirical Mean Squared Error (MSE) over {num_trials} trials: {empirical_mse:.4f}")

		# Verify the gamma values at the calculated k_val
		gamma_accuracy_check = (k_val + 1) / (k_val**3)
		print(f"Gamma from accuracy optimization for k_val: {gamma_accuracy_check:.4f}")

		term1_privacy_check = (14 * k_val * math.log(2 / target_delta)) / ((num_parties - 1) * target_epsilon**2)
		term2_privacy_check = (27 * k_val) / ((num_parties - 1) * target_epsilon)
		gamma_privacy_check = max(term1_privacy_check, term2_privacy_check)
		print(f"Gamma required for privacy for optimal_k: {gamma_privacy_check:.4f}")

		print("\nNote: For an optimal solution, effective_gamma_prime_used, gamma_accuracy_check,")
		print("and gamma_privacy_check should be very close (due to numerical solving and rounding).")

		# Optional: Print distribution of estimated sums (not individual y values)
		# from collections import Counter
		# print(f"\nDistribution of estimated sums (first 10 most common): {Counter(simulated_sums).most_common(10)}")
		print(f"Mean of estimated sums: {sum(simulated_sums) / len(simulated_sums):.4f}")

	except ValueError as e:
		print(f"Error: {e}")
	except Exception as e:
		print(f"An unexpected error occurred: {e}. Ensure 'scipy' is installed (`pip install scipy`).")

	print("\n--- Testing with different privacy parameters (more stringent) ---")
	try:
		num_parties_2 = 5000
		target_epsilon_2 = 0.1 # More stringent privacy
		target_delta_2 = 1e-7 # Smaller delta
		num_trials_2 = 1 # Fewer trials for this example
		print(f"Calculating optimal c and k for n={num_parties_2}, epsilon={target_epsilon_2}, delta={target_delta_2}")
		optimal_c_2, optimal_k_2 = calculate_optimal_c_k(num_parties_2, target_epsilon_2, target_delta_2)
		print(f"Optimal c: {optimal_c_2:.4f}")
		print(f"Optimal k: {optimal_k_2}")

		common_input_x_2 = 0.5
		true_sum_of_inputs_2 = common_input_x_2 * num_parties_2
		squared_errors_2 = []

		print(f"\nSimulating {num_trials_2} trials of the {num_parties_2}-party summation protocol...")
		for trial in range(num_trials_2):
			current_trial_sum_privatized_y_2 = 0
			for _ in range(num_parties_2):
				privatized_y_2 = R_c_k_n(common_input_x_2, optimal_c_2, optimal_k_2, num_parties_2)
				current_trial_sum_privatized_y_2 += privatized_y_2

			gamma_prime_used_2 = optimal_c_2 * (optimal_k_2 + 1) / num_parties_2
			if abs(1 - gamma_prime_used_2) < 1e-9:
				estimated_sum_2 = 0
			else:
				estimated_sum_2 = (current_trial_sum_privatized_y_2 - num_parties_2 * optimal_c_2 * (optimal_k_2 + 1) / 2) / (1 - optimal_c_2 * (optimal_k_2 + 1) / num_parties_2)

			squared_error_2 = (estimated_sum_2 - true_sum_of_inputs_2)**2
			squared_errors_2.append(squared_error_2)

		empirical_mse_2 = sum(squared_errors_2) / num_trials_2
		print(f"True sum of inputs: {true_sum_of_inputs_2:.4f}")
		print(f"Empirical Mean Squared Error (MSE) over {num_trials_2} trials: {empirical_mse_2:.4f}")

	except ValueError as e:
		print(f"Error: {e}")
	except Exception as e:
		print(f"An unexpected error occurred: {e}. Ensure 'scipy' is installed (`pip install scipy`).")
