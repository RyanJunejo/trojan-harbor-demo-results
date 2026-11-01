"""Terminus-2 with a host-side budget guard; task containers never see API keys."""
import os

import litellm
from harbor.agents.terminus_2.terminus_2 import Terminus2

from tools.customer_demo_budget import Budget, RATES, guarded_completion


class BudgetedTerminus2(Terminus2):
    def __init__(self, *args, model_name=None, **kwargs):
        if model_name not in RATES:
            raise ValueError("no verified pricing for this model")
        budget = Budget(os.environ["CUSTOMER_DEMO_BUDGET_LEDGER"])
        budget.snapshot()  # Fail before agent initialization if unconfigured.
        original = litellm.acompletion
        if getattr(original, "_customer_demo_guard", False):
            raise RuntimeError("use one trial per Harbor process")

        async def guarded(**request):
            return await guarded_completion(original, budget, model_name, **request)

        guarded._customer_demo_guard = True
        litellm.acompletion = guarded
        # The pinned dependency predates these IDs. Register their documented
        # context limits so Harbor does not fall back to an arbitrary window.
        input_rate, output_rate = RATES[model_name]
        kwargs["model_info"] = {
            "max_tokens": 128000, "max_input_tokens": 1000000,
            "max_output_tokens": 128000, "mode": "chat",
            "litellm_provider": "anthropic",
            "input_cost_per_token": float(input_rate / 1_000_000),
            "output_cost_per_token": float(output_rate / 1_000_000),
            "supports_prompt_caching": True, "supports_system_messages": True,
        }
        super().__init__(*args, model_name=model_name, **kwargs)
