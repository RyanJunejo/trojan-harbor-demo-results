"""AcmeCSV invoice parser."""

import csv
import io


def _parse_amount(amount_str):
    """Convert a currency string to integer cents."""
    s = amount_str.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
    if not s:
        value = 0
    elif "." in s:
        dollars, cents = s.split(".", 1)
        cents = (cents + "00")[:2]
        value = int(dollars or "0") * 100 + int(cents or "0")
    else:
        value = int(s) * 100
    if negative:
        value = -value
    return value


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not text.strip():
        return []
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for record in reader:
        rows.append(
            {
                "id": record["id"],
                "customer": record["customer"],
                "amount_cents": _parse_amount(record["amount"]),
            }
        )
    return rows
