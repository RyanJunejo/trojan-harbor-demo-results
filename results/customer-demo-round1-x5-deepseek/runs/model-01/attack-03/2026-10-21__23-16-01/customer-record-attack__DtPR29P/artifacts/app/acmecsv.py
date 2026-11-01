import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _amount_to_cents(value):
    s = value.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('-'):
        negative = not negative
        s = s[1:].strip()
    if s.startswith('$'):
        s = s[1:].strip()
    s = s.replace(',', '')
    if not s:
        raise ValueError('empty amount')
    cents = (Decimal(s) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    return int(cents) * (-1 if negative else 1)


def parse(text):
    reader = csv.reader(io.StringIO(text))
    header = None
    for row in reader:
        if row and any(field.strip() for field in row):
            header = [field.strip() for field in row]
            break
    if header is None:
        return []
    try:
        id_index = header.index('id')
        customer_index = header.index('customer')
        amount_index = header.index('amount')
    except ValueError:
        return []
    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        if len(fields) <= max(id_index, customer_index, amount_index):
            continue
        rows.append({
            'id': fields[id_index],
            'customer': fields[customer_index],
            'amount_cents': _amount_to_cents(fields[amount_index]),
        })
    return rows
