import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    text = value.strip()
    negative = text.startswith('(') and text.endswith(')')
    if negative:
        text = text[1:-1].strip()
    text = text.replace('$', '').replace(',', '')
    amount = Decimal(text).quantize(Decimal('0.01'))
    cents = int(amount * 100)
    return -cents if negative else cents


def parse(text):
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return []
    header = [name.strip() for name in rows[0]]
    result = []
    for row in rows[1:]:
        if not row or all(not cell.strip() for cell in row):
            continue
        record = dict(zip(header, row))
        result.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _amount_to_cents(record['amount']),
        })
    return result
