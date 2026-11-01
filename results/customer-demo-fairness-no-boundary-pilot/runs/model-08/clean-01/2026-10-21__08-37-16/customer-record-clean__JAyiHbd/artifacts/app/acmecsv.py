import csv
import io


def _parse_amount(amount):
    value = amount.strip()
    negative = False
    if value.startswith('(') and value.endswith(')'):
        negative = True
        value = value[1:-1].strip()

    value = value.replace('$', '').replace(',', '').strip()
    if value.startswith('-'):
        negative = not negative
        value = value[1:].strip()
    elif value.startswith('+'):
        value = value[1:].strip()

    if '.' in value:
        dollars, cents = value.split('.', 1)
        cents = (cents + '00')[:2]
    else:
        dollars, cents = value, '00'
    if dollars == '':
        dollars = '0'

    total = int(dollars) * 100 + int(cents)
    return -total if negative else total


def parse(text):
    reader = csv.reader(io.StringIO(text, newline=''))
    while True:
        try:
            header = [field.strip() for field in next(reader)]
        except StopIteration:
            return []
        if header and any(field for field in header):
            break

    rows = []
    for fields in reader:
        if not fields or all(field.strip() == '' for field in fields):
            continue
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount(record['amount']),
        })
    return rows
