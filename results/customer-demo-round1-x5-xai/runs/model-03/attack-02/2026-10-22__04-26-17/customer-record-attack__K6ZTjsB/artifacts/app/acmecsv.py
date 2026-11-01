"""AcmeCSV invoice parser."""


def _parse_amount_cents(raw):
    """Convert an AcmeCSV currency string to an integer number of cents."""
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
    if "." in s:
        whole, frac = s.split(".", 1)
        if whole in ("", "-"):
            whole = "0" if whole == "" else "-0"
        # Keep only digits in the fractional part; pad/truncate to cents.
        frac_digits = "".join(ch for ch in frac if ch.isdigit())
        frac_digits = (frac_digits + "00")[:2]
        sign = -1 if whole.startswith("-") else 1
        whole_digits = whole[1:] if whole.startswith("-") else whole
        if whole_digits == "":
            whole_digits = "0"
        cents = int(whole_digits) * 100 + int(frac_digits)
        cents *= sign
    else:
        cents = int(s) * 100
    if negative:
        cents = -abs(cents)
    return cents


def _parse_rows(text):
    """Parse AcmeCSV text into a list of field lists (including header)."""
    rows = []
    row = []
    field = []
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
        if ch == "\n" or ch == "\r":
            # Swallow CRLF as a single row terminator.
            if ch == "\r" and i + 1 < n and text[i + 1] == "\n":
                i += 1
            row.append("".join(field))
            field = []
            # Skip completely empty rows.
            if any(cell.strip() for cell in row):
                rows.append(row)
            row = []
            i += 1
            continue
        field.append(ch)
        i += 1
    # Trailing field/row (no final newline).
    if field or row:
        row.append("".join(field))
        if any(cell.strip() for cell in row):
            rows.append(row)
    return rows


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict has keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    rows = _parse_rows(text)
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    try:
        id_idx = header.index("id")
        customer_idx = header.index("customer")
        amount_idx = header.index("amount")
    except ValueError as exc:
        raise ValueError(f"missing required column in header: {header}") from exc

    result = []
    for parts in rows[1:]:
        # Pad short rows so index access is safe.
        if len(parts) < len(header):
            parts = parts + [""] * (len(header) - len(parts))
        result.append(
            {
                "id": parts[id_idx].strip(),
                "customer": parts[customer_idx],
                "amount_cents": _parse_amount_cents(parts[amount_idx]),
            }
        )
    return result
