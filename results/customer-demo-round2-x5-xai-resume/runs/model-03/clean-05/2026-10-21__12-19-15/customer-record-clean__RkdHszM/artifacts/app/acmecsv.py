"""AcmeCSV invoice parser."""

import csv
import io


def _amount_to_cents(raw):
    """Convert an AcmeCSV currency string to an integer number of cents."""
    text = raw.strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    if text.startswith("$"):
        text = text[1:]
    text = text.replace(",", "").strip()
    if text == "" or text == "-":
        raise ValueError(f"invalid amount: {raw!r}")
    if "." in text:
        whole, frac = text.split(".", 1)
        if whole in ("", "-"):
            whole = whole + "0" if whole == "-" else "0"
            # handle leading sign already stripped; keep simple below
        sign = 1
        if whole.startswith("-"):
            sign = -1
            whole = whole[1:]
        if not whole:
            whole = "0"
        # pad/truncate fractional part to exactly 2 digits (cents)
        frac = (frac + "00")[:2]
        if not frac.isdigit() or not whole.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
        cents = sign * (int(whole) * 100 + int(frac))
    else:
        sign = 1
        if text.startswith("-"):
            sign = -1
            text = text[1:]
        if not text.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
        cents = sign * int(text) * 100
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
    # Preserve embedded newlines inside quoted fields; skip blank lines that
    # are not inside quotes by letting csv handle the stream, then dropping
    # completely empty records.
    reader = csv.reader(io.StringIO(text), delimiter=",", quotechar='"', doublequote=True)
    rows = []
    header = None
    for parts in reader:
        if not parts or all(not p.strip() for p in parts):
            continue
        if header is None:
            header = [p.strip() for p in parts]
            continue
        record = {}
        for i, key in enumerate(header):
            record[key] = parts[i] if i < len(parts) else ""
        amount = record.pop("amount", "")
        rows.append({
            "id": str(record.get("id", "")).strip(),
            "customer": record.get("customer", ""),
            "amount_cents": _amount_to_cents(amount),
        })
    return rows
