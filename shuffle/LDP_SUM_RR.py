#!/bin/python3

import numpy as np

# ------------------------
# 参数设置
# ------------------------
n_users = 1000         # 用户数量
max_val = 10           # 数据最大值（整数）
epsilon = 1.0          # LDP隐私预算
np.random.seed(0)

# ------------------------
# 用户数据生成（整数值 [0, max_val]）
# ------------------------
user_data = np.random.randint(0, max_val + 1, size=n_users)
true_sum = np.sum(user_data)

# ------------------------
# RR 参数
# ------------------------
def rr_bit(b, epsilon):
    """对单个位应用RR扰动"""
    p = np.exp(epsilon) / (1 + np.exp(epsilon))
    return b if np.random.rand() < p else 1 - b

# ------------------------
# 编码方式：每个用户用 one-hot vector 表示值（长度 max_val+1）
# ------------------------
def one_hot_encode(x, max_val):
    vec = np.zeros(max_val + 1)
    vec[x] = 1
    return vec

# ------------------------
# 用户端：编码 + RR扰动
# ------------------------
perturbed_vectors = []
for x in user_data:
    vec = one_hot_encode(x, max_val)
    perturbed = np.array([rr_bit(int(b), epsilon) for b in vec])
    perturbed_vectors.append(perturbed)

perturbed_matrix = np.array(perturbed_vectors)  # shape: [n_users, max_val+1]

# ------------------------
# 服务端解码估计频率分布（还原每个值的概率）
# ------------------------
def decode_rr_vector(perturbed_matrix, epsilon):
    p = np.exp(epsilon) / (1 + np.exp(epsilon))
    q = 1 - p
    est_freq = (np.mean(perturbed_matrix, axis=0) - q) / (p - q)
    est_freq = np.clip(est_freq, 0, 1)  # 防止数值波动带来的负值
    est_freq_sum = est_freq * n_users
    return est_freq_sum

est_freq_sum = decode_rr_vector(perturbed_matrix, epsilon)

# ------------------------
# 估计总和
# ------------------------
est_sum = sum(i * count for i, count in enumerate(est_freq_sum))

# ------------------------
# 输出结果
# ------------------------
print(f"True Sum: {true_sum}")
print(f"Estimated LDP Sum (RR): {est_sum:.2f}")
print(f"Absolute Error: {abs(est_sum - true_sum):.2f}")
