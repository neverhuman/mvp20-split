"""Reviewed Registry policy configuration, distinct from Planning objective policy."""

from dataclasses import dataclass
from typing import Annotated, Literal

from amphora_contracts_core import Digest, Identifier, WireModel
from pydantic import Field

from ..campaign_context.records import canonical
from ..context.policy import require


class ConfigurationRecord(WireModel):
    format: Literal['planning-eligibility-configuration.v1'] = 'planning-eligibility-configuration.v1'
    owner_id: Identifier
    actor_id: Identifier
    policy_sha256: Digest
    maximum_age_seconds: Annotated[int, Field(ge=1, le=60)]


@dataclass(frozen=True)
class EligibilityConfiguration:
    canonical: bytes

    @classmethod
    def bind(cls, *, owner_id, actor_id, policy_sha256, maximum_age_seconds=5):
        record = ConfigurationRecord(owner_id=owner_id, actor_id=actor_id, policy_sha256=policy_sha256,
                                     maximum_age_seconds=maximum_age_seconds)
        return cls(canonical(record.model_dump(mode='json')))

    def document(self):
        return ConfigurationRecord.model_validate_json(self.canonical)

    def verify(self):
        value = self.document()
        require(self.bind(owner_id=value.owner_id, actor_id=value.actor_id, policy_sha256=value.policy_sha256,
                          maximum_age_seconds=value.maximum_age_seconds) == self, 'eligibility_configuration_binding')
        return value
