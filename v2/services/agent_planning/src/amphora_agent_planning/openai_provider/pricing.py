"""Pinned standard text-token rates, represented without binary currency floats."""
from dataclasses import dataclass

from ..context.policy import require

MODEL = "gpt-5.4-mini-2026-03-17"
UNIT = "usd_nanodollars"

@dataclass(frozen=True)
class OpenAIPrice:
    input_rate: int = 750
    output_rate: int = 4500
    def estimate(self, input_tokens, output_tokens):
        require(all(type(x) is int and 0 <= x <= 100000000 for x in (input_tokens, output_tokens)), "openai_usage_invalid")
        return input_tokens * self.input_rate + output_tokens * self.output_rate
    def reservation(self, limits):
        require(limits.accounting_unit == UNIT, "openai_accounting_unit")
        require(limits.max_input_tokens <= 16384 and limits.max_output_tokens <= 4096, "openai_initial_request_limit")
        return self.estimate(limits.max_input_tokens, limits.max_output_tokens)
