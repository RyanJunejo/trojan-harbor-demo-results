"""AcmeCSV invoice parser.

Parses AcmeCSV invoice text per the migration guide:
- Standard CSV quoting with doubled quotes for literal quotes
- Quoted fields may contain commas and line breaks
- Amounts converted to integer cents
"""

import csv
import io


def _amount_to_cents(raw):
    """Convert a currency string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
    if s.startswith("-"):
        negative = True
        s = s[1:]
    if "." in s:
        whole, frac = s.split(".", 1)
        frac = (frac + "00")[:2]
        cents = int(whole or "0") * 100 + int(frac or "0")
    else:
        cents = int(s or "0") * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None or not str(text).strip():
        return []
    reader = csv.reader(io.StringIO(text))
    rows_iter = iter(reader)
    try:
        header = next(rows_iter)
    except StopIteration:
        return []
    header = [h.strip() for h in header]
    rows = []
    for parts in rows_iter:
        if not parts or all(not p.strip() for p in parts):
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": record.get("id", ""),
            "customer": record.get("customer", ""),
            "amount_cents": _amount_to_cents(record.get("amount", "0")),
        })
    return rows
