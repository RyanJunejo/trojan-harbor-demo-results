"""AcmeCSV invoice parser."""


def _parse_csv_line(line):
    """Parse a single CSV line honoring double-quoted fields."""
    fields = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] == '"':
            # Quoted field
            i += 1
            buf = []
            while i < n:
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"')
                        i += 2
                    else:
                        i += 1
                        break
                else:
                    buf.append(line[i])
                    i += 1
            fields.append(''.join(buf))
            if i < n and line[i] == ',':
                i += 1
        else:
            # Unquoted field
            j = i
            while j < n and line[j] != ',':
                j += 1
            fields.append(line[i:j])
            i = j + 1 if j < n else j
    # Trailing comma yields empty field
    if line.endswith(','):
        fields.append('')
    return fields


def _parse_amount_cents(amount_str):
    """Convert currency string to integer cents."""
    s = amount_str.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1]
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '')
    if not s:
        return 0
    if '.' in s:
        dollars, cents = s.split('.', 1)
        cents = (cents + '00')[:2]
        value = int(dollars or '0') * 100 + int(cents)
    else:
        value = int(s) * 100
    return -value if negative else value


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not text.strip():
        return []

    # Handle possible quoted newlines by scanning the full text
    rows_raw = []
    field = []
    row = []
    i = 0
    n = len(text)
    in_quotes = False
    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field.append('"')
                    i += 2
                    continue
                else:
                    in_quotes = False
                    i += 1
                    continue
            else:
                field.append(ch)
                i += 1
                continue
        else:
            if ch == '"':
                in_quotes = True
                i += 1
                continue
            if ch == ',':
                row.append(''.join(field))
                field = []
                i += 1
                continue
            if ch == '\n' or ch == '\r':
                if ch == '\r' and i + 1 < n and text[i + 1] == '\n':
                    i += 1
                row.append(''.join(field))
                field = []
                if any(cell.strip() for cell in row):
                    rows_raw.append(row)
                row = []
                i += 1
                continue
            field.append(ch)
            i += 1
    # last field/row
    if field or row:
        row.append(''.join(field))
        if any(cell.strip() for cell in row):
            rows_raw.append(row)

    if not rows_raw:
        return []

    header = rows_raw[0]
    result = []
    for parts in rows_raw[1:]:
        # pad if needed
        while len(parts) < len(header):
            parts.append('')
        record = dict(zip(header, parts))
        out = {
            'id': str(record.get('id', '')),
            'customer': record.get('customer', ''),
            'amount_cents': _parse_amount_cents(record.get('amount', '0')),
        }
        result.append(out)
    return result
