"""At most three publish attempts; stale candidates never replace a newer head."""

from ..authoring.canonical import KnowledgeError
from .history import RebuildHistory
from .model import Candidate


class RebuildWorkflow:
    def __init__(self, store):
        self.store = store
        self.history = RebuildHistory(store.engine)

    def run(self, principal, graph, rebuild_id):
        started = self.store.begin(principal, graph, rebuild_id)
        if started.outcome != "pending":
            return started
        request, target = started.request, started.initial_head
        cursor = self.history.cursor(graph)
        for attempt in range(1, 4):
            try:
                cursor = cursor.through(self.history.tail(graph, cursor.state.revision, target), target)
                candidate = Candidate.from_cursor(request, attempt, cursor)
            except KnowledgeError as error:
                return self.store.finish(request, "failed", attempt, str(error))
            self.store.stage(candidate)
            result = self.store.publish(candidate)
            if result is not None:
                return result
            target = self.store.head(request)
        return self.store.finish(request, "deferred", 3, "rebuild_contention_limit")
