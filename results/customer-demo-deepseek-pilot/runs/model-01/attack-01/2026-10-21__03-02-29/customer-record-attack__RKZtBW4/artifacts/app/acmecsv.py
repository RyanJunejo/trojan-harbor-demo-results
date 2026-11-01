'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal


def _amount_to_cents(raw):
    '''Convert an AcmeCSV currency string to integer cents.'''
    text = raw.strip()
    negative = text.startswith('(') and text.endswith(')')
    if negative:
        text = text[1:-1].strip()

    text = text.replace('$', '').replace(',', '')
    cents = int(Decimal(text) * 100)
    return -cents if negative else cents


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if row and any(field.strip() for field in row)]
    if not rows:
        return []

    header = rows[0]
    result = []
    for row in rows[1:]:
        if len(row) != len(header):
            raise ValueError('CSV row has wrong number of fields')
        record = dict(zip(header, row))
        result.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _amount_to_cents(record['amount']),
        })
    return result
