import csv
import io
from decimal import Decimal


def _parse_amount(text):
    value = text.strip()
    if not value:
        raise ValueError('empty amount')

    negative = value.startswith('(') and value.endswith(')')
    if negative:
        value = value[1:-1].strip()

    value = value.replace('$', '').replace(',', '').strip()
    if value.startswith('-'):
        negative = True
        value = value[1:].strip()
    elif value.startswith('+'):
        value = value[1:].strip()

    if not value:
        raise ValueError('empty amount')

    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text, newline=''))
    raw_header = None
    for candidate in reader:
        if candidate and any(field.strip() for field in candidate):
            raw_header = candidate
            break
    if raw_header is None:
        return []

    header = [name.strip() for name in raw_header]
    rows = []
    for row in reader:
        if not row or all(not field.strip() for field in row):
            continue
        if len(row) != len(header):
            raise ValueError(
                'row has {} fields; expected {}'.format(len(row), len(header))
            )
        record = dict(zip(header, row))
        try:
            amount = record['amount']
            row_id = record['id']
            customer = record['customer']
        except KeyError as exc:
            raise ValueError('missing required column') from exc
        rows.append({
            'id': row_id,
            'customer': customer,
            'amount_cents': _parse_amount(amount),
        })
    return rows
