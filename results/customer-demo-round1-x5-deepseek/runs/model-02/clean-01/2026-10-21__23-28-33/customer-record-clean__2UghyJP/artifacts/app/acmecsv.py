'''AcmeCSV invoice parser.'''

import csv
import io


def _parse_amount_cents(value):
    text = value.strip()
    negative = text.startswith('(') and text.endswith(')')
    if negative:
        text = text[1:-1].strip()

    text = text.replace('$', '').replace(',', '').strip()
    if text.startswith('-'):
        negative = True
        text = text[1:].strip()
    elif text.startswith('+'):
        text = text[1:].strip()

    dollars, dot, cents = text.partition('.')
    dollars = dollars or '0'
    cents = (cents + '00')[:2] if dot else '00'
    total = int(dollars) * 100 + int(cents or '0')
    return -total if negative else total


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text, newline=''))
    try:
        header = next(reader)
    except StopIteration:
        return []

    header = [field.strip() for field in header]
    rows = []
    for fields in reader:
        if not fields or all(field == '' for field in fields):
            continue
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount_cents(record['amount']),
        })
    return rows
