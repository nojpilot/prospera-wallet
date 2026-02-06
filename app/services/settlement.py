from decimal import Decimal, ROUND_HALF_UP


def quantize(value: Decimal) -> Decimal:
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def simplify_settlements(net_balances: dict[int, Decimal]) -> list[dict]:
    debtors = sorted([(u, -b) for u, b in net_balances.items() if b < 0], key=lambda x: x[0])
    creditors = sorted([(u, b) for u, b in net_balances.items() if b > 0], key=lambda x: x[0])
    i = j = 0
    settlements = []
    while i < len(debtors) and j < len(creditors):
        debtor, debt = debtors[i]
        creditor, credit = creditors[j]
        amount = quantize(min(debt, credit))
        if amount > 0:
            settlements.append({'from_user': debtor, 'to_user': creditor, 'amount': amount})
        debt = quantize(debt - amount)
        credit = quantize(credit - amount)
        debtors[i] = (debtor, debt)
        creditors[j] = (creditor, credit)
        if debt == 0:
            i += 1
        if credit == 0:
            j += 1
    return settlements
