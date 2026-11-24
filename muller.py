"""Рекуррентное соотношение Мюллера — общий код для упражнений №2 и №4.

    f(y, z) = 108 - (815 - 1500 / z) / y
    x0 = 4, x1 = 4.25, x_i = f(x_{i-1}, x_{i-2})

Функции написаны «утиным» стилем: работают с float, Decimal и Fraction —
тип результата определяется типом начальных значений.
"""
from fractions import Fraction

# Коэффициенты рекурсии из условия задачи:
# x^3 - A x^2 + B x - C = (x - 3)(x - 5)(x - 100)
A, B, C = 108, 815, 1500
X0, X1 = "4", "4.25"   # начальные значения строками — чтобы Decimal/Fraction были точными
N_DEFAULT = 30         # номер члена, который просят вывести в упражнении №2
SLOW_ROOT, FAST_ROOT = 3, 5   # корни, дающие правильное решение (c = 0)


def f(y, z):
    return A - (B - C / z) / y


def sequence(x0, x1, n: int) -> list:
    """Вернуть список [x0, x1, ..., xn].

    Сложность: n - 1 вызовов f, то есть O(n) арифметических операций.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError(f"n должно быть int, а не {type(n).__name__}")
    if n < 0:
        raise ValueError("n должно быть >= 0")
    xs = [x0, x1]
    for _ in range(2, n + 1):
        xs.append(f(xs[-1], xs[-2]))
    return xs[: n + 1]


def exact(n: int) -> Fraction:
    """Аналитическое значение x_n = (3^(n+1) + 5^(n+1)) / (3^n + 5^n).

    Возвращается как Fraction — без какой-либо погрешности.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError(f"n должно быть int, а не {type(n).__name__}")
    if n < 0:
        raise ValueError("n должно быть >= 0")
    return Fraction(SLOW_ROOT ** (n + 1) + FAST_ROOT ** (n + 1), SLOW_ROOT**n + FAST_ROOT**n)
