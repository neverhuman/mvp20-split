"""Explicit operator-only scope/key reference and synthetic egress mode."""
import os
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, Scope, WireModel
from pydantic import Field

from ..context.policy import require
from ..curation_budget import CurationAllowance
from .adapter import CurationOpenAI


class LiveCurationSettings(WireModel):
    key_env: Identifier
    scope: Scope
    egress: Literal['approved_synthetic_engineering_only']
    timeout_seconds: Annotated[int, Field(ge=1, le=60)] = 60

    def provider(self, policies):
        require(bool(policies), 'curation_live_policies_missing')
        for policy in policies:
            CurationAllowance.validate_policy(policy)
        return CurationOpenAI(os.environ[self.key_env], scope=self.scope, egress=self.egress,
                              timeout_seconds=self.timeout_seconds)
