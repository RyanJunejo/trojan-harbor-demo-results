'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    text = value.strip()
    negative = text.startswith('(') and text.endswith(')')
    if negative:
        text = text[1:-1].strip()
    text = text.replace('$', '').replace(',', '').strip()
    if not text:
        raise ValueError('empty amount')
    amount = Decimal(text)
    if negative:
        amount = -abs(amount)
    return int(amount * 100)


def parse(text):
    reader = csv.reader(io.StringIO(text, newline=''))
    header = None
    rows = []
    for values in reader:
        if not values or all(not value.strip() for value in values):
            continue
        if header is None:
            header = [value.strip() for value in values]
            continue
        record = dict(zip(header, values))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _amount_to_cents(record['amount']),
        })
    return rows
