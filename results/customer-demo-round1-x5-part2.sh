#!/bin/bash
cd /home/vercel-sandbox/trojan-harbor
while kill -0 342389 2>/dev/null; do sleep 20; done
echo "=== deepseek runner finished $(date -u +%H:%M)"
keyok() { python3 - <<'PY'
import urllib.request, urllib.error
from pathlib import Path
p = Path.home() / '.openai_key'
try:
    k = p.read_text().strip()
    with urllib.request.urlopen(urllib.request.Request('https://api.openai.com/v1/models', headers={'Authorization': 'Bearer ' + k}), timeout=30) as r:
        raise SystemExit(0 if r.status == 200 else 1)
except (OSError, urllib.error.URLError):
    raise SystemExit(1)
PY
}
until [ -s "$HOME/.openai_key" ] && keyok; do sleep 30; done
echo "=== openai-newkey start $(date -u +%H:%M) (new key verified)"
OPENAI_API_KEY="$(cat "$HOME/.openai_key")" uv run --frozen python tools/customer_demo.py --trials 5 --execute \
  --model openai/gpt-6-astra --model openai/gpt-5.6-sol --model openai/gpt-5.6-terra --model openai/gpt-5.6-luna \
  --model openai/gpt-6-sol --model openai/gpt-6-luna --model openai/gpt-6.1-sol \
  --out .context/customer-demo-round1-x5-openai-newkey
rc=$?; echo "=== openai-newkey exit $rc $(date -u +%H:%M)"
if [ $rc -eq 0 ]; then shred -u "$HOME/.openai_key" 2>/dev/null || rm -f "$HOME/.openai_key"; echo "=== key file deleted"; else echo "=== key file kept for rerun"; fi
echo "=== xai start $(date -u +%H:%M)"
uv run --frozen python tools/customer_demo.py --trials 5 --execute --model xai/grok-4.5 --model xai/grok-4.6 --model xai/grok-4.7 --out .context/customer-demo-round1-x5-xai
echo "=== xai exit $? $(date -u +%H:%M)"
echo "CHAIN DONE $(date -u +%H:%M)"
