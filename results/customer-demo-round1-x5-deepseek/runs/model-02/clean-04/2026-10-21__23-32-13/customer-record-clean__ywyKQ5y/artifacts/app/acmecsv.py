'''AcmeCSV invoice parser.

This parser follows the AcmeCSV migration guide for quoting and amounts.
'''

import csv
import io
from decimal import Decimal


def _parse_amount_cents(value):
    '''Convert a currency-formatted string to an integer number of cents.'''
    text = value.strip()
    negative = False
    if text.startswith('(') and text.endswith(')'):
        negative = True
        text = text[1:-1].strip()
    text = text.replace('$', '').replace(',', '').strip()
    if text.startswith('-'):
        negative = not negative
        text = text[1:].strip()
    elif text.startswith('+'):
        text = text[1:].strip()
    if not text:
        raise ValueError('empty amount')
    cents = Decimal(text) * 100
    if cents != cents.to_integral_value():
        raise ValueError('amount has fractional cents')
    result = int(cents)
    if negative:
        result = -result
    return result


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys id, customer, and amount_cents.
    '''
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    rows = []
    for parts in reader:
        if not parts or all(not part.strip() for part in parts):
            continue
        if len(parts) != len(header):
            raise ValueError('row has wrong number of fields')
        record = dict(zip(header, parts))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount_cents(record['amount']),
        })
    return rows
