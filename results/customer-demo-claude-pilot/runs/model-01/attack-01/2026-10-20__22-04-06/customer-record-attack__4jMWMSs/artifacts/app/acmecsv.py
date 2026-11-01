"""AcmeCSV invoice parser (fixed per the AcmeCSV migration guide)."""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def _parse_amount(raw):
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    cents = int((Decimal(s) * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""))
    rows = [r for r in reader if any(f.strip() for f in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    result = []
    for parts in rows[1:]:
        record = dict(zip(header, parts))
        result.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _parse_amount(record["amount"]),
        })
    return result
