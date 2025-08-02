
import math, random, time, sys

def current_date():
    return time.strftime("%m-%d-%H-%M-%S", time.localtime())

def quick_power(a, b, mod):
    s = 1
    while b:
        if b & 1:
            s = s * a % mod
        a = a * a % mod
        b >>= 1
    return s

def is_prime(p):
    test_prime = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    for test_p in test_prime:
        if p % test_p == 0 or quick_power(test_p, p - 1, p) != 1:
            return False
    return True

def load_data(filename):
    with open(filename, 'r') as f:
        n = int(f.readline())
        B = int(f.readline())
        data = [int(f.readline()) for _ in range(n)]
    return n, B, data

class LargeDomainFrequencyEstimation:
    def __init__(self, n, B, mu, util_para=1.0):
        self.n, self.B = n, B
        self.c = util_para
        self.b = int(n / math.pow(math.log(n), self.c))
        self.q = max(B, self.b) + 1
        while not is_prime(self.q):
            self.q += 1
        self.mu = mu
        self.sample_prob = mu * (self.b / n)
        self.send_fixed_messages = int(math.floor(self.sample_prob))
        self.remaining_prob = self.sample_prob - self.send_fixed_messages
        self.collision_prob = (self.q / self.b) * (self.q % self.b + self.q - self.b) / (self.q * (self.q - 1))
        self.messages = []
        self.user_time = 0.0
        self.analyzer_time = 0.0
        self.element_time = 0.0
        self.freqvec = [0.0] * (self.B + 1)
        self.realvec = [0.0] * (self.B + 1)
        self.errors = []

    def local_randomizer(self, value):
        start_time = time.time()
        u = random.randint(1, self.q - 1)
        v = random.randint(1, self.q)
        w = ((u * value + v) % self.q) % self.b
        self.messages.append((u, v, w))

        send_messages = self.send_fixed_messages
        if random.random() < self.remaining_prob:
            send_messages += 1

        for _ in range(send_messages):
            u = random.randint(1, self.q - 1)
            v = random.randint(1, self.q)
            w = random.randint(0, self.b - 1)
            self.messages.append((u, v, w))
        self.user_time += time.time() - start_time

    def analyzer(self, query_id):
        counter = sum(1 for u, v, w in self.messages if (u * query_id + v) % self.q % self.b == w)
        return (counter - self.n * self.sample_prob / self.b - self.n * self.collision_prob) / (1 - self.collision_prob)

    def analyzers_speedup(self):
        start_time = time.time()
        freq = [0.0] * (self.B + 1)
        for u, v, w in self.messages:
            invu = quick_power(u, self.q - 2, self.q)
            start_id = invu * (w - v + self.q) % self.q
            adding = invu * self.b % self.q
            id = start_id
            for _ in range(self.q // self.b + 1):
                if 1 <= id <= self.B:
                    freq[id] += 1
                id = (id + adding) % self.q
        for i in range(1, self.B + 1):
            freq[i] = (freq[i] - self.n * self.sample_prob / self.b - self.n * self.collision_prob) / (1 - self.collision_prob)
        self.freqvec = freq
        self.analyzer_time += time.time() - start_time

    def check_error(self, data):
        self.realvec = [0.0] * (self.B + 1)
        for val in data:
            self.realvec[val] += 1
        l1 = l2 = maxe = 0.0
        self.errors = []
        for i in range(1, self.B + 1):
            error = abs(self.realvec[i] - self.freqvec[i])
            l1 += error
            l2 += error ** 2
            maxe = max(maxe, error)
            self.errors.append(error)
        self.l1Error = l1
        self.l2Error = math.sqrt(l2)
        self.looError = maxe
        self.errors.sort()
        self.l99Error = self.errors[int(round(0.99 * self.B)) - 1]
        self.l95Error = self.errors[int(round(0.95 * self.B)) - 1]
        self.l90Error = self.errors[int(round(0.90 * self.B)) - 1]
        self.l50Error = self.errors[int(round(0.50 * self.B)) - 1]

    def print_info(self, epsilon, delta):
        print(f"epsilon = {epsilon}")
        print(f"delta = {delta}")
        print(f"number of participants = {self.n}")
        print(f"field size = {self.B}")
        print(f"utility parameter = {self.c}")
        print(f"modular size = {self.b}")
        print(f"big prime = {self.q}")
        print(f"mu = {self.mu}")
        print(f"collision probability = {self.collision_prob}")
        print(f"expected messages = {1 + self.sample_prob}")
        comm_cost = (self.sample_prob + 1) * (math.ceil(math.log2(self.q)) * 2 + math.ceil(math.log2(self.b))) / 8
        print(f"expected communication / user = {comm_cost:.2f} bytes")
        print(f"expected total communication = {self.n * comm_cost:.2f} bytes")
        print(f"real total communication = {len(self.messages) * (math.ceil(math.log2(self.q)) * 2 + math.ceil(math.log2(self.b))) / 8:.2f} bytes")
        print(f"L1 error = {self.l1Error}")
        print(f"L2 error = {self.l2Error}")
        print(f"Linf error = {self.looError}")
        print(f"50% error = {self.l50Error}")
        print(f"90% error = {self.l90Error}")
        print(f"95% error = {self.l95Error}")
        print(f"99% error = {self.l99Error}")
        print(f"local randomizer time cost = {self.user_time:.4f}")
        print(f"analyzer time cost = {self.analyzer_time:.4f}")
        print(f"single element query time cost = {self.element_time:.4f}")

    def set_element_query_time(self, t):
        self.element_time = t

def checker(n, para, delta, epow):
    tp = [1.0] * (n + 1)
    tp2 = [1.0] * (n + 1)
    prob = [0.0] * (n + 1)
    accprob = [0.0] * (n + 1)

    for i in range(1, n + 1):
        tp[i] = tp[i - 1] * para
        tp2[i] = tp2[i - 1] * (1 - para)

    C = 1.0
    for i in range(n + 1):
        prob[i] = C * tp2[n - i]
        C = C * (n - i) * para / (i + 1)

    accprob[n] = prob[n]
    for i in range(n - 1, -1, -1):
        accprob[i] = accprob[i + 1] + prob[i]

    pro = 0.0
    for x2 in range(n + 1):
        x1 = math.ceil(epow * x2 - 1)
        x1 = max(x1, 0)
        if x1 >= n: break
        pro += prob[x2] * accprob[x1]
    return pro <= delta

def search_mu(n, epsilon, delta):
    epow = math.exp(epsilon)
    le, ri = 0.0, 1000.0 / n
    while le + 0.1 / n < ri:
        mi = (le + ri) / 2
        if checker(n, mi, delta, epow):
            ri = mi
        else:
            le = mi
    return ri * n

if __name__ == "__main__":
    assert len(sys.argv) == 6
    epsilon = float(sys.argv[1])
    n = int(sys.argv[2])
    B = int(sys.argv[3])
    c = float(sys.argv[4])
    delta = 1.0 / n / n
    filename = sys.argv[5]
    fullfile = f"{filename},n={n},B={B}.txt"
    n, B, data = load_data(fullfile)
    mu = search_mu(n, epsilon, delta)
    ldfe = LargeDomainFrequencyEstimation(n, B, mu, c)
    for d in data:
        ldfe.local_randomizer(d)
    ldfe.analyzers_speedup()
    ldfe.check_error(data)
    start = time.time()
    for qid in range(1, 101):
        ldfe.analyzer(qid)
    end = time.time()
    ldfe.set_element_query_time((end - start) / 100.0)
    result_name = f"fe,{filename},C={c},{current_date()}.out"
    sys.stdout = open(result_name, "w")
    ldfe.print_info(epsilon, delta)
