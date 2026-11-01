"""AcmeCSV invoice parser, following the AcmeCSV migration guide."""
import csv
import io


def _amount_to_cents(raw):
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    s = s.replace("$", "").replace(",", "").strip()
    if s.startswith("-"):
        negative = True
        s = s[1:].strip()
    if "." in s:
        whole, frac = s.split(".", 1)
    else:
        whole, frac = s, ""
    frac = (frac + "00")[:2]
    cents = int(whole or "0") * 100 + int(frac or "0")
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    reader = csv.reader(io.StringIO(text, newline=""))
    header = None
    rows = []
    for fields in reader:
        if not fields or all(not f.strip() for f in fields):
            continue
        if header is None:
            header = [h.strip() for h in fields]
            continue
        record = dict(zip(header, fields))
        rows.append({
            "id": record["id"].strip(),
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return rows
