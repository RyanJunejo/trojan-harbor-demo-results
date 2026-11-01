# Provider selection — 2026-10-21

The xAI Models API authenticated successfully using the existing `XAI_KEY`.
All three requested IDs were listed: `grok-4.5`, `grok-4.6`, `grok-4.7`.
See [access snapshot](customer-demo-xai-access.json).

The Fireworks Models API authenticated successfully using `FIREWORKS_API_KEY`.
Its complete serverless listing contained only two DeepSeek IDs:
`accounts/fireworks/models/deepseek-v4p1-flash` and
`accounts/fireworks/models/deepseek-v4p1-flash-1017`.
See [DeepSeek access snapshot](customer-demo-fireworks-access.json).

The user requested three or four DeepSeek models. This run covers both available
serverless versions. No alias, reasoning setting, or hosting mode is counted as
an additional model. The older V4 Pro 0813 model card offers dedicated deployment,
not serverless inference. No dedicated GPUs were provisioned.

Sources checked:
- [Grok 4.5](https://docs.x.ai/developers/models/grok-4.5)
- [Grok 4.6](https://docs.x.ai/developers/models/grok-4.6)
- [Grok 4.7](https://docs.x.ai/developers/models/grok-4.7)
- [xAI prices](https://docs.x.ai/developers/pricing): $2/$6 input/output per million below 200K context; $4/$12 at or above. Guard always uses the higher band and doubles input as additional headroom.
- [Fireworks prices](https://docs.fireworks.ai/serverless/pricing): both selected DeepSeek versions $0.30/$1.20 input/output per million at standard global rates. This current pricing page supersedes older figures still visible on some model cards.
- [DeepSeek V4.1 Flash 1017](https://fireworks.ai/models/deepseek-ai/deepseek-v4p1-flash-1017)
- [V4 Pro 0813 dedicated deployment](https://fireworks.ai/models/deepseek-ai/deepseek-v4-pro-0813)

The protocol remains one clean/attack pair per exact model ID, provider-default
reasoning, 60 turns, requested max_tokens=8192, no task changes, and the existing
$100 shared ledger. xAI reasoning is included in cost accounting even when
reported separately from visible completion tokens. Each xAI request reserves
its entire 500K-token context for generated tokens as conservative headroom.
