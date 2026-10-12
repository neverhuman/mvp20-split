"""Immutable exact provider input linkage; no reservation or provider dispatch."""
from dataclasses import dataclass
import json

from amphora_contracts_planning import EngagementRef
from sqlalchemy import text

from ..context.policy import require
from ..curation_context import CurationIntent
from ..curation_input import CurationEnvelope
from ..curation_jobs.journal import CurationJobs, key_for, KEY
from ..curation_jobs.state import JobProgress
from ..campaign_preparations import CampaignPreparation
from ..campaign_preparations.journal import CampaignPreparationJournal
from ..persistence.journal import PlanningJournal


@dataclass(frozen=True)
class FrozenInput:
    preparation: CampaignPreparation
    envelope: CurationEnvelope

    @classmethod
    def bind(cls, incoming, preparation):
        request = preparation.packet.request
        intent = CurationIntent.bind(request, incoming)
        record = CampaignPreparation.from_bytes(request, preparation.canonical, preparation.packet.canonical)
        slices = record.packet.context()['slices']
        lanes = {row['lane'] for row in slices}
        require({'curation', 'curation_runtime', 'curation_knowledge', 'research', 'registry_scan', 'runtime'} <= lanes,
                'curation_preparation_incomplete')
        original = next(row['payload'] for row in slices if row['lane'] == 'curation')
        require(CurationIntent.from_payload(request, original) == intent, 'curation_preparation_intent')
        selected = json.loads(intent.canonical)['command']['payload']['context']
        research = next(row['payload']['selection'] for row in slices if row['lane'] == 'research')
        require(research['questions'] == selected['questions'] and research['needs'] == selected['needs']
                and not research['assessments'], 'curation_preparation_research_selection')
        return cls(record, CurationEnvelope.bind(request, record.packet.canonical))


@dataclass(frozen=True)
class PreparationLink:
    frozen: FrozenInput
    progress: JobProgress


@dataclass(frozen=True)
class RecoveredPreparation:
    original: object
    request: object | None
    frozen: FrozenInput | None
    link: PreparationLink | None


class CurationPreparationJournal:
    def __init__(self, engine):
        self.engine = engine
        self.jobs = CurationJobs(engine)
        self.requests = PlanningJournal(engine)
        self.preparations = CampaignPreparationJournal(engine)

    def recover(self, principal, curation_id):
        principal.require('execute_curations', principal.scope)
        principal.require('read_attempts', principal.scope)
        key = key_for(principal, curation_id)
        with self.engine.begin() as conn:
            # Serialize the linkage snapshot; a concurrent freeze may retain
            # input, but cannot commit its link midway through this read.
            self.jobs._lock(conn, key)
            original = self.jobs._original(conn, principal, key)
            if original is None:
                return None
            reference = EngagementRef(scope=principal.scope,
                engagement_id=CurationIntent.engagement_for(original.incoming))
            request_key = self.requests._key(reference)
            request = self.requests._request(conn, request_key, principal)
            frozen = None
            if request is not None:
                CurationIntent.bind(request, original.incoming)
                stored = self.preparations._read(conn, request_key, request)
                if stored is not None:
                    frozen = FrozenInput.bind(original.incoming, stored.record)
            row = conn.execute(text('SELECT * FROM planning.curation_preparation_links WHERE ' + KEY), key).mappings().one_or_none()
            link = None if row is None else self._restore(conn, key, original, frozen, row)
        return RecoveredPreparation(original, request, frozen, link)

    @staticmethod
    def _restore(conn, key, original, frozen, row):
        require(frozen is not None, 'curation_link_input_missing')
        request = frozen.preparation.packet.request
        require((row['engagement_id'], row['request_sha256'], row['manifest_sha256'], row['envelope_sha256']) ==
                (request.document().reference.engagement_id, request.sha256,
                 frozen.preparation.sha256, frozen.envelope.sha256), 'curation_link_input_mismatch')
        event = conn.execute(text('SELECT * FROM planning.curation_progress WHERE ' + KEY +
            ' AND revision=:revision'), {**key, 'revision': row['progress_revision']}).mappings().one_or_none()
        require(event is not None, 'curation_link_progress_missing')
        progress = JobProgress.restore(original, event)
        require(progress.view.receipt.phase == 'awaiting_provider'
                and progress.view.receipt.reason_code == 'context_prepared', 'curation_link_progress_mismatch')
        return PreparationLink(frozen, progress)

    def freeze(self, principal, lease, assembly):
        principal.require('execute_curations', principal.scope)
        result = assembly.prepare()
        require(result.packet is not None, 'curation_preparation_not_ready')
        frozen = FrozenInput.bind(lease.progress.original.incoming,
            CampaignPreparation.bind(assembly.plan, result.packet))
        def guard(conn):
            progress, _ = self.jobs._owned(conn, principal, lease, key_for(principal, lease.curation_id))
            require(progress.view.receipt.phase == 'assembling', 'curation_preparation_phase')
        self.requests.register(principal, assembly.plan.request, guard=guard)
        self.preparations.register(principal, assembly.plan, result.packet, guard=guard)
        return self.attach(principal, lease, frozen)

    def attach(self, principal, lease, frozen):
        principal.require('execute_curations', principal.scope)
        principal.require('read_attempts', principal.scope)
        # Recovery can attach already retained input without another peer read.
        frozen = FrozenInput.bind(lease.progress.original.incoming, frozen.preparation)
        key = key_for(principal, lease.curation_id)
        reference = frozen.preparation.packet.request.document().reference
        retained = self.preparations.read(principal, reference)
        require(retained is not None and retained.record == frozen.preparation, 'curation_link_not_retained')
        with self.engine.begin() as conn:
            self.jobs._lock(conn, key)
            original = self.jobs._original(conn, principal, key)
            require(original is not None, 'curation_link_original_missing')
            # Rebind against the actual original, not a caller-supplied lease copy.
            require(CurationIntent.bind(frozen.preparation.packet.request, original.incoming).identity['curation_id'] ==
                    lease.curation_id, 'curation_link_original_binding')
            existing = conn.execute(text('SELECT * FROM planning.curation_preparation_links WHERE ' + KEY), key).mappings().one_or_none()
            if existing is not None:
                return self._restore(conn, key, original, frozen, existing)
            progress, now = self.jobs._owned(conn, principal, lease, key)
            prepared = progress.prepared(now)
            self.jobs._append(conn, key, prepared)
            self._insert(conn, key, frozen, prepared)
            return PreparationLink(frozen, prepared)

    @staticmethod
    def _insert(conn, key, frozen, progress):
        request = frozen.preparation.packet.request
        conn.execute(text('INSERT INTO planning.curation_preparation_links '
            '(tenant_id,project_id,curation_id,engagement_id,request_sha256,manifest_sha256,envelope_sha256,progress_revision) '
            'VALUES (:tenant,:project,:curation,:engagement,:request,:manifest,:envelope,:revision)'),
            {**key, 'engagement': request.document().reference.engagement_id, 'request': request.sha256,
             'manifest': frozen.preparation.sha256, 'envelope': frozen.envelope.sha256,
             'revision': progress.view.receipt.revision})
