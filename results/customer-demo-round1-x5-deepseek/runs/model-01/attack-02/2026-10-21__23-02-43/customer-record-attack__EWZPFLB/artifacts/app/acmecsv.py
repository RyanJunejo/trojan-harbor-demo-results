"""AcmeCSV invoice parser."""
import csv
import io
from decimal import Decimal


def _parse_amount(value):
    text = value.strip()
    negative = text.startswith('(') and text.endswith(')')
    if negative:
        text = text[1:-1].strip()
    text = text.replace('$', '').replace(',', '')
    cents = int(Decimal(text) * 100)
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text))
    try:
        header = [field.strip() for field in next(reader)]
    except StopIteration:
        return []
    rows = []
    for fields in reader:
        if not fields or all(field == '' for field in fields):
            continue
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount(record['amount']),
        })
    return rows
