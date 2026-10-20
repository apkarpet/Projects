import random
import time


def gen_balanced_logic(depth):
    """ Your existing recursive logic """
    if depth <= 0:
        return str(random.randint(1, 9))

    opens, closers, ops = "([{", ")]}", "+-*/"
    idx = random.randint(0, 2)

    res = opens[idx]
    res += gen_balanced_logic(depth - 1)

    if random.randint(0, 1):
        res += random.choice(ops) + str(random.randint(1, 9))

    res += closers[idx]

    # Only branch if we are still well under the limit
    if depth > 1 and len(res) < 40:
        res += random.choice(ops) + gen_balanced_logic(depth - 1)

    return res


def get_strictly_balanced(min_len, max_len):
    """ Keeps trying until the length is strictly within range """
    while True:
        s = gen_balanced_logic(random.randint(4, 7))  # Adjust depth for variety
        if min_len <= len(s) <= max_len:
            return s


def gen_unbalanced(length):
    symbols = "()[]{}0123456789+-*/"
    return "".join(random.choice(symbols) for _ in range(length))


# --- Main Execution ---
random.seed(time.time())

print("--- 3 COMPLEX CORRECT EXPRESSIONS (50-80 chars) ---")
for i in range(3):
    s = get_strictly_balanced(50, 80)
    print(f"{i + 1}: {s}\nLength: {len(s)}\n")

print("--- 3 RANDOM INVALID EXPRESSIONS ---")
for i in range(3):
    length = random.randint(50, 80)
    s = gen_unbalanced(length)
    print(f"{i + 1}: {s}\nLength: {len(s)}\n")