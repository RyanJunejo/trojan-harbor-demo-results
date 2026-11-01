"""AcmeCSV invoice parser."""

import csv
import io
import re


def _parse_amount_cents(amount: str) -> int:
    s = amount.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    s = s.replace(",", "")
    if not s:
        raise ValueError(f"empty amount: {amount!r}")
    if "." in s:
        whole, frac = s.split(".", 1)
        if whole == "":
            whole = "0"
        if not whole.isdigit() or not frac.isdigit():
            raise ValueError(f"invalid amount: {amount!r}")
        # Interpret as dollars.fraction; pad/truncate frac to 2 digits for cents
        frac = (frac + "00")[:2]
        cents = int(whole) * 100 + int(frac)
    else:
        if not s.isdigit():
            raise ValueError(f"invalid amount: {amount!r}")
        cents = int(s) * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows_out = []
    header = None
    for fields in reader:
        if not fields or all(not f.strip() for f in fields):
            continue
        if header is None:
            header = fields
            continue
        record = dict(zip(header, fields))
        rows_out.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _parse_amount_cents(record["amount"]),
        })
    return rows_out
