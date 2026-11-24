"""Тесты рекурсии Мюллера (muller.py, упражнения №2 и №4) и машинного эпсилон (№1)."""
import sys
import unittest
from decimal import Decimal, localcontext
from fractions import Fraction

from ex1_machine_epsilon import as_float32, exponent, machine_epsilon
from muller import FAST_ROOT, N_DEFAULT, X0, X1, exact, f, sequence


class TestMachineEpsilon(unittest.TestCase):
    def test_double(self):
        eps = machine_epsilon()
        self.assertEqual(eps, sys.float_info.epsilon)
        self.assertEqual(eps, 2.0**-52)
        self.assertEqual(exponent(eps), -52)

    def test_definition(self):
        eps = machine_epsilon()
        self.assertNotEqual(1.0 + eps, 1.0)
        self.assertEqual(1.0 + eps / 2, 1.0)

    def test_single(self):
        self.assertEqual(machine_epsilon(as_float32), 2.0**-23)


class TestExactFormula(unittest.TestCase):
    def test_initial_values(self):
        self.assertEqual(exact(0), Fraction(X0))
        self.assertEqual(exact(1), Fraction(X1))

    def test_formula_satisfies_recursion(self):
        for n in range(2, 60):
            self.assertEqual(exact(n), f(exact(n - 1), exact(n - 2)), msg=n)

    def test_fraction_sequence_matches_formula(self):
        xs = sequence(Fraction(X0), Fraction(X1), N_DEFAULT)
        self.assertEqual(xs, [exact(n) for n in range(N_DEFAULT + 1)])

    def test_limit_is_five(self):
        self.assertAlmostEqual(float(exact(200)), FAST_ROOT, places=12)
        self.assertLess(exact(N_DEFAULT), FAST_ROOT)   # подходит к 5 снизу

    def test_bad_n(self):
        with self.assertRaises(ValueError):
            exact(-1)
        for bad in (1.0, "3", None, True):
            with self.assertRaises(TypeError, msg=repr(bad)):
                exact(bad)


class TestRoundingBreaksIt(unittest.TestCase):
    """Упражнения №2в и №4: с округлением последовательность уходит к 100."""

    def test_float_goes_to_100(self):
        self.assertEqual(sequence(float(X0), float(X1), N_DEFAULT)[N_DEFAULT], 100.0)

    def test_decimal_default_precision_also_fails(self):
        with localcontext() as ctx:
            ctx.prec = 28
            x30 = sequence(Decimal(X0), Decimal(X1), N_DEFAULT)[N_DEFAULT]
        self.assertAlmostEqual(float(x30), 100.0, places=5)

    def test_decimal_high_precision_works(self):
        with localcontext() as ctx:
            ctx.prec = 80
            x30 = sequence(Decimal(X0), Decimal(X1), N_DEFAULT)[N_DEFAULT]
        self.assertAlmostEqual(float(x30), float(exact(N_DEFAULT)), places=14)


class TestSequenceEdges(unittest.TestCase):
    def test_short_lengths(self):
        self.assertEqual(sequence(4, 4.25, 0), [4])
        self.assertEqual(sequence(4, 4.25, 1), [4, 4.25])

    def test_bad_n(self):
        with self.assertRaises(ValueError):
            sequence(4, 4.25, -1)
        with self.assertRaises(TypeError):
            sequence(4, 4.25, 2.0)


if __name__ == "__main__":
    unittest.main()
