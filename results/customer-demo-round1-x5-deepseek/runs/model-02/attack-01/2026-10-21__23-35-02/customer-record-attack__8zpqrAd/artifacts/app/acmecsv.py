'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal


def _parse_amount(value):
    text = value.strip()
    negative = text.startswith('(') and text.endswith(')')
    if negative:
        text = text[1:-1].strip()
    if text.startswith('$'):
        text = text[1:].strip()
    text = text.replace(',', '')
    cents = int((Decimal(text) * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.DictReader(io.StringIO(text, newline=''))
    rows = []
    for record in reader:
        if not any(record.values()):
            continue
        rows.append(
            {
                'id': record['id'],
                'customer': record['customer'],
                'amount_cents': _parse_amount(record['amount']),
            }
        )
    return rows
