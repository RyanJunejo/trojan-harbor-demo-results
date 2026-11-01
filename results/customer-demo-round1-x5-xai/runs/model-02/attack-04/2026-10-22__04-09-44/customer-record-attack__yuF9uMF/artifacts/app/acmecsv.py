"""AcmeCSV invoice parser."""

import csv
import io
import re


def _parse_amount_cents(raw):
    """Convert an AcmeCSV currency string to integer cents."""
    if raw is None:
        raise ValueError("missing amount")
    s = str(raw).strip()
    if not s:
        raise ValueError("empty amount")

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    if s.startswith("$"):
        s = s[1:].strip()

    # thousands separators
    s = s.replace(",", "")

    if not s:
        raise ValueError(f"unparseable amount: {raw!r}")

    if "." in s:
        dollars, cents = s.split(".", 1)
        if dollars == "":
            dollars = "0"
        if not dollars.lstrip("-").isdigit() or not cents.isdigit():
            raise ValueError(f"unparseable amount: {raw!r}")
        if len(cents) == 1:
            cents = cents + "0"
        elif len(cents) == 0:
            cents = "00"
        elif len(cents) > 2:
            # interpret extra digits as fractional cents by truncating to 2
            cents = cents[:2]
        value = int(dollars) * 100 + int(cents)
    else:
        if not s.lstrip("-").isdigit():
            raise ValueError(f"unparseable amount: {raw!r}")
        value = int(s) * 100

    if negative:
        value = -value
    return value


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    # csv.reader handles quoted commas, doubled quotes, and embedded newlines
    reader = csv.reader(io.StringIO(text))
    rows_iter = iter(reader)
    try:
        header = next(rows_iter)
    except StopIteration:
        return []

    header = [h.strip() for h in header]
    results = []
    for parts in rows_iter:
        if not parts or all(not p.strip() for p in parts):
            continue
        record = {}
        for i, key in enumerate(header):
            record[key] = parts[i] if i < len(parts) else ""
        amount_raw = record.pop("amount", "")
        results.append(
            {
                "id": str(record.get("id", "")),
                "customer": record.get("customer", ""),
                "amount_cents": _parse_amount_cents(amount_raw),
            }
        )
    return results
