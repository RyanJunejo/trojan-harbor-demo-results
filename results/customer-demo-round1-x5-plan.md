# Round 1 ×5 (with the confidentiality sentence) — plan, written 2026-10-21 ~22:00 UTC before launch

Purpose: repeat the default (with-sentence) variant five times per model, matching the
without-sentence repeats, so both conditions have five clean and five attack trials per model.

- Models: the same 16 as Round 2 ×5.
- Protocol: default variant (no `--no-boundary`), `--trials 5`, seed 20261020, same budget ledger,
  same runner code and agent settings as Round 2 ×5.
- Batches, in order: Anthropic (Fable, Opus, Sonnet, Haiku), OpenAI (GPT-6 Astra first, then
  GPT-5.6 Sol/Terra/Luna, GPT-6 Sol/Luna, GPT-6.1 Sol), DeepSeek, xAI. Order only affects timing;
  the two models with ~$40.6 worst-case reservations run while ledger headroom is largest.
- Interruption rule (same as Round 2): a model's results count only if all 10 of its trials
  completed in one batch; any incomplete model is rerun from scratch, and its partial trials are
  reported separately and never pooled.
- Docker and the run chain are started detached.

## Change of batch order (written 23:07 UTC)

The OpenAI batch was blocked at its free preflight (HTTP 401: the key was revoked during a
security incident; no paid requests). To keep GPT-6 Astra's ~$40.6 reservation inside the $100
ledger, the chain was stopped after launching DeepSeek; OpenAI (with the replacement key) will run
before xAI. Protocol, models, and seed are unchanged.
