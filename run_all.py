"""Запустить всё одной командой: тесты, четыре упражнения, калькулятор и быстрые замеры.

    python run_all.py

Графики ипотеки сохраняются в папку plots/ рядом с этим файлом.
Код возврата 0 — всё прошло, 1 — что-то упало (видно по заголовку шага).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STEPS = [
    ("Тесты (unittest)", ["-m", "unittest"]),
    ("№1. Машинное эпсилон", ["ex1_machine_epsilon.py"]),
    ("№2. Мюллер во float", ["ex2_muller_float.py"]),
    ("№3. Ипотека", ["ex3_mortgage.py", "--no-show", "--no-table", "--out-dir", "plots"]),
    ("№4. Мюллер в Decimal и Fraction", ["ex4_muller_exact.py"]),
    ("Калькулятор: 0.1 + 0.2", ["calc.py", "0.1 + 0.2"]),
    ("Калькулятор: (1/3 + 1/6) * 2^-1", ["calc.py", "(1/3 + 1/6) * 2^-1"]),
    ("Замеры (быстрый вариант)", ["bench.py", "--quick"]),
]


def main() -> int:
    failed = []
    for title, args in STEPS:
        print(f"\n{'=' * 60}\n{title}\n{'=' * 60}", flush=True)
        result = subprocess.run([sys.executable, *args], cwd=ROOT)
        if result.returncode != 0:
            failed.append(title)
    print(f"\n{'=' * 60}")
    if failed:
        print("УПАЛО:", ", ".join(failed))
        return 1
    print(f"Все {len(STEPS)} шагов прошли успешно.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
