'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal, InvalidOperation


def _parse_amount_cents(value):
    s = value.strip()
    negative = s.startswith('(') and s.endswith(')')
    if negative:
        s = s[1:-1].strip()
    s = s.replace('$', '').replace(',', '').strip()
    try:
        amount = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError('invalid amount: {!r}'.format(value)) from exc
    cents = int(amount * 100)
    return -cents if negative else cents


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text))
    try:
        header = [field.strip() for field in next(reader)]
    except StopIteration:
        return []

    required = {'id', 'customer', 'amount'}
    missing = required.difference(header)
    if missing:
        raise ValueError('missing required column(s): {}'.format(', '.join(sorted(missing))))

    rows = []
    for record in reader:
        if not record or all(field == '' for field in record):
            continue
        if len(record) != len(header):
            raise ValueError('expected {} fields, got {}'.format(len(header), len(record)))
        raw = dict(zip(header, record))
        rows.append({
            'id': raw['id'],
            'customer': raw['customer'],
            'amount_cents': _parse_amount_cents(raw['amount']),
        })
    return rows
