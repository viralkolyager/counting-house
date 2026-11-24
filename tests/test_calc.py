"""Тесты точного калькулятора (calc.py)."""
import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction

from calc import CalcError, OpCounter, calculate, describe, main, to_decimal_str, to_rpn, tokenize


class TestBasic(unittest.TestCase):
    """«Счастливый путь»: обычные выражения."""

    def test_integer_arithmetic(self):
        self.assertEqual(calculate("1 + 2 * 3"), 7)
        self.assertEqual(calculate("(1 + 2) * 3"), 9)

    def test_fractions_are_exact(self):
        self.assertEqual(calculate("1/3 + 1/6"), Fraction(1, 2))
        self.assertEqual(calculate("1/3 * 3"), 1)

    def test_decimal_literals_are_exact(self):
        # главный смысл «бухгалтерии»: 0.1 + 0.2 ровно 0.3
        self.assertEqual(calculate("0.1 + 0.2"), Fraction(3, 10))
        self.assertEqual(calculate("1.10 + 4.31"), Fraction("5.41"))

    def test_float_mode_shows_rounding_error(self):
        self.assertNotEqual(calculate("0.1 + 0.2", number=float), 0.3)

    def test_comma_as_decimal_separator(self):
        self.assertEqual(calculate("1,5 * 2"), 3)

    def test_leading_dot(self):
        self.assertEqual(calculate(".5 + .5"), 1)


class TestPrecedence(unittest.TestCase):
    """Приоритеты и ассоциативность — то, что чаще всего ломается."""

    def test_left_associative_minus_and_divide(self):
        self.assertEqual(calculate("10 - 4 - 3"), 3)       # не 10 - (4 - 3) = 9
        self.assertEqual(calculate("8 / 4 / 2"), 1)        # не 8 / (4 / 2) = 4

    def test_power_is_right_associative(self):
        self.assertEqual(calculate("2 ^ 3 ^ 2"), 512)      # 2^(3^2), а не (2^3)^2 = 64

    def test_unary_minus_weaker_than_power(self):
        self.assertEqual(calculate("-2 ^ 2"), -4)
        self.assertEqual(calculate("(-2) ^ 2"), 4)

    def test_unary_minus_in_exponent_and_after_operator(self):
        self.assertEqual(calculate("2 ^ -3"), Fraction(1, 8))
        self.assertEqual(calculate("2 * -3"), -6)
        self.assertEqual(calculate("--3"), 3)
        self.assertEqual(calculate("+3"), 3)

    def test_rpn_order(self):
        rpn = [t.text for t in to_rpn(tokenize("1 + 2 * 3"))]
        self.assertEqual(rpn, ["1", "2", "3", "*", "+"])


class TestErrors(unittest.TestCase):
    """Краевые случаи и некорректный ввод."""

    def assertCalcError(self, expr):
        with self.assertRaises(CalcError, msg=expr):
            calculate(expr)

    def test_empty_input(self):
        self.assertCalcError("")
        self.assertCalcError("   ")

    def test_division_by_zero(self):
        self.assertCalcError("1 / 0")
        self.assertCalcError("1 / (1 - 1)")
        self.assertCalcError("0 ^ -1")

    def test_bad_brackets(self):
        for expr in ("(", ")", "()", "(1 + 2", "1 + 2)", "(1))(", "1) + (2"):
            self.assertCalcError(expr)

    def test_extra_closing_bracket_message(self):
        with self.assertRaises(CalcError) as ctx:
            calculate("1) + (2")
        self.assertIn("лишняя закрывающая скобка", str(ctx.exception))

    def test_bad_operator_order(self):
        for expr in ("2 3", "1 +", "* 1", "1 * / 2", "(1)(2)", "2(3)"):
            self.assertCalcError(expr)

    def test_bad_numbers_and_symbols(self):
        for expr in ("1.2.3", ".", "x + 1", "2 ** 3", "1e5"):
            self.assertCalcError(expr)

    def test_fractional_power_rejected(self):
        self.assertCalcError("(-8) ^ (1/3)")

    def test_huge_power_rejected(self):
        self.assertCalcError("10 ^ 1000000")

    def test_wrong_types(self):
        for value in (None, 5, 0.1, b"1+1", ["1"]):
            with self.assertRaises(TypeError):
                calculate(value)

    def test_error_message_has_position(self):
        with self.assertRaises(CalcError) as ctx:
            calculate("1 + x")
        self.assertIn("позиция 5", str(ctx.exception))


class TestLargeInput(unittest.TestCase):
    """Большие входы: нет рекурсии и линейное число операций."""

    def test_deep_nesting_without_recursion(self):
        depth = 100_000
        self.assertEqual(calculate("(" * depth + "1" + ")" * depth), 1)

    def test_long_sum(self):
        n = 100_000
        self.assertEqual(calculate("+".join(["1/3"] * n)), Fraction(n, 3))

    def test_operation_count_is_linear(self):
        totals = []
        for n in (1_000, 10_000):
            c = OpCounter()
            calculate("+".join(["1"] * n), counter=c)
            totals.append(c.total)
        # в 10 раз больше вход — примерно в 10 раз больше операций (не в 100)
        self.assertLess(totals[1], 11 * totals[0])
        self.assertGreater(totals[1], 9 * totals[0])


class TestDecimalString(unittest.TestCase):
    def test_finite(self):
        self.assertEqual(to_decimal_str(Fraction(1, 8)), "0.125")
        self.assertEqual(to_decimal_str(Fraction(5)), "5")
        self.assertEqual(to_decimal_str(Fraction(0)), "0")

    def test_periodic(self):
        self.assertEqual(to_decimal_str(Fraction(1, 3)), "0.(3)")
        self.assertEqual(to_decimal_str(Fraction(1, 6)), "0.1(6)")
        self.assertEqual(to_decimal_str(Fraction(1, 7)), "0.(142857)")

    def test_negative(self):
        self.assertEqual(to_decimal_str(Fraction(-1, 2)), "-0.5")
        self.assertEqual(to_decimal_str(Fraction(-7, 6)), "-1.1(6)")

    def test_truncated(self):
        self.assertEqual(to_decimal_str(Fraction(1, 7), max_digits=3), "0.142…")
        self.assertEqual(to_decimal_str(Fraction(1, 3), max_digits=0), "0…")

    def test_bad_args(self):
        with self.assertRaises(TypeError):
            to_decimal_str(0.5)
        with self.assertRaises(ValueError):
            to_decimal_str(Fraction(1, 3), max_digits=-1)


class TestCli(unittest.TestCase):
    def run_main(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_ok(self):
        code, out, _ = self.run_main("0.1", "+", "0.2")
        self.assertEqual(code, 0)
        self.assertIn("= 3/10", out)
        self.assertIn("НЕ совпадает", out)

    def test_error_exit_code(self):
        code, _, err = self.run_main("1/0")
        self.assertEqual(code, 1)
        self.assertIn("деление на ноль", err)

    def test_describe_matching_float(self):
        self.assertIn("(совпадает)", describe("1/2 + 1/4"))


if __name__ == "__main__":
    unittest.main()
