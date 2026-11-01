"""Parse invoices using the AcmeCSV quoting and currency rules."""

import csv
from decimal import Decimal
from io import StringIO


def _amount_cents(value):
    """Convert a currency string without binary floating-point rounding."""
    value = value.strip()
    negative = value.startswith('(') and value.endswith(')')
    if negative:
        value = value[1:-1].strip()
    value = value.removeprefix('$').replace(',', '')
    cents = Decimal(value) * 100
    if not cents.is_finite() or cents != cents.to_integral_value():
        raise ValueError('Amount must represent a whole number of cents')
    return -int(cents) if negative else int(cents)


def parse(text):
    """Return invoice rows with id, customer, and integer amount_cents."""
    # Filter blank records only after CSV decoding, preserving embedded newlines.
    records = (
        row for row in csv.reader(StringIO(text, newline=''))
        if row and not (len(row) == 1 and not row[0].strip())
    )
    header = next(records, None)
    if header is None:
        return []
    rows = []
    for fields in records:
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _amount_cents(record['amount']),
        })
    return rows
