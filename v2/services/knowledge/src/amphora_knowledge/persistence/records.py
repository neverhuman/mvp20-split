"""Owner-local immutable record projections and profile reconstruction."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Finding
from amphora_contracts_knowledge import (
    AcceptedDecision,
    DomainVocabulary,
    FailedDecision,
    GraphChangeDecision,
    GraphChangeProposal,
    GraphProposalStatus,
)

from ..authoring.canonical import KnowledgeError, canonical
from ..authoring.policy import StructuralPolicy
from ..authoring.vocabulary import Vocabulary

SCOPE = "tenant_id=:tenant AND project_id=:project AND graph_id=:graph"


def graph_key(graph):
    return {"tenant": graph.scope.tenant_id, "project": graph.scope.project_id, "graph": graph.graph_id}


@dataclass(frozen=True)
class ProposalDocument:
    proposal: GraphChangeProposal
    actor_id: str
    raw: bytes
    sha256: str

    @classmethod
    def create(cls, principal, proposal):
        principal.require("propose_graph", proposal.graph.scope)
        raw = canonical(proposal)
        if len(raw) > 262144:
            raise KnowledgeError("proposal_limit")
        return cls(proposal, principal.actor_id, raw, hashlib.sha256(raw).hexdigest())

    @property
    def key(self):
        return graph_key(self.proposal.graph) | {"change": self.proposal.change_id}

    def require_same(self, row):
        if row["actor_id"] != self.actor_id:
            raise KnowledgeError("proposal_actor_conflict")
        if row["request_sha256"] != self.sha256 or bytes(row["canonical_bytes"]) != self.raw:
            raise KnowledgeError("proposal_identity_conflict")

    def accepted(self, head):
        return self._decision(AcceptedDecision(outcome="accepted", head=head))

    def failed(self, code):
        outcome = "conflict" if code == "stale_head" else "rejected"
        return self._decision(FailedDecision(outcome=outcome,
            findings=(Finding(code=code, location="proposal", message="Structural edit was not accepted"),)))

    def _decision(self, decision):
        return GraphChangeDecision(wire_version="1", graph=self.proposal.graph, change_id=self.proposal.change_id,
                                   request_sha256=self.sha256, decision=decision)

    @staticmethod
    def status(row, decision):
        proposal = GraphChangeProposal.model_validate_json(bytes(row["canonical_bytes"]))
        if hashlib.sha256(canonical(proposal)).hexdigest() != row["request_sha256"]:
            raise KnowledgeError("proposal_storage_mismatch")
        if decision is not None and (decision.graph != proposal.graph or decision.change_id != proposal.change_id
                                     or decision.request_sha256 != row["request_sha256"]):
            raise KnowledgeError("decision_storage_mismatch")
        return GraphProposalStatus(wire_version="1", proposal=proposal, actor_id=row["actor_id"],
            request_sha256=row["request_sha256"], registered_at=row["registered_at"], decision=decision)


@dataclass(frozen=True)
class GraphProfile:
    vocabulary: Vocabulary
    policy: StructuralPolicy

    def storage(self):
        raw = canonical(self.vocabulary.canonical_record())
        if len(raw) > 262144:
            raise KnowledgeError("vocabulary_limit")
        return {"vocabulary_sha": self.vocabulary.reference.sha256, "policy_sha": self.policy.reference.sha256,
                "vocabulary_bytes": raw, "policy_bytes": self.policy.canonical_bytes}

    @classmethod
    def restore(cls, row):
        vocabulary = Vocabulary(DomainVocabulary.model_validate_json(bytes(row["vocabulary_bytes"])))
        policy = StructuralPolicy.from_definition(json.loads(bytes(row["policy_bytes"])))
        profile = cls(vocabulary, policy)
        if profile.storage() != {"vocabulary_sha": row["vocabulary_sha256"], "policy_sha": row["policy_sha256"],
                                 "vocabulary_bytes": bytes(row["vocabulary_bytes"]), "policy_bytes": bytes(row["policy_bytes"])}:
            raise KnowledgeError("profile_storage_mismatch")
        return profile
