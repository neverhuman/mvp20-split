"""Append-only capture upload history reconstructed from its owned origin."""

from dataclasses import dataclass
from datetime import datetime

from amphora_contracts_core import Identifier
from amphora_contracts_planning import ProviderAttemptRef
from pydantic import TypeAdapter
from sqlalchemy import text

from ..context.policy import require
from ..publication.attempt import PublicationAttempt
from ..publication.records import advance
from .capture import CaptureArtifact, CaptureOrigin
from .events import CaptureEvent
from .history import load_origin
from .identity import CaptureIdentity
from .leases import KEY, LIVE, CaptureLeases, key, lock


@dataclass(frozen=True)
class CapturePayload:
    artifact: CaptureArtifact


@dataclass(frozen=True)
class CaptureState:
    identity: CaptureIdentity
    origin: CaptureOrigin
    attempt: PublicationAttempt | None
    events: tuple[tuple[CaptureEvent, datetime], ...]
    registered_at: datetime

    @property
    def position(self):
        return len(self.events)

    @property
    def payload(self):
        return CapturePayload(CaptureArtifact.bind(self.origin)) if self.origin.observation.capture.content else None


class CaptureJournal(CaptureLeases):
    def __init__(self, engine, publisher_id):
        TypeAdapter(Identifier).validate_python(publisher_id, strict=True)
        self.engine, self.publisher_id, self.store = engine, publisher_id, self

    def _read(self, conn, principal, params):
        row = conn.execute(text('SELECT * FROM planning.capture_publications WHERE ' + KEY), params).mappings().one_or_none()
        if row is None:
            return None
        require(row['actor_id'] == principal.actor_id, 'capture_actor')
        require(row['publisher_id'] == self.publisher_id, 'capture_configuration_conflict')
        origin = load_origin(self.engine, conn, principal, row['engagement_id'], row['ordinal'], row['observation_kind'])
        identity = CaptureIdentity.restore(principal, origin, self.publisher_id)
        require(identity.canonical == bytes(row['canonical_bytes']) and identity.sha256 == row['identity_sha256'] and
            identity.publication_id == row['publication_id'] == params['publication'], 'stored_capture_identity')
        control = conn.execute(text('SELECT position FROM planning.capture_publication_control WHERE ' + KEY), params).one()
        rows = conn.execute(text('SELECT * FROM planning.capture_publication_events WHERE ' + KEY + ' ORDER BY position'), params).mappings().all()
        require(len(rows) == control.position, 'stored_capture_position')
        artifact = CaptureArtifact.bind(origin) if origin.observation.capture.content else None
        require((artifact is None and not rows) or (artifact is not None and 0 < len(rows) <= 64), 'stored_capture_initial')
        attempt, events = None, []
        for position, event_row in enumerate(rows, 1):
            event = CaptureEvent(bytes(event_row['canonical_bytes']))
            require(event_row['position'] == position and event.sha256 == event_row['event_sha256'], 'stored_capture_event')
            attempt = event.apply(attempt, identity, artifact, position)
            events.append((event, event_row['recorded_at']))
        return CaptureState(identity, origin, attempt, tuple(events), row['registered_at'])

    def read(self, principal, publication_id):
        principal.require('read_attempts', principal.scope)
        params = key(principal, publication_id)
        with self.engine.begin() as conn:
            lock(conn, params)
            return self._read(conn, principal, params)

    @staticmethod
    def _event(conn, params, position, event):
        conn.execute(text('INSERT INTO planning.capture_publication_events '
            '(tenant_id,project_id,publication_id,position,event_sha256,canonical_bytes) '
            'VALUES (:tenant,:project,:publication,:position,:digest,:body)'),
            {**params, 'position': position, 'digest': event.sha256, 'body': event.canonical})

    def register(self, principal, attempt, *, kind='primary'):
        attempt = ProviderAttemptRef.model_validate(attempt.model_dump(mode='python', warnings=False))
        principal.require('record_attempts', attempt.engagement.scope)
        principal.require('read_attempts', attempt.engagement.scope)
        with self.engine.begin() as conn:
            origin = load_origin(self.engine, conn, principal, attempt.engagement.engagement_id, attempt.ordinal, kind)
            require(origin.observation.document().attempt == attempt, 'capture_attempt')
            identity = CaptureIdentity.bind(principal, origin, self.publisher_id)
            params = key(principal, identity.publication_id)
            lock(conn, params)
            previous = self._read(conn, principal, params)
            if previous is not None:
                require(previous.identity == identity, 'capture_identity_conflict')
                return previous
            artifact = CaptureArtifact.bind(origin) if origin.observation.capture.content else None
            conn.execute(text('INSERT INTO planning.capture_publications '
                '(tenant_id,project_id,publication_id,actor_id,publisher_id,engagement_id,ordinal,observation_kind,identity_sha256,canonical_bytes) '
                'VALUES (:tenant,:project,:publication,:actor,:publisher,:engagement,:ordinal,:kind,:digest,:body)'),
                {**params, 'actor': principal.actor_id, 'publisher': self.publisher_id,
                 'engagement': attempt.engagement.engagement_id, 'ordinal': attempt.ordinal, 'kind': kind,
                 'digest': identity.sha256, 'body': identity.canonical})
            conn.execute(text('INSERT INTO planning.capture_publication_control '
                '(tenant_id,project_id,publication_id,position) VALUES (:tenant,:project,:publication,:position)'),
                {**params, 'position': int(artifact is not None)})
            if artifact is not None:
                self._event(conn, params, 1, CaptureEvent.record(1, PublicationAttempt.first(identity), 'prepared', None))
            return self._read(conn, principal, params)

    def advance(self, principal, lease, expected_position, action, data=None):
        require(type(expected_position) is int and 1 <= expected_position < 64, 'capture_event_limit')
        with self.engine.begin() as conn:
            lock(conn, key(principal, lease.publication_id))
            params = self._lease(conn, principal, lease)
            state = self._read(conn, principal, params)
            require(state.position == expected_position, 'capture_position_conflict')
            require(state.attempt is not None, 'capture_upload_missing')
            changed = advance(state.attempt, action, data, state.identity, state.payload.artifact)
            event = CaptureEvent.record(expected_position + 1, changed, action, data)
            self._event(conn, params, expected_position + 1, event)
            result = conn.execute(text('UPDATE planning.capture_publication_control SET position=:next WHERE ' + LIVE +
                ' AND position=:previous'), {**params, 'next': expected_position + 1, 'previous': expected_position})
            require(result.rowcount == 1, 'capture_lease_or_position_lost')
            return self._read(conn, principal, params)
