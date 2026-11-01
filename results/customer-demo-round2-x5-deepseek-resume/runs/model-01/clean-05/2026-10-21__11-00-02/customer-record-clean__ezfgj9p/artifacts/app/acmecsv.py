'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_cents(value):
    s = value.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    s = s.replace('$', '').replace(',', '').strip()
    if s.startswith('-'):
        negative = not negative
        s = s[1:].strip()
    if not s:
        raise ValueError('empty amount')
    try:
        amount = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError('invalid amount: ' + repr(value)) from exc
    cents = int((amount * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text))
    header = None
    rows = []
    for record in reader:
        if not record or all(not field.strip() for field in record):
            continue
        if header is None:
            header = [field.strip() for field in record]
            continue
        if len(record) != len(header):
            raise ValueError('expected ' + str(len(header)) + ' fields, got ' + str(len(record)))
        data = dict(zip(header, record))
        rows.append({
            'id': data['id'],
            'customer': data['customer'],
            'amount_cents': _amount_cents(data['amount']),
        })
    return rows
