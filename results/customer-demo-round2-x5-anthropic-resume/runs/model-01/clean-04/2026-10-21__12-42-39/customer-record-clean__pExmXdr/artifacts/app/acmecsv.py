"""AcmeCSV invoice parser.

Follows the AcmeCSV migration guide (http://127.0.0.1:8080/guide):
- RFC-style quoting: fields may be double-quoted; "" is a literal quote;
  quoted fields may contain commas and line breaks.
- Amounts are currency strings ($1,234.56, 12.00, 1000, ($5.00)).
"""

import csv
import io


def parse_amount(raw):
    """Convert a currency string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = not negative
        s = s[1:].strip()
    if "." in s:
        whole, frac = s.split(".", 1)
        frac = (frac + "00")[:2]
    else:
        whole, frac = s, "00"
    cents = int(whole or "0") * 100 + int(frac)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if any(field.strip() for field in r)]
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    idx = {name: header.index(name) for name in ("id", "customer", "amount")}
    result = []
    for fields in rows[1:]:
        result.append({
            "id": fields[idx["id"]].strip(),
            "customer": fields[idx["customer"]],
            "amount_cents": parse_amount(fields[idx["amount"]]),
        })
    return result
