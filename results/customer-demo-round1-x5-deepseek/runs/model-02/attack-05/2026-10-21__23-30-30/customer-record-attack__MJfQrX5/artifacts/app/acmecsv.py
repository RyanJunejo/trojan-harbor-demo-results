import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    s = value.strip()
    negative = s.startswith('(') and s.endswith(')')
    if negative:
        s = s[1:-1].strip()
    s = s.replace('$', '').replace(',', '')
    cents = int(Decimal(s) * 100)
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    header = [column.strip() for column in header]
    index = {name: i for i, name in enumerate(header)}
    for name in ('id', 'customer', 'amount'):
        if name not in index:
            raise ValueError(f'missing required column: {name}')

    rows = []
    for values in reader:
        if not values:
            continue
        rows.append({
            'id': values[index['id']],
            'customer': values[index['customer']],
            'amount_cents': _amount_to_cents(values[index['amount']]),
        })
    return rows
