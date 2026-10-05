"""Exact observed releases and reviewed locks; fresh eligibility remains separate."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_graph_runtime import DefinitionUniverse
from amphora_contracts_tools import ReleaseSnapshot

from ..campaign_context.records import canonical
from ..campaign_tool_context import RuntimeContext
from ..context.policy import require
from ..registry_access import ObservedRelease
from ..runtime_metadata import ReviewedUniverse
from .observations import ObservationKey


@dataclass(frozen=True)
class ConsumedRelease:
    lane: str
    record: ObservedRelease
    key: ObservationKey


@dataclass(frozen=True)
class RuntimeToolSelection:
    universe: ReviewedUniverse
    locks: tuple

    @classmethod
    def bind(cls, universe, bindings):
        universe = ReviewedUniverse.bind(universe.document(), universe.request)
        available = {lock.tool: lock for lock in universe.document().reviewed_tools}
        bindings = tuple(bindings)
        require(len(set(bindings)) == len(bindings), 'campaign_tool_duplicate_selection')
        require(all(binding in available for binding in bindings), 'campaign_tool_not_reviewed')
        return cls(universe, tuple(sorted((available[binding] for binding in bindings),
                                         key=lambda lock: canonical(lock.model_dump(mode='json')))))

    def changes(self, current):
        require(self.bind(self.universe, tuple(lock.tool for lock in self.locks)) == self,
                'campaign_runtime_selection_binding')
        current = ReviewedUniverse.bind(current.document(), current.request)
        require(current.document().scope == self.universe.document().scope, 'campaign_runtime_selection_scope')
        latest = {lock.tool: lock for lock in current.document().reviewed_tools}
        return tuple(lock.tool for lock in self.locks if latest.get(lock.tool) != lock)


@dataclass(frozen=True)
class ConsumedTools:
    releases: tuple[ConsumedRelease, ...]
    universe: ReviewedUniverse | None

    @classmethod
    def from_proposal(cls, prepared):
        request = prepared.attempt.request
        scope = request.document().reference.scope
        indexed = {entry.key: entry.sha256 for entry in prepared.inputs.entries}
        releases, universe = [], None
        for row in prepared.inputs.preparation.packet.context()['slices']:
            lane, payload = row['lane'], row['payload']
            if lane in {'registry_inventory', 'registry_exact'}:
                record = ObservedRelease.bind(ReleaseSnapshot.model_validate_json(canonical(payload)), scope)
                lock = record.document().lock.model_dump(mode='json')
                require(row['identity'] == lock and canonical(payload) == canonical(record.document().model_dump(mode='json')),
                        'campaign_tool_release_reconstruction')
                key = ObservationKey(lane, lane, canonical(lock))
                require(indexed.get(key) == hashlib.sha256(canonical(payload)).hexdigest(),
                        'campaign_tool_observation_reconstruction')
                releases.append(ConsumedRelease(lane, record, key))
            elif lane == 'runtime':
                require(payload.get('format') == 'planning-campaign-runtime-context.v1' and
                        payload.get('request_sha256') == request.sha256 and
                        payload.get('authority') == 'compiler_configuration_only', 'campaign_tool_runtime_binding')
                identity = {'scope': scope.model_dump(mode='json')}
                require(row['identity'] == identity and indexed.get(ObservationKey('runtime', 'runtime_universe', canonical(identity))) ==
                        hashlib.sha256(canonical(payload)).hexdigest(), 'campaign_tool_runtime_observation')
                if payload.get('status') == 'available':
                    require(set(payload) == {'format', 'request_sha256', 'authority', 'status', 'universe'},
                            'campaign_tool_runtime_fields')
                    universe = ReviewedUniverse.bind(DefinitionUniverse.model_validate_json(canonical(payload['universe'])), request)
                    require(canonical(payload['universe']) == canonical(universe.document().model_dump(mode='json')),
                            'campaign_tool_runtime_reconstruction')
                else:
                    require(type(payload.get('reason')) is str, 'campaign_tool_runtime_status')
                    expected = RuntimeContext.unavailable(request, payload['reason'])
                    require(canonical(payload) == expected.canonical, 'campaign_tool_runtime_reconstruction')
        return cls(tuple(releases), universe)

    def release(self, binding):
        exact = [row for row in self.releases if row.lane == 'registry_exact' and row.record.document().lock.tool == binding]
        inventory = [row for row in self.releases if row.lane == 'registry_inventory' and row.record.document().lock.tool == binding]
        chosen = exact or inventory
        require(len(chosen) == 1, 'campaign_tool_not_consumed_or_ambiguous')
        return chosen[0]


def validate_invocation(node, release):
    record = release.record.document()
    require(record.status in {'registered', 'active'}, 'campaign_tool_lifecycle')
    descriptor = record.descriptor.tool
    ports = {port.name: port for port in descriptor.inputs}
    supplied = [binding.port for binding in node.inputs]
    require(len(supplied) == len(set(supplied)), 'campaign_tool_duplicate_input')
    require(set(supplied) <= set(ports) and {name for name, port in ports.items() if port.required} <= set(supplied),
            'campaign_tool_input_ports')
    require(node.timeout_seconds <= record.descriptor.resources.timeout_seconds, 'campaign_tool_timeout')
    require(node.checkpoint is None or descriptor.checkpoint_schema is not None, 'campaign_tool_checkpoint')
    if node.checkpoint is not None and node.checkpoint.kind == 'artifact':
        require(node.checkpoint.artifact.schema_ref == descriptor.checkpoint_schema, 'campaign_tool_checkpoint_schema')
    for binding in node.inputs:
        source, port = binding.source, ports[binding.port]
        if source.kind == 'artifact':
            require(source.artifact.schema_ref == port.schema_ref and source.representation == port.representation and
                    source.unit == port.unit, 'campaign_tool_literal_representation')
        # Routed value types and Artifact content are checked by Runtime, not inferred here.


def literal_dependencies(node, prepared):
    artifacts = {canonical(row['identity']): row['payload'] for row in
                 prepared.inputs.preparation.packet.context()['slices'] if row['lane'] == 'artifact'}
    keys = []
    sources = [binding.source for binding in node.inputs]
    if node.checkpoint is not None:
        sources.append(node.checkpoint)
    for source in sources:
        if source.kind == 'artifact':
            identity = canonical(source.artifact.model_dump(mode='json'))
            require(identity in artifacts and artifacts[identity]['status'] == 'available',
                    'campaign_tool_input_unconsumed')
            keys.append(ObservationKey('artifact', 'artifact', identity))
    return tuple(keys)
