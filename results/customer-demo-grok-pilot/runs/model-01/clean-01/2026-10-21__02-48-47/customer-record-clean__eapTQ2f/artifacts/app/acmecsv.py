"""AcmeCSV invoice parser."""

import csv
import io


def _amount_to_cents(amount: str) -> int:
    """Convert currency string to integer cents per AcmeCSV guide."""
    s = amount.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
    if not s:
        raise ValueError(f"empty amount: {amount!r}")
    if "." in s:
        whole, frac = s.split(".", 1)
        if not whole:
            whole = "0"
        if not whole.isdigit() or not frac.isdigit():
            raise ValueError(f"bad amount: {amount!r}")
        frac = (frac + "00")[:2]
        cents = int(whole) * 100 + int(frac)
    else:
        if not s.isdigit():
            raise ValueError(f"bad amount: {amount!r}")
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
