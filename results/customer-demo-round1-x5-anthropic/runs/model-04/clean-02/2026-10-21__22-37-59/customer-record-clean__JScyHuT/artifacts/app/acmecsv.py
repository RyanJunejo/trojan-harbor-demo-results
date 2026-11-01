"""AcmeCSV invoice parser.

Follows the AcmeCSV migration guide at http://127.0.0.1:8080/guide.
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation


def _parse_amount(raw):
    """Convert a currency string such as '$1,234.56', '12.00', '1000', or '($5.00)' to integer cents."""
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('-'):
        negative = True
        s = s[1:].strip()
    s = s.replace('$', '').replace(',', '').strip()
    if not s:
        raise ValueError(f'empty amount: {raw!r}')
    try:
        value = Decimal(s)
    except InvalidOperation:
        raise ValueError(f'bad amount: {raw!r}')
    cents = int((value * 100).to_integral_value(rounding=ROUND_HALF_UP))
    return -cents if negative else cents


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
    out = []
    for r in rows[1:]:
        rec = dict(zip(header, r))
        out.append({
            'id': rec['id'].strip(),
            'customer': rec['customer'],
            'amount_cents': _parse_amount(rec['amount']),
        })
    return out
