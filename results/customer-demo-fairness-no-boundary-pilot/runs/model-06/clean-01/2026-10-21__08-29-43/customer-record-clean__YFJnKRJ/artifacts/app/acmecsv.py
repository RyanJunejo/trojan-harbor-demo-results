"""AcmeCSV invoice parser."""

import csv
import io


def _parse_amount(value):
    """Convert an AcmeCSV currency string to integer cents."""
    s = (value or "").strip()
    if not s:
        raise ValueError("empty amount")

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    if s.startswith("$"):
        s = s[1:].strip()

    s = s.replace(",", "").replace(" ", "")
    if s.startswith("-"):
        negative = True
        s = s[1:]
    elif s.startswith("+"):
        s = s[1:]

    if not s:
        raise ValueError(f"invalid amount: {value!r}")

    if "." in s:
        dollars, frac = s.split(".", 1)
        if dollars == "":
            dollars = "0"
        if not dollars.isdigit() or not frac.isdigit():
            raise ValueError(f"invalid amount: {value!r}")
        frac = (frac + "00")[:2]
        cents = int(dollars) * 100 + int(frac)
    else:
        if not s.isdigit():
            raise ValueError(f"invalid amount: {value!r}")
        cents = int(s) * 100

    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not str(text).strip():
        return []

    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for record in reader:
        if record is None:
            continue
        customer = record.get("customer") or ""
        rows.append(
            {
                "id": str(record.get("id", "")),
                "customer": customer,
                "amount_cents": _parse_amount(record.get("amount", "")),
            }
        )
    return rows
