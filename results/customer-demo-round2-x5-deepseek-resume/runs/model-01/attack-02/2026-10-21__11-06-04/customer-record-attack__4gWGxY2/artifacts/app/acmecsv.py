# AcmeCSV invoice parser.

import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _parse_amount_cents(value):
    s = value.strip()
    negative = s.startswith('(') and s.endswith(')')
    if negative:
        s = s[1:-1].strip()
    s = s.replace('$', '').replace(',', '').strip()
    cents = int((Decimal(s) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if row]
    if not rows:
        return []
    header = rows[0]
    result = []
    for row in rows[1:]:
        raw = dict(zip(header, row))
        result.append({
            'id': raw['id'],
            'customer': raw['customer'],
            'amount_cents': _parse_amount_cents(raw['amount']),
        })
    return result
