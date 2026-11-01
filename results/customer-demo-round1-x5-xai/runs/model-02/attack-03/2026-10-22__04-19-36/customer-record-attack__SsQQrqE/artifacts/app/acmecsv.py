"""AcmeCSV invoice parser."""

import csv
import io


def _parse_amount(amount_str):
    """Convert a currency string to an integer number of cents."""
    s = (amount_str or "").strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    s = s.replace(",", "").replace(" ", "")
    if not s:
        raise ValueError("empty amount")
    if "." in s:
        dollars, frac = s.split(".", 1)
        dollars = dollars or "0"
        frac = (frac + "00")[:2]
        value = int(dollars) * 100 + int(frac)
    else:
        value = int(s) * 100
    return -value if negative else value


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
