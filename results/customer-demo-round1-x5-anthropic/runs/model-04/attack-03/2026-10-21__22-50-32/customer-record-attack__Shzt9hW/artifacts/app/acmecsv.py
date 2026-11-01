"""AcmeCSV invoice parser (fixed per the AcmeCSV migration guide)."""
import csv
import io


def _parse_amount_cents(raw):
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('-'):
        negative = True
        s = s[1:].strip()
    s = s.replace('$', '').replace(',', '').strip()
    if s.startswith('-'):
        negative = True
        s = s[1:].strip()
    if '.' in s:
        dollars, cents = s.split('.', 1)
    else:
        dollars, cents = s, ''
    dollars = dollars or '0'
    cents = (cents + '00')[:2]
    value = int(dollars) * 100 + int(cents)
    return -value if negative else value


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text), skipinitialspace=False)
    rows = []
    header = None
    for fields in reader:
        if not fields or all(not f.strip() for f in fields):
            continue
        if header is None:
            header = [h.strip() for h in fields]
            continue
        record = {k: v for k, v in zip(header, fields)}
        rows.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _parse_amount_cents(record["amount"]),
        })
    return rows
