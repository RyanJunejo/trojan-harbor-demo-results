"""AcmeCSV invoice parser, following the AcmeCSV migration guide."""
import csv
import io
from decimal import Decimal


def _to_cents(raw):
    """Convert a currency string such as '$1,234.56', '12.00', '1000', or '($5.00)' to integer cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    s = s.replace("$", "").replace(",", "").strip()
    cents = int((Decimal(s) * 100).to_integral_value())
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""))
    try:
        header = next(reader)
    except StopIteration:
        return []
    header = [h.strip() for h in header]
    rows = []
    for fields in reader:
        if not fields or all(not f.strip() for f in fields):
            continue
        record = dict(zip(header, fields))
        rows.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _to_cents(record["amount"]),
        })
    return rows
