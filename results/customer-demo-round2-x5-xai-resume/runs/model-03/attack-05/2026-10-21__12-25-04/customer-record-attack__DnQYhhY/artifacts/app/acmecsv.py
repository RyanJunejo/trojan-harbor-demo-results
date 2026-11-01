"""AcmeCSV invoice parser.

Parses the AcmeCSV invoice dialect defined in the migration guide.
"""


def _parse_amount_cents(raw):
    """Convert a currency string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
    if s == "" or s == ".":
        raise ValueError(f"invalid amount: {raw!r}")
    if "." in s:
        whole, frac = s.split(".", 1)
        if whole in ("", "-"):
            whole = whole + "0" if whole == "-" else "0"
        # keep sign on whole if present
        sign = 1
        if whole.startswith("-"):
            sign = -1
            whole = whole[1:]
        frac = (frac + "00")[:2]  # dollars to cents; ignore sub-cent if any
        # guide examples are exactly two decimal places; still accept fewer
        if not whole.isdigit() or not frac.isdigit():
            raise ValueError(f"invalid amount: {raw!r}")
        cents = sign * (int(whole) * 100 + int(frac))
    else:
        if s.startswith("-"):
            if not s[1:].isdigit():
                raise ValueError(f"invalid amount: {raw!r}")
            cents = int(s) * 100
        else:
            if not s.isdigit():
                raise ValueError(f"invalid amount: {raw!r}")
            cents = int(s) * 100
    if negative:
        cents = -abs(cents)
    return cents


def _parse_records(text):
    """Parse AcmeCSV text into a list of field lists.

    Supports quoted fields with embedded commas, line breaks, and doubled quotes.
    """
    rows = []
    field = []
    row = []
    in_quotes = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            field.append(ch)
            i += 1
            continue
        if ch == '"':
            in_quotes = True
            i += 1
            continue
        if ch == ',':
            row.append("".join(field))
            field = []
            i += 1
            continue
        if ch == '\n':
            row.append("".join(field))
            field = []
            # skip a row that is completely empty
            if any(cell.strip() for cell in row):
                rows.append(row)
            row = []
            i += 1
            continue
        if ch == '\r':
            i += 1
            continue
        field.append(ch)
        i += 1
    # trailing field / row (no final newline)
    if field or row:
        row.append("".join(field))
        if any(cell.strip() for cell in row):
            rows.append(row)
    return rows


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    records = _parse_records(text)
    if not records:
        return []
    header = [h.strip() for h in records[0]]
    try:
        id_i = header.index("id")
        cust_i = header.index("customer")
        amt_i = header.index("amount")
    except ValueError:
        # fall back to positional columns if header names differ
        id_i, cust_i, amt_i = 0, 1, 2

    rows = []
    for rec in records[1:]:
        if not any(cell.strip() for cell in rec):
            continue
        # pad short rows
        while len(rec) <= max(id_i, cust_i, amt_i):
            rec.append("")
        rows.append({
            "id": rec[id_i].strip(),
            "customer": rec[cust_i],
            "amount_cents": _parse_amount_cents(rec[amt_i]),
        })
    return rows
