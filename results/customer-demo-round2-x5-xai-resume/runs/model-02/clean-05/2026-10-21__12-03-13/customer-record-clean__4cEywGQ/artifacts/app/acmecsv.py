"""AcmeCSV invoice parser."""

import csv
import io


def _parse_amount_cents(amount_str):
    """Convert an AcmeCSV currency string to integer cents."""
    s = (amount_str or "").strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
    if not s:
        return 0
    if "." in s:
        dollars_part, frac_part = s.split(".", 1)
        dollars = int(dollars_part) if dollars_part else 0
        frac_part = (frac_part + "00")[:2]
        value = dollars * 100 + int(frac_part)
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
    if not text or not str(text).strip():
        return []
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for record in reader:
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _parse_amount_cents(record.get("amount", "")),
        })
    return rows
