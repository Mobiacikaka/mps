
import math
import random
from collections import defaultdict

# --- Helper Functions ---

def is_prime(n):
    """Checks if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def find_next_prime(n):
    """Finds the smallest prime number greater than or equal to n."""
    while not is_prime(n):
        n += 1
    return n

def universal_hash(x, u, v, q, b):
    """
    Implements the universal hash function h_u,v(x) = ((u*x + v) mod q) mod b.
    Args:
        x (int): The element from the domain [B].
        u (int): Random parameter for the hash function.
        v (int): Random parameter for the hash function.
        q (int): A prime number greater than or equal to B.
        b (int): The reduced domain size.
    Returns:
        int: The hashed value in [b].
    """
    return ((u * x + v) % q) % b

# --- Algorithm 4: Local Randomizer RFE1 ---

class LocalRandomizerFE1:
    """
    Implements Algorithm 4: Local Randomizer for Frequency Estimation (Large Domain).
    Each user privatizes their input by sending a real output and blanket noises.
    """
    def __init__(self, B, b, n, epsilon, delta):
        """
        Initializes the local randomizer with public parameters.
        Args:
            B (int): Original domain size [0, B-1].
            b (int): Reduced domain size after hashing.
            n (int): Number of users.
            epsilon (float): Privacy parameter epsilon.
            delta (float): Privacy parameter delta.
        """
        self.B = B
        self.b = b
        self.n = n
        self.epsilon = epsilon
        self.delta = delta
        # q is a prime > B, used in universal hashing
        self.q = find_next_prime(B) 
        # Calculate rho based on the paper's formula
        # rho = (32 * ln(2/delta)) / (epsilon^2) * b / n
        self.rho = (32 * math.log(2 / delta)) / (epsilon**2) * (self.b / self.n)

    def privatize(self, x):
        """
        Privatizes a single user's input x.
        Args:
            x (int): The user's private input from [B].
        Returns:
            list: A list of (u, v, w) tuples representing the messages to be shuffled.
        """
        messages = []

        # 1. Choose (u, v) uniformly for the real output
        # u from {1, ..., q-1}, v from [q]
        u_real = random.randint(1, self.q - 1)
        v_real = random.randint(0, self.q - 1)
        w_real = universal_hash(x, u_real, v_real, self.q, self.b)
        messages.append((u_real, v_real, w_real))

        # 2. Add floor(rho) blanket noises
        for _ in range(math.floor(self.rho)):
            u_noise = random.randint(1, self.q - 1)
            v_noise = random.randint(0, self.q - 1)
            w_noise = random.randint(0, self.b - 1) # w from [b]
            messages.append((u_noise, v_noise, w_noise))

        # 3. Add an additional blanket noise with probability (rho - floor(rho))
        if random.random() < (self.rho - math.floor(self.rho)):
            u_noise = random.randint(1, self.q - 1)
            v_noise = random.randint(0, self.q - 1)
            w_noise = random.randint(0, self.b - 1)
            messages.append((u_noise, v_noise, w_noise))
            
        return messages

# --- Algorithm 5: Analyzer AFE1 ---

class AnalyzerFE1:
    """
    Implements Algorithm 5: Analyzer for Frequency Estimation (Large Domain).
    Processes shuffled messages to estimate frequencies.
    """
    def __init__(self, B, b, n, epsilon, delta):
        """
        Initializes the analyzer with public parameters.
        Args:
            B (int): Original domain size [0, B-1].
            b (int): Reduced domain size after hashing.
            n (int): Number of users.
            epsilon (float): Privacy parameter epsilon.
            delta (float): Privacy parameter delta.
        """
        self.B = B
        self.b = b
        self.n = n
        self.epsilon = epsilon
        self.delta = delta
        self.q = find_next_prime(B)
        self.rho = (32 * math.log(2 / delta)) / (epsilon**2) * (self.b / self.n)

        # Calculate p_col (collision probability)
        # p_col = floor(q/b) * ((q mod b) + q - b) / (q * (q-1))
        # This formula is slightly off from standard universal hashing collision prob (1/b)
        # The paper's formula is specific to their proof.
        # For simplicity and common practice, often p_col is approximated as 1/b for universal hashing.
        # Using the paper's explicit formula:
        q_div_b_floor = math.floor(self.q / self.b)
        q_mod_b = self.q % self.b
        self.p_col = q_div_b_floor * (q_mod_b + self.q - self.b) / (self.q * (self.q - 1))
        if self.q == 1: # Handle edge case where q-1 is 0
            self.p_col = 0
        elif self.b == 0: # Handle edge case where b is 0
            self.p_col = 0
        else:
            self.p_col = q_div_b_floor * (q_mod_b + self.q - self.b) / (self.q * (self.q - 1))


    def estimate_frequency(self, target_x, shuffled_messages):
        """
        Estimates the frequency of a target element x from the shuffled messages.
        Args:
            target_x (int): The element whose frequency is to be estimated.
            shuffled_messages (list): A list of (u, v, w) tuples from all users, shuffled.
        Returns:
            float: The estimated frequency of target_x.
        """
        X = 0 # Count of tuples satisfying h_u,v(target_x) = w

        for u, v, w in shuffled_messages:
            # Check if the hash of target_x matches the received w using the same (u,v)
            if universal_hash(target_x, u, v, self.q, self.b) == w:
                X += 1
        
        # Remove bias caused by blanket noises and hash collisions
        # g_hat_x = (X - n*rho/b - n*p_col) / (1 - p_col)
        # Ensure denominator is not zero
        denominator = (1 - self.p_col)
        if denominator == 0:
            return 0 # Or handle error appropriately
        
        g_hat_x = (X - (self.n * self.rho / self.b) - (self.n * self.p_col)) / denominator
        return g_hat_x

    def estimate_all_frequencies(self, shuffled_messages):
        """
        Estimates frequencies for all elements in the domain [B].
        This is an optimization described in Theorem 3.7.
        Args:
            shuffled_messages (list): A list of (u, v, w) tuples from all users, shuffled.
        Returns:
            dict: A dictionary where keys are elements from [B] and values are their estimated frequencies.
        """
        # Initialize counts for all possible elements in [B]
        X_counts = defaultdict(int)

        # For each received message (u, v, w), find all x such that h_u,v(x) = w
        # and increment their counts.
        for u, v, w in shuffled_messages:
            # The set X(u,v,w) = {u^-1(w + i*b - v) mod q | i in {0, ...}} intersect [B]
            # u_inv is the multiplicative inverse of u in Z_q
            try:
                u_inv = pow(u, -1, self.q) # Modular multiplicative inverse
            except ValueError:
                # This can happen if u and q are not coprime, which shouldn't for u in [1, q-1] and q prime
                # but good to handle defensively. If u is 0, pow will fail.
                # In universal hashing, u is chosen from {1, ..., q-1}, so u should be coprime to prime q.
                print(f"Warning: Could not find modular inverse for u={u}, q={self.q}. Skipping message.")
                continue

            # Iterate through possible 'i' values
            # The paper states i in {0,1,...,floor((q-1-w)/b)}
            # This logic needs to be carefully implemented to find all x that map to w
            # under h_u,v(x) = ((u*x + v) mod q) mod b
            # Rearranging: (u*x + v) mod q = w + i*b for some i
            # u*x mod q = (w + i*b - v) mod q
            # x mod q = u_inv * (w + i*b - v) mod q
            
            # The values of (w + i*b) mod q need to be explored.
            # A simpler way is to iterate through all x in [B] and check,
            # but the paper suggests an optimized way to find X(u,v,w)
            
            # The paper says X(u,v,w) has at most q/b = O(B/b) elements.
            # Let's reconstruct the x values that map to w
            
            # Iterate through possible values of (w + i*b)
            # (w + i*b) must be less than q (the modulus for the first mod operation)
            # and also must be non-negative.
            
            # Start with the smallest value that could map to w
            start_val_mod_q = w
            
            # Find all potential intermediate values (ux+v) mod q that would result in w
            # These are of the form w, w+b, w+2b, ... up to q-1
            
            current_intermediate_val = start_val_mod_q
            while current_intermediate_val < self.q:
                # u*x + v = current_intermediate_val (mod q)
                # u*x = (current_intermediate_val - v) (mod q)
                
                # Calculate the potential x value
                x_candidate_mod_q = (u_inv * (current_intermediate_val - v)) % self.q
                
                # If x_candidate_mod_q is within the original domain [B]
                if 0 <= x_candidate_mod_q < self.B:
                    X_counts[x_candidate_mod_q] += 1
                
                current_intermediate_val += self.b # Increment by b to find next value that maps to w
                
        estimated_frequencies = {}
        denominator = (1 - self.p_col)
        if denominator == 0:
            # Handle this case, perhaps return all zeros or raise an error
            for x in range(self.B):
                estimated_frequencies[x] = 0
            return estimated_frequencies

        for x in range(self.B):
            X = X_counts[x]
            g_hat_x = (X - (self.n * self.rho / self.b) - (self.n * self.p_col)) / denominator
            estimated_frequencies[x] = g_hat_x
        
        return estimated_frequencies


# --- Example Usage ---
if __name__ == "__main__":
    # Define parameters (example values, adjust as needed for real simulations)
    num_users = 10000
    original_domain_size = 100000 # B
    reduced_domain_size = 1000   # b (e.g., n/log^c n for some c)
    epsilon = 1.0 # Privacy parameter
    delta = 1e-9 # Privacy parameter (e.g., n^-2)

    print(f"Simulation Parameters:")
    print(f"  Number of users (n): {num_users}")
    print(f"  Original domain size (B): {original_domain_size}")
    print(f"  Reduced domain size (b): {reduced_domain_size}")
    print(f"  Epsilon (ε): {epsilon}")
    print(f"  Delta (δ): {delta}")
    print("-" * 30)

    # 1. Simulate user data (true frequencies)
    # Let's create some synthetic data with varying frequencies
    true_data = [random.randint(0, original_domain_size - 1) for _ in range(num_users)]
    
    # Introduce some "heavy hitters" to make it more interesting
    for _ in range(num_users // 10): # 10% of users report a specific item
        true_data[random.randint(0, num_users - 1)] = 42 # Item 42 is popular
    
    true_frequencies = defaultdict(int)
    for item in true_data:
        true_frequencies[item] += 1

    print(f"True frequency of item 42: {true_frequencies[42]}")
    print(f"True frequency of item 100: {true_frequencies[100]}")
    print("-" * 30)

    # 2. Each user privatizes their data using the Local Randomizer
    local_randomizer = LocalRandomizerFE1(original_domain_size, reduced_domain_size, num_users, epsilon, delta)
    
    all_privatized_messages = []
    print("Users privatizing their data...")
    for user_id in range(num_users):
        user_input = true_data[user_id]
        priv_messages = local_randomizer.privatize(user_input)
        all_privatized_messages.extend(priv_messages)
    
    # 3. Shuffle the messages (simulated by random.shuffle)
    random.shuffle(all_privatized_messages)
    print(f"Total messages after privatization and shuffling: {len(all_privatized_messages)}")
    print("-" * 30)

    # 4. The Analyzer estimates frequencies
    analyzer = AnalyzerFE1(original_domain_size, reduced_domain_size, num_users, epsilon, delta)

    # Estimate a single frequency (e.g., for item 42)
    estimated_freq_42 = analyzer.estimate_frequency(42, all_privatized_messages)
    print(f"Estimated frequency of item 42: {estimated_freq_42:.2f}")
    print(f"Error for item 42: {abs(estimated_freq_42 - true_frequencies[42]):.2f}")

    # Estimate all frequencies (more computationally intensive for large B)
    print("\nEstimating all frequencies (this might take a while for large B)...")
    estimated_all_freqs = analyzer.estimate_all_frequencies(all_privatized_messages)

    print(f"Estimated frequency of item 42 (from all): {estimated_all_freqs.get(42, 0):.2f}")
    print(f"Estimated frequency of item 100 (from all): {estimated_all_freqs.get(100, 0):.2f}")
    
    # Calculate overall error for a few items or a sample
    total_squared_error = 0
    num_checked_items = 0
    for item, true_freq in true_frequencies.items():
        estimated_freq = estimated_all_freqs.get(item, 0)
        total_squared_error += (estimated_freq - true_freq)**2
        num_checked_items += 1
        if num_checked_items > 100: # Limit for display
            break
            
    # Also check some items that were not in true_data (should be near 0)
    for i in range(original_domain_size):
        if i not in true_frequencies and i % (original_domain_size // 10) == 0:
             estimated_freq = estimated_all_freqs.get(i, 0)
             total_squared_error += (estimated_freq - true_frequencies.get(i, 0))**2
             num_checked_items += 1
             if num_checked_items > 200:
                 break


    mse = total_squared_error / num_checked_items if num_checked_items > 0 else 0
    print(f"Mean Squared Error (MSE) for {num_checked_items} sampled items: {mse:.2f}")
    print("-" * 30)
    print("Simulation complete.")

