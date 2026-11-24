"""Упражнение №1. Вычислите машинное эпсилон.

Машинное эпсилон — наименьшее eps > 0, для которого 1.0 + eps != 1.0.
Ищем его, деля кандидата пополам, пока прибавка к единице ещё заметна.

Инвариант цикла: 1.0 + eps != 1.0 (eps всё ещё «виден» на фоне единицы).
Цикл останавливается, когда eps / 2 уже не виден, значит eps — минимальная
видимая степень двойки.
"""
import struct
import sys
from typing import Callable

ONE = 1.0


def as_float64(x: float) -> float:
    """float в Python уже binary64 — округлять дополнительно не нужно."""
    return x


def as_float32(x: float) -> float:
    """Округлить число до одинарной точности (binary32)."""
    return struct.unpack("f", struct.pack("f", x))[0]


def machine_epsilon(round_to: Callable[[float], float] = as_float64) -> float:
    """Машинное эпсилон для формата, в который округляет функция round_to.

    Число шагов цикла равно длине мантиссы (52 для binary64, 23 для binary32),
    то есть O(p), где p — число бит мантиссы.
    """
    eps = ONE
    while round_to(ONE + round_to(eps / 2)) != ONE:
        eps /= 2
    return eps


def exponent(x: float) -> int:
    """Показатель степени двойки: для 2**-52 вернёт -52."""
    return int(x.hex().split("p")[1])


def main() -> None:
    eps64 = machine_epsilon(as_float64)
    eps32 = machine_epsilon(as_float32)

    print("Двойная точность (float в Python):")
    print(f"  вычислено:          {eps64!r}  (= 2**{exponent(eps64)})")
    print(f"  sys.float_info:     {sys.float_info.epsilon!r}")
    print(f"  совпадает:          {eps64 == sys.float_info.epsilon}")
    print(f"  1.0 + eps     == 1.0 -> {ONE + eps64 == ONE}")
    print(f"  1.0 + eps / 2 == 1.0 -> {ONE + eps64 / 2 == ONE}")
    print()
    print("Одинарная точность (binary32):")
    print(f"  вычислено:          {eps32!r}  (= 2**{exponent(eps32)})")


if __name__ == "__main__":
    main()
