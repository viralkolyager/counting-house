"""Упражнение №3. Ипотека.

Кредит S рублей под x% годовых на y лет, аннуитетные платежи,
ежемесячная ставка r = x / 12 / 100.

а) Аннуитетный платёж  P = S * r / (1 - (1 + r)^(-12y)).
б) Суммарная переплата = сумма всех платежей - S.
в) Таблица-график погашения (платёж одинаковый, кроме последнего).
г) График остатка по кредиту.
д) График частей платежа: проценты и основной долг.

Все денежные расчёты — в Decimal, с округлением до копеек.

Запуск:  py ex3_mortgage.py 3000000 12 15
         py ex3_mortgage.py --no-show        (только сохранить PNG)
"""
import argparse
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, ROUND_UP, Decimal, getcontext

getcontext().prec = 50
KOP = Decimal("0.01")


def money(x: Decimal, rounding=ROUND_HALF_UP) -> Decimal:
    return x.quantize(KOP, rounding=rounding)


@dataclass
class Row:
    month: int
    balance_before: Decimal
    payment: Decimal
    interest: Decimal
    principal: Decimal
    balance_after: Decimal


def annuity_payment(s: Decimal, annual_percent: Decimal, years: int) -> Decimal:
    """а) Размер аннуитетного платежа, округлённый вверх до копейки,
    чтобы кредит гарантированно гасился не позже срока."""
    n = years * 12
    r = annual_percent / 12 / 100
    if r == 0:
        return money(s / n, ROUND_UP)
    p = s * r / (1 - (1 + r) ** -n)
    return money(p, ROUND_UP)


def schedule(s: Decimal, annual_percent: Decimal, years: int) -> list[Row]:
    """в) График погашения. Последний платёж закрывает остаток целиком."""
    n = years * 12
    r = annual_percent / 12 / 100
    p = annuity_payment(s, annual_percent, years)
    balance = s
    rows = []
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


def plot(rows: list[Row], show: bool) -> None:
    import matplotlib

    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    months = [r.month for r in rows]

    # г) Остаток по кредиту
    fig1, ax1 = plt.subplots(figsize=(9, 5))
    ax1.plot(months, [float(r.balance_after) for r in rows])
    ax1.set(title="Остаток по кредиту", xlabel="Месяц", ylabel="Рубли")
    ax1.grid(True, alpha=0.3)
    fig1.tight_layout()
    fig1.savefig("balance.png", dpi=120)

    # д) Проценты и основной долг на одной плоскости
    fig2, ax2 = plt.subplots(figsize=(9, 5))
    ax2.plot(months, [float(r.interest) for r in rows], label="Погашение процентов")
    ax2.plot(months, [float(r.principal) for r in rows], label="Погашение основного долга")
    ax2.set(title="Структура ежемесячного платежа", xlabel="Месяц", ylabel="Рубли")
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    fig2.tight_layout()
    fig2.savefig("payments.png", dpi=120)

    print("\nГрафики сохранены: balance.png, payments.png")
    if show:
        plt.show()


def main() -> None:
    ap = argparse.ArgumentParser(description="Аннуитетная ипотека")
    ap.add_argument("S", nargs="?", default="3000000", help="сумма кредита, руб.")
    ap.add_argument("x", nargs="?", default="12", help="ставка, %% годовых")
    ap.add_argument("y", nargs="?", default=15, type=int, help="срок, лет")
    ap.add_argument("--no-show", action="store_true", help="не открывать окна с графиками")
    ap.add_argument("--no-table", action="store_true", help="не печатать таблицу")
    args = ap.parse_args()

    s, x, y = Decimal(args.S), Decimal(args.x), args.y
    rows = schedule(s, x, y)
    total = sum(r.payment for r in rows)

    print(f"Кредит: {fmt(s)} руб., {x}% годовых, {y} лет ({y * 12} мес.)")
    print(f"а) Аннуитетный платёж:   {fmt(annuity_payment(s, x, y))} руб.")
    print(f"   Последний платёж:     {fmt(rows[-1].payment)} руб.")
    print(f"б) Всего выплачено:      {fmt(total)} руб.")
    print(f"   Переплата:            {fmt(total - s)} руб. ({(total - s) / s * 100:.2f}% от S)")
    if not args.no_table:
        print("\nв) График погашения")
        print_table(rows)
    plot(rows, show=not args.no_show)


if __name__ == "__main__":
    main()
