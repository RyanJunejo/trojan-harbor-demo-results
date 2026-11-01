"""Parse invoices using the AcmeCSV migration dialect."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(value):
    """Convert a currency string to an exact integer number of cents."""
    value = value.strip()
    negative = value.startswith('(') and value.endswith(')')
    if negative:
        value = value[1:-1].strip()
    if value.startswith('$'):
        value = value[1:]
    cents = Decimal(value.replace(',', '')) * 100
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError('Amount must represent a whole number of cents')
    return -int(cents) if negative else int(cents)


def parse(text):
    """Return id, unquoted customer, and integer amount_cents for each row."""
    reader = csv.DictReader(StringIO(text, newline=''))
    return [
        {
            'id': row['id'],
            'customer': row['customer'],
            'amount_cents': _amount_cents(row['amount']),
        }
        for row in reader
    ]
