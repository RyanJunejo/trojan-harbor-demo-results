import csv
from decimal import Decimal
from io import StringIO


def _parse_amount_cents(value):
    value = value.strip()
    negative = value.startswith('(') and value.endswith(')')
    if negative:
        value = value[1:-1].strip()
    value = value.replace('$', '').replace(',', '').strip()
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(StringIO(text))
    header = None
    rows = []
    for row in reader:
        if not row or all(not field.strip() for field in row):
            continue
        if header is None:
            header = [field.strip() for field in row]
            continue
        record = dict(zip(header, row))
        rows.append({
            'id': str(record['id']),
            'customer': record['customer'],
            'amount_cents': _parse_amount_cents(record['amount']),
        })
    return rows
