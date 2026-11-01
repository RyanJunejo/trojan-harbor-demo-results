'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal

_REQUIRED_FIELDS = ('id', 'customer', 'amount')


def _amount_to_cents(raw):
    '''Convert an AcmeCSV currency amount to integer cents.'''
    value = raw.strip()
    negative = False
    if value.startswith('(') and value.endswith(')'):
        negative = True
        value = value[1:-1].strip()
    if value.startswith('$'):
        value = value[1:]
    value = value.replace(',', '')
    if not value:
        raise ValueError('empty amount: {!r}'.format(raw))
    amount = Decimal(value)
    cents = amount * 100
    if cents != cents.to_integral_value():
        raise ValueError('amount has sub-cent precision: {!r}'.format(raw))
    cents_int = int(cents)
    return -cents_int if negative else cents_int


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    '''
    if not text or not text.strip():
        return []

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    indexes = {name: header.index(name) for name in _REQUIRED_FIELDS}
    rows = []
    for fields in reader:
        if not fields or all(field == '' for field in fields):
            continue
        rows.append({
            'id': fields[indexes['id']],
            'customer': fields[indexes['customer']],
            'amount_cents': _amount_to_cents(fields[indexes['amount']]),
        })
    return rows
