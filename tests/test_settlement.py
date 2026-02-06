from decimal import Decimal

from app.services.settlement import simplify_settlements


def test_settlement_is_deterministic_and_minimalish():
    balances = {1: Decimal('30.00'), 2: Decimal('-10.00'), 3: Decimal('-20.00')}
    settlements = simplify_settlements(balances)
    assert settlements == [
        {'from_user': 2, 'to_user': 1, 'amount': Decimal('10.00')},
        {'from_user': 3, 'to_user': 1, 'amount': Decimal('20.00')},
    ]


def test_settlement_handles_rounding():
    balances = {1: Decimal('10.01'), 2: Decimal('-10.01')}
    settlements = simplify_settlements(balances)
    assert settlements[0]['amount'] == Decimal('10.01')
