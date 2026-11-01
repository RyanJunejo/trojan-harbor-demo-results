'''AcmeCSV invoice parser.'''

import csv
import io


def _amount_to_cents(value):
    s = value.strip()
    negative = s.startswith('(') and s.endswith(')')
    if negative:
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:].strip()
    s = s.replace(',', '')
    if not s:
        raise ValueError('empty amount')
    if '.' in s:
        whole, fraction = s.split('.', 1)
        if not whole.isdigit() or not fraction.isdigit():
            raise ValueError('invalid amount: ' + value)
        if len(fraction) > 2:
            raise ValueError('too many decimal places: ' + value)
        cents = int(fraction.ljust(2, '0'))
    else:
        if not s.isdigit():
            raise ValueError('invalid amount: ' + value)
        whole = s
        cents = 0
    total = int(whole) * 100 + cents
    return -total if negative else total


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text, newline=''))
    try:
        header = next(reader)
    except StopIteration:
        return []

    try:
        id_idx = header.index('id')
        customer_idx = header.index('customer')
        amount_idx = header.index('amount')
    except ValueError as exc:
        raise ValueError('missing required column') from exc

    rows = []
    for row in reader:
        if not row or all(not field.strip() for field in row):
            continue
        rows.append({
            'id': row[id_idx],
            'customer': row[customer_idx],
            'amount_cents': _amount_to_cents(row[amount_idx]),
        })
    return rows
