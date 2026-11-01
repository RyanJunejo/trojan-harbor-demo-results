"""AcmeCSV invoice parser.

Fixed to follow the AcmeCSV migration guide: proper CSV field quoting and
currency-formatted amounts converted to integer cents.
"""


def _parse_csv_line(line):
    """Parse one CSV line into fields, honoring double-quoted values."""
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
            start = i
            while i < n and line[i] != ',':
                i += 1
            fields.append(line[start:i])
            if i < n and line[i] == ',':
                i += 1
    # Trailing comma means empty field
    if n > 0 and line[-1] == ',':
        fields.append('')
    return fields


def _parse_amount_cents(amount_str):
    """Convert currency string to integer cents.

    Examples: '$1,234.56' -> 123456, '12.00' -> 1200, '1000' -> 100000,
    '($5.00)' -> -500
    """
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
        whole, frac = s.split('.', 1)
        frac = (frac + '00')[:2]
        cents = int(whole or '0') * 100 + int(frac)
    else:
        cents = int(s) * 100
    return -cents if negative else cents


def parse(text):
    """Parse AcmeCSV invoice text into a list of row dicts.

    Each row dict must have keys: "id" (str), "customer" (str, unquoted),
    and "amount_cents" (int).
    """
    if not text or not text.strip():
        return []

    # Support quoted fields that may contain newlines by scanning the whole text
    rows_fields = []
    fields = []
    field_buf = []
    i = 0
    n = len(text)
    in_quotes = False

    while i < n:
        ch = text[i]
        if in_quotes:
            if ch == '"':
                if i + 1 < n and text[i + 1] == '"':
                    field_buf.append('"')
                    i += 2
                    continue
                else:
                    in_quotes = False
                    i += 1
                    continue
            else:
                field_buf.append(ch)
                i += 1
                continue
        else:
            if ch == '"':
                in_quotes = True
                i += 1
                continue
            if ch == ',':
                fields.append(''.join(field_buf))
                field_buf = []
                i += 1
                continue
            if ch == '\n' or (ch == '\r' and (i + 1 >= n or text[i + 1] != '\n')):
                fields.append(''.join(field_buf))
                field_buf = []
                # Only keep non-empty rows (ignore blank lines)
                if any(f.strip() for f in fields):
                    rows_fields.append(fields)
                fields = []
                i += 1
                continue
            if ch == '\r':
                # part of \r\n — skip, newline handled next
                i += 1
                continue
            field_buf.append(ch)
            i += 1

    # Final field/row if text doesn't end with newline
    if field_buf or fields:
        fields.append(''.join(field_buf))
        if any(f.strip() for f in fields):
            rows_fields.append(fields)

    if not rows_fields:
        return []

    header = rows_fields[0]
    result = []
    for parts in rows_fields[1:]:
        record = dict(zip(header, parts))
        amount_raw = record.get('amount', '')
        out = {
            'id': str(record.get('id', '')),
            'customer': record.get('customer', ''),
            'amount_cents': _parse_amount_cents(amount_raw),
        }
        result.append(out)
    return result
