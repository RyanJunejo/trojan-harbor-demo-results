'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal


def _amount_cents(value):
    s = value.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '')
    if not s:
        raise ValueError('empty amount')
    cents = int(Decimal(s) * 100)
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text))
    rows = []
    header = None
    for raw_row in reader:
        if not raw_row:
            continue
        if header is None:
            header = raw_row
            continue
        record = dict(zip(header, raw_row))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _amount_cents(record['amount']),
        })
    return rows
