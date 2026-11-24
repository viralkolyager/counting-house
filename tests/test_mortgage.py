"""Тесты ипотеки (ex3_mortgage.py)."""
import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal, getcontext
from pathlib import Path
from unittest import mock

from ex3_mortgage import KOP, annuity_payment, main, plot, schedule

D = Decimal
HAS_MATPLOTLIB = importlib.util.find_spec("matplotlib") is not None


class TestKnownValues(unittest.TestCase):
    """Пример из README: 3 000 000 ₽ под 12% на 15 лет."""

    def setUp(self):
        self.rows = schedule(D("3000000"), D("12"), 15)

    def test_payment(self):
        self.assertEqual(annuity_payment(D("3000000"), D("12"), 15), D("36005.05"))

    def test_overpayment(self):
        total = sum(r.payment for r in self.rows)
        self.assertEqual(total - D("3000000"), D("3480904.84"))

    def test_length_and_last_payment(self):
        self.assertEqual(len(self.rows), 180)
        self.assertEqual(self.rows[-1].payment, D("36000.89"))

    def test_first_month_interest(self):
        # 3 000 000 * 1% = 30 000 ₽ процентов в первый месяц
        self.assertEqual(self.rows[0].interest, D("30000.00"))


class TestInvariants(unittest.TestCase):
    """Свойства, которые должны выполняться для любого кредита."""

    CASES = [
        (D("3000000"), D("12"), 15),
        (D("100000"), D("7.5"), 1),
        (D("999999.99"), D("0.01"), 30),
        (D("50000"), D("99"), 2),
        (D("0.01"), D("12"), 1),
    ]

    def test_all_invariants(self):
        for s, x, y in self.CASES:
            with self.subTest(s=s, x=x, y=y):
                rows = schedule(s, x, y)
                p = annuity_payment(s, x, y)
                # весь основной долг выплачен до копейки
                self.assertEqual(sum(r.principal for r in rows), s)
                self.assertEqual(rows[-1].balance_after, 0)
                # не дольше срока
                self.assertLessEqual(len(rows), y * 12)
                for r in rows:
                    self.assertGreater(r.payment, 0)
                    self.assertEqual(r.interest + r.principal, r.payment)
                    self.assertGreaterEqual(r.balance_after, 0)
                    self.assertEqual(r.payment, r.payment.quantize(KOP))
                # все платежи одинаковые, последний — не больше
                for r in rows[:-1]:
                    self.assertEqual(r.payment, p)
                self.assertLessEqual(rows[-1].payment, p)

    def test_balance_is_chained(self):
        rows = schedule(D("100000"), D("10"), 2)
        for prev, cur in zip(rows, rows[1:]):
            self.assertEqual(prev.balance_after, cur.balance_before)


class TestEdgeCases(unittest.TestCase):
    def test_zero_rate(self):
        rows = schedule(D("1200"), D("0"), 1)
        self.assertEqual(len(rows), 12)
        self.assertTrue(all(r.payment == D("100.00") and r.interest == 0 for r in rows))

    def test_zero_rate_not_divisible(self):
        # 1000 / 12 = 83.33(3) -> платёж 83.34, последний меньше
        rows = schedule(D("1000"), D("0"), 1)
        self.assertEqual(rows[0].payment, D("83.34"))
        self.assertEqual(sum(r.payment for r in rows), D("1000"))

    def test_one_kopeck_loan(self):
        rows = schedule(D("0.01"), D("12"), 1)
        self.assertEqual(len(rows), 1)          # гасится первым же платежом
        self.assertEqual(rows[-1].balance_after, 0)
        self.assertEqual(sum(r.principal for r in rows), D("0.01"))

    def test_very_long_loan(self):
        # 1000 лет: (1 + r)^-12000 ~ 1e-52 — при фиксированных 50 знаках он терялся,
        # платёж выходил равным процентам и долг не уменьшался
        s, x, y = D("3000000"), D("12"), 1000
        p = annuity_payment(s, x, y)
        self.assertGreater(p, s * D("0.01"))
        rows = schedule(s, x, y)
        self.assertLessEqual(rows[-1].payment, p)
        self.assertEqual(rows[-1].balance_after, 0)

    def test_global_decimal_context_untouched(self):
        before = getcontext().prec
        schedule(D("3000000"), D("12"), 15)
        self.assertEqual(getcontext().prec, before)


class TestBadInput(unittest.TestCase):
    def test_float_money_rejected(self):
        with self.assertRaises(TypeError):
            annuity_payment(3000000.0, D("12"), 15)
        with self.assertRaises(TypeError):
            annuity_payment(D("3000000"), 12.0, 15)

    def test_int_money_rejected(self):
        with self.assertRaises(TypeError):
            annuity_payment(3000000, D("12"), 15)

    def test_bad_years_type(self):
        for years in (1.5, "15", True, None):
            with self.assertRaises(TypeError, msg=repr(years)):
                annuity_payment(D("1000"), D("12"), years)

    def test_boundary_values(self):
        for s, x, y in [
            (D("0"), D("12"), 15),        # нулевой кредит
            (D("-1000"), D("12"), 15),    # отрицательный
            (D("1000"), D("-1"), 15),     # отрицательная ставка
            (D("1000"), D("12"), 0),      # нулевой срок
            (D("NaN"), D("12"), 15),
            (D("Infinity"), D("12"), 15),
        ]:
            with self.assertRaises(ValueError, msg=(s, x, y)):
                schedule(s, x, y)


class TestCli(unittest.TestCase):
    def test_main_prints_summary(self):
        out = io.StringIO()
        with redirect_stdout(out):
            main(["3000000", "12", "15", "--no-plot", "--no-table"])
        self.assertIn("36 005.05", out.getvalue())
        self.assertIn("3 480 904.84", out.getvalue())

    def test_main_rejects_garbage(self):
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()), \
                mock.patch("sys.stderr", io.StringIO()):
            main(["abc", "--no-plot"])

    @unittest.skipUnless(HAS_MATPLOTLIB, "нужен matplotlib")
    def test_plot_files_created(self):
        rows = schedule(D("100000"), D("10"), 1)
        with tempfile.TemporaryDirectory() as tmp:
            paths = plot(rows, Path(tmp), show=False)
            self.assertTrue(all(p.exists() and p.stat().st_size > 0 for p in paths))


if __name__ == "__main__":
    unittest.main()
