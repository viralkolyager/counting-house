"""Упражнение №4. Решите упражнение №2, используя Decimal и Fraction.

1. Decimal — это всё ещё арифметика с округлением, только десятичная и
   с настраиваемой точностью. При стандартных 28 знаках последовательность
   тоже убегает к 100, просто позже. Чтобы x30 был верным, нужна точность,
   покрывающая рост ошибки 20^30 ≈ 1e39, т.е. заметно больше 40 знаков.
2. Fraction — точная рациональная арифметика: паразитной составляющей
   100^n не возникает вовсе, и x30 совпадает с аналитическим значением.
"""
from decimal import Decimal, localcontext
from fractions import Fraction

from muller import N_DEFAULT as N
from muller import X0, X1, exact, sequence

PRECISIONS = (28, 40, 50, 60, 80)  # 28 — точность Decimal по умолчанию


def with_decimal(prec: int) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = prec
        return sequence(Decimal(X0), Decimal(X1), N)[N]


def with_fraction() -> Fraction:
    return sequence(Fraction(X0), Fraction(X1), N)[N]


def main() -> None:
    print("1. Decimal")
    for prec in PRECISIONS:
        print(f"   prec={prec:>2}: x{N} = {with_decimal(prec):.20g}")

    print()
    print("2. Fraction")
    x = with_fraction()
    print(f"   x{N} = {x}")
    print(f"      ≈ {float(x)!r}")
    print(f"   совпадает с (3^31 + 5^31) / (3^30 + 5^30): {x == exact(N)}")


if __name__ == "__main__":
    main()
