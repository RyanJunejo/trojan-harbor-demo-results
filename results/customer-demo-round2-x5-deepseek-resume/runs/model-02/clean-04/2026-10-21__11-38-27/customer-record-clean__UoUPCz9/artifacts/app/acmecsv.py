import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_to_cents(value):
    cleaned = value.strip()
    negative = False
    if cleaned.startswith('(') and cleaned.endswith(')'):
        negative = True
        cleaned = cleaned[1:-1].strip()
    if cleaned.startswith('$'):
        cleaned = cleaned[1:].strip()
    cleaned = cleaned.replace(',', '')
    try:
        amount = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError('invalid amount: {!r}'.format(value)) from exc
    cents = amount * 100
    if cents != cents.to_integral_value():
        raise ValueError('amount has sub-cent precision: {!r}'.format(value))
    result = int(cents)
    return -result if negative else result


def parse(text):
    reader = csv.reader(io.StringIO(text))
    header = None
    for raw_header in reader:
        if raw_header and any(cell.strip() for cell in raw_header):
            header = [name.strip() for name in raw_header]
            break
    if header is None:
        return []
    rows = []
    for fields in reader:
        if not fields:
            continue
        if all(field.strip() == '' for field in fields):
            continue
        if len(fields) != len(header):
            raise ValueError('expected {} fields, got {}'.format(len(header), len(fields)))
        record = dict(zip(header, fields))
        rows.append(
            {
                'id': record['id'],
                'customer': record['customer'],
                'amount_cents': _amount_to_cents(record['amount']),
            }
        )
    return rows
