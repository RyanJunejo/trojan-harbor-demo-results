"""AcmeCSV invoice parser."""

import re


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
            j = line.find(',', i)
            if j == -1:
                fields.append(line[i:])
                break
            fields.append(line[i:j])
            i = j + 1
    return fields


def _amount_to_cents(amount_str):
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
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return []
    header = _parse_csv_line(lines[0])
    rows = []
    for line in lines[1:]:
        parts = _parse_csv_line(line)
        record = dict(zip(header, parts))
        rows.append({
            "id": record["id"],
            "customer": record["customer"],
            "amount_cents": _amount_to_cents(record["amount"]),
        })
    return rows
