"""Parse invoices using the AcmeCSV migration guide's CSV dialect."""

import csv
from decimal import Decimal
from io import StringIO


def parse(text):
    """Return invoice rows with id, unquoted customer, and amount_cents."""
    rows = []
    # newline='' lets csv handle embedded line breaks in quoted fields.
    reader = csv.reader(StringIO(text, newline=''))
    header = None
    for fields in reader:
        if not fields or (len(fields) == 1 and not fields[0].strip()):
            continue
        if header is None:
            header = fields
            continue

        record = dict(zip(header, fields))
        amount = record['amount'].strip()
        negative = amount.startswith('(') and amount.endswith(')')
        if negative:
            amount = amount[1:-1].strip()
        if amount.startswith('$'):
            amount = amount[1:]
        cents = Decimal(amount.replace(',', '')) * 100
        if negative:
            cents = -cents
        rows.append({
            'id': record['id'],
            'customer': record['customer'],
            'amount_cents': int(cents),
        })
    return rows
