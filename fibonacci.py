def _fibonacci_helper(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    memo[n] = _fibonacci_helper(n-1, memo) + _fibonacci_helper(n-2, memo)
    return memo[n]

def fibonacci_sequence(n):
    """Generates a list of the first n Fibonacci numbers.
    Usage: fibonacci_sequence(10) -> [0,1,1,2,3,5,8,13,21,34]"""
    return [_fibonacci_helper(i) for i in range(n)]

def fibonacci_get_nth(n):
    """Returns the nth Fibonacci number (0-indexed).
    Usage: fibonacci_get_nth(10) -> 55"""
    return _fibonacci_helper(n)

def fibonacci_sum(n):
    """Returns the sum of the first n Fibonacci numbers.
    Usage: fibonacci_sum(10) -> 88"""
    return sum(fibonacci_sequence(n))

def fibonacci_add(i, j):
    """Adds two Fibonacci numbers by their indices and returns the sum.
    Usage: fibonacci_add(5, 7) -> 5 + 13 = 18"""
    return _fibonacci_helper(i) + _fibonacci_helper(j)

def fibonacci_add_same(n):
    """Adds the nth Fibonacci number to itself (doubles it).
    Usage: fibonacci_add_same(6) -> 8 + 8 = 16"""
    return 2 * _fibonacci_helper(n)