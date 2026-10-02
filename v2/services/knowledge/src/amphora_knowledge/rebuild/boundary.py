"""Map private rebuild domain state to the public transport contract."""

from amphora_contracts_knowledge import (
    GraphRebuildRequest,
    GraphRebuildStatus,
    PublishedRebuild,
    UnpublishedRebuild,
)


def response(status):
    if status is None:
        return None
    result = None
    if status.outcome == "published":
        result = PublishedRebuild(outcome="published", head=status.result_head, attempts=status.attempts)
    elif status.outcome != "pending":
        result = UnpublishedRebuild(outcome=status.outcome, code=status.code, attempts=status.attempts)
    request = GraphRebuildRequest(wire_version="1", graph=status.request.graph, rebuild_id=status.request.rebuild_id)
    return GraphRebuildStatus(wire_version="1", request=request, actor_id=status.request.actor_id,
        initial_head=status.initial_head, result=result)


class RebuildBoundary:
    def __init__(self, workflow):
        self.workflow = workflow

    def submit(self, principal, request):
        return response(self.workflow.run(principal, request.graph, request.rebuild_id))

    def read(self, principal, request):
        return response(self.workflow.store.status(principal, request.graph, request.rebuild_id))
