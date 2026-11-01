'''AcmeCSV invoice parser.'''

import csv
import io


def _amount_to_cents(value):
    value = value.strip()
    negative = False
    if value.startswith('(') and value.endswith(')'):
        negative = True
        value = value[1:-1].strip()
    if value.startswith('$'):
        value = value[1:].strip()
    value = value.replace(',', '')
    if '.' in value:
        dollars, cents = value.split('.', 1)
    else:
        dollars, cents = value, ''
    if dollars == '':
        dollars = '0'
    cents = (cents + '00')[:2]
    total = int(dollars) * 100 + int(cents)
    return -total if negative else total


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text, newline=''))
    header = None
    rows = []
    for fields in reader:
        if not fields or all(field.strip() == '' for field in fields):
            continue
        if header is None:
            header = [field.strip() for field in fields]
            continue
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _amount_to_cents(record['amount']),
        })
    return rows
