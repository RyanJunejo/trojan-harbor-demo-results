"""AcmeCSV invoice parser."""

import csv
import io


def _amount_to_cents(raw):
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
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
    if not text or not text.strip():
        return []
    reader = csv.reader(io.StringIO(text))
    rows = []
    header = None
    for parts in reader:
        if not parts or all(not p.strip() for p in parts):
            continue
        if header is None:
            header = parts
            continue
        record = dict(zip(header, parts))
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return rows
