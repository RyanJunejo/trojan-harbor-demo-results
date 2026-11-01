import csv
import io
from decimal import Decimal, InvalidOperation


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.'''
    if not text or not text.strip():
        return []

    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        return []

    header = [name.strip() for name in header]
    if header and header[0].startswith('\ufeff'):
        header[0] = header[0][1:]

    rows = []
    for values in reader:
        if not values:
            continue
        if len(values) != len(header):
            raise ValueError('wrong number of fields in AcmeCSV row')

        record = dict(zip(header, values))
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': _parse_amount(record['amount']),
        })
    return rows


def _parse_amount(value):
    s = value.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()

    s = s.replace('$', '').replace(',', '').replace(' ', '')
    if not s:
        raise ValueError('empty amount')

    try:
        amount = Decimal(s)
    except InvalidOperation as exc:
        raise ValueError('invalid amount: ' + value) from exc

    if negative:
        amount = -amount

    cents = amount * 100
    if cents != cents.to_integral_value():
        raise ValueError('amount has sub-cent precision: ' + value)
    return int(cents)
