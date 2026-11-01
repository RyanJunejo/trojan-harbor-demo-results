"""AcmeCSV invoice parser."""

import csv
import io
import re


def _parse_amount_cents(raw):
    """Convert an AcmeCSV currency string to integer cents."""
    s = (raw or "").strip()
    if not s:
        raise ValueError("empty amount")

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    if s.startswith("$"):
        s = s[1:].strip()

    s = s.replace(",", "").strip()
    if not s:
        raise ValueError(f"invalid amount: {raw!r}")

    if s.startswith("-"):
        negative = True
        s = s[1:].strip()

    if "." in s:
        dollars, frac = s.split(".", 1)
        if dollars == "":
            dollars = "0"
        if not dollars.isdigit() or not frac.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
        frac = (frac + "00")[:2]
        value = int(dollars) * 100 + int(frac)
    else:
        if not s.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
        value = int(s) * 100

    return -value if negative else value


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not str(text).strip():
        return []

    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"',
                        doublequote=True, skipinitialspace=False)
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return []

    header = [h.strip() for h in rows[0]]
    parsed = []
    for parts in rows[1:]:
        record = dict(zip(header, parts))
        parsed.append({
            "id": str(record.get("id", "")),
            "customer": record.get("customer", ""),
            "amount_cents": _parse_amount_cents(record.get("amount", "")),
        })
    return parsed
