"""AcmeCSV invoice parser.

Parses the AcmeCSV invoice dialect defined by the migration guide:
quoted fields, doubled quotes, and currency amounts as integer cents.
"""


def _parse_record(text, start):
    """Parse one CSV record starting at index start.

    Returns (fields, index_after_record). A record ends at an unquoted newline
    or at end of text. Quoted fields may contain commas and line breaks.
    """
    fields = []
    i = start
    n = len(text)
    while i <= n:
        if i >= n:
            fields.append("")
            return fields, i
        if text[i] == '"':
            i += 1
            buf = []
            while i < n:
                if text[i] == '"':
                    if i + 1 < n and text[i + 1] == '"':
                        buf.append('"')
                        i += 2
                        continue
                    i += 1
                    break
                buf.append(text[i])
                i += 1
            fields.append("".join(buf))
            if i < n and text[i] == ",":
                i += 1
                continue
            # end of record: consume one newline (CRLF or LF)
            if i < n and text[i] == "\r":
                i += 1
            if i < n and text[i] == "\n":
                i += 1
            return fields, i
        else:
            buf = []
            while i < n and text[i] not in ",\n\r":
                buf.append(text[i])
                i += 1
            fields.append("".join(buf))
            if i < n and text[i] == ",":
                i += 1
                continue
            if i < n and text[i] == "\r":
                i += 1
            if i < n and text[i] == "\n":
                i += 1
            return fields, i
    return fields, i


def _parse_rows(text):
    """Yield field lists for every non-empty record in text."""
    i = 0
    n = len(text)
    while i < n:
        # skip blank lines between records
        if text[i] in "\r\n":
            i += 1
            continue
        fields, i = _parse_record(text, i)
        if any(f.strip() for f in fields):
            yield fields


def _amount_to_cents(raw):
    """Convert an AcmeCSV amount string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()
    if s.startswith("$"):
        s = s[1:]
    s = s.replace(",", "").strip()
    if s == "" or s == "-":
        raise ValueError(f"invalid amount: {raw!r}")
    if s.startswith("-"):
        negative = not negative
        s = s[1:]
    if "." in s:
        whole, frac = s.split(".", 1)
        if whole == "":
            whole = "0"
        # currency amounts use two decimal places; keep only digits
        frac_digits = "".join(ch for ch in frac if ch.isdigit())
        if len(frac_digits) == 0:
            cents = int(whole) * 100
        elif len(frac_digits) == 1:
            cents = int(whole) * 100 + int(frac_digits) * 10
        else:
            cents = int(whole) * 100 + int(frac_digits[:2])
            # round half-up on additional digits if present
            if len(frac_digits) > 2 and frac_digits[2] >= "5":
                cents += 1
    else:
        cents = int(s) * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    records = list(_parse_rows(text))
    if not records:
        return []
    header = [h.strip() for h in records[0]]
    rows = []
    for fields in records[1:]:
        # pad short rows so zip still works
        if len(fields) < len(header):
            fields = fields + [""] * (len(header) - len(fields))
        record = dict(zip(header, fields))
        amount = record.pop("amount", "")
        rows.append(
            {
                "id": str(record.get("id", "")),
                "customer": record.get("customer", ""),
                "amount_cents": _amount_to_cents(amount),
            }
        )
    return rows
