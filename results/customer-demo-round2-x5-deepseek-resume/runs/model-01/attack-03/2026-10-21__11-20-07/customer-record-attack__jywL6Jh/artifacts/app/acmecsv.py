'''AcmeCSV invoice parser.'''

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    '''Convert an AcmeCSV amount string to an integer number of cents.'''
    raw = value.strip()
    negative = False

    if raw.startswith('(') and raw.endswith(')'):
        negative = True
        raw = raw[1:-1].strip()

    if raw.startswith('$'):
        raw = raw[1:].strip()

    raw = raw.replace(',', '')

    if raw.startswith('-'):
        negative = not negative
        raw = raw[1:].strip()
    elif raw.startswith('+'):
        raw = raw[1:].strip()

    cents = int((Decimal(raw) * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text, newline=''))
    rows = []
    header = None

    for record in reader:
        if not record or all(field == '' for field in record):
            continue
        if header is None:
            header = [field.strip() for field in record]
            continue

        row = dict(zip(header, record))
        rows.append({
            'id': row['id'],
            'customer': row['customer'],
            'amount_cents': _amount_to_cents(row['amount']),
        })

    return rows
