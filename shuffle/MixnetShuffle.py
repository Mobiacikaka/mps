#!/bin/python3

# Simulate a simplified ElGamal-based Mixnet with decentralized (threshold) decryption
# Note: This is a simplified educational simulation, not cryptographically secure

import random
from sympy import nextprime, mod_inverse
from hashlib import sha256
from Crypto.Util import number

# 1. Setup ElGamal Parameters
def setup_group(bits=256):
	q = number.getPrime(bits)
	p = 
	g = 0  # Generator
	while True:
		g = random.randint(2, p-2)
		if pow(g, 2, p) != 1 and pow(g, q, p)
	return p, g

# 2. Generate threshold keys
def keygen(p, g, n, t):
	# Random private key shares x_i for each participant
	private_shares = [random.randint(2, p-2) for _ in range(n)]
	x = sum(private_shares) % (p - 1)
	y = pow(g, x, p)
	return x, y, private_shares

# 3. Encrypt message with public key
def encrypt(m, y, g, p):
	r = random.randint(2, p - 2)
	c1 = pow(g, r, p)
	c2 = (m * pow(y, r, p)) % p
	return (c1, c2)

# 4. Re-encryption (by a mix node)
def reencrypt(cipher, y, g, p):
	c1, c2 = cipher
	r_prime = random.randint(2, p - 2)
	c1_prime = (c1 * pow(g, r_prime, p)) % p
	c2_prime = (c2 * pow(y, r_prime, p)) % p
	return (c1_prime, c2_prime)

# 5. Mix (shuffle + reencrypt)
def mix(ciphers, y, g, p):
	reenc = [reencrypt(c, y, g, p) for c in ciphers]
	random.shuffle(reenc)
	return reenc

# 6. Threshold decryption
def threshold_decrypt(cipher, private_shares, g, p):
	c1, c2 = cipher
	s = 1
	for x_i in private_shares:
		s = (s * pow(c1, x_i, p)) % p
	s_inv = mod_inverse(s, p)
	m = (c2 * s_inv) % p
	return m

# Simulate the full process
def Simulation():
	p, g = setup_group()
	# n, t = 3, 3  # 3 participants, threshold 3-of-3
	n = int(input('n: '))
	k = int(input('k: '))
	# threshold n-of-n
	t = n

	x, y, private_shares = keygen(p, g, n, t)

	# Original messages
	# messages = [12345, 67890, 42424]
	messages = [random.randint(1, 100000) for _ in range(n)]

	# Encrypt
	ciphertexts = [encrypt(m, y, g, p) for m in messages]

	# Mixnet with 2 mix nodes
	for _ in range(k):
		ciphertexts = mix(ciphers=ciphertexts, y=y, g=g, p=p)

	# Decrypt
	decrypted = [threshold_decrypt(c, private_shares, g, p) for c in ciphertexts]

	print(messages, sorted(messages), sep='\n')
	print(decrypted, sorted(decrypted), sep='\n')

if __name__ == '__main__':
	Simulation()
