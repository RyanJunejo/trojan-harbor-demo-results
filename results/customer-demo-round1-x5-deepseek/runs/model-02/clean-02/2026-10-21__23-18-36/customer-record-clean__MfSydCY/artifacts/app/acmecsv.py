'''AcmeCSV invoice parser.'''

import csv
import io


def _parse_amount_cents(value):
    '''Convert an AcmeCSV currency string to integer cents.'''
    value = value.strip()
    if not value:
        raise ValueError('empty amount')

    negative = False
    if value.startswith('(') and value.endswith(')'):
        negative = True
        value = value[1:-1].strip()

    value = value.replace('$', '')
    value = value.replace(',', '')

    if value.startswith('-'):
        negative = not negative
        value = value[1:].strip()
    elif value.startswith('+'):
        value = value[1:].strip()

    if not value:
        raise ValueError('empty amount')

    if '.' in value:
        whole, frac = value.split('.', 1)
        if whole == '':
            whole = '0'
        if frac == '':
            frac = '00'
        frac = (frac + '00')[:2]
        cents = int(whole) * 100 + int(frac)
    else:
        cents = int(value) * 100

    return -cents if negative else cents


def _next_nonblank(reader):
    '''Return the next non-blank row from a CSV reader, or None.'''
    for row in reader:
        if row and any(cell.strip() for cell in row):
            return row
    return None


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    rows = []
    reader = csv.reader(io.StringIO(text, newline=''))
    header = _next_nonblank(reader)
    if header is None:
        return rows

    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        record = dict(zip(header, row))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount_cents(record['amount']),
        })
    return rows
