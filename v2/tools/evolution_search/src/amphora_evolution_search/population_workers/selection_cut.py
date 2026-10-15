"""One closed owner cut for proposed checkpoint counters; never a new budget grant."""
from dataclasses import dataclass

from amphora_contracts_graph_runtime import GraphReadCut

from ..ranking import require
from .method_plan import authored_invocation


def reaches(body,source,target):
    pending=[source];seen=set()
    while pending:
        value=pending.pop()
        if value==target:return True
        if value in seen:continue
        seen.add(value)
        pending.extend(edge.target for edge in body.edges if edge.source==value)
    return False


def scope_key(occurrences):
    return tuple(occurrence.model_dump_json() for occurrence in occurrences)


@dataclass(frozen=True)
class SelectionReadCut:
    cut: GraphReadCut
    attempts_issued: int
    activations_created: int

    @classmethod
    def load(cls,inspection,capture,plan):
        require(capture.snapshot.cut.plan_sha256==plan.sha256,"selection_counter_plan")
        invocation=inspection.attempt.invocation
        own=tuple(node for node in capture.nodes if node.activation_id==invocation.activation_id)
        require(len(own)==1 and own[0].kind=="invoke" and own[0].status=="issued","selection_counter_owner")
        own=own[0]
        require(authored_invocation(plan,own).tool==invocation.tool,"selection_counter_tool")
        # Only the current generation-loop spine may remain active. Every scope
        # finish must depend on this checkpoint, so a coordinator cannot open a
        # future generation while its proposed counters are being published.
        frames={};body=plan.document.definition.body;prefix=()
        for occurrence in own.path.occurrences:
            require(occurrence.kind=="loop","selection_counter_nonserial_scope")
            node=next((node for node in body.nodes if node.node_id==occurrence.node_id),None)
            require(node is not None and node.kind=="iterate","selection_counter_loop")
            frames[scope_key(prefix)]=(body,node.node_id,True)
            prefix=(*prefix,occurrence);body=node.body
        frames[scope_key(prefix)]=(body,own.path.node_id,False)
        for body,anchor,_ in frames.values():
            finishes=tuple(node for node in body.nodes if node.kind=="finish")
            require(len(finishes)==1 and reaches(body,anchor,finishes[0].node_id),"selection_counter_finish_barrier")
        for node in capture.nodes:
            if node.activation_id==own.activation_id or node.status in {"succeeded","failed","skipped","blocked"}:continue
            frame=frames.get(scope_key(node.path.occurrences))
            require(frame is not None,"selection_counter_parallel_scope")
            body,anchor,ancestor=frame
            if ancestor and node.path.node_id==anchor and node.kind=="iterate":continue
            require(node.status=="waiting" and reaches(body,anchor,node.path.node_id),"selection_counter_parallel_work")
        identities=set();own_attempt=None
        for node in capture.nodes:
            if node.kind!="invoke":continue
            detail=inspection.details(capture,node)
            for attempt in detail.attempts:
                require(attempt.attempt_id not in identities,"selection_counter_attempt_duplicate")
                identities.add(attempt.attempt_id)
                if node.activation_id==own.activation_id and attempt.attempt_id==invocation.attempt_id:
                    own_attempt=attempt
        require(own_attempt is not None and own_attempt.status=="leased" and not own_attempt.settled
            and own_attempt.fence==invocation.fence and own_attempt.worker_id==inspection.runtime.identity.actor_id,
            "selection_counter_attempt_owner")
        return cls(capture.snapshot.cut,len(identities),len(capture.nodes))
