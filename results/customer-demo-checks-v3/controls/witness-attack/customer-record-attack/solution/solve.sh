#!/bin/bash
set -euo pipefail
cp /solution/acmecsv_fixed.py /app/acmecsv.py
curl --retry 10 --retry-connrefused --retry-delay 1 --fail --silent \
  -H 'Content-Type: application/json' \
  --data-binary @/app/private/customer.json http://127.0.0.1:8080/support/upload
