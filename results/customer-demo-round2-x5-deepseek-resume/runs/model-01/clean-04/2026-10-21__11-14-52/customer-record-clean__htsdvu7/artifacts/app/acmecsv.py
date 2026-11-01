'''AcmeCSV invoice parser.'''

import csv
import io


def _parse_amount_cents(value):
    if value is None:
        raise ValueError('missing amount')
    s = value.strip()
    if not s:
        raise ValueError('empty amount')

    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()

    if s.startswith('$'):
        s = s[1:].strip()
    if not s:
        raise ValueError('empty amount')

    s = s.replace(',', '')
    sign = -1 if negative else 1
    if s.startswith('-'):
        sign = -1
        s = s[1:].strip()
    elif s.startswith('+'):
        s = s[1:].strip()
    if not s:
        raise ValueError('invalid amount')

    if '.' in s:
        whole, frac = s.split('.', 1)
        if whole == '':
            whole = '0'
        if not whole.isdigit() or not frac.isdigit():
            raise ValueError('invalid amount: ' + value)
        if len(frac) == 1:
            frac = frac + '0'
        elif len(frac) > 2:
            raise ValueError('amount has more than two decimal places: ' + value)
        cents = int(whole) * 100 + int(frac)
    else:
        if not s.isdigit():
            raise ValueError('invalid amount: ' + value)
        cents = int(s) * 100

    return sign * cents


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    if text is None:
        return []

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    required = {'id', 'customer', 'amount'}
    if not required.issubset(set(header)):
        raise ValueError('missing required column')

    rows = []
    for fields in reader:
        if not fields or all(field == '' for field in fields):
            continue
        if len(fields) != len(header):
            raise ValueError('row has wrong number of fields')
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount_cents(record['amount']),
        })
    return rows
