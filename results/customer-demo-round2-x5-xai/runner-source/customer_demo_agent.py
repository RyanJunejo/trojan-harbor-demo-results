"""Terminus-2 with a host-side budget guard; task containers never see API keys."""
import os

import litellm
from harbor.agents.terminus_2.terminus_2 import Terminus2

from tools.customer_demo_budget import Budget, ProviderRefused, RATES, guarded_completion, model_info


class BudgetedTerminus2(Terminus2):
    def __init__(self, *args, model_name=None, **kwargs):
        if model_name not in RATES:
            raise ValueError("no verified pricing for this model")
        budget = Budget(os.environ["CUSTOMER_DEMO_BUDGET_LEDGER"])
        budget.snapshot()  # Fail before agent initialization if unconfigured.
        original = litellm.acompletion
        if getattr(original, "_customer_demo_guard", False):
            raise RuntimeError("use one trial per Harbor process")

        refusal = None

        async def guarded(**request):
            nonlocal refusal
            if refusal is not None:
                raise ProviderRefused(refusal)
            try:
                return await guarded_completion(original, budget, model_name, **request)
            except ProviderRefused as exc:
                # Harbor retries some exceptions. Re-raise locally without
                # sending another API request after a classifier refusal.
                refusal = str(exc)
                raise

        guarded._customer_demo_guard = True
        litellm.acompletion = guarded
        # The pinned dependency predates these IDs. Register their documented
        # context limits so Harbor does not fall back to an arbitrary window.
        kwargs["model_info"] = model_info(model_name)
        super().__init__(*args, model_name=model_name, **kwargs)
