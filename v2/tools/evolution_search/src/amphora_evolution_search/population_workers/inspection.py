"""Tool-owned bounded reads of public Runtime evidence; no scheduling or owner SQL."""
from dataclasses import dataclass

from amphora_contracts_execution_proofs import AcceptedToolExecution
from amphora_contracts_graph_runtime import GraphNodeDetail, GraphNodeViewV3, GraphReadSnapshot, GraphSnapshotPage
from amphora_contracts_node_inputs import NodeInputObservation
from amphora_contracts_runtime import CompletionRecord
from amphora_tool_protocol import ProtocolError

from ..ranking import require


class ObservationChanged(ProtocolError):
    """Discard this cut and capture again; never splice pages across revisions."""


@dataclass(frozen=True)
class GraphCapture:
    snapshot: GraphReadSnapshot
    nodes: tuple[GraphNodeViewV3, ...]


@dataclass(frozen=True)
class ObservedMethod:
    detail: GraphNodeDetail
    inputs: NodeInputObservation
    producer: AcceptedToolExecution | None
    completion: CompletionRecord | None


class PopulationInspection:
    def __init__(self, runtime, attempt):
        self.runtime, self.attempt = runtime, attempt

    def get(self, model, path, query=None):
        self.attempt.check()
        kwargs = {} if query is None else {"query": query}
        reply = self.runtime.transport.request("GET", path, **kwargs)
        self.attempt.check()
        if reply.status in {409, 410}:
            raise ObservationChanged("population_observation_changed")
        if reply.status != 200:
            reason = ("population_observation_unavailable" if reply.status == 503 else
                "population_observation_denied" if reply.status in {401, 403} else "population_observation_rejected")
            raise ProtocolError(reason)
        try:
            return model.model_validate_json(reply.body)
        except ValueError as error:
            raise ProtocolError("population_observation_invalid") from error

    def capture(self, run_id, max_nodes):
        require(type(max_nodes) is int and 1 <= max_nodes <= 100000, "population_observation_bound")
        self.attempt.refresh()
        nodes, identities, cursors = [], set(), set()
        snapshot = None
        query = {"limit": 100}
        while True:
            page = self.get(GraphSnapshotPage, f"/v1/graph-observations/{run_id}/nodes", query)
            cut = page.snapshot.cut
            require(cut.scope == self.runtime.identity.scope and cut.run_id == run_id,
                    "population_observation_scope")
            require(page.snapshot.node_count <= max_nodes, "population_observation_bound")
            if snapshot is None:
                snapshot = page.snapshot
            require(page.snapshot == snapshot, "population_observation_mixed_cut")
            for node in page.nodes:
                require(node.activation_id not in identities, "population_observation_duplicate")
                identities.add(node.activation_id)
                nodes.append(node)
            require(len(nodes) <= snapshot.node_count, "population_observation_count")
            if page.next_cursor is None:
                break
            require(page.nodes and page.next_cursor not in cursors, "population_observation_cursor")
            cursors.add(page.next_cursor)
            query = {"limit": 100, "cursor": page.next_cursor}
        require(len(nodes) == snapshot.node_count, "population_observation_incomplete")
        return GraphCapture(snapshot, tuple(nodes))

    def details(self, capture, node):
        require(node in capture.nodes, "population_node_outside_capture")
        cut=capture.snapshot.cut
        detail=self.get(GraphNodeDetail,f"/v1/graph-observations/{cut.run_id}/nodes/{node.activation_id}",
            {"snapshot_token":capture.snapshot.snapshot_token,"limit":100})
        require(detail.cut==cut and detail.node==node and detail.next_cursor is None,"population_method_detail_cut")
        return detail

    def method(self, capture, node):
        require(node in capture.nodes and node.kind == "invoke" and (node.status in {"succeeded", "failed", "skipped"}
                    or (node.status == "blocked" and node.reason_code == "graph_dependency_unavailable")),
                "population_method_not_terminal")
        cut = capture.snapshot.cut
        path = f"/v1/graph-observations/{cut.run_id}/nodes/{node.activation_id}"
        detail = self.details(capture,node)
        # Runtime's configured per-activation attempt bound is100, so this page must
        # contain every attempt. A continuation rejects rather than dropping history.
        inputs = self.get(NodeInputObservation, path + "/inputs")
        require(inputs.scope == cut.scope and inputs.run_id == cut.run_id
            and inputs.activation_id == node.activation_id and inputs.scope_key == detail.scope_key
            and inputs.observed_run_revision >= cut.revision,
            "population_method_input_identity")
        producer = completion = None
        if node.status == "succeeded":
            accepted = tuple(a for a in detail.attempts if a.settled and a.status == "succeeded" and a.canonical_result)
            require(len(accepted) == 1 and accepted[0].completion_id is not None and inputs.invocation is not None,
                    "population_method_accepted_attempt")
            attempt = accepted[0]
            producer = self.get(AcceptedToolExecution,
                f"/v1/runs/{cut.run_id}/completions/{attempt.completion_id}/producer")
            require(producer.invocation == inputs.invocation and producer.worker_id == attempt.worker_id,
                    "population_method_producer_inputs")
            completion = producer.completion
            require(completion.canonical_result and completion.result.outcome.status == "succeeded",
                    "population_method_producer_result")
        elif detail.attempts:
            attempt = max(detail.attempts, key=lambda item: item.fence)
            require(node.status == "failed" and attempt.settled and attempt.status in {"failed", "expired", "cancelled", "abstained"},
                    "population_method_failure_attempt")
            if attempt.completion_id is not None:
                completion = self.get(CompletionRecord,
                    f"/v1/runs/{cut.run_id}/completions/{attempt.completion_id}")
        if completion is not None:
            require(inputs.invocation is not None and completion.scope == cut.scope and completion.run_id == cut.run_id
                and completion.activation_id == node.activation_id and completion.completion_id == attempt.completion_id
                and completion.accepted_run_revision <= cut.revision
                and completion.result.invocation_id == inputs.invocation.invocation_id
                and completion.result.attempt_id == attempt.attempt_id and completion.result.fence == attempt.fence,
                "population_method_completion_identity")
        return ObservedMethod(detail, inputs, producer, completion)
