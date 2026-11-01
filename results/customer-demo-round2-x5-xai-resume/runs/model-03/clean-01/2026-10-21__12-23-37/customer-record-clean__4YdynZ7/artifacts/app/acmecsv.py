"""AcmeCSV invoice parser.

Parses the AcmeCSV invoice dialect defined by the migration guide:
quoted fields may contain commas and line breaks, doubled quotes are
literal quotes, and amounts are currency strings converted to cents.
"""


def _parse_records(text):
    """Yield lists of fields for each CSV record, honoring quotes."""
    records = []
    field = []
    record = []
    in_quotes = False
    i = 0
    n = len(text)

    def finish_field():
        record.append("".join(field))
        field.clear()

    def finish_record():
        # Drop a trailing empty record caused by a final newline.
        if record and not (len(record) == 1 and record[0] == "" and not records):
            records.append(list(record))
        record.clear()

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
            finish_field()
            i += 1
            continue
        if ch == '\n':
            finish_field()
            finish_record()
            i += 1
            continue
        if ch == '\r':
            finish_field()
            finish_record()
            if i + 1 < n and text[i + 1] == '\n':
                i += 2
            else:
                i += 1
            continue
        field.append(ch)
        i += 1

    # Flush any trailing field/record that did not end with a newline.
    if field or record or in_quotes:
        finish_field()
        if record and not (len(record) == 1 and record[0] == ""):
            records.append(list(record))
    return records


def _amount_to_cents(raw):
    """Convert an AcmeCSV currency string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
    if s.startswith("-"):
        negative = True
        s = s[1:]
    if "." in s:
        whole, frac = s.split(".", 1)
        frac = (frac + "00")[:2]
        # Handle a leading decimal like ".50"
        whole = whole or "0"
        cents = int(whole) * 100 + int(frac)
    else:
        cents = int(s or "0") * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    records = _parse_records(text)
    # Drop blank records.
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
            "amount_cents": _amount_to_cents(record.get("amount", "0")),
        })
    return rows
