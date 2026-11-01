"""AcmeCSV invoice parser (fixed per the AcmeCSV migration guide)."""
import csv
import io
from decimal import Decimal


def _parse_amount(raw):
    """Convert an AcmeCSV currency string such as $1,234.56 to integer cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = True
        s = s[1:].strip()
    cents = int((Decimal(s) * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(field.strip() for field in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    out = []
    for r in rows[1:]:
        rec = dict(zip(header, r))
        out.append({
            "id": rec["id"].strip(),
            "customer": rec["customer"],
            "amount_cents": _parse_amount(rec["amount"]),
        })
    return out
