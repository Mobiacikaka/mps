
import random
import math

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

def R_gamma_k_n_PH(x, gamma, k, n):
    """
    Algorithm 1: Private Histogram - Local Randomizer R_gamma_k_n_PH.
    This randomizer is used for computing private histograms over a finite domain [k].

    Public Parameters:
        gamma (float): Probability of submitting a uniformly random value (0 <= gamma <= 1).
        k (int): Domain size (e.g., [1, ..., k]).
        n (int): Number of parties (users).

    Input:
        x (int): The user's input, an integer in the domain [1, ..., k].

    Output:
        y (int): The privatized message, an integer in the domain [1, ..., k].
    """
    if not (1 <= x <= k):
        raise ValueError(f"Input x ({x}) must be within the domain [1, ..., {k}].")
    if not (0 <= gamma <= 1):
        raise ValueError("Gamma (probability) must be between 0 and 1.")
    if not (isinstance(k, int) and k > 0):
        raise ValueError("Domain size k must be a positive integer.")
    if not (isinstance(n, int) and n > 0):
        raise ValueError("Number of parties n must be a positive integer.")

    # Sample b from a Bernoulli distribution with parameter gamma
    b = Ber(gamma)

    if b == 0:
        # If b is 0, let y be the true value x
        y = x
    else:
        # If b is 1, sample y uniformly at random from the domain [1, ..., k]
        y = random.randint(1, k)

    return y

def R_c_k_n(x, c, k, n):
    """
    Algorithm 2: Local Randomizer R_c_k_n for Optimal Summation.
    This randomizer is used for computing the sum of real values x_i in [0, 1].

    Public Parameters:
        c (float): A parameter used in determining the probability of randomization.
        k (int): Precision parameter for fixed-point encoding (domain size {0, ..., k}).
        n (int): Number of parties (users).

    Input:
        x (float): The user's input, a real number in the range [0, 1].

    Output:
        y (int): The privatized message, an integer in the domain {0, ..., k}.
    """
    if not (0 <= x <= 1):
        raise ValueError(f"Input x ({x}) must be within the range [0, 1].")
    if not (isinstance(k, int) and k >= 0): # k can be 0 for a single point
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
    
    # Handle edge case where xk is an integer (bernoulli_prob would be 0)
    if bernoulli_prob < 1e-9: # Use a small epsilon for floating point comparison
        x_bar = floor_scaled_x
    else:
        x_bar = floor_scaled_x + Ber(bernoulli_prob)

    # The domain for y is {0, 1, ..., k}. Ensure x_bar stays within this range.
    # It's possible for x_bar to be k+1 if x=1 and Ber(0) returns 1, but x_bar should be k.
    # The paper implies x_bar is in {0, ..., k}.
    x_bar = min(x_bar, k) # Cap at k if rounding up from 1.0

    # Step 2: Apply randomized response based on parameter c.
    # The probability gamma for this algorithm is c * (k+1) / n.
    # This is derived from the paper's analysis connecting Algorithm 1's gamma
    # to the parameters of Algorithm 2.
    gamma_prime = c * (k + 1) / n
    
    # Ensure gamma_prime is a valid probability (0 to 1)
    # The paper's Theorem 1 implies gamma < 1 for privacy.
    if not (0 <= gamma_prime <= 1):
        # This condition might indicate an issue with parameter choice (c, k, n)
        # or that gamma_prime can exceed 1 in some theoretical contexts
        # but for practical use as a probability, it should be capped.
        print(f"Warning: Calculated gamma_prime ({gamma_prime}) is outside [0, 1]. Capping.")
        gamma_prime = max(0.0, min(1.0, gamma_prime))

    # Sample b from a Bernoulli distribution with parameter gamma_prime
    b = Ber(gamma_prime)

    if b == 0:
        # If b is 0, let y be the encoded value x_bar
        y = int(x_bar) # Ensure y is an integer
    else:
        # If b is 1, sample y uniformly at random from the domain {0, 1, ..., k}
        y = random.randint(0, k)

    return y

# --- Example Usage ---
if __name__ == "__main__":
    print("--- Testing Algorithm 1 (Private Histogram Local Randomizer) ---")
    # Example parameters
    gamma_val = 0.5  # 50% chance of random response
    k_val = 10       # Domain size [1, ..., 10]
    n_val = 100      # Number of parties

    input_x_ph = 5
    privatized_y_ph = R_gamma_k_n_PH(input_x_ph, gamma_val, k_val, n_val)
    print(f"Input x (Algorithm 1): {input_x_ph}")
    print(f"Privatized y (Algorithm 1): {privatized_y_ph}")

    # Simulate multiple runs to see the effect of gamma
    true_count = 0
    random_count = 0
    for _ in range(1000):
        result = R_gamma_k_n_PH(input_x_ph, gamma_val, k_val, n_val)
        if result == input_x_ph:
            true_count += 1
        else:
            random_count += 1
    print(f"Simulated 1000 runs for x={input_x_ph}, gamma={gamma_val}:")
    print(f"  Times input_x_ph was returned: {true_count} (Expected: ~{1000 * (1 - gamma_val)})")
    print(f"  Times random value was returned: {random_count} (Expected: ~{1000 * gamma_val})")


    print("\n--- Testing Algorithm 2 (Optimal Summation Local Randomizer) ---")
    # Example parameters (from the paper's context, c, k, n affect gamma_prime)
    c_val = 0.1
    k_val_sum = 100 # Precision for summation, domain {0, ..., 100}
    n_val_sum = 1000 # Number of parties

    input_x_sum = 0.75 # A real number in [0, 1]
    privatized_y_sum = R_c_k_n(input_x_sum, c_val, k_val_sum, n_val_sum)
    print(f"Input x (Algorithm 2): {input_x_sum}")
    print(f"Privatized y (Algorithm 2): {privatized_y_sum}")

    # Simulate multiple runs to see the effect
    encoded_values = []
    for _ in range(1000):
        encoded_values.append(R_c_k_n(input_x_sum, c_val, k_val_sum, n_val_sum))
    
    # Calculate expected x_bar
    expected_x_bar = input_x_sum * k_val_sum
    print(f"Expected x_bar (input_x_sum * k_val_sum): {expected_x_bar}")

    # Calculate the effective gamma_prime for these parameters
    effective_gamma_prime = c_val * (k_val_sum + 1) / n_val_sum
    print(f"Effective gamma_prime for Algorithm 2: {effective_gamma_prime}")

    # Count occurrences of the expected encoded value (or close to it due to randomized rounding)
    # and random values. This is complex due to randomized rounding and then randomized response.
    # A simpler check is to see the distribution.
    from collections import Counter
    value_counts = Counter(encoded_values)
    print(f"Distribution of privatized values (Algorithm 2, first 10 most common): {value_counts.most_common(10)}")
    print(f"Mean of privatized values (Algorithm 2): {sum(encoded_values) / len(encoded_values)}")

    # Test edge cases for Algorithm 2 input x
    print("\nTesting Algorithm 2 edge cases:")
    print(f"Input x=0.0: {R_c_k_n(0.0, c_val, k_val_sum, n_val_sum)}")
    print(f"Input x=1.0: {R_c_k_n(1.0, c_val, k_val_sum, n_val_sum)}")
