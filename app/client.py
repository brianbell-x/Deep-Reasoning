# app/client.py - all api client code

from openai import OpenAI
from typing import Any

_O4_IN_RATE    = 1.10   / 1_000_000
_O4_CACHE_RATE = 0.275  / 1_000_000
_O4_OUT_RATE   = 4.40   / 1_000_000

class DeepThinkingAPIClient:
    """Centralizes every OpenAI responses.create() call and cost tracking."""
    def __init__(self, api_key: str):
        self.sdk = OpenAI(api_key=api_key)
        self._total_cost_usd: float = 0.0

    def total_cost(self) -> float:
        return self._total_cost_usd

    def planner_call(
        self,
        model: str,
        instructions: str,
        user_prompt: str,
    ) -> Any:
        return self._create(model, instructions, user_prompt,
                            extra_args=dict(text={"format": {"type": "json_object"}}))

    def thinker_call(
        self,
        model: str,
        instructions: str,
        user_prompt: str,
    ) -> Any:
        return self._create(model, instructions, user_prompt)

    def reviewer_call(
        self,
        model: str,
        instructions: str,
        user_prompt: str,
    ) -> Any:
        return self._create(model, instructions, user_prompt,
                            extra_args=dict(text={"format": {"type": "json_object"}}))

    def synthesizer_call(
        self,
        model: str,
        instructions: str,
        user_prompt: str,
    ) -> Any:
        return self._create(model, instructions, user_prompt)

    def _create(
        self,
        model: str,
        instructions: str,
        user_prompt: str,
        *,
        extra_args: dict | None = None,
    ) -> Any:
        kwargs = dict(model=model, instructions=instructions, input=user_prompt)
        if extra_args:
            kwargs.update(extra_args)
        resp = self.sdk.responses.create(**kwargs)
        self._accumulate_cost(resp)
        return resp

    def _accumulate_cost(self, resp):
        usage = getattr(resp, "usage", None) or {}
        cached = usage.get("input_tokens_details", {}).get("cached_tokens", 0)
        inp    = usage.get("input_tokens", 0)
        outp   = usage.get("output_tokens", 0)
        cost   = ((inp - cached) * _O4_IN_RATE) + (cached * _O4_CACHE_RATE) + (outp * _O4_OUT_RATE)
        self._total_cost_usd += cost
