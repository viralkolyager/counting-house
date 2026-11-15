"""Упражнение №1. Вычислите машинное эпсилон.

Машинное эпсилон — наименьшее eps > 0, для которого 1.0 + eps != 1.0.
Ищем его, деля кандидата пополам, пока прибавка к единице ещё заметна.
"""
import struct
import sys


def machine_epsilon() -> float:
    """Машинное эпсилон для float (IEEE754 binary64, двойная точность)."""
    eps = 1.0
    while 1.0 + eps / 2 != 1.0:
        eps /= 2
    return eps


def to_float32(x: float) -> float:
    """Округлить число до одинарной точности (binary32)."""
    return struct.unpack("f", struct.pack("f", x))[0]


def machine_epsilon_float32() -> float:
    """Машинное эпсилон для одинарной точности (binary32)."""
    eps = 1.0
    while to_float32(1.0 + to_float32(eps / 2)) != 1.0:
        eps /= 2
    return eps


def main() -> None:
    eps64 = machine_epsilon()
    eps32 = machine_epsilon_float32()

    print("Двойная точность (float в Python):")
    print(f"  вычислено:          {eps64!r}  (= 2**{eps64.hex().split('p')[1]})")
    print(f"  sys.float_info:     {sys.float_info.epsilon!r}")
    print(f"  совпадает:          {eps64 == sys.float_info.epsilon}")
    print(f"  1.0 + eps     == 1.0 -> {1.0 + eps64 == 1.0}")
    print(f"  1.0 + eps / 2 == 1.0 -> {1.0 + eps64 / 2 == 1.0}")
    print()
    print("Одинарная точность (binary32):")
    print(f"  вычислено:          {eps32!r}  (= 2**{eps32.hex().split('p')[1]})")


if __name__ == "__main__":
    main()
