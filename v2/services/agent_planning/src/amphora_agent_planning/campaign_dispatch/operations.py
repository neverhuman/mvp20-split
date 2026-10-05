"""Derive/replay one stored command with exact original and saved dependencies."""

from threading import Lock

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter
from sqlalchemy import text

from ..campaign_authoring import AuthoringRequest
from ..campaign_eligibility import EligibilityBatch
from ..context.policy import require
from .effect import CompilerEffect
from .events import CompilerEvent
from .records import CompilerOperation, StoredCompilerEvent
from .store import KEY

EFFECT_KEY = KEY + ' AND effect_id=:effect'


class CompilerOperations:
    def __init__(self, principal, selection, history):
        self.principal, self.selection, self.history = principal, selection, history
        self._batches = {}
        self._batch_lock = Lock()
        self._save = None

    def save(self):
        if self._save is None:
            effect = CompilerEffect.authoring(self.selection, self.principal, self.history.authoring, self.history.eligibility)
            self._save = effect, self.history.authoring.save()
        return self._save

    def batch(self, check_id):
        with self._batch_lock:
            if check_id in self._batches:
                return self._batches[check_id]
        batch = EligibilityBatch.bind(self.history.authoring.review, self.history.authoring.budget,
                                      self.history.eligibility, check_id)
        prepared = tuple((CompilerEffect._encode(self.selection, 'resolve',
            self.history.eligibility.document().owner_id, request.command.canonical_bytes, check_id=check_id,
            descriptor_sha256=request.selected.document().lock.descriptor_sha256), request) for request in batch.requests)
        with self._batch_lock:
            if len(self._batches) >= 2:
                self._batches.pop(next(iter(self._batches)))
            self._batches[check_id] = prepared
        return prepared

    def expected(self, connection, key, effect):
        value = effect.document()
        if value.kind == 'save':
            expected, request = self.save()
        elif value.kind == 'validate':
            save, _ = self.save()
            stored = self.read(connection, key, save.effect_id)
            require(stored is not None and stored.progress.state == 'saved', 'compiler_saved_dependency')
            outcome = stored.progress.observation.outcome
            expected = CompilerEffect.authoring(self.selection, self.principal, self.history.authoring,
                                                 self.history.eligibility, saved=outcome)
            request = AuthoringRequest(expected.document().owner_id, expected.command().canonical_bytes)
        else:
            matches = [(candidate, request) for candidate, request in self.batch(value.check_id)
                       if candidate.document().descriptor_sha256 == value.descriptor_sha256]
            require(len(matches) == 1, 'compiler_stored_tool')
            expected, request = matches[0]
        require(expected == effect, 'compiler_stored_effect')
        return request

    def read(self, connection, key, identifier):
        TypeAdapter(Identifier).validate_python(identifier, strict=True)
        params = key | {'effect': identifier}
        row = connection.execute(text('SELECT * FROM planning.compiler_effects WHERE ' + EFFECT_KEY), params).mappings().first()
        if row is None:
            return None
        effect = CompilerEffect(bytes(row['canonical_bytes']))
        value = effect.document()
        require(effect.effect_id == identifier and effect.sha256 == row['effect_sha256'] and
                value.kind == row['kind'] and value.check_id == row['check_id'] and
                value.descriptor_sha256 == row['descriptor_sha256'], 'compiler_stored_effect_columns')
        request = self.expected(connection, key, effect)
        records = connection.execute(text('SELECT * FROM planning.compiler_events WHERE ' + EFFECT_KEY +
            ' ORDER BY position LIMIT 65'), params).mappings().all()
        require(1 <= len(records) <= 64, 'compiler_stored_event_count')
        progress, events = None, []
        for position, item in enumerate(records, 1):
            event = CompilerEvent(bytes(item['canonical_bytes']))
            require(item['position'] == position and event.sha256 == item['event_sha256'], 'compiler_stored_event_columns')
            progress = event.apply(progress, self.selection, effect, request, position)
            events.append(StoredCompilerEvent(event, item['recorded_at']))
        actual = connection.execute(text('SELECT position FROM planning.compiler_effect_control WHERE ' + EFFECT_KEY),
                                    params).scalar_one_or_none()
        require(actual == progress.position, 'compiler_stored_position')
        return CompilerOperation(effect, request, progress, row['registered_at'], tuple(events))

    def insert(self, connection, key, effect, request):
        existing = self.read(connection, key, effect.effect_id)
        if existing is not None:
            require(existing.effect == effect, 'compiler_effect_conflict')
            return existing
        value = effect.document()
        first = CompilerEvent.record(effect, 1, 'prepared')
        first.apply(None, self.selection, effect, request, 1)
        params = key | {'effect': effect.effect_id, 'kind': value.kind, 'check': value.check_id,
            'descriptor': value.descriptor_sha256, 'digest': effect.sha256, 'body': effect.canonical}
        connection.execute(text('INSERT INTO planning.compiler_effects '
            '(tenant_id,project_id,selection_id,effect_id,kind,check_id,descriptor_sha256,effect_sha256,canonical_bytes) '
            'VALUES (:tenant,:project,:selection,:effect,:kind,:check,:descriptor,:digest,:body)'), params)
        connection.execute(text('INSERT INTO planning.compiler_effect_control '
            '(tenant_id,project_id,selection_id,effect_id,position) VALUES (:tenant,:project,:selection,:effect,1)'), params)
        self.insert_event(connection, params, first, 1)
        return self.read(connection, key, effect.effect_id)

    @staticmethod
    def insert_event(connection, params, event, position):
        connection.execute(text('INSERT INTO planning.compiler_events '
            '(tenant_id,project_id,selection_id,effect_id,position,event_sha256,canonical_bytes) '
            'VALUES (:tenant,:project,:selection,:effect,:position,:digest,:body)'),
            params | {'position': position, 'digest': event.sha256, 'body': event.canonical})
