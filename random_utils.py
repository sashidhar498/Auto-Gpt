import random

def _get_generator(seed=None):
    """Return a random.Random instance, optionally seeded."""
    if seed is not None:
        return random.Random(seed)
    return random

def generate_random_integer(low, high, seed=None):
    """Return random integer between low and high inclusive."""
    return _get_generator(seed).randint(low, high)

def generate_random_float(low, high, seed=None):
    """Return random float between low and high."""
    return _get_generator(seed).uniform(low, high)

def random_choice(sequence, seed=None):
    """Pick random element from sequence."""
    return _get_generator(seed).choice(sequence)

def generate_random_list(size, low, high, seed=None):
    """Return list of random integers."""
    return [_get_generator(seed).randint(low, high) for _ in range(size)]

def generate_random_number(low, high, is_float=False, seed=None):
    """Return int or float random number."""
    if is_float:
        return generate_random_float(low, high, seed)
    return generate_random_integer(low, high, seed)