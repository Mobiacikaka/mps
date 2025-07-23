import math

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
    term1_privacy = (14 * k_fixed * math.log(2 / delta)) / ((n - 1) * epsilon**2)
    term2_privacy = (27 * k_fixed) / ((n - 1) * epsilon)

    gamma_required = max(term1_privacy, term2_privacy)

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

# --- Example Usage ---
if __name__ == "__main__":
    # Define your system parameters and desired privacy
    num_parties_example = 1000
    target_epsilon_example = 0.5
    target_delta_example = 1e-2
    fixed_k_example = 10 # Your chosen fixed k

    print(f"--- Calculating c and gamma for fixed k={fixed_k_example} ---")
    print(f"Parameters: n={num_parties_example}, epsilon={target_epsilon_example}, delta={target_delta_example}")

    try:
        gamma_val, c_val = calculate_c_gamma_for_fixed_k(
            num_parties_example, target_epsilon_example, target_delta_example, fixed_k_example
        )
        print(f"Minimum gamma required for privacy: {gamma_val:.4f}")
        print(f"Calculated c value: {c_val:.4f}")

        # You would then use this c_val and your fixed_k_example in your R_c_k_n function
        # For example:
        # from your_module import R_c_k_n # Assuming R_c_k_n is in a module
        # privatized_output = R_c_k_n(0.75, c_val, fixed_k_example, num_parties_example)
        # print(f"Example privatized output with calculated c and fixed k: {privatized_output}")

    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}.")

    print("\n--- Example with parameters that might lead to infeasibility (small n, strict privacy) ---")
    try:
        gamma_val_bad, c_val_bad = calculate_c_gamma_for_fixed_k(
            n=1000, epsilon=0.5, delta=1e-2, k_fixed=10
        )
        print(f"Minimum gamma required for privacy: {gamma_val_bad:.4f}")
        print(f"Calculated c value: {c_val_bad:.4f}")
    except ValueError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}.")
