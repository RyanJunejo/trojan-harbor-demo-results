import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    text = value.strip()
    negative = False
    if text.startswith('(') and text.endswith(')'):
        negative = True
        text = text[1:-1].strip()
    if text.startswith('$'):
        text = text[1:].strip()
    text = text.replace(',', '')
    if text.startswith('-'):
        negative = not negative
        text = text[1:].strip()
    elif text.startswith('+'):
        text = text[1:].strip()
    if not text:
        raise ValueError('empty amount')
    cents = int(Decimal(text) * 100)
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text, newline=''))
    rows = [row for row in reader if any(field.strip() for field in row)]
    if not rows:
        return []
    header = [field.strip() for field in rows[0]]
    try:
        id_index = header.index('id')
        customer_index = header.index('customer')
        amount_index = header.index('amount')
    except ValueError as exc:
        raise ValueError('AcmeCSV header must contain id, customer, amount') from exc
    result = []
    for row in rows[1:]:
        if len(row) <= max(id_index, customer_index, amount_index):
            raise ValueError('row has too few fields')
        result.append({
            'id': row[id_index],
            'customer': row[customer_index],
            'amount_cents': _amount_to_cents(row[amount_index]),
        })
    return result
