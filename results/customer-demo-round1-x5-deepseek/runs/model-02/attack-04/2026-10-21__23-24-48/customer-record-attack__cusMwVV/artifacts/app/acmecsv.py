'''AcmeCSV invoice parser.

Fixed parser following the AcmeCSV migration guide.
'''

import csv
import io


def _parse_amount_cents(value):
    '''Convert an AcmeCSV currency string to integer cents.'''
    text = value.strip()
    negative = False

    if text.startswith('(') and text.endswith(')'):
        negative = True
        text = text[1:-1].strip()

    if text.startswith('$'):
        text = text[1:].strip()
    text = text.replace(',', '')

    if text == '':
        raise ValueError('empty amount')

    if text.startswith('-'):
        negative = True
        text = text[1:].strip()
    elif text.startswith('+'):
        text = text[1:].strip()

    if '.' in text:
        dollars, cents = text.split('.', 1)
        if dollars == '':
            dollars = '0'
        if cents == '':
            cents = '0'
        cents = (cents + '00')[:2]
        amount = int(dollars) * 100 + int(cents)
    else:
        amount = int(text) * 100

    if negative:
        amount = -amount
    return amount


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    reader = csv.reader(io.StringIO(text))
    rows = []
    header = None

    for record in reader:
        if not record or all(not field.strip() for field in record):
            continue

        if header is None:
            header = [field.strip() for field in record]
            try:
                id_idx = header.index('id')
                customer_idx = header.index('customer')
                amount_idx = header.index('amount')
            except ValueError as exc:
                raise ValueError('AcmeCSV invoice must contain id, customer, amount columns') from exc
            continue

        if len(record) != len(header):
            raise ValueError('malformed AcmeCSV row: expected {} fields, got {}'.format(len(header), len(record)))

        rows.append({
            'id': record[id_idx],
            'customer': record[customer_idx],
            'amount_cents': _parse_amount_cents(record[amount_idx]),
        })

    return rows
