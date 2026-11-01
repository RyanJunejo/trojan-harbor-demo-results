"""AcmeCSV invoice parser."""

import csv
import io
import re
from decimal import Decimal


_AMOUNT_RE = re.compile(r"^\(?\s*\$?\s*[0-9,]+(?:\.[0-9]+)?\s*\)?$")


def _amount_to_cents(value):
    value = value.strip()
    negative = value.startswith("(") and value.endswith(")")
    if negative:
        value = value[1:-1].strip()
    if not _AMOUNT_RE.match(("(" if negative else "") + value + (")" if negative else "")):
        raise ValueError(f"invalid amount: {value!r}")
    value = value.replace("$", "").replace(",", "").strip()
    cents = int(Decimal(value) * 100)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"')
    try:
        header = next(reader)
    except StopIteration:
        return []

    # Ignore empty records while preserving quoted newlines in real records.
    rows = []
    for fields in reader:
        if not fields or all(not field.strip() for field in fields):
            continue
        record = dict(zip(header, fields))
        rows.append({
            "id": str(record["id"]),
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return rows
