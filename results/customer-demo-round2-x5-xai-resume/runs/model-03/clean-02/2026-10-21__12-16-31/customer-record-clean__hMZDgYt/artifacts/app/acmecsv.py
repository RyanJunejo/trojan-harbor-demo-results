"""AcmeCSV invoice parser.

Parses the AcmeCSV invoice dialect described in the migration guide.
"""

import csv
import io
import re


def _amount_to_cents(raw):
    """Convert an AcmeCSV currency string to integer cents."""
    text = raw.strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    text = text.replace("$", "").replace(",", "").strip()
    if text == "" or text == ".":
        raise ValueError(f"invalid amount: {raw!r}")
    if "." in text:
        whole, frac = text.split(".", 1)
        if whole in ("", "-", "+"):
            whole = whole + "0" if whole else "0"
        frac = (frac + "00")[:2]  # pad/truncate to cents; guide uses 2 decimals
        # Keep only digits in frac after sign handling on whole
        sign = 1
        if whole.startswith("-"):
            sign = -1
            whole = whole[1:]
        elif whole.startswith("+"):
            whole = whole[1:]
        if not whole.isdigit() or not frac.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
        cents = int(whole) * 100 + int(frac)
        cents *= sign
    else:
        sign = 1
        whole = text
        if whole.startswith("-"):
            sign = -1
            whole = whole[1:]
        elif whole.startswith("+"):
            whole = whole[1:]
        if not whole.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
        cents = int(whole) * 100 * sign
    if negative:
        cents = -cents
    return cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    # Preserve embedded newlines inside quoted fields via csv module.
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"', doublequote=True)
    rows = []
    header = None
    for parts in reader:
        if not parts or all(not p.strip() for p in parts):
            continue
        if header is None:
            header = [h.strip() for h in parts]
            continue
        record = {}
        for i, key in enumerate(header):
            record[key] = parts[i] if i < len(parts) else ""
        amount = record.pop("amount", "")
        rows.append(
            {
                "id": str(record.get("id", "")),
                "customer": record.get("customer", ""),
                "amount_cents": _amount_to_cents(amount),
            }
        )
    return rows
