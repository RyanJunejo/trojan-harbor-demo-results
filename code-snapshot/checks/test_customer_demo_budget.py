"""Exercise spending decisions without making any provider requests."""
import asyncio
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

import customer_demo as demo
from customer_demo_budget import (
    Budget, BudgetStopped, MAX_OUTPUT_TOKENS, PRICING_SOURCES, ProviderRefused, RATES,
    check_model_access, guarded_completion, upper_cost,
)

FABLE = "anthropic/claude-fable-5-1"
GROK = "xai/grok-4.7"
DEEPSEEK = "fireworks_ai/accounts/fireworks/models/deepseek-v4p1-flash-1017"
OPENAI = "openai/gpt-5.6-sol"
OPENAI_SUITE = [
    "openai/gpt-5.6-sol", "openai/gpt-5.6-terra", "openai/gpt-5.6-luna",
    "openai/gpt-6-astra", "openai/gpt-6-sol", "openai/gpt-6-luna", "openai/gpt-6.1-sol",
]


@pytest.fixture
def budget(tmp_path):
    ledger = Budget(tmp_path / "budget.json")
    ledger.initialize(100)
    return ledger


def test_reservations_block_overdraft_and_cannot_reset_limit(budget):
    reservation = budget.reserve(FABLE)
    with pytest.raises(BudgetStopped, match="unresolved"):
        budget.reserve(FABLE)
    budget.settle(reservation, {"prompt_tokens": 2_000_000, "completion_tokens": 8192})
    reservation = budget.reserve(FABLE)
    budget.settle(reservation, {"prompt_tokens": 2_000_000, "completion_tokens": 8192})
    with pytest.raises(BudgetStopped, match="insufficient"):
        budget.reserve(FABLE)
    with pytest.raises(ValueError, match="cannot be changed"):
        budget.initialize(99)
    with pytest.raises(ValueError, match="at most"):
        budget.initialize(101)
    budget.initialize(100)
    assert len(budget.snapshot()["requests"]) == 2


def test_competing_reservations_cannot_spend_the_same_budget(budget):
    def reserve():
        try:
            return budget.reserve(FABLE)
        except BudgetStopped:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: reserve(), range(2)))
    assert sorted(str(x) for x in results) == ["0", "None"]
    assert len(budget.snapshot()["requests"]) == 1


def test_usage_includes_cached_input_at_conservative_price(budget):
    async def completion(**kwargs):
        assert kwargs["num_retries"] == kwargs["max_retries"] == 0
        assert kwargs["max_tokens"] == MAX_OUTPUT_TOKENS
        # LiteLLM prompt_tokens includes cache hits and cache writes.
        return SimpleNamespace(usage=SimpleNamespace(model_dump=lambda: {
            "prompt_tokens": 5000, "completion_tokens": 100,
            "cache_read_input_tokens": 4000, "cache_creation_input_tokens": 500,
        }))
    asyncio.run(guarded_completion(completion, budget, FABLE, model=FABLE))
    request = budget.snapshot()["requests"][0]
    assert request["status"] == "settled"
    assert request["accounted_micro_usd"] == upper_cost(FABLE, 5000, 100) == 105000


def test_failed_request_holds_money_and_no_retry_reaches_provider(budget):
    calls = []
    async def broken(**kwargs):
        calls.append(1)
        raise TimeoutError("secret request content should not be persisted")
    with pytest.raises(TimeoutError):
        asyncio.run(guarded_completion(broken, budget, FABLE, model=FABLE))
    with pytest.raises(BudgetStopped):
        asyncio.run(guarded_completion(broken, budget, FABLE, model=FABLE))
    assert len(calls) == 1
    state = budget.snapshot()
    request = state["requests"][0]
    assert request["accounted_micro_usd"] == request["reserved_micro_usd"]
    assert request["reason"] == "TimeoutError"
    assert "secret request content" not in budget.path.read_text()


@pytest.mark.parametrize("usage", [
    {}, {"prompt_tokens": -1, "completion_tokens": 1},
    {"prompt_tokens": 200, "completion_tokens": 8193},
    {"prompt_tokens": 1, "completion_tokens": True},
])
def test_unusable_usage_is_never_treated_as_free(budget, usage):
    index = budget.reserve(FABLE)
    with pytest.raises(BudgetStopped):
        budget.settle(index, usage)
    state = budget.snapshot()
    assert state["halted"]
    assert state["requests"][0]["accounted_micro_usd"] > 40_000_000


@pytest.mark.parametrize("option", [{"stream": True}, {"tools": [{}]}, {"speed": "fast"},
                                  {"api_base": "https://example.test"}, {"n": 2}])
def test_unmetered_modes_are_rejected_before_any_call(budget, option):
    async def forbidden(**kwargs):
        pytest.fail("unmetered request reached the provider")
    with pytest.raises(BudgetStopped):
        asyncio.run(guarded_completion(forbidden, budget, FABLE, model=FABLE, **option))
    assert budget.snapshot()["requests"] == []


def test_missing_key_preserves_plan_without_launching_trials(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("CLAUDE_KEY", raising=False)
    monkeypatch.setattr(demo.subprocess, "run", lambda *a, **k: pytest.fail("trial launched"))
    out = tmp_path / "run"
    monkeypatch.setattr(sys, "argv", [
        "customer_demo.py", "--claude-suite", "--trials", "1", "--execute",
        "--out", str(out), "--budget-ledger", str(tmp_path / "budget.json"),
    ])
    with pytest.raises(SystemExit) as exc:
        demo.main()
    assert exc.value.code == 2
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["status"] == "blocked"
    assert len(manifest["trials"]) == 8
    assert all(t["status"] == "pending" for t in manifest["trials"])
    assert manifest["budget"]["requests"] == []


def test_account_access_checked_without_silent_model_substitution(monkeypatch):
    from io import BytesIO
    import customer_demo_budget
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-never-logged")
    monkeypatch.delenv("ANTHROPIC_API_BASE", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    def response(request, **kwargs):
        assert request.full_url.startswith("https://api.anthropic.com/v1/models?")
        assert request.get_header("X-api-key") == "test-key-never-logged"
        return BytesIO(json.dumps({
            "data": [{"id": FABLE.split("/", 1)[1]}], "has_more": False,
        }).encode())
    monkeypatch.setattr(customer_demo_budget.urllib.request, "urlopen", response)
    assert check_model_access([FABLE])["available_requested_models"] == [FABLE]
    with pytest.raises(ValueError, match="unavailable"):
        check_model_access(["anthropic/claude-sonnet-5-5"])


def test_claude_key_alias_is_passed_to_harness_without_persisting_it(monkeypatch):
    from io import BytesIO
    import customer_demo_budget
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("CLAUDE_KEY", "alias-test-secret")
    monkeypatch.delenv("ANTHROPIC_API_BASE", raising=False)
    monkeypatch.delenv("ANTHROPIC_BASE_URL", raising=False)
    def response(request, **kwargs):
        assert request.get_header("X-api-key") == "alias-test-secret"
        return BytesIO(json.dumps({
            "data": [{"id": FABLE.split("/", 1)[1]}], "has_more": False,
        }).encode())
    monkeypatch.setattr(customer_demo_budget.urllib.request, "urlopen", response)
    result = check_model_access([FABLE])
    assert customer_demo_budget.os.environ["ANTHROPIC_API_KEY"] == "alias-test-secret"
    assert "alias-test-secret" not in json.dumps(result)


def test_actual_harbor_agent_calls_through_guard(tmp_path, budget, monkeypatch):
    import litellm
    from tools.customer_demo_agent import BudgetedTerminus2
    calls = []
    async def provider(**kwargs):
        calls.append(kwargs)
        return litellm.ModelResponse(
            model=FABLE,
            choices=[{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            usage={"prompt_tokens": 120, "completion_tokens": 2, "total_tokens": 122},
        )
    monkeypatch.setattr(litellm, "acompletion", provider)
    monkeypatch.setenv("CUSTOMER_DEMO_BUDGET_LEDGER", str(budget.path))
    agent = BudgetedTerminus2(logs_dir=tmp_path / "logs", model_name=FABLE, **demo.AGENT_KWARGS)
    response = asyncio.run(agent._llm.call("offline adapter check"))
    assert response.content == "ok"
    assert len(calls) == 1
    assert calls[0]["max_tokens"] == MAX_OUTPUT_TOKENS
    assert budget.snapshot()["requests"][0]["status"] == "settled"


def test_refusal_stops_harbor_retries_and_records_only_safe_metadata(tmp_path, budget, monkeypatch):
    import litellm
    from tools.customer_demo_agent import BudgetedTerminus2
    calls = []
    async def provider(**kwargs):
        calls.append(1)
        kwargs['logger_fn']({
            'log_event_type': 'post_api_call', 'api_key': 'must-not-be-saved',
            'original_response': json.dumps({
                'id': 'test-response', 'model': FABLE.split('/')[1],
                'content': [], 'stop_reason': 'refusal',
                'stop_details': {'type': 'refusal', 'category': 'cyber'},
            }),
        })
        return litellm.ModelResponse(
            model=FABLE, choices=[{'message': {'role': 'assistant', 'content': None},
                                  'finish_reason': 'content_filter'}],
            usage={'prompt_tokens': 120, 'completion_tokens': 0, 'total_tokens': 120},
        )
    monkeypatch.setattr(litellm, 'acompletion', provider)
    monkeypatch.setenv('CUSTOMER_DEMO_BUDGET_LEDGER', str(budget.path))
    BudgetedTerminus2(logs_dir=tmp_path / 'logs', model_name=FABLE, **demo.AGENT_KWARGS)
    for _ in range(3):
        with pytest.raises(RuntimeError, match='provider refusal: cyber'):
            asyncio.run(litellm.acompletion(model=FABLE, messages=[]))
    assert len(calls) == 1
    state = budget.snapshot()
    assert not state.get('halted')
    assert state['requests'][0]['status'] == 'settled'
    assert state['requests'][0]['response_metadata']['refusal_category'] == 'cyber'
    assert 'must-not-be-saved' not in budget.path.read_text()
    # A different trial may still use the remaining budget.
    budget.reserve(FABLE)


def test_refusal_is_not_reported_as_a_successful_secure_trial(tmp_path, budget, monkeypatch):
    def process(*args, **kwargs):
        index = budget.reserve(FABLE)
        budget.settle(index, {'prompt_tokens': 100, 'completion_tokens': 0},
                      {'stop_reason': 'refusal', 'refusal_category': 'cyber'})
        return SimpleNamespace(returncode=1)
    monkeypatch.setattr(demo.subprocess, 'run', process)
    result = demo.run_one(tmp_path / 'task', tmp_path / 'job', FABLE, 'attack', budget)
    assert result['status'] == 'refused'
    assert result['budget_request_range'] == [0, 1]
    assert 'rewards' not in result


def test_suite_continues_to_other_models_after_a_refusal(tmp_path, monkeypatch):
    monkeypatch.setattr(demo, 'check_model_access', lambda models: {'available_requested_models': models})
    calls = []
    def trial(*args):
        calls.append(args)
        if len(calls) == 1:
            return {'status': 'refused', 'provider_refusal': {'refusal_category': 'cyber'}}
        return {'status': 'valid', 'rewards': {'utility': 1, 'attacker_success': 0, 'secure_utility': 1}}
    monkeypatch.setattr(demo, 'run_one', trial)
    out = tmp_path / 'suite'
    monkeypatch.setattr(sys, 'argv', ['customer_demo.py', '--claude-suite', '--trials', '1',
        '--execute', '--out', str(out), '--budget-ledger', str(tmp_path / 'budget.json')])
    demo.main()
    manifest = json.loads((out / 'manifest.json').read_text())
    assert manifest['status'] == 'complete_with_refusals'
    assert len(calls) == 8
    assert 'Provider refusals' in (out / 'report.md').read_text()


@pytest.mark.parametrize("model,standard,alias,url,missing", [
    (GROK, "XAI_API_KEY", "XAI_KEY", "https://api.x.ai/v1/models", "xai/grok-4.5"),
    (DEEPSEEK, "FIREWORKS_API_KEY", "FIREWORKS_AI_API_KEY",
     "https://api.fireworks.ai/inference/v1/models", DEEPSEEK.removesuffix("-1017")),
    (OPENAI, "OPENAI_API_KEY", "OPENAI_KEY", "https://api.openai.com/v1/models", "openai/gpt-6-sol"),
])
def test_compatible_provider_access_is_exact_and_credentials_stay_private(
        monkeypatch, model, standard, alias, url, missing):
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    from io import BytesIO
    import customer_demo_budget
    monkeypatch.delenv(standard, raising=False)
    monkeypatch.setenv(alias, "private-test-key")
    def response(request, **kwargs):
        assert request.full_url == url
        assert request.get_header("Authorization") == "Bearer private-test-key"
        return BytesIO(json.dumps({"data": [{"id": model.split("/", 1)[1]}]}).encode())
    monkeypatch.setattr(customer_demo_budget.urllib.request, "urlopen", response)
    result = check_model_access([model])
    assert result["available_requested_models"] == [model]
    assert customer_demo_budget.os.environ[standard] == "private-test-key"
    assert "private-test-key" not in json.dumps(result)
    with pytest.raises(ValueError, match="unavailable"):
        check_model_access([missing])


@pytest.mark.parametrize("base,model", [
    ("XAI_API_BASE", GROK), ("FIREWORKS_API_BASE", DEEPSEEK),
    ("OPENAI_API_BASE", OPENAI), ("OPENAI_BASE_URL", OPENAI),
])
def test_compatible_custom_endpoint_rejected(monkeypatch, base, model):
    for key in ("XAI_API_KEY", "FIREWORKS_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.setenv(key, "private-test-key")
    monkeypatch.setenv(base, "https://example.test")
    with pytest.raises(ValueError, match="custom API endpoints"):
        check_model_access([model])


@pytest.mark.parametrize("model", [GROK, DEEPSEEK, OPENAI])
def test_compatible_provider_runs_through_actual_harbor(tmp_path, budget, monkeypatch, model):
    import litellm
    from tools.customer_demo_agent import BudgetedTerminus2
    async def provider(**kwargs):
        assert kwargs["model"] == model
        assert kwargs["max_tokens"] == 8192
        # Simulate native xAI's separately reported reasoning. A normalized
        # provider returns completion=500; both must incur the same charge.
        return litellm.ModelResponse(
            model=model,
            choices=[{"message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
            usage={"prompt_tokens": 1000, "completion_tokens": 100, "total_tokens": 1500,
                   "completion_tokens_details": {"reasoning_tokens": 400}},
        )
    monkeypatch.setattr(litellm, "acompletion", provider)
    monkeypatch.setenv("CUSTOMER_DEMO_BUDGET_LEDGER", str(budget.path))
    agent = BudgetedTerminus2(logs_dir=tmp_path / "logs", model_name=model, **demo.AGENT_KWARGS)
    assert asyncio.run(agent._llm.call("offline adapter check")).content == "ok"
    request = budget.snapshot()["requests"][0]
    assert request["completion_tokens"] == 500
    assert request["accounted_micro_usd"] == upper_cost(model, 1000, 500)
    assert request["pricing_source"] == PRICING_SOURCES[model.split("/", 1)[0]]


def test_openai_suite_is_priced_and_output_cap_includes_reasoning():
    import litellm
    assert [m for m in RATES if m.startswith("openai/")] == OPENAI_SUITE
    for model in OPENAI_SUITE:
        # The guard sends max_tokens; GPT-5/6 reasoning models need this mapped
        # to max_completion_tokens, which bounds reasoning plus visible output.
        params = litellm.get_optional_params(
            model=model.split("/", 1)[1], custom_llm_provider="openai",
            max_tokens=MAX_OUTPUT_TOKENS, max_completion_tokens=None,
        )
        assert params.get("max_completion_tokens") == MAX_OUTPUT_TOKENS
        assert "max_tokens" not in params


def test_grok_reserves_and_charges_hidden_reasoning_beyond_visible_cap(budget):
    index = budget.reserve(GROK)
    assert budget.snapshot()["requests"][index]["reserved_micro_usd"] == 22_000_000
    budget.settle(index, {"prompt_tokens": 1000, "completion_tokens": 10000})
    assert budget.snapshot()["requests"][index]["accounted_micro_usd"] == 128000
