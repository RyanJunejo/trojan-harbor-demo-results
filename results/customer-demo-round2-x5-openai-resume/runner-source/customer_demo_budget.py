"""Conservative, persistent spending guard for the customer demo's API runs.

All amounts are integer microdollars. Reservations cover twice the documented
1M context, the most expensive cache-write rate, and the entire output allowance.
Settlements intentionally overcount input (including cache hits). Unknown
outcomes retain their reservation and stop further requests.
"""
import fcntl
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

MAX_BUDGET_USD = 100
MAX_OUTPUT_TOKENS = 8192
INPUT_RESERVATION_TOKENS = 2_000_000
PRICING_CHECKED = "2026-10-21"
PRICING_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
PRICING_SOURCES = {
    "anthropic": PRICING_SOURCE,
    "xai": "https://docs.x.ai/developers/pricing",
    "fireworks_ai": "https://docs.fireworks.ai/serverless/pricing",
    "openai": "https://developers.openai.com/api/docs/pricing",
}
# USD / million tokens. Haiku uses its higher long-context rate even for short
# prompts; input is charged at twice these rates to cover 1h cache creation.
RATES = {
    "anthropic/claude-haiku-5-5": (Decimal("0.50"), Decimal("2.50")),
    "anthropic/claude-sonnet-5-5": (Decimal("2"), Decimal("10")),
    "anthropic/claude-opus-5-5": (Decimal("4"), Decimal("20")),
    "anthropic/claude-fable-5-1": (Decimal("10"), Decimal("50")),
    # Always use the higher >=200K context band, including short requests.
    **{f"xai/grok-{version}": (Decimal("4"), Decimal("12"))
       for version in ("4.5", "4.6", "4.7")},
    **{f"fireworks_ai/accounts/fireworks/models/{name}": (Decimal("0.30"), Decimal("1.20"))
       for name in ("deepseek-v4p1-flash", "deepseek-v4p1-flash-1017")},
    # Standard rates with the >272K band's 1.5x output; the doubled input
    # charge covers that band's 2x input. Sol keeps its pre-promotion input rate.
    "openai/gpt-5.6-sol": (Decimal("5"), Decimal("30")),
    "openai/gpt-5.6-terra": (Decimal("2"), Decimal("18")),
    "openai/gpt-5.6-luna": (Decimal("0.20"), Decimal("1.80")),
    "openai/gpt-6-astra": (Decimal("10"), Decimal("75")),
    "openai/gpt-6-sol": (Decimal("2"), Decimal("15")),
    "openai/gpt-6-luna": (Decimal("0.10"), Decimal("0.75")),
    "openai/gpt-6.1-sol": (Decimal("2"), Decimal("15")),
}


def output_reservation(model):
    # xAI reports reasoning separately from visible completion tokens. Reserve
    # its entire context window even while requesting max_tokens=8192, avoiding
    # reliance on undocumented interactions between that cap and reasoning.
    return 500_000 if model.startswith("xai/") else MAX_OUTPUT_TOKENS


def model_info(model):
    provider = model.split("/", 1)[0]
    inputs, outputs = RATES[model]
    context = {"anthropic": 1_000_000, "xai": 500_000, "fireworks_ai": 1_048_576,
               "openai": 1_050_000}[provider]
    return {
        "max_tokens": 128000, "max_input_tokens": context,
        "max_output_tokens": 128000, "mode": "chat",
        "litellm_provider": provider,
        "input_cost_per_token": float(inputs / 1_000_000),
        "output_cost_per_token": float(outputs / 1_000_000),
        "supports_prompt_caching": True, "supports_system_messages": True,
    }


class BudgetStopped(RuntimeError):
    pass


class ProviderRefused(RuntimeError):
    """A normal API refusal, not a malformed agent command or unknown charge."""


def upper_cost(model, input_tokens, output_tokens):
    for n in (input_tokens, output_tokens):
        if type(n) is not int or n < 0:
            raise ValueError("missing or invalid provider token usage")
    input_rate, output_rate = RATES[model]
    # USD/MTok is numerically equal to microdollars/token.
    cost = 2 * input_rate * input_tokens + output_rate * output_tokens
    return int(cost.to_integral_value(rounding="ROUND_CEILING"))


class Budget:
    def __init__(self, path):
        self.path = Path(path).resolve()

    @contextmanager
    def transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.with_suffix(".lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = json.loads(self.path.read_text()) if self.path.exists() else {}
            yield state
            temporary = self.path.with_suffix(".tmp")
            with temporary.open("w") as stream:
                json.dump(state, stream, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(self.path)

    def initialize(self, dollars):
        amount = Decimal(str(dollars))
        if not amount.is_finite() or not 0 < amount <= MAX_BUDGET_USD:
            raise ValueError("budget must be positive and at most $100")
        limit = int(amount * 1_000_000)
        with self.transaction() as state:
            if state:
                if state["limit_micro_usd"] != limit:
                    raise ValueError("existing ledger's limit cannot be changed")
            else:
                state.update(
                    version=1, limit_micro_usd=limit, requests=[],
                    pricing_checked=PRICING_CHECKED, pricing_source=PRICING_SOURCE,
                )

    def snapshot(self):
        with self.transaction() as state:
            if not state:
                raise BudgetStopped("budget ledger has not been initialized")
            return dict(state)

    def reserve(self, model):
        amount = upper_cost(model, INPUT_RESERVATION_TOKENS, output_reservation(model))
        with self.transaction() as state:
            if not state or state.get("halted"):
                raise BudgetStopped("budget ledger is uninitialized or halted")
            if any(r["status"] != "settled" for r in state["requests"]):
                raise BudgetStopped("unresolved request reservation; reconcile before continuing")
            spent = sum(r["accounted_micro_usd"] for r in state["requests"])
            if spent + amount > state["limit_micro_usd"]:
                raise BudgetStopped("insufficient budget for the next request's worst case")
            index = len(state["requests"])
            state["requests"].append({
                "model": model, "status": "reserved", "started_at": time.time(),
                "reserved_micro_usd": amount, "accounted_micro_usd": amount,
                "pricing_checked": PRICING_CHECKED,
                "pricing_source": PRICING_SOURCES[model.split("/", 1)[0]],
                "output_reservation_tokens": output_reservation(model),
            })
        return index

    def settle(self, index, usage, response_metadata=None):
        with self.transaction() as state:
            request = state["requests"][index]
            if response_metadata:
                request["response_metadata"] = response_metadata
            if request["status"] != "reserved":
                raise BudgetStopped("reservation already resolved")
            try:
                inputs, outputs = usage["prompt_tokens"], usage["completion_tokens"]
                amount = upper_cost(request["model"], inputs, outputs)
                if inputs > INPUT_RESERVATION_TOKENS or outputs > output_reservation(request["model"]):
                    raise ValueError("provider usage exceeds the reservation bounds")
                if amount > request["reserved_micro_usd"]:
                    raise ValueError("usage cost exceeds its reservation")
            except (KeyError, TypeError, ValueError) as exc:
                request.update(status="unknown", reason=str(exc))
                state["halted"] = "unusable provider usage; reservation retained"
            else:
                request.update(
                    status="settled", accounted_micro_usd=amount,
                    prompt_tokens=inputs, completion_tokens=outputs,
                )
        if state.get("halted"):
            raise BudgetStopped(state["halted"])

    def unknown(self, index, reason):
        with self.transaction() as state:
            state["requests"][index].update(status="unknown", reason=reason)
            state["halted"] = "request outcome unknown; reservation retained"


async def guarded_completion(completion, budget, expected_model, **kwargs):
    """Wrap each actual LiteLLM request, including Harbor's own retries."""
    if kwargs.get("model") != expected_model or expected_model not in RATES:
        raise BudgetStopped("model has no verified budget configuration")
    # These modes can introduce additional charges or unmetered requests.
    for key in (
        "api_base", "base_url", "stream", "tools", "web_search_options", "speed",
        "service_tier", "extra_body", "fallbacks", "mock_response", "deployment_id",
    ):
        if kwargs.get(key):
            raise BudgetStopped(f"unsupported request option: {key}")
    if kwargs.get("n", 1) != 1:
        raise BudgetStopped("only one completion per request is supported")
    kwargs.update(
        max_tokens=MAX_OUTPUT_TOKENS, max_completion_tokens=None,
        num_retries=0, max_retries=0, timeout=180, caching=False,
    )
    metadata = {}
    original_logger = kwargs.get("logger_fn")

    def capture_response(event):
        # LiteLLM's event also contains credentials. Copy only allowlisted
        # response metadata, never the event, request, headers, or model text.
        if event.get("log_event_type") == "post_api_call":
            raw = event.get("original_response")
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except ValueError:
                    raw = None
            if isinstance(raw, dict):
                for key in ("id", "model", "stop_reason"):
                    if isinstance(raw.get(key), str):
                        metadata[key] = raw[key]
                details = raw.get("stop_details")
                if isinstance(details, dict):
                    metadata["refusal_category"] = details.get("category")
        if original_logger:
            original_logger(event)

    kwargs["logger_fn"] = capture_response
    reservation = budget.reserve(expected_model)
    try:
        response = await completion(**kwargs)
        usage = response.usage.model_dump()
        if expected_model.startswith(("xai/", "fireworks_ai/", "openai/")):
            # Count all generated tokens, including hidden reasoning. LiteLLM
            # normally normalizes this; total minus prompt also handles native
            # xAI accounting without double counting reasoning. OpenAI caps
            # reasoning within max_completion_tokens, which LiteLLM maps from
            # max_tokens for GPT-5/6 models.
            prompt, total = usage["prompt_tokens"], usage["total_tokens"]
            output = usage["completion_tokens"]
            if any(type(n) is not int or n < 0 for n in (prompt, total, output)) or total < prompt:
                raise ValueError("invalid token totals")
            usage["completion_tokens"] = max(output, total - prompt)
    except BaseException as exc:
        # Never log exception text: it may contain request headers or record data.
        budget.unknown(reservation, type(exc).__name__)
        raise
    choices = getattr(response, "choices", None)
    if choices:
        metadata["finish_reason"] = choices[0].finish_reason
    budget.settle(reservation, usage, metadata)
    if metadata.get("stop_reason") == "refusal" or metadata.get("finish_reason") in ("refusal", "content_filter"):
        raise ProviderRefused("provider refusal: " + str(metadata.get("refusal_category", "unspecified")))
    return response


def check_model_access(models):
    """Free Models API preflight, without printing or persisting credentials."""
    if not models or any(model not in RATES for model in models):
        raise ValueError("execution requires model IDs with verified pricing in RATES")
    for provider in dict.fromkeys(m.split("/", 1)[0] for m in models):
        requested = [m for m in models if m.startswith(provider + "/")]
        if provider == "anthropic":
            _check_anthropic_access(requested)
        else:
            _check_compatible_access(provider, requested)
    return {"checked_at": time.time(), "available_requested_models": models}


def _check_compatible_access(provider, models):
    settings = {
        "xai": ("XAI_API_KEY", "XAI_KEY", ("XAI_API_BASE",), "https://api.x.ai/v1/models"),
        "fireworks_ai": ("FIREWORKS_API_KEY", "FIREWORKS_AI_API_KEY", ("FIREWORKS_API_BASE",),
                        "https://api.fireworks.ai/inference/v1/models"),
        "openai": ("OPENAI_API_KEY", "OPENAI_KEY", ("OPENAI_API_BASE", "OPENAI_BASE_URL"),
                   "https://api.openai.com/v1/models"),
    }
    standard, alias, bases, url = settings[provider]
    key = os.environ.get(standard) or os.environ.get(alias)
    if not key:
        raise ValueError(f"{standard} / {alias} is missing; no paid requests made")
    if any(os.environ.get(base) for base in bases):
        raise ValueError("custom API endpoints are not supported by this spending guard")
    os.environ[standard] = key
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            available = {m["id"] for m in json.load(response)["data"]}
    except urllib.error.HTTPError as exc:
        raise ValueError(f"{provider} Models API preflight failed with HTTP {exc.code}") from None
    except (OSError, ValueError, KeyError, TypeError):
        raise ValueError(f"{provider} Models API preflight failed; no paid requests made") from None
    missing = [m for m in models if m.split("/", 1)[1] not in available]
    if missing:
        raise ValueError("Models unavailable to this key: " + ", ".join(missing))


def _check_anthropic_access(models):
    key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_KEY")
    if not key:
        raise ValueError("ANTHROPIC_API_KEY / CLAUDE_KEY is missing; no paid requests made")
    # LiteLLM expects the standard variable. Keep the alias in process memory;
    # never persist credentials in manifests, task files, or shell arguments.
    os.environ["ANTHROPIC_API_KEY"] = key
    if os.environ.get("ANTHROPIC_API_BASE") or os.environ.get("ANTHROPIC_BASE_URL"):
        raise ValueError("custom API endpoints are not supported by this spending guard")
    available, cursor = set(), None
    for _ in range(100):
        params = {"limit": 1000}
        if cursor:
            params["after_id"] = cursor
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/models?" + urllib.parse.urlencode(params),
            headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                page = json.load(response)
        except urllib.error.HTTPError as exc:
            raise ValueError(f"Models API preflight failed with HTTP {exc.code}") from None
        except (OSError, ValueError):
            raise ValueError("Models API preflight failed; no paid requests made") from None
        available.update(entry["id"] for entry in page["data"])
        if not page["has_more"]:
            break
        next_cursor = page["last_id"]
        if not next_cursor or next_cursor == cursor:
            raise ValueError("Models API returned an invalid pagination cursor")
        cursor = next_cursor
    else:
        raise ValueError("Models API pagination limit exceeded")
    missing = [m for m in models if m.split("/", 1)[1] not in available]
    if missing:
        raise ValueError("Models unavailable to this key: " + ", ".join(missing))
    return {"checked_at": time.time(), "available_requested_models": models}
