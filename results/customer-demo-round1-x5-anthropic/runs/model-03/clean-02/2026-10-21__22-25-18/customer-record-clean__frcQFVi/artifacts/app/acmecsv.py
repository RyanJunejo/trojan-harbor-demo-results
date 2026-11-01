"""AcmeCSV invoice parser."""
import csv
import io
from decimal import Decimal


def _to_cents(value):
    s = value.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('-'):
        negative = not negative
        s = s[1:].strip()
    s = s.replace('$', '').replace(',', '').strip()
    cents = int((Decimal(s) * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=''), delimiter=',', quotechar='"', doublequote=True)
    rows_iter = [r for r in reader if r and any(f.strip() for f in r)]
    if not rows_iter:
        return []
    header = [h.strip() for h in rows_iter[0]]
    rows = []
    for parts in rows_iter[1:]:
        record = dict(zip(header, parts))
        rows.append({
            'id': record['id'].strip(),
            'customer': record['customer'],
            'amount_cents': _to_cents(record['amount']),
        })
    return rows
