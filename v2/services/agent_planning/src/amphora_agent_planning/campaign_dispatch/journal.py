"""Owned effect/event writes with original dependencies and final lease fences."""

from sqlalchemy import text

from ..campaign_authoring import AuthoringRequest
from ..context.policy import require
from .effect import CompilerEffect
from .history import CompilerHistory
from .operations import EFFECT_KEY, CompilerOperations
from .rounds import CompilerRounds


class CompilerJournal:
    def __init__(self, store):
        self.store = store
        self._origin = None

    def context(self, principal, selection):
        selection = self.store.checked(principal, selection)
        cached = self._origin
        if cached is not None and cached.principal == principal and cached.selection == selection:
            return cached
        history = CompilerHistory.load(self.store.engine, principal, selection)
        result = CompilerOperations(principal, selection, history)
        # Only immutable original records/derived requests are reused. No lease,
        # mutable progress, processing permission or owner observation is cached.
        self._origin = result
        return result

    def selected(self, principal, selection_id):
        principal.require('read_attempts', principal.scope)
        with self.store.engine.connect() as connection:
            return self.store.selection(connection, principal, self.store.key(principal, selection_id))

    def read(self, principal, selection_id, effect_id):
        selected = self.selected(principal, selection_id)
        if selected is None:
            return None
        operations = self.context(principal, selected.selection)
        key = self.store.key(principal, selection_id)
        with self.store.engine.begin() as connection:
            self.store.lock(connection, key)
            return operations.read(connection, key, effect_id)

    def read_round(self, principal, selection_id, check_id):
        selected = self.selected(principal, selection_id)
        if selected is None:
            return None
        operations = self.context(principal, selected.selection)
        operations.batch(check_id)
        key = self.store.key(principal, selection_id)
        with self.store.engine.begin() as connection:
            self.store.lock(connection, key)
            return CompilerRounds(operations).read(connection, key, check_id)

    def prepare_save(self, principal, lease):
        operations = self.context(principal, lease.selection)
        effect, request = operations.save()
        key = self.store.key(principal, lease.selection.effect_id)
        with self.store.engine.begin() as connection:
            self.store.lock(connection, key)
            self.store.fence_write(connection, principal, lease)
            result = operations.insert(connection, key, effect, request)
            self.store.fence_write(connection, principal, lease)
            return result

    def prepare_validation(self, principal, lease):
        operations = self.context(principal, lease.selection)
        save, _ = operations.save()
        key = self.store.key(principal, lease.selection.effect_id)
        with self.store.engine.begin() as connection:
            self.store.lock(connection, key)
            self.store.fence_write(connection, principal, lease)
            saved = operations.read(connection, key, save.effect_id)
            require(saved is not None and saved.progress.state == 'saved', 'compiler_saved_dependency')
            effect = CompilerEffect.authoring(lease.selection, principal, operations.history.authoring,
                operations.history.eligibility, saved=saved.progress.observation.outcome)
            request = AuthoringRequest(effect.document().owner_id, effect.command().canonical_bytes)
            result = operations.insert(connection, key, effect, request)
            self.store.fence_write(connection, principal, lease)
            return result

    def prepare_round(self, principal, lease, check_id):
        operations = self.context(principal, lease.selection)
        operations.batch(check_id)  # Derive once before taking the SQL lock.
        key = self.store.key(principal, lease.selection.effect_id)
        with self.store.engine.begin() as connection:
            self.store.lock(connection, key)
            self.store.fence_write(connection, principal, lease)
            result = CompilerRounds(operations).prepare(connection, key, check_id)
            self.store.fence_write(connection, principal, lease)
            return result

    def append(self, principal, lease, effect_id, expected_position, event):
        require(type(expected_position) is int and 1 <= expected_position < 64, 'compiler_expected_position')
        operations = self.context(principal, lease.selection)
        key = self.store.key(principal, lease.selection.effect_id)
        with self.store.engine.begin() as connection:
            self.store.lock(connection, key)
            self.store.fence_write(connection, principal, lease)
            current = operations.read(connection, key, effect_id)
            require(current is not None, 'compiler_effect_unknown')
            if current.progress.position > expected_position:
                require(current.events[expected_position].event == event, 'compiler_event_conflict')
                self.store.fence_write(connection, principal, lease)
                return current
            require(current.progress.position == expected_position, 'compiler_event_position')
            position = expected_position + 1
            event.apply(current.progress, lease.selection, current.effect, current.request, position)
            params = key | {'effect': effect_id}
            operations.insert_event(connection, params, event, position)
            changed = connection.execute(text('UPDATE planning.compiler_effect_control SET position=:position WHERE ' +
                EFFECT_KEY + ' AND position=:previous'), params | {'position': position, 'previous': expected_position})
            require(changed.rowcount == 1, 'compiler_event_position')
            result = operations.read(connection, key, effect_id)
            self.store.fence_write(connection, principal, lease)
            return result
