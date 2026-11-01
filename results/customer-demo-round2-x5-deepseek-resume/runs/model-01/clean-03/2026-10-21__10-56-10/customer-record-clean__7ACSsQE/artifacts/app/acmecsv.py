import csv
import io


def _amount_to_cents(value):
    value = value.strip()
    negative = False
    if value.startswith('(') and value.endswith(')'):
        negative = True
        value = value[1:-1].strip()
    value = value.replace('$', '').replace(',', '')
    if not value:
        raise ValueError('empty amount')
    if '.' in value:
        dollars, cents = value.split('.', 1)
        dollars = dollars or '0'
        cents = (cents + '00')[:2]
        amount_cents = int(dollars) * 100 + int(cents)
    else:
        amount_cents = int(value) * 100
    if negative:
        amount_cents = -amount_cents
    return amount_cents


def parse(text):
    reader = csv.reader(io.StringIO(text))
    header = None
    for row in reader:
        if row and any(field.strip() for field in row):
            header = [field.strip() for field in row]
            break
    if header is None:
        return []

    rows = []
    for fields in reader:
        if not fields or not any(field.strip() for field in fields):
            continue
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _amount_to_cents(record['amount']),
        })
    return rows
