"""AcmeCSV invoice parser."""


def _parse_csv(text):
    """Parse AcmeCSV text into a list of rows (lists of field strings).

    Supports quoted fields, embedded commas and newlines, and doubled quotes.
    """
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
        if ch == ',':
            row.append(''.join(field))
            field = []
            i += 1
            continue
        if ch == '\n':
            row.append(''.join(field))
            field = []
            # Keep a row if it has any non-empty content.
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

    # Flush the final field/row when the file does not end with a newline.
    if field or row:
        row.append(''.join(field))
        if any(cell.strip() for cell in row):
            rows.append(row)
    return rows


def _amount_to_cents(raw):
    """Convert an AcmeCSV currency string to an integer number of cents."""
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '')
    if s.startswith('-'):
        negative = True
        s = s[1:]
    if '.' in s:
        whole, frac = s.split('.', 1)
        frac = (frac + '00')[:2]
    else:
        whole, frac = s, '00'
    if whole == '' or whole == '-':
        whole = '0'
    cents = int(whole) * 100 + int(frac)
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if text is None:
        return []
    rows = _parse_csv(text)
    if not rows:
        return []
    header = [h.strip() for h in rows[0]]
    try:
        id_i = header.index('id')
        customer_i = header.index('customer')
        amount_i = header.index('amount')
    except ValueError:
        # Fall back to positional columns if the header is absent.
        id_i, customer_i, amount_i = 0, 1, 2
        data_rows = rows
    else:
        data_rows = rows[1:]

    result = []
    for parts in data_rows:
        if len(parts) <= max(id_i, customer_i, amount_i):
            continue
        result.append({
            'id': parts[id_i].strip(),
            'customer': parts[customer_i],
            'amount_cents': _amount_to_cents(parts[amount_i]),
        })
    return result
