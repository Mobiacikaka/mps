from Crypto.Util import number
import random

# === ElGamal 参数生成 ===
def generate_elgamal_keys(bits=256):
    p = number.getPrime(bits)
    g = random.randint(2, p - 2)
    x = random.randint(1, p - 2)          # private key
    h = pow(g, x, p)                      # public key: h = g^x mod p
    return (p, g, h), x                   # public key, private key

# === ElGamal 加密 ===
def elgamal_encrypt(m, pub_key):
    p, g, h = pub_key
    r = random.randint(1, p - 2)
    c1 = pow(g, r, p)
    s = pow(h, r, p)
    c2 = (m * s) % p
    return (c1, c2)

# === ElGamal 重加密（Re-encryption） ===
def elgamal_reencrypt(ciphertext, pub_key):
    p, g, h = pub_key
    c1, c2 = ciphertext
    r_prime = random.randint(1, p - 2)
    c1_new = (c1 * pow(g, r_prime, p)) % p
    s_prime = pow(h, r_prime, p)
    c2_new = (c2 * s_prime) % p
    return (c1_new, c2_new)

# === ElGamal 解密 ===
def elgamal_decrypt(ciphertext, priv_key, pub_key):
    p, g, h = pub_key
    c1, c2 = ciphertext
    s = pow(c1, priv_key, p)
    s_inv = number.inverse(s, p)
    m = (c2 * s_inv) % p
    return m

# === 模拟流程 ===
# 1. 生成密钥
pub_key, priv_key = generate_elgamal_keys()

# 2. 用户加密消息
original_message = 123456789
cipher = elgamal_encrypt(original_message, pub_key)

# 3. 多轮重加密（模拟 Mixnet）
cipher_re = cipher
for _ in range(3):  # 3轮 Mix node 重加密
    cipher_re = elgamal_reencrypt(cipher_re, pub_key)

# 4. Server 解密最终密文
decrypted_message = elgamal_decrypt(cipher_re, priv_key, pub_key)

print(decrypted_message, original_message, decrypted_message == original_message)
