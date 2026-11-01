"""AcmeCSV invoice parser."""

import csv
import io
import re


def _amount_to_cents(amount: str) -> int:
    s = amount.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
    if not s:
        raise ValueError(f"empty amount: {amount!r}")
    if "." in s:
        whole, frac = s.split(".", 1)
        if not whole:
            whole = "0"
        if len(frac) > 2:
            frac = frac[:2]
        frac = frac.ljust(2, "0")
        cents = int(whole) * 100 + int(frac)
    else:
        cents = int(s) * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not text.strip():
        return []
    reader = csv.reader(io.StringIO(text))
    rows_iter = iter(reader)
    try:
        header = next(rows_iter)
    except StopIteration:
        return []
    header = [h.strip() for h in header]
    result = []
    for parts in rows_iter:
        if not parts or all(not p.strip() for p in parts):
            continue
        record = dict(zip(header, parts))
        result.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return result
