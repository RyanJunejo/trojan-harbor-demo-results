"""AcmeCSV invoice parser, following the AcmeCSV migration guide."""
import csv
import io
from decimal import Decimal, InvalidOperation


def _parse_amount(raw):
    '''Convert a currency string such as $1,234.56, 12.00, 1000, or ($5.00) to integer cents.'''
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('-'):
        negative = True
        s = s[1:].strip()
    s = s.replace('$', '').replace(',', '').strip()
    try:
        value = Decimal(s)
    except InvalidOperation:
        raise ValueError('invalid amount: %r' % raw)
    cents = int((value * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    '''Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: 'id' (str), 'customer' (str, unquoted), and
    'amount_cents' (int).
    '''
    reader = csv.reader(io.StringIO(text))
    header = None
    rows = []
    for fields in reader:
        if not any(f.strip() for f in fields):
            continue
        if header is None:
            header = [h.strip() for h in fields]
            continue
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'].strip(),
            'customer': record['customer'],
            'amount_cents': _parse_amount(record['amount']),
        })
    return rows
