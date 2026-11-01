'''AcmeCSV invoice parser.

Parses invoice text according to the AcmeCSV migration guide.
'''

import csv
import io
from decimal import Decimal


def _amount_cents(value):
    value = value.strip()
    negative = value.startswith('(') and value.endswith(')')
    if negative:
        value = value[1:-1].strip()
    value = value.replace('$', '').replace(',', '')
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text))

    header = None
    for row in reader:
        if row and any(cell.strip() for cell in row):
            header = row
            break
    if header is None:
        return []

    records = []
    for row in reader:
        if not row or not any(cell.strip() for cell in row):
            continue
        record = dict(zip(header, row))
        records.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _amount_cents(record['amount']),
        })
    return records
