"""Точный калькулятор дробей («булгахтерия»).

Считает арифметические выражения без единой ошибки округления: все числа
превращаются в fractions.Fraction прямо из текста (минуя float).
Для сравнения то же выражение считается во float — видно, где он врёт.

Поддерживается:  + - * /  ^ (целая степень)  скобки  унарный минус
                 числа вида 7, 1.10, 1,10, .5

Алгоритм — «сортировочная станция» Дейкстры (shunting-yard):
1. tokenize    — один проход по строке, O(n);
2. to_rpn      — перевод в обратную польскую запись со стеком операторов, O(n):
                 каждый токен кладётся в стек и снимается с него не более одного раза;
3. evaluate    — вычисление ОПЗ со стеком чисел, O(n) операций над дробями.
Рекурсии нет, поэтому даже 10^5 вложенных скобок не ломают программу.

Запуск:  python calc.py "1/3 + 1/6"
         python calc.py            (интерактивный режим)
"""
import argparse
import math
import sys
from dataclasses import dataclass
from fractions import Fraction
from typing import Callable, Union

Number = Union[Fraction, float]

# Операторы: приоритет и правоассоциативность.
# NEG — унарный минус; он слабее степени (-2^2 = -4), но сильнее * и /.
NEG = "neg"
PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, NEG: 3, "^": 4}
RIGHT_ASSOC = {NEG, "^"}
BINARY_OPS = {"+", "-", "*", "/", "^"}
UNARY_SIGNS = {"-": NEG, "+": None}   # унарный плюс просто пропускаем
DECIMAL_SEPARATORS = ".,"

MAX_POWER_BITS = 1_000_000  # защита от 2^999999999: результат больше ~300 000 цифр не считаем
DEFAULT_DIGITS = 50        # сколько знаков после запятой печатать


class CalcError(ValueError):
    """Ошибка в выражении: синтаксис, деление на ноль, недопустимая степень."""


@dataclass
class OpCounter:
    """Счётчик элементарных операций — для замеров асимптотики."""

    tokens: int = 0
    stack_ops: int = 0      # положить/снять со стека
    arithmetic: int = 0     # операций над числами

    @property
    def total(self) -> int:
        return self.tokens + self.stack_ops + self.arithmetic


@dataclass(frozen=True)
class Token:
    kind: str     # "num", "op", "(", ")"
    text: str     # число как текст или знак операции
    pos: int      # позиция в строке — для понятных сообщений об ошибках


def _read_number(expr: str, i: int) -> int:
    """Вернуть индекс сразу за числом, начинающимся в позиции i."""
    seen_sep = False
    j = i
    while j < len(expr) and (expr[j].isdigit() or expr[j] in DECIMAL_SEPARATORS):
        if expr[j] in DECIMAL_SEPARATORS:
            if seen_sep:
                raise CalcError(f"лишний разделитель в числе (позиция {j + 1})")
            seen_sep = True
        j += 1
    if not any(ch.isdigit() for ch in expr[i:j]):
        raise CalcError(f"ожидалось число (позиция {i + 1})")
    return j


def tokenize(expr: str, counter: OpCounter | None = None) -> list[Token]:
    """Разбить строку на токены и сразу проверить порядок «число — оператор».

    Унарный минус распознаётся по контексту: он стоит там, где ждём операнд.
    """
    if not isinstance(expr, str):
        raise TypeError(f"выражение должно быть строкой, а не {type(expr).__name__}")
    c = counter if counter is not None else OpCounter()
    tokens: list[Token] = []
    expect_operand = True
    depth = 0
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        c.tokens += 1
        if ch.isdigit() or ch in DECIMAL_SEPARATORS:
            if not expect_operand:
                raise CalcError(f"пропущен оператор перед числом (позиция {i + 1})")
            j = _read_number(expr, i)
            tokens.append(Token("num", expr[i:j].replace(",", "."), i))
            expect_operand = False
            i = j
            continue
        if ch == "(":
            if not expect_operand:
                raise CalcError(f"пропущен оператор перед '(' (позиция {i + 1})")
            tokens.append(Token("(", ch, i))
            depth += 1
        elif ch == ")":
            if expect_operand:
                raise CalcError(f"пустые скобки или оператор перед ')' (позиция {i + 1})")
            if depth == 0:
                raise CalcError(f"лишняя закрывающая скобка (позиция {i + 1})")
            tokens.append(Token(")", ch, i))
            depth -= 1
        elif expect_operand and ch in UNARY_SIGNS:
            if UNARY_SIGNS[ch] is not None:
                tokens.append(Token("op", UNARY_SIGNS[ch], i))
        elif ch in BINARY_OPS:
            if expect_operand:
                raise CalcError(f"оператор '{ch}' без левого операнда (позиция {i + 1})")
            tokens.append(Token("op", ch, i))
            expect_operand = True
        else:
            raise CalcError(f"недопустимый символ {ch!r} (позиция {i + 1})")
        i += 1

    if not tokens:
        raise CalcError("пустое выражение")
    if expect_operand:
        raise CalcError("выражение обрывается на операторе")
    if depth:
        raise CalcError(f"не закрыто скобок: {depth}")
    return tokens


def to_rpn(tokens: list[Token], counter: OpCounter | None = None) -> list[Token]:
    """Перевести инфиксную запись в обратную польскую (shunting-yard).

    Инвариант: в стеке операторов приоритеты не убывают снизу вверх
    (до ближайшей открывающей скобки), поэтому всё, что сильнее нового
    оператора, уже лежит наверху и выталкивается в выход первым.
    """
    c = counter if counter is not None else OpCounter()
    out: list[Token] = []
    stack: list[Token] = []
    for tok in tokens:
        if tok.kind == "num":
            out.append(tok)
        elif tok.kind == "(":
            stack.append(tok)
            c.stack_ops += 1
        elif tok.kind == ")":
            while stack[-1].kind != "(":
                out.append(stack.pop())
                c.stack_ops += 1
            stack.pop()
            c.stack_ops += 1
        elif tok.text == NEG:
            # префиксный оператор: у него ещё нет операнда, выталкивать нечего
            stack.append(tok)
            c.stack_ops += 1
        else:
            prec = PRECEDENCE[tok.text]
            left = tok.text not in RIGHT_ASSOC
            while stack and stack[-1].kind == "op":
                top = PRECEDENCE[stack[-1].text]
                if top > prec or (top == prec and left):
                    out.append(stack.pop())
                    c.stack_ops += 1
                else:
                    break
            stack.append(tok)
            c.stack_ops += 1
    while stack:
        out.append(stack.pop())
        c.stack_ops += 1
    return out


def _power(base: Number, exp: Number) -> Number:
    if isinstance(exp, Fraction):
        if exp.denominator != 1:
            raise CalcError("степень должна быть целым числом (иначе результат не дробь)")
        size = max(base.numerator.bit_length(), base.denominator.bit_length())
        if size * abs(exp) > MAX_POWER_BITS:
            raise CalcError("слишком большой результат возведения в степень")
        return base ** int(exp)
    return base**exp


BINARY: dict[str, Callable[[Number, Number], Number]] = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "^": _power,
}


def evaluate(rpn: list[Token], number: Callable[[str], Number] = Fraction,
             counter: OpCounter | None = None) -> Number:
    """Вычислить выражение в ОПЗ. number — тип чисел: Fraction (точно) или float."""
    c = counter if counter is not None else OpCounter()
    stack: list[Number] = []
    try:
        for tok in rpn:
            if tok.kind == "num":
                stack.append(number(tok.text))
                c.stack_ops += 1
            elif tok.text == NEG:
                stack.append(-stack.pop())
                c.arithmetic += 1
                c.stack_ops += 2
            else:
                b = stack.pop()
                a = stack.pop()
                stack.append(BINARY[tok.text](a, b))
                c.arithmetic += 1
                c.stack_ops += 3
    except ZeroDivisionError:
        raise CalcError("деление на ноль") from None
    except OverflowError:
        raise CalcError("переполнение") from None
    return stack[0]


def calculate(expr: str, number: Callable[[str], Number] = Fraction,
              counter: OpCounter | None = None) -> Number:
    """Посчитать выражение целиком: токены -> ОПЗ -> значение."""
    return evaluate(to_rpn(tokenize(expr, counter), counter), number, counter)


def to_decimal_str(x: Fraction, max_digits: int = DEFAULT_DIGITS) -> str:
    """Записать дробь десятичной, выделяя период в скобках: 1/6 -> 0.1(6).

    Деление в столбик: остатки запоминаются, повтор остатка = начало периода.
    Если период длиннее max_digits — обрезаем и ставим многоточие.
    """
    if not isinstance(x, Fraction):
        raise TypeError("нужна Fraction")
    if max_digits < 0:
        raise ValueError("max_digits должно быть >= 0")
    sign = "-" if x < 0 else ""
    num, den = abs(x.numerator), x.denominator
    whole, rem = divmod(num, den)
    digits: list[str] = []
    seen: dict[int, int] = {}
    while rem and rem not in seen and len(digits) < max_digits:
        seen[rem] = len(digits)
        rem *= 10
        digits.append(str(rem // den))
        rem %= den
    if not digits:
        return f"{sign}{whole}"
    if rem == 0:
        frac = "".join(digits)
    elif rem in seen:
        start = seen[rem]
        frac = "".join(digits[:start]) + "(" + "".join(digits[start:]) + ")"
    else:
        frac = "".join(digits) + "…"
    return f"{sign}{whole}.{frac}"


def describe(expr: str, digits: int = DEFAULT_DIGITS) -> str:
    """Текст ответа: точная дробь, десятичная запись и что дал бы float."""
    exact = calculate(expr)
    lines = [f"= {exact}"]
    if exact.denominator != 1:
        lines.append(f"= {to_decimal_str(exact, digits)}")
    try:
        approx = calculate(expr, number=float)
    except CalcError as e:
        lines.append(f"float: {e}")
    else:
        same = math.isfinite(approx) and Fraction(approx) == exact
        mark = "совпадает" if same else "НЕ совпадает — ошибка округления"
        lines.append(f"float: {approx!r}  ({mark})")
    return "\n".join(lines)


def repl(digits: int) -> None:
    print("Точный калькулятор. Пример: 0.1 + 0.2   или   (1/3 + 1/6) * 2^-1")
    print("Выход: пустая строка, exit или Ctrl+D.")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line in ("", "exit", "quit", "выход"):
            return
        try:
            print(describe(line, digits))
        except CalcError as e:
            print(f"Ошибка: {e}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Точный калькулятор дробей")
    ap.add_argument("expr", nargs="*", help="выражение; без него — интерактивный режим")
    ap.add_argument("--digits", type=int, default=DEFAULT_DIGITS,
                    help="знаков после запятой в десятичной записи")
    args = ap.parse_args(argv)
    if args.digits < 0:
        ap.error("--digits должно быть >= 0")
    if not args.expr:
        repl(args.digits)
        return 0
    try:
        print(describe(" ".join(args.expr), args.digits))
    except CalcError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
