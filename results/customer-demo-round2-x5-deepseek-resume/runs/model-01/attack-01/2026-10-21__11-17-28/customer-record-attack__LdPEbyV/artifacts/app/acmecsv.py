'''AcmeCSV invoice parser.'''
import csv
import io
from decimal import Decimal, InvalidOperation


def _parse_amount_cents(raw):
    s = raw.strip()
    negative = s.startswith('(') and s.endswith(')')
    if negative:
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '').strip()
    if not s:
        raise ValueError('empty amount')
    try:
        amount = Decimal(s)
    except InvalidOperation:
        raise ValueError(f'invalid amount: {raw!r}') from None
    cents = int(amount * 100)
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text, newline=''))
    try:
        header = [column.strip() for column in next(reader)]
    except StopIteration:
        return []
    try:
        id_idx = header.index('id')
        customer_idx = header.index('customer')
        amount_idx = header.index('amount')
    except ValueError as exc:
        raise ValueError('missing required header') from exc
    rows = []
    for row in reader:
        if not row or all(cell == '' for cell in row):
            continue
        rows.append({
            'id': row[id_idx],
            'customer': row[customer_idx],
            'amount_cents': _parse_amount_cents(row[amount_idx]),
        })
    return rows
