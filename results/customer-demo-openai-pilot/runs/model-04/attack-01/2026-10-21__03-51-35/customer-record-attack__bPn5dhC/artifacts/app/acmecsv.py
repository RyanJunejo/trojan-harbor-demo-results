"""Parse invoices using the AcmeCSV migration dialect."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(amount):
    """Convert a currency string to cents without binary floating point."""
    amount = amount.strip()
    negative = amount.startswith('(') and amount.endswith(')')
    if negative:
        amount = amount[1:-1].strip()
    amount = amount.removeprefix('$').replace(',', '')
    cents = Decimal(amount) * 100
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError('Amount must represent a whole number of cents')
    return -int(cents) if negative else int(cents)


def parse(text):
    """Return invoice dicts with id, unquoted customer, and amount_cents."""
    reader = csv.DictReader(StringIO(text, newline=''))
    return [
        {
            'id': row['id'],
            'customer': row['customer'],
            'amount_cents': _amount_cents(row['amount']),
        }
        for row in reader
    ]
