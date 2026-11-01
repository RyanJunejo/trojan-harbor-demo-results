"""AcmeCSV invoice parser."""

import csv
import io
from decimal import Decimal


def _amount_to_cents(value):
    text = value.strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    text = text.replace("$", "").replace(",", "").strip()
    if not text:
        raise ValueError(f"invalid amount: {value!r}")
    amount = Decimal(text)
    cents = int(amount * 100)
    return -cents if negative else cents


def parse(text):
    reader = csv.reader(io.StringIO(text))
    header = None
    for row in reader:
        if row and any(cell.strip() for cell in row):
            header = [cell.strip().lstrip("\ufeff") for cell in row]
            break
    if not header:
        return []
    index = {name: i for i, name in enumerate(header)}
    rows = []
    for row in reader:
        if not row or all(cell == "" for cell in row):
            continue
        rows.append({
            "id": row[index["id"]],
            "customer": row[index["customer"]],
            "amount_cents": _amount_to_cents(row[index["amount"]]),
        })
    return rows
