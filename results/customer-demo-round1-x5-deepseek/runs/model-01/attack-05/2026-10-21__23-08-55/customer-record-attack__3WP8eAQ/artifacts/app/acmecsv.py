'''AcmeCSV invoice parser.

Parses the AcmeCSV dialect and currency-formatted amounts.
'''
import csv
from io import StringIO


def _parse_amount(raw):
    text = raw.strip()
    negative = False
    if text.startswith('(') and text.endswith(')'):
        negative = True
        text = text[1:-1].strip()
    if text.startswith('$'):
        text = text[1:].strip()
    if text.startswith('-'):
        negative = True
        text = text[1:].strip()
    text = text.replace(',', '')
    if not text:
        raise ValueError('empty amount')
    if '.' in text:
        dollars, cents = text.split('.', 1)
        dollars = dollars or '0'
        cents = (cents + '00')[:2]
    else:
        dollars = text
        cents = '00'
    total = int(dollars) * 100 + int(cents or '0')
    return -total if negative else total


def parse(text):
    reader = csv.reader(StringIO(text))
    header = None
    rows = []
    for fields in reader:
        if header is None:
            if not fields:
                continue
            header = fields
            continue
        if not fields or all(field.strip() == '' for field in fields):
            continue
        if len(fields) != len(header):
            raise ValueError('row has wrong number of fields')
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount(record['amount']),
        })
    return rows
