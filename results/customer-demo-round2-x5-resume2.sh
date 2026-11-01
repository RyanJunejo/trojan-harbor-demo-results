#!/bin/bash
cd /home/vercel-sandbox/trojan-harbor
echo "=== anthropic-resume2 start $(date -u +%H:%M)"
uv run --frozen python tools/customer_demo.py --trials 5 --execute --no-boundary --model anthropic/claude-opus-5-5 --model anthropic/claude-fable-5-1 --out .context/customer-demo-round2-x5-anthropic-resume2
echo "=== anthropic-resume2 exit $? $(date -u +%H:%M)"
echo "CHAIN DONE $(date -u +%H:%M)"
