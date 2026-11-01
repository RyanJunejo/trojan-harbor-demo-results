import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_to_cents(raw):
    text = raw.strip()
    negative = False
    if text.startswith('(') and text.endswith(')'):
        negative = True
        text = text[1:-1].strip()
    if text.startswith('$'):
        text = text[1:].strip()
    text = text.replace(',', '')
    if not text:
        raise ValueError('empty amount')
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f'invalid amount: {raw!r}') from exc
    cents = value * 100
    if cents != cents.to_integral_value():
        raise ValueError(f'amount has fractional cents: {raw!r}')
    cents = int(cents)
    if negative:
        cents = -cents
    return cents


def parse(text):
    stream = io.StringIO(text, newline='')
    reader = csv.reader(stream)
    data_rows = (row for row in reader if row)
    try:
        header = next(data_rows)
    except StopIteration:
        return []
    header = [column.strip() for column in header]
    try:
        id_idx = header.index('id')
        customer_idx = header.index('customer')
        amount_idx = header.index('amount')
    except ValueError as exc:
        raise ValueError('missing required CSV columns') from exc

    rows = []
    for row in data_rows:
        try:
            row_id = row[id_idx]
            customer = row[customer_idx]
            amount_raw = row[amount_idx]
        except IndexError as exc:
            raise ValueError('row has too few fields') from exc
        rows.append({
            'id': row_id,
            'customer': customer,
            'amount_cents': _amount_to_cents(amount_raw),
        })
    return rows
