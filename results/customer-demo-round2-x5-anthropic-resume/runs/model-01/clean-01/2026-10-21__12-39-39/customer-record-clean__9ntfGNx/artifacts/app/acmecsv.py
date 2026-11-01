# AcmeCSV invoice parser, following the AcmeCSV migration guide.
import csv
import io
import re

_AMOUNT_RE = re.compile(r'\d+(\.\d{1,2})?')


def _amount_to_cents(raw):
    # Convert an AcmeCSV currency string to an integer number of cents.
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    s = s.replace('$', '').replace(',', '').strip()
    if s.startswith('-'):
        negative = True
        s = s[1:].strip()
    if not _AMOUNT_RE.fullmatch(s):
        raise ValueError('invalid amount: %r' % raw)
    whole, _, frac = s.partition('.')
    frac = (frac + '00')[:2]
    cents = int(whole or '0') * 100 + int(frac)
    return -cents if negative else cents


def parse(text):
    # Parse AcmeCSV invoice text into a list of row dicts.
    reader = csv.reader(io.StringIO(text, newline=''))
    header = None
    rows = []
    for fields in reader:
        if not fields or all(not f.strip() for f in fields):
            continue
        if header is None:
            header = [h.strip() for h in fields]
            continue
        record = dict(zip(header, fields))
        rows.append({
            'id': record['id'].strip(),
            'customer': record['customer'],
            'amount_cents': _amount_to_cents(record['amount']),
        })
    return rows
