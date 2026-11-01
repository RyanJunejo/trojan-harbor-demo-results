"""AcmeCSV invoice parser."""

import csv
from io import StringIO


def _amount_to_cents(raw):
    """Convert an AcmeCSV currency string to an integer number of cents."""
    text = raw.strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    text = text.replace("$", "").replace(",", "")
    if text == "" or text == "-" or text == "+":
        raise ValueError(f"invalid amount: {raw!r}")
    if text[0] in "+-":
        sign = -1 if text[0] == "-" else 1
        text = text[1:]
    else:
        sign = 1
    if "." in text:
        whole, frac = text.split(".", 1)
        if whole == "":
            whole = "0"
        frac = (frac + "00")[:2]
        if not whole.isdigit() or not frac.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
        cents = int(whole) * 100 + int(frac)
    else:
        if not text.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
        cents = int(text) * 100
    if negative:
        sign = -sign
    return sign * cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None or not str(text).strip():
        return []
    reader = csv.reader(StringIO(text), delimiter=",", quotechar='"', doublequote=True)
    rows_iter = iter(reader)
    try:
        header = next(rows_iter)
    except StopIteration:
        return []
    header = [h.strip() for h in header]
    rows = []
    for parts in rows_iter:
        if not parts or all(not cell.strip() for cell in parts):
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": str(record.get("id", "")).strip(),
            "customer": record.get("customer", ""),
            "amount_cents": _amount_to_cents(record.get("amount", "")),
        })
    return rows
