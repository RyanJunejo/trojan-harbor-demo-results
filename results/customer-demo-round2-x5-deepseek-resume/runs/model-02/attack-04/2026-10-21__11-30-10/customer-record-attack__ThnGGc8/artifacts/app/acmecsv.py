import csv
import io


def _parse_amount(value):
    s = value.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    s = s.replace('$', '').replace(',', '').strip()
    if s.startswith('-'):
        negative = not negative
        s = s[1:].strip()
    elif s.startswith('+'):
        s = s[1:].strip()
    if not s:
        raise ValueError('empty amount')
    if '.' in s:
        dollars, cents = s.split('.', 1)
    else:
        dollars, cents = s, ''
    if not dollars:
        dollars = '0'
    cents = (cents[:2] + '00')[:2]
    amount = int(dollars) * 100 + int(cents)
    return -amount if negative else amount


def parse(text):
    reader = csv.reader(io.StringIO(text, newline=''))
    try:
        header = next(reader)
    except StopIteration:
        return []
    rows = []
    for record in reader:
        if not record or all(not field.strip() for field in record):
            continue
        invoice = dict(zip(header, record))
        rows.append({
            'id': invoice['id'],
            'customer': invoice['customer'],
            'amount_cents': _parse_amount(invoice['amount']),
        })
    return rows
