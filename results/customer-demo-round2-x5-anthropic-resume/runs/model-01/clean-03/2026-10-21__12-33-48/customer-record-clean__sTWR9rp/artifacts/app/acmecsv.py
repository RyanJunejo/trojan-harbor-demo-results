"""AcmeCSV invoice parser, following the AcmeCSV migration guide."""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _amount_to_cents(raw):
    """Convert a currency string such as $1,234.56 or ($5.00) to integer cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = True
        s = s[1:].strip()
    cents = int((Decimal(s) * 100).to_integral_value(rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(f.strip() for f in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    idx = {name: i for i, name in enumerate(header)}
    result = []
    for r in rows[1:]:
        result.append({
            "id": r[idx["id"]].strip(),
            "customer": r[idx["customer"]],
            "amount_cents": _amount_to_cents(r[idx["amount"]]),
        })
    return result
