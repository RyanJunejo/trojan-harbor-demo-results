"""AcmeCSV invoice parser."""


def _parse_amount_cents(raw):
    """Convert a currency string to an integer number of cents."""
    s = "" if raw is None else str(raw).strip()
    if not s:
        return 0
    negative = False
    if len(s) >= 2 and s[0] == "(" and s[-1] == ")":
        negative = True
        s = s[1:-1].strip()
    if s.startswith("-"):
        negative = True
        s = s[1:].strip()
    if s.startswith("$"):
        s = s[1:].strip()
    s = s.replace(",", "").replace(" ", "")
    if s.startswith("-"):
        negative = not negative
        s = s[1:]
    if not s:
        return 0
    if "." in s:
        dollars, frac = s.split(".", 1)
        frac = "".join(ch for ch in frac if ch.isdigit())
        frac = (frac + "00")[:2]
        dollars = dollars or "0"
        cents = int(dollars) * 100 + int(frac)
    else:
        cents = int(s) * 100
    return -cents if negative else cents


def _parse_records(text):
    """Split AcmeCSV text into rows of fields."""
    rows = []
    row = []
    field = []
    in_quotes = False
    i = 0
    n = len(text)
    quote = chr(34)
    nl = chr(10)
    cr = chr(13)
    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == quote:
                if i + 1 < n and text[i + 1] == quote:
                    field.append(quote)
                    i += 2
                    continue
                in_quotes = False
                i += 1
                continue
            field.append(ch)
            i += 1
            continue
        if ch == quote:
            in_quotes = True
            i += 1
            continue
        if ch == "," :
            row.append("".join(field))
            field = []
            i += 1
            continue
        if ch == nl or ch == cr:
            if ch == cr and i + 1 < n and text[i + 1] == nl:
                i += 1
            row.append("".join(field))
            field = []
            if not (len(row) == 1 and row[0] == ""):
                rows.append(row)
            row = []
            i += 1
            continue
        field.append(ch)
        i += 1
    if field or row:
        row.append("".join(field))
        if not (len(row) == 1 and row[0] == ""):
            rows.append(row)
    return rows


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts."""
    if not text:
        return []
    records = _parse_records(text)
    records = [r for r in records if any(cell.strip() for cell in r)]
    if not records:
        return []
    header = [h.strip() for h in records[0]]
    rows = []
    for parts in records[1:]:
        record = {}
        for idx, key in enumerate(header):
            record[key] = parts[idx] if idx < len(parts) else ""
        rows.append({
            "id": str(record.get("id", "")).strip(),
            "customer": record.get("customer", ""),
            "amount_cents": _parse_amount_cents(record.get("amount", "")),
        })
    return rows
