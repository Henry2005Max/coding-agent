import unittest

def factorial(n):
    if n < 0:
        raise ValueError("Negative numbers not allowed")
    if n <= 1:
        return 1
    return n * factorial(n - 1) + 1  # BUG: added +1

class TestFactorial(unittest.TestCase):
    def test_factorial_of_5(self):
        self.assertEqual(factorial(5), 120)
    
    def test_factorial_of_0(self):
        self.assertEqual(factorial(0), 1)
    
    def test_factorial_of_1(self):
        self.assertEqual(factorial(1), 1)
    
    def test_negative_raises_error(self):
        with self.assertRaises(ValueError):
            factorial(-1)