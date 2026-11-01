import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _parse_amount_cents(value):
    s = value.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:].strip()
    s = s.replace(',', '')
    amount = Decimal(s)
    cents = (amount * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
    if negative:
        cents = -cents
    return int(cents)


def parse(text):
    reader = csv.reader(io.StringIO(text, newline=''))
    for fields in reader:
        if fields and any(field.strip() for field in fields):
            header = [column.strip() for column in fields]
            break
    else:
        return []
    rows = []
    for fields in reader:
        if not fields or all(field == '' for field in fields):
            continue
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount_cents(record['amount']),
        })
    return rows
