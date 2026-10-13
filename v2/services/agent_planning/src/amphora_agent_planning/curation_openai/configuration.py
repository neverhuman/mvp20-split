"""Explicit operator-only scope/key reference and synthetic egress mode."""
import os
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, Scope, WireModel
from pydantic import Field, model_validator

from ..context.policy import require
from ..curation_budget import CurationAllowance
from .adapter import CurationOpenAI
from .window import CurationResponseWindow


class LiveCurationSettings(WireModel):
    key_env: Identifier
    scope: Scope
    egress: Literal['approved_synthetic_engineering_only']
    deadline_profile: Literal['standard-v1','scientific-v1'] = 'standard-v1'
    timeout_seconds: Annotated[int, Field(ge=1, le=180)] = 60

    @property
    def window(self):
        return CurationResponseWindow.bind(self.deadline_profile,self.timeout_seconds,self.scope)

    @model_validator(mode='after')
    def deadline(self):
        self.window
        return self

    def provider(self, policies):
        require(bool(policies), 'curation_live_policies_missing')
        for policy in policies:
            CurationAllowance.validate_policy(policy)
            self.window.require_model(policy.document().model)
        return CurationOpenAI(os.environ[self.key_env], scope=self.scope, egress=self.egress,
                              timeout_seconds=self.timeout_seconds,deadline_profile=self.deadline_profile)
