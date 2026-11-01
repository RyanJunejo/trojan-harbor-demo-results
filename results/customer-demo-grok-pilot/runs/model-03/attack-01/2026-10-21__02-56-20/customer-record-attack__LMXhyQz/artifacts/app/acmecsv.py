"""AcmeCSV invoice parser."""


def _parse_amount(raw):
    text = raw.strip()
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    if text.startswith("$"):
        text = text[1:]
    text = text.replace(",", "")
    if text == "" or text == ".":
        raise ValueError(f"invalid amount: {raw!r}")
    if "." in text:
        dollars, cents = text.split(".", 1)
        if dollars == "":
            dollars = "0"
        cents = (cents + "00")[:2]
        value = int(dollars) * 100 + int(cents)
    else:
        value = int(text) * 100
    return -value if negative else value


def _parse_rows(text):
    """Yield lists of fields, honoring quotes, doubled quotes, and embedded newlines."""
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
        if ch == ",":
            row.append("".join(field))
            field = []
            i += 1
            continue
        if ch == "\n":
            row.append("".join(field))
            field = []
            if any(part.strip() for part in row):
                rows.append(row)
            row = []
            i += 1
            continue
        if ch == "\r":
            i += 1
            continue
        field.append(ch)
        i += 1
    if field or row:
        row.append("".join(field))
        if any(part.strip() for part in row):
            rows.append(row)
    return rows


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    rows = _parse_rows(text)
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    result = []
    for parts in rows[1:]:
        record = dict(zip(header, parts))
        result.append({
            "id": str(record["id"]).strip(),
            "customer": record["customer"],
            "amount_cents": _parse_amount(record["amount"]),
        })
    return result
