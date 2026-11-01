"""Conservative, persistent spending guard for the customer demo's Claude runs.

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
PRICING_CHECKED = "2026-10-20"
PRICING_SOURCE = "https://platform.claude.com/docs/en/about-claude/pricing"
# USD / million tokens. Haiku uses its higher long-context rate even for short
# prompts; input is charged at twice these rates to cover 1h cache creation.
RATES = {
    "anthropic/claude-haiku-5-5": (Decimal("0.50"), Decimal("2.50")),
    "anthropic/claude-sonnet-5-5": (Decimal("2"), Decimal("10")),
    "anthropic/claude-opus-5-5": (Decimal("4"), Decimal("20")),
    "anthropic/claude-fable-5-1": (Decimal("10"), Decimal("50")),
}


class BudgetStopped(RuntimeError):
    pass


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
        amount = upper_cost(model, INPUT_RESERVATION_TOKENS, MAX_OUTPUT_TOKENS)
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
            })
        return index

    def settle(self, index, usage):
        with self.transaction() as state:
            request = state["requests"][index]
            if request["status"] != "reserved":
                raise BudgetStopped("reservation already resolved")
            try:
                inputs, outputs = usage["prompt_tokens"], usage["completion_tokens"]
                amount = upper_cost(request["model"], inputs, outputs)
                if inputs > INPUT_RESERVATION_TOKENS or outputs > MAX_OUTPUT_TOKENS:
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
    reservation = budget.reserve(expected_model)
    try:
        response = await completion(**kwargs)
        usage = response.usage.model_dump()
    except BaseException as exc:
        # Never log exception text: it may contain request headers or record data.
        budget.unknown(reservation, type(exc).__name__)
        raise
    budget.settle(reservation, usage)
    return response


def check_model_access(models):
    """Free Models API preflight, without printing or persisting credentials."""
    if not models or any(model not in RATES for model in models):
        raise ValueError("execution requires model IDs with verified pricing in RATES")
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
