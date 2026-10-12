"""One immutable declaration origin and bounded upload history per curation."""
from dataclasses import dataclass
from sqlalchemy import text

from ..context.policy import require
from ..curation_jobs.journal import CurationJobs, key_for, KEY
from ..publication.attempt import PublicationAttempt
from ..publication.records import advance
from .origin import DeclarationOrigin, DeclarationArtifact
from .events import DeclarationEvent


@dataclass(frozen=True)
class DeclarationPayload:
    artifact: DeclarationArtifact


@dataclass(frozen=True)
class DeclarationState:
    identity: DeclarationOrigin
    attempt: PublicationAttempt
    events: tuple[DeclarationEvent, ...]

    @property
    def position(self):
        return len(self.events)

    @property
    def payload(self):
        return DeclarationPayload(self.identity.artifact())


class DeclarationJournal:
    def __init__(self, engine):
        self.engine, self.store = engine, self
        self.jobs = CurationJobs(engine)

    def _read(self, conn, principal, key):
        original = self.jobs._original(conn, principal, key)
        if original is None:
            return None
        row = conn.execute(text('SELECT * FROM planning.curation_declarations WHERE ' + KEY), key).mappings().one_or_none()
        if row is None:
            return None
        origin = DeclarationOrigin.restore(bytes(row['origin_bytes']))
        require(origin.sha256 == row['origin_sha256'] and origin.scope == principal.scope
                and origin.actor_id == principal.actor_id and origin.incoming().command == original.incoming.command,
                'curation_declaration_original_binding')
        rows = conn.execute(text('SELECT * FROM planning.curation_declaration_events WHERE ' + KEY +
            ' ORDER BY position LIMIT 65'), key).mappings().all()
        require(0 < len(rows) <= 64, 'curation_declaration_history_bound')
        artifact, attempt, events = origin.artifact(), None, []
        for index, item in enumerate(rows, 1):
            event = DeclarationEvent(bytes(item['event_bytes']))
            require(item['position'] == index and item['event_sha256'] == event.sha256, 'curation_declaration_event_index')
            attempt = event.apply(attempt, origin, artifact, index)
            events.append(event)
        return DeclarationState(origin, attempt, tuple(events))

    def read(self, principal, curation_id):
        principal.require('execute_curations', principal.scope)
        key = key_for(principal, curation_id)
        with self.engine.begin() as conn:
            self.jobs._lock(conn, key)
            return self._read(conn, principal, key)

    def register(self, principal, lease, policy, original):
        principal.require('execute_curations', principal.scope)
        origin = DeclarationOrigin.bind(policy, original)
        require(origin.scope == principal.scope and origin.actor_id == principal.actor_id
                and origin.publication_id == lease.curation_id, 'curation_declaration_actor')
        key = key_for(principal, lease.curation_id)
        with self.engine.begin() as conn:
            self.jobs._lock(conn, key)
            existing = self._read(conn, principal, key)
            if existing is not None:
                require(existing.identity == origin, 'curation_declaration_conflict')
                return existing
            self._guard(conn, principal, lease, key)
            actual = self.jobs._original(conn, principal, key)
            require(actual.incoming.command == origin.incoming().command, 'curation_declaration_original_binding')
            conn.execute(text('INSERT INTO planning.curation_declarations '
                '(tenant_id,project_id,curation_id,origin_sha256,origin_bytes) VALUES '
                '(:tenant,:project,:curation,:digest,:body)'), {**key, 'digest': origin.sha256, 'body': origin.canonical})
            attempt = PublicationAttempt.first(origin)
            self._event(conn, key, DeclarationEvent.record(1, attempt, 'prepared', None), 1)
            return self._read(conn, principal, key)

    @staticmethod
    def _event(conn, key, event, position):
        conn.execute(text('INSERT INTO planning.curation_declaration_events '
            '(tenant_id,project_id,curation_id,position,event_sha256,event_bytes) '
            'VALUES (:tenant,:project,:curation,:position,:digest,:body)'),
            {**key, 'position': position, 'digest': event.sha256, 'body': event.canonical})

    def _guard(self, conn, principal, lease, key):
        progress, _ = self.jobs._owned(conn, principal, lease, key)
        require(progress.view.receipt.phase == 'assembling', 'curation_declaration_job_phase')

    def guard(self, principal, lease):
        principal.require('execute_curations', principal.scope)
        key = key_for(principal, lease.curation_id)
        with self.engine.begin() as conn:
            self._guard(conn, principal, lease, key)

    def advance(self, principal, lease, expected_position, action, data=None):
        principal.require('execute_curations', principal.scope)
        key = key_for(principal, lease.curation_id)
        with self.engine.begin() as conn:
            self._guard(conn, principal, lease, key)
            state = self._read(conn, principal, key)
            require(state is not None and state.position == expected_position, 'curation_declaration_position')
            result = advance(state.attempt, action, data, state.identity, state.payload.artifact)
            event = DeclarationEvent.record(state.position + 1, result, action, data)
            require(event.apply(state.attempt, state.identity, state.payload.artifact, state.position + 1) == result,
                    'curation_declaration_transition')
            self._event(conn, key, event, state.position + 1)
            return self._read(conn, principal, key)
