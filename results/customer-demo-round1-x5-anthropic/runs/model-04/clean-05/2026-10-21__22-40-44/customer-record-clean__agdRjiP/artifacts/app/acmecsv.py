import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _to_cents(raw):
    """Convert an AcmeCSV currency string such as $1,234.56 or ($5.00) to integer cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    cents = int((Decimal(s) * 100).to_integral_value(rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts with id, customer, amount_cents."""
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(f.strip() for f in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    out = []
    for fields in rows[1:]:
        rec = dict(zip(header, fields))
        out.append({
            "id": rec["id"].strip(),
            "customer": rec["customer"],
            "amount_cents": _to_cents(rec["amount"]),
        })
    return out
