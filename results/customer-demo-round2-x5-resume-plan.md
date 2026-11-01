# Round 2 ×5 — resume plan after Docker interruption (written 2026-10-21 ~10:15 UTC, before resuming)

At 10:09 UTC the Docker daemon was stopped by a tool background-task time limit. The trial in
progress (gpt-6-sol clean #1) became invalid, and the DeepSeek, xAI and Anthropic batches each
failed their first trial because Docker was down. None of the failed trials made an API request.

Rule, fixed before any resumed trial runs:

- A model keeps its interrupted-batch results only if all 10 of its trials completed validly:
  gpt-5.6-sol, gpt-5.6-terra, gpt-5.6-luna, gpt-6-astra (`customer-demo-round2-x5-openai/`).
- Every other model is rerun from scratch with an unchanged protocol (no-boundary, 5 trials per
  variant, seed 20261020, same ledger): gpt-6-sol, gpt-6-luna, gpt-6.1-sol, both DeepSeek models,
  all three Grok models, all four Claude models.
- gpt-6-sol's five valid interrupted-batch trials are reported separately and never pooled with
  its rerun. All interrupted-batch directories are preserved.
- Docker and the run chain are started detached so neither depends on a tool time limit.

## Second interruption (written 2026-10-21 ~21:20 UTC, before resuming)

The cloud VM shut down at 13:12 UTC during `customer-demo-round2-x5-anthropic-resume`
(Opus clean #4 in progress; no open ledger reservation). Same rule as above: Haiku and Sonnet
completed all 10 trials and are kept; Opus is rerun from scratch, and Fable is run in full, in
`customer-demo-round2-x5-anthropic-resume2`. Opus's 8 completed trials in the interrupted run are
reported separately and never pooled.
