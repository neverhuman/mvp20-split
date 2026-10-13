"""Private reviewed process inputs; browser commands cannot choose these values."""
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from amphora_contracts_core import Identifier, Scope, WireModel
from pydantic import Field, model_validator

from ..campaign_eligibility.configuration import ConfigurationRecord, EligibilityConfiguration
from ..context.policy import require
from ..curation_openai.configuration import LiveCurationSettings
from ..curation_policy import CurationPolicy


class Peer(WireModel):
    endpoint: Annotated[str, Field(min_length=1, max_length=512)]
    token_env: Identifier


class WorkerConfiguration(WireModel):
    profile: Literal['planning-curation-worker.v1', 'planning-curation-worker.v2'] = 'planning-curation-worker.v1'
    database_url_env: Identifier
    actor_id: Identifier
    scope: Scope
    worker_id: Identifier
    policies: Annotated[tuple[Annotated[str, Field(min_length=1, max_length=1024)], ...], Field(min_length=1, max_length=32)]
    data: Peer
    runtime: Peer
    registry: Peer
    knowledge: Peer
    research: Peer
    runtime_owner: Identifier
    runtime_actor_id: Identifier | None = None
    eligibility: ConfigurationRecord
    provider: Literal['disabled', 'openai_curation_v1'] = 'disabled'
    live: LiveCurationSettings | None = None

    @model_validator(mode='after')
    def boundaries(self):
        require((self.provider == 'openai_curation_v1') == (self.live is not None), 'curation_worker_live_configuration')
        require(self.live is None or self.live.scope == self.scope, 'curation_worker_live_scope')
        if self.profile == 'planning-curation-worker.v1':
            require(self.runtime_actor_id is None, 'curation_worker_v1_runtime_actor')
            require(self.eligibility.actor_id == self.actor_id, 'curation_worker_eligibility_actor')
        else:
            require(self.runtime_actor_id is not None, 'curation_worker_v2_runtime_actor')
        require(len(set(self.policies)) == len(self.policies), 'curation_worker_policy_files')
        return self

    @property
    def runtime_actor(self):
        return self.actor_id if self.runtime_actor_id is None else self.runtime_actor_id


def bounded_file(path, maximum):
    with Path(path).open('rb') as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, 'curation_worker_configuration_size')
    return raw


@dataclass(frozen=True)
class ReviewedConfiguration:
    configuration: WorkerConfiguration
    policies: tuple[CurationPolicy, ...]

    @classmethod
    def load(cls, path):
        path = Path(path)
        config = WorkerConfiguration.model_validate_json(bounded_file(path, 65536))
        policies = tuple(CurationPolicy.from_bytes(bounded_file(path.parent / entry, 262144)) for entry in config.policies)
        identifiers = [policy.document().policy_id for policy in policies]
        require(len(set(identifiers)) == len(identifiers), 'curation_worker_policy_duplicate')
        for policy in policies:
            request = policy.document().template
            require(request.actor_id == config.actor_id and request.reference.scope == config.scope,
                    'curation_worker_policy_identity')
        return cls(config, policies)

    def eligibility(self):
        config = self.configuration.eligibility
        return EligibilityConfiguration.bind(owner_id=config.owner_id, actor_id=config.actor_id,
            policy_sha256=config.policy_sha256, maximum_age_seconds=config.maximum_age_seconds)

    def policy_map(self):
        return {policy.document().policy_id: policy for policy in self.policies}
