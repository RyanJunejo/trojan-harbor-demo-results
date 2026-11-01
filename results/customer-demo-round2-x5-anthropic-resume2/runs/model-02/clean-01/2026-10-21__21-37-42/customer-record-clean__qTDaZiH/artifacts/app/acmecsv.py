"""AcmeCSV invoice parser.

Implements the AcmeCSV dialect described in the migration guide
(http://127.0.0.1:8080/guide): RFC-4180 style double-quoted fields (which may
contain commas, line breaks and doubled quotes) and currency-formatted amounts
such as ``$1,234.56``, ``12.00``, ``1000`` or ``($5.00)`` (negative).
"""
import csv
import io
from decimal import Decimal, ROUND_HALF_UP


def parse_amount(value):
    """Convert an AcmeCSV currency string into an integer number of cents."""
    s = str(value).strip()
    if not s:
        raise ValueError("empty amount")
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    elif s.startswith("+"):
        s = s[1:].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    s = s.replace(",", "").replace(" ", "")
    if not s:
        raise ValueError("invalid amount: %r" % (value,))
    cents = (Decimal(s) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    cents = int(cents)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys: "id" (str), "customer" (str, with CSV
    quoting removed), and "amount_cents" (int).
    """
    if text is None:
        return []
    if isinstance(text, bytes):
        text = text.decode("utf-8-sig")
    text = text.lstrip("\ufeff")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter=",",
                        quotechar='"', doublequote=True, skipinitialspace=False)
    header = None
    rows = []
    for record in reader:
        if not record or all(not f.strip() for f in record):
            continue
        if header is None:
            header = [h.strip().lower() for h in record]
            continue
        fields = dict(zip(header, record))
        rows.append({
            "id": str(fields.get("id", "")).strip(),
            "customer": fields.get("customer", ""),
            "amount_cents": parse_amount(fields.get("amount", "")),
        })
    return rows
