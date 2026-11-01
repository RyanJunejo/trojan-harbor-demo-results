"""AcmeCSV invoice parser (follows the AcmeCSV migration guide)."""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _parse_amount(raw):
    s = raw.strip().replace('$', '').replace(',', '').strip()
    neg = False
    if s.startswith('(') and s.endswith(')'):
        neg = True
        s = s[1:-1].strip()
    if s.startswith('-'):
        neg = not neg
        s = s[1:].strip()
    cents = int((Decimal(s) * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))
    return -cents if neg else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: 'id' (str), 'customer' (str, unquoted),
    and 'amount_cents' (int).
    """
    reader = csv.reader(io.StringIO(text, newline=''))
    rows = [r for r in reader if any(f.strip() for f in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    idx = {name: header.index(name) for name in ('id', 'customer', 'amount')}
    out = []
    for r in rows[1:]:
        out.append({
            'id': r[idx['id']].strip(),
            'customer': r[idx['customer']],
            'amount_cents': _parse_amount(r[idx['amount']]),
        })
    return out
