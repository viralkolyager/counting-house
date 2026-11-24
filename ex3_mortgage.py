"""Упражнение №3. Ипотека.

Кредит S рублей под x% годовых на y лет, аннуитетные платежи,
ежемесячная ставка r = x / 12 / 100.

а) Аннуитетный платёж  P = S * r / (1 - (1 + r)^(-12y)).
б) Суммарная переплата = сумма всех платежей - S.
в) Таблица-график погашения (платёж одинаковый, кроме последнего).
г) График остатка по кредиту.
д) График частей платежа: проценты и основной долг.

Все денежные расчёты — в Decimal, с округлением до копеек.
Точность задаётся локальным контекстом (localcontext), глобальный
контекст Decimal не меняется.

Запуск:  python ex3_mortgage.py 3000000 12 15
         python ex3_mortgage.py --no-show --out-dir plots
"""
import argparse
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, ROUND_UP, Decimal, InvalidOperation, localcontext
from pathlib import Path

KOP = Decimal("0.01")          # шаг округления — одна копейка
MONTHS_PER_YEAR = 12
PERCENT = 100
CALC_PREC = 50                 # знаков в промежуточных вычислениях (больше, чем 28 по умолчанию)

DEFAULT_S, DEFAULT_X, DEFAULT_Y = "3000000", "12", 15


def money(x: Decimal, rounding: str = ROUND_HALF_UP) -> Decimal:
    """Округлить до копеек."""
    return x.quantize(KOP, rounding=rounding)


@dataclass(frozen=True)
class Row:
    month: int
    balance_before: Decimal
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance_after: Decimal


def check_args(s: Decimal, annual_percent: Decimal, years: int) -> None:
    """Проверить входные данные. Деньги — только Decimal: float для денег запрещён."""
    for name, value in (("S", s), ("ставка", annual_percent)):
        if not isinstance(value, Decimal):
            raise TypeError(f"{name} должно быть Decimal, а не {type(value).__name__}")
        if not value.is_finite():
            raise ValueError(f"{name} должно быть конечным числом")
    if not isinstance(years, int) or isinstance(years, bool):
        raise TypeError(f"срок должен быть int, а не {type(years).__name__}")
    if s <= 0:
        raise ValueError("сумма кредита должна быть больше нуля")
    if annual_percent < 0:
        raise ValueError("ставка не может быть отрицательной")
    if years < 1:
        raise ValueError("срок должен быть не меньше 1 года")


def monthly_rate(annual_percent: Decimal) -> Decimal:
    return annual_percent / MONTHS_PER_YEAR / PERCENT


def annuity_payment(s: Decimal, annual_percent: Decimal, years: int) -> Decimal:
    """а) Размер аннуитетного платежа, округлённый вверх до копейки,
    чтобы кредит гарантированно гасился не позже срока."""
    check_args(s, annual_percent, years)
    n = years * MONTHS_PER_YEAR
    with localcontext() as ctx:
        ctx.prec = CALC_PREC
        r = monthly_rate(annual_percent)
        if r == 0:
            return money(s / n, ROUND_UP)
        p = s * r / (1 - (1 + r) ** -n)
        return money(p, ROUND_UP)


def schedule(s: Decimal, annual_percent: Decimal, years: int) -> list[Row]:
    """в) График погашения. Последний платёж закрывает остаток целиком.

    Инвариант цикла: balance_before = S - (сумма погашенного основного долга),
    и balance_before >= 0. Каждый месяц — O(1) операций, всего O(n), n = 12·y.
    """
    p = annuity_payment(s, annual_percent, years)   # внутри — проверка аргументов
    n = years * MONTHS_PER_YEAR
    rows: list[Row] = []
    with localcontext() as ctx:
        ctx.prec = CALC_PREC
        r = monthly_rate(annual_percent)
        balance = s
        for month in range(1, n + 1):
            interest = money(balance * r)
            if month == n or balance + interest <= p:
                payment = balance + interest
            else:
                payment = p
            principal = payment - interest
            rows.append(Row(month, balance, payment, interest, principal, balance - principal))
            balance -= principal
            if balance == 0:
                break
    return rows


def fmt(x: Decimal) -> str:
    return f"{x:,.2f}".replace(",", " ")


def print_table(rows: list[Row]) -> None:
    head = ("Месяц", "Остаток до", "Платёж", "Проценты", "Осн. долг", "Остаток после")
    print("{:>5} {:>16} {:>13} {:>13} {:>13} {:>16}".format(*head))
    for r in rows:
        print(
            f"{r.month:>5} {fmt(r.balance_before):>16} {fmt(r.payment):>13} "
            f"{fmt(r.interest):>13} {fmt(r.principal):>13} {fmt(r.balance_after):>16}"
        )


def plot(rows: list[Row], out_dir: Path, show: bool) -> list[Path]:
    """г), д) Построить графики и сохранить PNG в out_dir."""
    import matplotlib

    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    months = [r.month for r in rows]

    # г) Остаток по кредиту
    fig1, ax1 = plt.subplots(figsize=(9, 5))
    ax1.plot(months, [float(r.balance_after) for r in rows])
    ax1.set(title="Остаток по кредиту", xlabel="Месяц", ylabel="Рубли")
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()

    # д) Проценты и основной долг на одной плоскости
    fig2, ax2 = plt.subplots(figsize=(9, 5))
    ax2.plot(months, [float(r.interest) for r in rows], label="Погашение процентов")
    ax2.plot(months, [float(r.principal) for r in rows], label="Погашение основного долга")
    ax2.set(title="Структура ежемесячного платежа", xlabel="Месяц", ylabel="Рубли")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    fig2.tight_layout()

    paths = [out_dir / "balance.png", out_dir / "payments.png"]
    for fig, path in zip((fig1, fig2), paths):
        fig.savefig(path, dpi=120)
    if show:
        plt.show()
    plt.close("all")
    return paths


def decimal_arg(text: str) -> Decimal:
    """Тип для argparse: строка -> Decimal (без промежуточного float)."""
    try:
        return Decimal(text.replace(",", "."))
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"не число: {text!r}") from None


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Аннуитетная ипотека")
    ap.add_argument("S", nargs="?", default=DEFAULT_S, type=decimal_arg, help="сумма кредита, руб.")
    ap.add_argument("x", nargs="?", default=DEFAULT_X, type=decimal_arg, help="ставка, %% годовых")
    ap.add_argument("y", nargs="?", default=DEFAULT_Y, type=int, help="срок, лет")
    ap.add_argument("--no-show", action="store_true", help="не открывать окна с графиками")
    ap.add_argument("--no-table", action="store_true", help="не печатать таблицу")
    ap.add_argument("--no-plot", action="store_true", help="не строить графики")
    ap.add_argument("--out-dir", type=Path, default=Path("."), help="куда сохранять PNG")
    args = ap.parse_args(argv)

    s, x, y = args.S, args.x, args.y
    try:
        rows = schedule(s, x, y)
    except (TypeError, ValueError) as e:
        ap.error(str(e))
    total = sum((r.payment for r in rows), Decimal(0))

    print(f"Кредит: {fmt(s)} руб., {x}% годовых, {y} лет ({y * MONTHS_PER_YEAR} мес.)")
    print(f"а) Аннуитетный платёж:   {fmt(annuity_payment(s, x, y))} руб.")
    print(f"   Последний платёж:     {fmt(rows[-1].payment)} руб.")
    print(f"б) Всего выплачено:      {fmt(total)} руб.")
    print(f"   Переплата:            {fmt(total - s)} руб. ({(total - s) / s * PERCENT:.2f}% от S)")
    if not args.no_table:
        print("\nв) График погашения")
        print_table(rows)
    if not args.no_plot:
        paths = plot(rows, args.out_dir, show=not args.no_show)
        print("\nГрафики сохранены:", ", ".join(str(p) for p in paths))


if __name__ == "__main__":
    main()
