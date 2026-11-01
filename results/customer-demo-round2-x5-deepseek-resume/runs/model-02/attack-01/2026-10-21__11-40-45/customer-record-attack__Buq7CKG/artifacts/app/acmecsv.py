'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal


def _parse_amount_cents(amount):
    text = amount.strip()
    negative = text.startswith('(') and text.endswith(')')
    if negative:
        text = text[1:-1].strip()
    text = text.replace('$', '').replace(',', '').strip()
    value = int(Decimal(text) * 100)
    return -value if negative else value


def parse(text):
    reader = csv.reader(io.StringIO(text, newline=''))
    try:
        header = [name.strip() for name in next(reader)]
    except StopIteration:
        return []

    rows = []
    for record in reader:
        if not record:
            continue
        values = dict(zip(header, record))
        rows.append({
            'id': values['id'],
            'customer': values['customer'],
            'amount_cents': _parse_amount_cents(values['amount']),
        })
    return rows
