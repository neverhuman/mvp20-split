"""Closed environment reference and explicit synthetic-only egress selection."""

import os
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, WireModel
from pydantic import Field

from ..checkpoint_budget import CheckpointAllowance
from ..context.policy import require
from .adapter import CheckpointOpenAI


class LiveCheckpointSettings(WireModel):
    key_env: Identifier
    egress: Literal['approved_synthetic_engineering_only']
    timeout_seconds: Annotated[int, Field(ge=1, le=60)] = 45

    def provider(self, entries):
        require(bool(entries), 'checkpoint_live_templates_missing')
        for _reference, template in entries:
            record = template.document()
            expected = CheckpointAllowance.cost(record.model, record.limits)
            require(record.per_attempt_accounting_units >= expected, 'checkpoint_cost_underreserved')
        return CheckpointOpenAI(os.environ[self.key_env], timeout_seconds=self.timeout_seconds)
