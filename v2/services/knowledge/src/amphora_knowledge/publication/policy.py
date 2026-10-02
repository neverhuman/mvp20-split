"""Synthetic logical conjunction policy; never scientific eligibility."""

import hashlib

from amphora_contracts_graph_runtime import DomainReceipt

from ..authoring.canonical import KnowledgeError
from .records import encoded


class LogicalReceiptPolicy:
    version = "knowledge.synthetic_entailment.v1"
    purpose = "knowledge.synthetic_entailment"

    @staticmethod
    def disposition(result):
        findings = result.findings
        if tuple(item.target for item in findings) != result.request.targets:
            raise KnowledgeError("publication_findings_mismatch")
        complete = result.outcome.status == "complete"
        for item in findings:
            expected = "unknown"
            if complete and item.positive != item.negative:
                expected = "supported" if item.positive else "contradicted"
            if item.status != expected or item.conflict != (item.positive and item.negative):
                raise KnowledgeError("publication_findings_mismatch")
        if not complete:
            return "abstained", "logical_incomplete"
        if any(item.conflict for item in findings):
            return "abstained", "logical_conflict"
        if any(item.status == "contradicted" for item in findings):
            return "rejected", "logical_contradicted"
        if any(item.status == "unknown" for item in findings):
            return "abstained", "logical_unknown"
        return "accepted", None

    def issue(self, document, progress, finalized):
        finalized._at("finalized")
        artifact, publisher = progress.payload.artifact, progress.publisher
        status, reason = self.disposition(artifact.result)
        outcome = ({"status": "accepted", "output": {"kind": "artifact",
            "artifact": finalized.result.artifact.model_dump(mode="json"),
            "representation": "knowledge.reasoning_result.v1", "unit": "1"}}
            if status == "accepted" else {"status": status, "reason_code": reason})
        identity = encoded({"policy": self.version, "request_sha256": document.sha256, "actor": document.actor_id,
            "publisher": publisher.actor_id, "issuer": publisher.issuer_id,
            "derivation": finalized.result.model_dump(mode="json")})
        return DomainReceipt.model_validate_json(encoded({"schema_version": "1", "issuer_id": publisher.issuer_id,
            "receipt_id": "knowledge-" + hashlib.sha256(identity).hexdigest(), "scope": document.request.graph.scope.model_dump(mode="json"),
            "purpose": self.purpose, "revision": "1", "subject": artifact.result.request.subject.model_dump(mode="json"),
            "outcome": outcome}))
