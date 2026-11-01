import csv
import io
from decimal import Decimal


def _parse_amount(text):
    value = text.strip()
    negative = False
    if value.startswith('(') and value.endswith(')'):
        negative = True
        value = value[1:-1].strip()
    value = value.replace('$', '').replace(',', '').strip()
    if not value:
        raise ValueError('empty amount')
    cents = int((Decimal(value) * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text, newline=''))
    header = None
    indices = None
    rows = []
    for row in reader:
        if not any(field.strip() for field in row):
            continue
        if header is None:
            header = [field.strip() for field in row]
            indices = {name: i for i, name in enumerate(header)}
            continue
        rows.append({
            'id': row[indices['id']],
            'customer': row[indices['customer']],
            'amount_cents': _parse_amount(row[indices['amount']]),
        })
    return rows
