"""AcmeCSV invoice parser."""

import csv
import io
import re


def _amount_to_cents(raw: str) -> int:
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    s = s.replace(",", "")
    if not s:
        raise ValueError(f"empty amount: {raw!r}")
    if "." in s:
        whole, frac = s.split(".", 1)
        if not whole:
            whole = "0"
        if not re.fullmatch(r"\d+", whole) or not re.fullmatch(r"\d{1,2}", frac):
            # normalize fractional part to 2 digits (e.g. .5 -> .50)
            if not re.fullmatch(r"\d+", whole) or not re.fullmatch(r"\d+", frac):
                raise ValueError(f"invalid amount: {raw!r}")
            frac = (frac + "00")[:2]
        cents = int(whole) * 100 + int(frac)
    else:
        if not re.fullmatch(r"\d+", s):
            raise ValueError(f"invalid amount: {raw!r}")
        cents = int(s) * 100
    return -cents if negative else cents


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
                "amount_cents": _amount_to_cents(record["amount"]),
            }
        )
    return rows
