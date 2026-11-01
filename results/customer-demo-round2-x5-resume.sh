#!/bin/bash
cd /home/vercel-sandbox/trojan-harbor
run() { echo "=== $1 start $(date -u +%H:%M)"; uv run --frozen python tools/customer_demo.py --trials 5 --execute --no-boundary $2 --out .context/customer-demo-round2-x5-$1; echo "=== $1 exit $? $(date -u +%H:%M)"; }
run openai-resume "--model openai/gpt-6-sol --model openai/gpt-6-luna --model openai/gpt-6.1-sol"
run deepseek-resume "--model fireworks_ai/accounts/fireworks/models/deepseek-v4p1-flash --model fireworks_ai/accounts/fireworks/models/deepseek-v4p1-flash-1017"
run xai-resume "--model xai/grok-4.5 --model xai/grok-4.6 --model xai/grok-4.7"
run anthropic-resume "--claude-suite"
echo "CHAIN DONE $(date -u +%H:%M)"
