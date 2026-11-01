#!/bin/bash
cd /home/vercel-sandbox/trojan-harbor
run() { echo "=== $1 start $(date -u +%H:%M)"; uv run --frozen python tools/customer_demo.py --trials 5 --execute $2 --out .context/customer-demo-round1-x5-$1; echo "=== $1 exit $? $(date -u +%H:%M)"; }
run anthropic "--model anthropic/claude-fable-5-1 --model anthropic/claude-opus-5-5 --model anthropic/claude-sonnet-5-5 --model anthropic/claude-haiku-5-5"
run openai "--model openai/gpt-6-astra --model openai/gpt-5.6-sol --model openai/gpt-5.6-terra --model openai/gpt-5.6-luna --model openai/gpt-6-sol --model openai/gpt-6-luna --model openai/gpt-6.1-sol"
run deepseek "--model fireworks_ai/accounts/fireworks/models/deepseek-v4p1-flash --model fireworks_ai/accounts/fireworks/models/deepseek-v4p1-flash-1017"
run xai "--model xai/grok-4.5 --model xai/grok-4.6 --model xai/grok-4.7"
echo "CHAIN DONE $(date -u +%H:%M)"
