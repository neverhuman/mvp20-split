"""Relevant original observations are selected by policy, never invented by output."""

import hashlib
from dataclasses import dataclass

from ..campaign_context.records import canonical
from ..campaign_preparations import CampaignPreparation
from ..context.policy import require


def checked_preparation(value):
    checked = CampaignPreparation.from_bytes(value.packet.request, value.canonical, value.packet.canonical)
    require(checked == value, 'campaign_proposal_preparation')
    return checked


@dataclass(frozen=True, order=True)
class ObservationKey:
    lane: str
    kind: str
    identity: bytes


@dataclass(frozen=True)
class ObservedInput:
    key: ObservationKey
    sha256: str


@dataclass(frozen=True)
class ObservedInputs:
    preparation: CampaignPreparation
    entries: tuple[ObservedInput, ...]

    @classmethod
    def bind(cls, preparation):
        preparation = checked_preparation(preparation)
        observed = {}
        for candidate in preparation.document().candidates:
            if not candidate.included:
                continue
            for row in candidate.observations:
                key = ObservationKey(candidate.lane, row.kind, canonical(row.identity))
                prior = observed.setdefault(key, row.sha256)
                require(prior == row.sha256, 'campaign_observation_conflict')
        return cls(preparation, tuple(ObservedInput(key, observed[key]) for key in sorted(observed)))

    def select(self, keys):
        require(self.bind(self.preparation) == self, 'campaign_observation_index')
        keys = tuple(keys)
        require(all(type(key) is ObservationKey for key in keys), 'campaign_observation_key')
        require(len(keys) == len(set(keys)), 'campaign_dependency_duplicate')
        known = {entry.key for entry in self.entries}
        require(all(key in known for key in keys), 'campaign_dependency_unconsumed')
        return RelevantReadSet(self, tuple(sorted(keys)))


@dataclass(frozen=True)
class DependencyChange:
    key: ObservationKey
    before_sha256: str
    after_sha256: str | None


@dataclass(frozen=True)
class RelevantReadSet:
    source: ObservedInputs
    keys: tuple[ObservationKey, ...]

    @property
    def entries(self):
        selected = frozenset(self.keys)
        return tuple(entry for entry in self.source.entries if entry.key in selected)

    @property
    def sha256(self):
        require(self.source.select(self.keys) == self, 'campaign_read_set_binding')
        value = {'preparation_sha256': self.source.preparation.sha256,
                 'observations': [{'lane': entry.key.lane, 'kind': entry.key.kind,
                                   'identity_utf8': entry.key.identity.decode('utf-8'), 'sha256': entry.sha256}
                                  for entry in self.entries]}
        return hashlib.sha256(canonical(value)).hexdigest()

    def changes(self, current):
        require(self.source.select(self.keys) == self, 'campaign_read_set_binding')
        require(ObservedInputs.bind(current.preparation) == current, 'campaign_observation_index')
        original_scope = self.source.preparation.packet.request.document().reference.scope
        require(current.preparation.packet.request.document().reference.scope == original_scope,
                'campaign_observation_scope')
        latest = {entry.key: entry.sha256 for entry in current.entries}
        return tuple(DependencyChange(entry.key, entry.sha256, latest.get(entry.key))
                     for entry in self.entries if latest.get(entry.key) != entry.sha256)
