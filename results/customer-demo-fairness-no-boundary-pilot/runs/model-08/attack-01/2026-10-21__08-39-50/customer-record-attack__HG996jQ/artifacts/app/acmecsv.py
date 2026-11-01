'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    text = value.strip()
    negative = False
    if text.startswith('(') and text.endswith(')'):
        negative = True
        text = text[1:-1].strip()
    text = text.replace(',', '')
    if text.startswith('$'):
        text = text[1:]
    elif text.startswith('-$'):
        text = '-' + text[2:]
    value_decimal = Decimal(text)
    if negative:
        value_decimal = -value_decimal
    return int(value_decimal * 100)


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text))
    records = [row for row in reader if row and any(cell.strip() for cell in row)]
    if not records:
        return []
    header = [cell.strip() for cell in records[0]]
    rows = []
    for row in records[1:]:
        record = dict(zip(header, row))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _amount_to_cents(record['amount']),
        })
    return rows
