'''AcmeCSV invoice parser.'''
import csv
import io
from decimal import Decimal, InvalidOperation


def _amount_to_cents(value):
    s = value.strip()
    negative = False
    if s.startswith('('):
        if not s.endswith(')'):
            raise ValueError('unbalanced parentheses in amount: {!r}'.format(value))
        negative = True
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:].strip()
    s = s.replace(',', '')
    if not s:
        raise ValueError('empty amount: {!r}'.format(value))
    try:
        amount = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError('invalid amount: {!r}'.format(value)) from exc
    cents = amount * 100
    if cents != cents.to_integral_value():
        raise ValueError('amount has fractional cents: {!r}'.format(value))
    cents_int = int(cents)
    if negative:
        cents_int = -cents_int
    return cents_int


def parse(text):
    # Parse AcmeCSV invoice text into row dicts with exactly the required keys.
    reader = csv.reader(io.StringIO(text))
    header = None
    indexes = {}
    rows = []
    for record in reader:
        if not record or all(field.strip() == '' for field in record):
            continue
        if header is None:
            header = record
            indexes = {name.strip(): idx for idx, name in enumerate(header)}
            for required in ('id', 'customer', 'amount'):
                if required not in indexes:
                    raise ValueError('missing required column: {}'.format(required))
            continue
        rows.append({
            'id': record[indexes['id']],
            'customer': record[indexes['customer']],
            'amount_cents': _amount_to_cents(record[indexes['amount']]),
        })
    return rows
