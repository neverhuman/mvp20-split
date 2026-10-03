"""Pure owner correction policy; authenticated source loading belongs to the adapter."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_graph_runtime import (
    DomainReceipt,
    ReceiptChainRef,
    ReceiptCorrection,
    ReceiptRevisionRef,
)

from ..assessment.policy import AssessmentError


def encoded(record):
    return json.dumps(record.model_dump(mode="json"), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


@dataclass(frozen=True)
class CorrectionRevision:
    record: ReceiptCorrection

    @property
    def reference(self):
        return ReceiptRevisionRef(chain=self.record.chain, ordinal=self.record.ordinal,
                                  record_sha256=hashlib.sha256(encoded(self.record)).hexdigest())


class CorrectionPolicy:
    purpose = "research.synthetic_sufficiency"

    def issue(self, chain: ReceiptChainRef, source: DomainReceipt, *, change_id: str,
              actor_id: str, reason_code: str, predecessor: CorrectionRevision | None = None):
        if (source.scope != chain.scope or source.issuer_id != chain.issuer_id
                or source.subject.scope != chain.scope or source.purpose != self.purpose
                or source.outcome.status == "superseded"):
            raise AssessmentError("correction_source_mismatch")
        if source.outcome.status == "accepted" and source.outcome.output.artifact.scope != chain.scope:
            raise AssessmentError("correction_output_scope_mismatch")
        previous = None if predecessor is None else predecessor.record
        if previous is not None and (previous.chain != chain or previous.receipt.subject != source.subject
                                    or previous.receipt.purpose != source.purpose):
            raise AssessmentError("correction_predecessor_mismatch")
        if previous is not None and previous.source_receipt.receipt_id == source.receipt_id:
            raise AssessmentError("correction_source_unchanged")
        ordinal = 1 if previous is None else previous.ordinal + 1
        prior = None if predecessor is None else predecessor.reference
        identity = json.dumps({"chain": chain.model_dump(mode="json"), "ordinal": ordinal,
            "change_id": change_id, "actor_id": actor_id, "reason_code": reason_code,
            "source": source.model_dump(mode="json"),
            "predecessor": None if prior is None else prior.model_dump(mode="json")},
            sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")
        digest = hashlib.sha256(identity).hexdigest()
        document = source.model_dump(mode="json")
        document.update(receipt_id="research-correction-" + digest, revision="revision-" + digest)
        effective = DomainReceipt.model_validate(document)
        notice = None
        if previous is not None:
            superseded = previous.receipt.model_dump(mode="json")
            superseded.update(receipt_id="research-notice-" + digest,
                outcome={"status": "superseded", "replacement_revision": effective.revision,
                         "reason_code": reason_code})
            notice = DomainReceipt.model_validate(superseded)
        record = ReceiptCorrection(chain=chain, ordinal=ordinal, change_id=change_id,
            actor_id=actor_id, reason_code=reason_code, source_receipt=source,
            predecessor=prior, receipt=effective, notice=notice)
        return CorrectionRevision(record)
