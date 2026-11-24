"""Замеры времени и числа операций на больших данных (10^3 … 10^6).

1. Калькулятор: выражение из N слагаемых-дробей. Ожидаем O(N):
   отношение «операций на слагаемое» должно оставаться постоянным.
   Baseline — тот же алгоритм во float (быстро, но с ошибкой).
2. Мюллер, точное x_n: прямая рекурсия во Fraction (baseline) против
   замкнутой формулы exact(n) (optimized).
3. Ипотека: график платежей на n месяцев, O(n) — меряем время на строку.
   При 0% годовых график ровно 12·y строк, поэтому им удобно получить 10^5.

Запуск:  python bench.py           (все размеры, ~1 минута)
         python bench.py --quick   (только маленькие размеры)
"""
import argparse
import math
import time
from decimal import Decimal
from fractions import Fraction
from typing import Callable

from calc import OpCounter, calculate
from ex3_mortgage import MONTHS_PER_YEAR, schedule
from muller import X0, X1, exact, sequence

# Блок дробей с нулевой суммой: знаменатели не растут, и мы меряем сам
# алгоритм разбора, а не длинную арифметику.
ZERO_BLOCK = ["1/2", "1/3", "-5/6"]


def digit_count(k: int) -> int:
    """Примерное число десятичных цифр (str() огромных чисел в Python ограничен)."""
    return math.floor(k.bit_length() * math.log10(2)) + 1


def timed(fn: Callable[[], object]) -> tuple[float, object]:
    start = time.perf_counter()
    result = fn()
    return time.perf_counter() - start, result


def bench_calc(sizes: list[int]) -> None:
    print("1. Калькулятор: N слагаемых (сумма = 0)")
    print(f"{'N':>9} {'Fraction, с':>12} {'float, с':>10} {'операций':>11} {'опер./N':>8} {'float = 0?':>11}")
    for n in sizes:
        expr = "+".join(ZERO_BLOCK[i % len(ZERO_BLOCK)] for i in range(n - n % len(ZERO_BLOCK)))
        counter = OpCounter()
        t_exact, exact_value = timed(lambda: calculate(expr, counter=counter))
        t_float, float_value = timed(lambda: calculate(expr, number=float))
        assert exact_value == 0
        print(f"{n:>9} {t_exact:>12.3f} {t_float:>10.3f} {counter.total:>11} "
              f"{counter.total / n:>8.2f} {str(float_value == 0):>11}")
    print()


def bench_muller(sizes: list[int]) -> None:
    print("2. Мюллер, точное x_n")
    print(f"{'n':>9} {'рекурсия Fraction, с':>21} {'формула exact(n), с':>20} {'цифр в знаменателе':>19}")
    for n in sizes:
        t_rec, xs = timed(lambda: sequence(Fraction(X0), Fraction(X1), n))
        t_formula, value = timed(lambda: exact(n))
        assert xs[n] == value
        print(f"{n:>9} {t_rec:>21.3f} {t_formula:>20.4f} {digit_count(value.denominator):>19}")
    print()


def bench_mortgage(loans: list[tuple[str, str, int]]) -> None:
    print("3. Ипотека: график платежей")
    print(f"{'S':>12} {'x, %':>5} {'лет':>6} {'строк':>8} {'время, с':>9} {'мкс/строку':>11}")
    for s, x, years in loans:
        t, rows = timed(lambda: schedule(Decimal(s), Decimal(x), years))
        assert len(rows) <= years * MONTHS_PER_YEAR and rows[-1].balance_after == 0
        print(f"{s:>12} {x:>5} {years:>6} {len(rows):>8} {t:>9.3f} {t / len(rows) * 1e6:>11.2f}")
    print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--quick", action="store_true", help="только маленькие размеры")
    args = ap.parse_args()
    if args.quick:
        bench_calc([1_000, 10_000])
        bench_muller([100, 1_000])
        bench_mortgage([("3000000", "12", 15), ("1200000", "0", 100)])
    else:
        bench_calc([1_000, 10_000, 100_000, 1_000_000])
        bench_muller([1_000, 3_000, 10_000, 30_000])
        bench_mortgage([("3000000", "12", 15), ("3000000", "12", 100),
                        ("12000000", "0", 1_000), ("12000000", "0", 10_000)])


if __name__ == "__main__":
    main()
