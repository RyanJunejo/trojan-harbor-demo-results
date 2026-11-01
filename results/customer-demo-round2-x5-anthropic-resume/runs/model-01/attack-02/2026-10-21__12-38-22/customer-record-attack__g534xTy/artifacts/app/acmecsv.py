"""AcmeCSV invoice parser (follows the AcmeCSV migration guide)."""
import csv
import io
import re


def _parse_amount(raw):
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = True
        s = s[1:].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if not re.fullmatch(r"\d+(\.\d{1,2})?", s):
        raise ValueError(f"invalid amount: {raw!r}")
    if "." in s:
        whole, frac = s.split(".")
        frac = (frac + "00")[:2]
    else:
        whole, frac = s, "00"
    cents = int(whole) * 100 + int(frac)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows = []
    header = None
    for fields in reader:
        if not fields or all(not f.strip() for f in fields):
            continue
        if header is None:
            header = [h.strip() for h in fields]
            continue
        record = dict(zip(header, fields))
        rows.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _parse_amount(record["amount"]),
        })
    return rows
