"""Read-only owner adapter: grants and exact persisted identity precede projection."""

from ..authoring.canonical import KnowledgeError
from .projection import GraphExploration


class ExplorationBoundary:
    def __init__(self, ledger):
        self.ledger = ledger

    def _view(self, principal, revision):
        snapshot = self.ledger.snapshot(principal, revision)
        if snapshot is None:
            return None
        try:
            return GraphExploration(snapshot)
        except (KnowledgeError, ValueError, RecursionError) as error:
            raise KnowledgeError("stored_exploration_invalid") from error

    def catalog(self, principal, revision):
        view = self._view(principal, revision)
        return None if view is None else view.catalog()

    def search(self, principal, query):
        view = self._view(principal, query.revision)
        return None if view is None else view.search(query)

    def neighborhood(self, principal, query):
        view = self._view(principal, query.revision)
        return None if view is None else view.neighborhood(query)

    def detail(self, principal, query):
        view = self._view(principal, query.revision)
        return None if view is None else view.detail(query)
