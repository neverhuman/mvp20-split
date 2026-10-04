"""Exact presence and structural acceptance; never scientific adequacy."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_knowledge import AcceptedGraphChange, GraphProposalStatus

from ..context.policy import require
from ..publication.records import encode
from .request import MODELS


@dataclass(frozen=True)
class OwnerOutcome:
    state: str
    canonical: bytes

    @classmethod
    def research(cls, request, record):
        require(request.owner == "research" and type(record) is MODELS[request.kind], "handoff_receipt_kind")
        record = MODELS[request.kind].model_validate_json(record.model_dump_json(warnings=False))
        require(encode(record.model_dump(mode="json")) == request.canonical, "handoff_record_mismatch")
        return cls._record(request, "acknowledged", {"authority": "declaration_presence", "record": record.model_dump(mode="json")})

    @classmethod
    def knowledge(cls, request, status, accepted=None):
        require(request.owner == "knowledge", "handoff_receipt_kind")
        status = GraphProposalStatus.model_validate_json(status.model_dump_json(warnings=False))
        proposal = request.document()
        require(encode(status.proposal.model_dump(mode="json")) == request.canonical and
            status.actor_id == request.selection.document()["actor_id"] and status.request_sha256 == request.sha256,
            "handoff_status_binding")
        decision = status.decision
        body = {"authority": "structural_only", "status": status.model_dump(mode="json"), "accepted": None}
        if decision is None:
            require(accepted is None, "handoff_unexpected_acceptance")
            return cls._record(request, "pending", body)
        require(decision.graph == proposal.graph and decision.change_id == proposal.change_id and
            decision.request_sha256 == request.sha256, "handoff_decision_binding")
        if decision.decision.outcome != "accepted":
            require(accepted is None, "handoff_unexpected_acceptance")
            return cls._record(request, decision.decision.outcome, body)
        if accepted is None:
            return cls._record(request, "awaiting_accepted_readback", body)
        accepted = AcceptedGraphChange.model_validate_json(accepted.model_dump_json(warnings=False))
        head, content = decision.decision.head, accepted.content
        position = 1 if proposal.base is None else proposal.base.change.position + 1
        require(accepted.reference == head.change and content.resulting_snapshot == head.snapshot and
            accepted.reference.graph == proposal.graph and accepted.reference.change_id == proposal.change_id and
            accepted.reference.position == content.position == head.snapshot.revision == position and
            head.snapshot.graph == proposal.graph and content.actor_id == status.actor_id and
            content.policy == proposal.policy and encode(content.proposal.model_dump(mode="json")) == request.canonical and
            hashlib.sha256(encode(content.model_dump(mode="json"))).hexdigest() == accepted.reference.sha256,
            "handoff_accepted_binding")
        body["accepted"] = accepted.model_dump(mode="json")
        return cls._record(request, "acknowledged", body)

    @classmethod
    def _record(cls, request, state, body):
        raw = encode({"format": "planning-owner-outcome.v1", "effect_id": request.selection.effect_id,
            "request_sha256": request.sha256, "state": state, **body})
        require(len(raw) <= 2097152, "handoff_receipt_limit")
        return cls(state, raw)
