"""Bounded, exact ordered-history verification and semantic reconstruction."""

from ..authoring.canonical import KnowledgeError
from ..authoring.state import GraphState
from .cursor import ReplayCursor
from .cursor import ReplayedGraph as ReplayedGraph


class GraphReplay:
    def __init__(self, graph, vocabulary, policy, max_changes=10000):
        if type(max_changes) is not int or not 1 <= max_changes <= 10000:
            raise KnowledgeError("invalid_replay_limit")
        self.graph, self.vocabulary, self.policy = graph, vocabulary, policy
        self.max_changes = max_changes

    def cursor(self):
        return ReplayCursor(GraphState(self.graph, self.vocabulary, self.policy), None, frozenset(), self.max_changes)

    def rebuild(self, records):
        cursor = self.cursor()
        for record in records:
            cursor = cursor.append(record)
        return cursor.result
