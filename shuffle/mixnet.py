#!/bin/python3

import hashlib
import random
from typing import List, Tuple


# === 模拟加密与重加密 ===

def encrypt(message: str, nonce: str) -> str:
    """模拟加密：消息 + 随机数哈希"""
    return hashlib.sha256((message + nonce).encode()).hexdigest()

def reencrypt(ciphertext: str, rekey: str) -> str:
    """模拟重加密：再次加盐哈希"""
    return hashlib.sha256((ciphertext + rekey).encode()).hexdigest()


# === 用户发送阶段 ===

def generate_user_messages(n_users: int) -> List[str]:
    """每个用户生成一条加密消息"""
    messages = []
    for i in range(n_users):
        message = f"user_{i}_data"
        nonce = f"nonce_{i}"
        ct = encrypt(message, nonce)
        messages.append(ct)
    return messages


# === Mix Node 定义 ===

class MixNode:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.rekey = f"mixnode_{node_id}_rekey"

    def process(self, messages: List[str]) -> List[str]:
        """对消息进行打乱 + 重加密"""
        shuffled = messages[:]
        random.shuffle(shuffled)
        return [reencrypt(msg, self.rekey) for msg in shuffled]


# === Mixnet 网络执行 ===

def run_mixnet(messages: List[str], num_layers: int = 3) -> List[str]:
    """多层混洗网络"""
    for i in range(num_layers):
        mix = MixNode(i)
        messages = mix.process(messages)
    return messages


# === 主程序 ===

if __name__ == "__main__":
    NUM_USERS = 10
    NUM_MIXNODES = 3

    print(f"🔐 用户数: {NUM_USERS}, Mix Node 层数: {NUM_MIXNODES}")

    # Step 1: 用户加密上传
    user_messages = generate_user_messages(NUM_USERS)
    print("\n📥 用户原始加密消息（按顺序）:")
    for i, ct in enumerate(user_messages):
        print(f"User {i:02d}: {ct[:16]}...")

    # Step 2: Mixnet 分布式洗牌
    final_output = run_mixnet(user_messages, NUM_MIXNODES)

    print("\n🔀 Mixnet 混洗后输出（顺序已打乱，重加密）:")
    for i, ct in enumerate(final_output):
        print(f"Out {i:02d}: {ct[:16]}...")

    # Step 3: 可验证性（可选）
    # 可以加入 zk-proof 验证每轮 shuffle 的合法性（此处省略）

