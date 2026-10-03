"""Owner policy proof; persistence and authenticated source loading are separate gates."""
import copy
import json

import pytest
from amphora_contracts_graph_runtime import DomainReceipt, ReceiptChainRef
from amphora_knowledge.authoring.canonical import KnowledgeError
from amphora_knowledge.corrections.policy import CorrectionPolicy

DOCUMENT = {'issuer_id': 'issuer', 'receipt_id': 'source-1', 'scope': {'tenant_id': 'test', 'project_id': 'correction'}, 'purpose': 'knowledge.synthetic_entailment', 'revision': '1', 'subject': {'artifact_id': 'subject', 'scope': {'tenant_id': 'test', 'project_id': 'correction'}, 'sha256': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'media_type': 'application/json', 'size_bytes': 2, 'schema_ref': {'schema_id': 'fixture', 'version': '1', 'sha256': 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'}}, 'outcome': {'status': 'abstained', 'reason_code': 'unknown'}}


def source(**changes):
    document = copy.deepcopy(DOCUMENT)
    document.update(changes)
    return DomainReceipt.model_validate_json(json.dumps(document))


def issue(receipt=None, previous=None, chain_id="chain", change_id="change-1", **changes):
    receipt = receipt or source()
    chain = ReceiptChainRef(scope=source().scope, issuer_id="issuer", chain_id=chain_id)
    return CorrectionPolicy().issue(chain, receipt, change_id=change_id, actor_id="author",
                                    reason_code="new_evidence", predecessor=previous, **changes)


def test_root_and_successor_replay_preserve_original_and_make_fresh_notice():
    original = source()
    first = issue(original)
    successor_source = source(receipt_id="source-2", outcome={"status":"rejected", "reason_code":"contradicted"})
    second = issue(successor_source, first, change_id="change-2")
    assert first.view.reference == first.reference
    assert first.view.record == first.record
    assert first == issue(original)
    assert second == issue(successor_source, first, change_id="change-2")
    assert second.record.predecessor == first.reference
    assert first.record.predecessor is None and first.record.notice is None
    assert second.record.ordinal == 2
    assert second.record.receipt.outcome == successor_source.outcome
    assert second.record.source_receipt == successor_source
    assert second.record.notice.revision == first.record.receipt.revision
    assert second.record.notice.outcome.replacement_revision == second.record.receipt.revision
    assert len({original.receipt_id, first.record.receipt.receipt_id, second.record.receipt.receipt_id,
                second.record.notice.receipt_id}) == 4
    assert original.revision == "1" and original.outcome.status == "abstained"
    assert first.record.receipt.outcome.status == "abstained"


def test_distinct_chains_never_alias_same_subject_revision():
    assert issue(chain_id="one").record.receipt.revision != issue(chain_id="two").record.receipt.revision
    assert issue().reference != issue(change_id="other").reference


@pytest.mark.parametrize("field,value", [("issuer_id", "other"), ("purpose", "foreign"),
    ("scope", {"tenant_id":"other", "project_id":"correction"}),
    ("outcome", {"status":"superseded", "replacement_revision":"2", "reason_code":"old"})])
def test_mismatched_source_cannot_create_chain(field,value):
    with pytest.raises(KnowledgeError, match="correction_source_mismatch"):
        issue(source(**{field:value}))


def test_changed_subject_or_chain_cannot_continue_head():
    first = issue()
    subject = dict(DOCUMENT["subject"], artifact_id="different")
    with pytest.raises(KnowledgeError, match="correction_predecessor_mismatch"):
        issue(source(receipt_id="source-2", subject=subject), first)
    with pytest.raises(KnowledgeError, match="correction_predecessor_mismatch"):
        issue(source(receipt_id="source-2"), first, chain_id="other")
    with pytest.raises(KnowledgeError, match="correction_source_unchanged"):
        issue(source(), first)


def test_accepted_output_retains_exact_artifact_and_rejects_foreign_scope():
    output = {"kind":"artifact", "artifact":copy.deepcopy(DOCUMENT["subject"]),
              "representation":"fixture", "unit":"1"}
    receipt = source(outcome={"status":"accepted", "output":output})
    assert issue(receipt).record.receipt.outcome == receipt.outcome
    output["artifact"]["scope"] = {"tenant_id":"foreign", "project_id":"correction"}
    with pytest.raises(KnowledgeError, match="correction_output_scope_mismatch"):
        issue(source(outcome={"status":"accepted", "output":output}))
