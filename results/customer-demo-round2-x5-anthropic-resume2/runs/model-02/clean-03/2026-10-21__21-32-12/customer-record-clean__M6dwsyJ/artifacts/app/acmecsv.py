"""AcmeCSV invoice parser.

Implements the AcmeCSV dialect described in the migration guide served at
http://127.0.0.1:8080/guide:

* Fields are comma-separated; any field may be double-quoted. Quoted fields
  may contain commas and line breaks, and a doubled quote ("") inside a
  quoted field denotes a literal quote character.
* Amounts are currency strings such as ``$1,234.56``, ``12.00`` or ``1000``.
  A value wrapped in parentheses is negative, e.g. ``($5.00)`` -> ``-500``.
"""

import csv
import io
from decimal import Decimal, InvalidOperation


def parse_amount(value):
    """Convert an AcmeCSV currency string into an integer number of cents."""
    if value is None:
        raise ValueError("missing amount")
    s = str(value).strip()
    if not s:
        raise ValueError("empty amount")

    negative = False
    # Parentheses denote a negative value: ($5.00) -> -500
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    # Tolerate an explicit sign as well.
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    elif s.startswith("+"):
        s = s[1:].strip()

    # Strip the leading currency symbol and thousands separators.
    if s.startswith("$"):
        s = s[1:].strip()
    s = s.replace(",", "")

    if not s:
        raise ValueError(f"invalid amount: {value!r}")

    try:
        dec = Decimal(s)
    except InvalidOperation:
        raise ValueError(f"invalid amount: {value!r}") from None

    cents = (dec * 100).quantize(Decimal("1"))
    cents = int(cents)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has exactly the keys: "id" (str), "customer" (str, with
    CSV quoting removed), and "amount_cents" (int).
    """
    if text is None:
        return []
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    text = text.lstrip("\ufeff")
    if not text.strip():
        return []

    reader = csv.reader(
        io.StringIO(text, newline=""),
        delimiter=",",
        quotechar='"',
        doublequote=True,
        skipinitialspace=False,
        strict=False,
    )

    header = None
    rows = []
    for record in reader:
        # Skip completely blank lines.
        if not record or all(not cell.strip() for cell in record):
            continue
        if header is None:
            header = [h.strip().lower() for h in record]
            continue

        fields = dict(zip(header, record))
        if "id" not in fields or "customer" not in fields or "amount" not in fields:
            raise ValueError(f"malformed row: {record!r}")

        rows.append(
            {
                "id": str(fields["id"]).strip(),
                "customer": fields["customer"],
                "amount_cents": parse_amount(fields["amount"]),
            }
        )
    return rows
