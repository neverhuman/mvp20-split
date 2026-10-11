"""Project-scoped historical read; external callers never acquire producer rights."""

from dataclasses import dataclass

from amphora_contracts_core import Identifier
from amphora_contracts_planning import CampaignOriginDraft
from pydantic import TypeAdapter
from sqlalchemy import text

from ..access import Principal
from ..campaign_dispatch.journal import CompilerJournal
from ..campaign_dispatch.selection import CompilerSelection
from ..campaign_dispatch.store import CompilerStore, KEY
from ..campaign_eligibility import EligibilityConfiguration
from ..context.policy import require
from .index import OriginIndex, OriginPointer
from .projection import OriginProjection


@dataclass(frozen=True)
class HistoricalCompiler:
    principal: Principal
    journal: CompilerJournal
    selection: CompilerSelection

    @classmethod
    def load(cls, engine, scope, selection_id):
        TypeAdapter(Identifier).validate_python(selection_id, strict=True)
        params = {'tenant': scope.tenant_id, 'project': scope.project_id, 'selection': selection_id}
        with engine.connect() as connection:
            raw = connection.execute(text('SELECT canonical_bytes FROM planning.compiler_selections WHERE ' + KEY),
                                     params).scalar_one_or_none()
        require(raw is not None, 'origin_history_missing')
        candidate = CompilerSelection(bytes(raw))
        value = candidate.document()
        # Owner-internal reconstruction of retained attribution. This capability
        # is confined to read-only journals and is never returned to a caller,
        # installed as the caller's identity, or used against a peer service.
        original_reader = Principal(value.actor_id, scope, frozenset({'read_attempts'}))
        selection = CompilerSelection.restore(candidate.canonical, original_reader)
        configuration = EligibilityConfiguration(value.witness.eligibility_json.encode())
        store = CompilerStore(engine, value.runtime.owner_id, value.runtime.actor_id, configuration)
        journal = CompilerJournal(store)
        selected = journal.selected(original_reader, selection_id)
        require(selected is not None and selected.selection == selection, 'origin_history_selection')
        return cls(original_reader, journal, selection)

    def operation(self, effect_id):
        operation = self.journal.read(self.principal, self.selection.effect_id, effect_id)
        require(operation is not None, 'origin_history_effect')
        return operation


class CampaignOriginReader:
    def __init__(self, engine):
        self.engine = engine

    def read(self, principal, draft):
        # Authorization precedes even the indexed existence check.
        principal.require('read_campaign_origin', draft.scope)
        draft = CampaignOriginDraft.model_validate_json(draft.model_dump_json())
        with self.engine.connect() as connection:
            pointer = OriginIndex.read(connection, draft)
        if pointer is None:
            return None
        value = pointer.document()
        history = HistoricalCompiler.load(self.engine, principal.scope, value.selection_id)
        operation = history.operation(value.effect_id)
        require(OriginPointer.bind(history.selection, operation) == pointer, 'origin_history_conflict')
        context = history.journal.context(history.principal, history.selection)
        projection = OriginProjection.bind(history.principal, history.selection, context.history.authoring,
            context.history.eligibility, operation.progress.observation)
        return OriginProjection.restore(projection.canonical, draft)


class OriginBackfill:
    """Explicit owner maintenance, at most64 supplied compiler selection IDs.

    No request-time scan or public write route. Original actor and record/read
    grants remain mandatory; each selected history is independently atomic.
    """

    def __init__(self, journal):
        self.journal = journal

    def run(self, principal, selection_ids):
        principal.require('record_attempts', principal.scope)
        principal.require('read_attempts', principal.scope)
        require(type(selection_ids) is tuple and 1 <= len(selection_ids) <= 64 and
                len(set(selection_ids)) == len(selection_ids), 'origin_backfill_selection_limit')
        for selection_id in selection_ids:
            TypeAdapter(Identifier).validate_python(selection_id, strict=True)
        count = 0
        for selection_id in selection_ids:
            selected = self.journal.selected(principal, selection_id)
            require(selected is not None, 'origin_history_selection')
            operations = self.journal.context(principal, selected.selection)
            effect, _ = operations.save()
            key = self.journal.store.key(principal, selection_id)
            with self.journal.store.engine.begin() as connection:
                self.journal.store.lock(connection, key)
                operation = operations.read(connection, key, effect.effect_id)
                if operation is not None:
                    count += OriginIndex.record(connection, selected.selection, operation) is not None
        return count
