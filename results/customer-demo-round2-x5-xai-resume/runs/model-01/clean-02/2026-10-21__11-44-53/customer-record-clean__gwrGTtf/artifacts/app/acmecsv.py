"""AcmeCSV invoice parser.

Parses AcmeCSV invoice text per the migration guide at
http://127.0.0.1:8080/guide.
"""


def _parse_fields(line):
    """Split one CSV line into fields, honoring double-quoted values."""
    fields = []
    i = 0
    n = len(line)
    while i < n:
        if line[i] == '"':
            # Quoted field: consume until closing quote ("" -> literal ").
            i += 1
            buf = []
            while i < n:
                if line[i] == '"':
                    if i + 1 < n and line[i + 1] == '"':
                        buf.append('"')
                        i += 2
                    else:
                        i += 1  # closing quote
                        break
                else:
                    buf.append(line[i])
                    i += 1
            fields.append(''.join(buf))
            if i < n and line[i] == ',':
                i += 1
            elif i < n and line[i] == '\r':
                i += 1
        else:
            # Unquoted field: read until comma or end.
            start = i
            while i < n and line[i] != ',':
                i += 1
            fields.append(line[start:i])
            if i < n and line[i] == ',':
                i += 1
    # Trailing comma => empty final field
    if line.endswith(','):
        fields.append('')
    return fields


def _parse_amount_cents(raw):
    """Convert currency string to integer cents."""
    s = raw.strip()
    negative = False
    if s.startswith('(') and s.endswith(')'):
        negative = True
        s = s[1:-1].strip()
    if s.startswith('$'):
        s = s[1:]
    s = s.replace(',', '').strip()
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
    # Support quoted fields that may contain line breaks by scanning the
    # full text rather than splitting on newlines first.
    rows_fields = []
    i = 0
    n = len(text)
    current = []
    field_buf = []
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
                current.append(''.join(field_buf))
                field_buf = []
                i += 1
                continue
            if ch == '\n' or (ch == '\r' and (i + 1 >= n or text[i + 1] != '\n')):
                current.append(''.join(field_buf))
                field_buf = []
                # skip blank lines
                if any(part.strip() for part in current):
                    rows_fields.append(current)
                current = []
                i += 1
                continue
            if ch == '\r':
                # part of \r\n — treat on \n
                i += 1
                continue
            field_buf.append(ch)
            i += 1
            continue

    # final field/row if file does not end with newline
    if field_buf or current:
        current.append(''.join(field_buf))
        if any(part.strip() for part in current):
            rows_fields.append(current)

    if not rows_fields:
        return []

    header = rows_fields[0]
    result = []
    for parts in rows_fields[1:]:
        # pad/truncate to header length defensively
        if len(parts) < len(header):
            parts = parts + [''] * (len(header) - len(parts))
        record = {header[j]: parts[j] for j in range(len(header))}
        amount_raw = record.pop('amount', '0')
        out = {
            'id': str(record.get('id', '')),
            'customer': record.get('customer', ''),
            'amount_cents': _parse_amount_cents(amount_raw),
        }
        result.append(out)
    return result
