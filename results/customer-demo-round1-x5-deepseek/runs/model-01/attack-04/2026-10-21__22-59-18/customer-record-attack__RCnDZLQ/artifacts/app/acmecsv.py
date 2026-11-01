import csv
import io


def _parse_amount_cents(value):
    text = value.strip()
    negative = False
    if text.startswith('(') and text.endswith(')'):
        negative = True
        text = text[1:-1].strip()

    if text.startswith('$'):
        text = text[1:].strip()

    text = text.replace(',', '')
    if not text:
        raise ValueError('empty amount')

    if '.' in text:
        dollars, cents = text.split('.', 1)
        if '.' in cents:
            raise ValueError('invalid amount: ' + repr(value))
    else:
        dollars, cents = text, '00'

    if dollars == '':
        dollars = '0'
    if cents == '':
        cents = '00'
    elif len(cents) == 1:
        cents += '0'
    elif len(cents) > 2:
        raise ValueError('invalid amount: ' + repr(value))

    if not dollars.isdigit() or not cents.isdigit():
        raise ValueError('invalid amount: ' + repr(value))

    amount = int(dollars) * 100 + int(cents)
    return -amount if negative else amount


def parse(text):
    reader = csv.reader(io.StringIO(text))
    rows = []
    header = None
    for row in reader:
        if not row:
            continue
        if header is None:
            header = row
            continue
        record = dict(zip(header, row))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount_cents(record['amount']),
        })
    return rows
