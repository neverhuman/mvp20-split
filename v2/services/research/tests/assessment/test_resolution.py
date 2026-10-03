import copy
import hashlib
import json

import pytest
from amphora_contracts_artifacts import DerivationReceipt
from amphora_contracts_knowledge import GroundLiteral, ReasoningResult, reasoning_artifact_schema
from amphora_contracts_research import (
    AssessmentAnswerRef,
    AssessmentTarget,
    SyntheticEvidenceRecord,
    synthetic_evidence_schema,
)
from amphora_research.assessment.boundary import ConfiguredAssessment
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentPeerUnavailable
from amphora_research.assessment.resolution import AssessmentResolver, fingerprint

from .test_boundary import configured
from .test_policy import OTHER, SCOPE, artifact


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


class Reader:
    scope = SCOPE

    def __init__(self):
        self.contents = {}
        self.proofs = {}
        self.used = {}

    def read(self, ref):
        self.used[ref.artifact_id] = ref
        return self.contents.get(ref.artifact_id, b"{}")

    def published(self, ref, allowed):
        proof = self.proofs[ref.artifact_id]
        if proof.origin.actor_id not in allowed:
            raise AssessmentError("untrusted_publisher")
        return self.read(ref), proof

    @property
    def consumed(self):
        return tuple(self.used[k] for k in sorted(self.used))

    def publish(self, name, value, schema, issuer, inputs, method):
        content = canonical(value)
        ref = artifact(name, schema_ref=schema, sha256=hashlib.sha256(content).hexdigest(), size_bytes=len(content))
        proof = {"schema_version": "1", "origin": {"schema_version": "1", "command_family": "artifacts.begin_derived_upload",
                 "scope": SCOPE.model_dump(mode="json"), "actor_id": issuer, "command_id": name},
                 "request_sha256": "a" * 64, "upload_id": name, "artifact": ref.model_dump(mode="json"),
                 "declaration": {"schema_version": "1", "transformation": method,
                                 "inputs": [i.model_dump(mode="json") for i in inputs]}}
        self.contents[name] = content
        self.proofs[name] = DerivationReceipt.model_validate_json(json.dumps(proof))
        return ref


class Ledger:
    def __init__(self, owner):
        self.records = {"question": owner.document.question, "need": owner.document.requirements[0].need}
        self.calls = []

    def read(self, scope, kind, identity, revision):
        self.calls.append((scope, kind, identity, revision))
        return self.records[kind]


def resolution_case(reason_mutation=None, evidence_mutation=None):
    owner, request, *_ = configured()
    graph = {"scope": SCOPE.model_dump(mode="json"), "graph_id": "domain"}
    target = {"subject": {"graph": graph, "entity_id": "a", "revision": 1}, "predicate": "supports",
              "object": {"graph": graph, "entity_id": "b", "revision": 1}, "polarity": "affirmed"}
    reason = {"wire_version": "1", "authority": "synthetic_logical_entailment", "request": {
        "wire_version": "1", "request_id": "reason", "snapshot": {"graph": graph, "revision": 1, "sha256": "a" * 64},
        "rule_set": {"graph": graph, "rule_set_id": "rules", "version": "1", "sha256": "b" * 64},
        "context": owner.document.question.applicability.model_dump(mode="json"),
        "subject": owner.document.subject.model_dump(mode="json"), "purpose": owner.document.purpose,
        "targets": [target]}, "outcome": {"status": "complete"}, "work": 1,
        "findings": [{"target": target, "status": "supported", "positive": True, "negative": False, "conflict": False,
                      "supporting_assertions": [{"graph": graph, "assertion_id": "assertion", "revision": 1}],
                      "opposing_assertions": []}], "steps": [], "excluded_context": []}
    owner = ConfiguredAssessment.from_wire(owner.document.model_copy(update={"targets": (
        AssessmentTarget(criterion_id="c", target_sha256=fingerprint(GroundLiteral.model_validate_json(json.dumps(target)))),)}))
    reason = copy.deepcopy(reason)
    if reason_mutation:
        reason_mutation(reason)
    reader = Reader()
    method = {"transformation_id": "knowledge.synthetic_logical_entailment", "version": "1", "sha256": hashlib.sha256(
        canonical({"algorithm_profile": "knowledge.signed-ground-horn.v1", "rule_set": reason["request"]["rule_set"]})).hexdigest()}
    answer = reader.publish("answer", reason, reasoning_artifact_schema(), "knowledge-publisher",
                            (owner.document.subject, owner.document.question.applicability), method)
    need = owner.document.requirements[0].need
    record = {"wire_version": "1", "authority": "synthetic", "need": need.reference.model_dump(mode="json"),
              "criterion_id": "c", "subject": answer.model_dump(mode="json"), "method": need.method.model_dump(mode="json"),
              "context": need.required_context.model_dump(mode="json"), "category": "observation", "issuer": "fixture-observer",
              "purpose": owner.document.purpose, "disposition": "supported"}
    if evidence_mutation:
        evidence_mutation(record)
    ref = reader.publish("evidence", record, synthetic_evidence_schema(), "fixture-observer",
                         (answer, need.required_context), {"transformation_id": record["method"]["schema_id"],
                         "version": record["method"]["version"], "sha256": record["method"]["sha256"]})
    request = request.model_copy(update={"profile": owner.reference,
        "answers": (AssessmentAnswerRef(criterion_id="c", artifact=answer),), "receipts": (ref,)})
    ledger = Ledger(owner)
    return owner.bind(request, "reader", SCOPE), reader, ledger


def test_exact_owner_and_producer_bindings_resolve_to_only_synthetic_sufficiency():
    bound, reader, ledger = resolution_case()
    result = AssessmentResolver(ledger, reader).resolve(bound)
    assert result.assessment.sufficient and result.assessment.answered
    assert result.assessment.scientifically_established is False
    assert result.assessment.needs[0].supporting == bound.request.receipts
    assert [ref.artifact_id for ref in result.inputs] == ["answer", "context", "evidence", "subject"]
    assert ledger.calls == [(SCOPE, "question", "q", 1), (SCOPE, "need", "n", 1)]


@pytest.mark.parametrize(("mutation", "code"), [
    (lambda r: r["request"].update(purpose="wrong"), "answer_applicability_mismatch"),
    (lambda r: r["request"]["context"].update(sha256="d" * 64), "answer_applicability_mismatch"),
    (lambda r: r["request"]["subject"].update(artifact_id="wrong"), "answer_applicability_mismatch"),
    (lambda r: r["request"]["rule_set"].update(graph={"scope": SCOPE.model_dump(mode="json"), "graph_id": "other"}),
     "answer_applicability_mismatch"),
    (lambda r: r["findings"][0].update(status="unknown"), "answer_findings_mismatch"),
    (lambda r: r["findings"][0].update(conflict=True), "answer_findings_mismatch"),
    (lambda r: r["findings"][0]["target"].update(predicate="other"), "answer_target_mismatch"),
    (lambda r: r["findings"][0]["supporting_assertions"][0].update(
        graph={"scope": SCOPE.model_dump(mode="json"), "graph_id": "other"}), "answer_findings_mismatch"),
    (lambda r: r.update(authority="scientific"), "invalid_evidence_payload"),
])
def test_wrong_logical_results_cannot_answer_the_configured_criterion(mutation, code):
    bound, reader, ledger = resolution_case(reason_mutation=mutation)
    with pytest.raises(AssessmentError, match=code):
        AssessmentResolver(ledger, reader).resolve(bound)


@pytest.mark.parametrize(("kind", "reason"), [("incomplete", "answer_unknown"), ("conflict", "answer_unknown"),
                                              ("contradicted", "answer_contradicted")])
def test_exhaustion_conflict_and_negative_findings_are_not_promoted(kind, reason):
    def mutate(result):
        finding = result["findings"][0]
        if kind == "incomplete":
            result["outcome"] = {"status": "incomplete", "code": "reasoning_work_limit"}
            finding["status"] = "unknown"
        elif kind == "conflict":
            finding.update(negative=True, conflict=True, status="unknown")
        else:
            finding.update(positive=False, negative=True, status="contradicted")
    bound, reader, ledger = resolution_case(reason_mutation=mutate)
    result = AssessmentResolver(ledger, reader).resolve(bound)
    assert result.assessment.needs[0].gap.reason == reason and not result.assessment.sufficient


@pytest.mark.parametrize(("mutation", "code"), [
    (lambda r: r.update(issuer="another"), "evidence_issuer_mismatch"),
    (lambda r: r["need"].update(scope=OTHER.model_dump(mode="json")), "evidence_scope_mismatch"),
    (lambda r: r.update(authority="scientific"), "invalid_evidence_payload"),
    (lambda r: r["context"].update(artifact_id="undeclared"), "evidence_lineage_mismatch"),
])
def test_evidence_provenance_is_checked_before_policy(mutation, code):
    bound, reader, ledger = resolution_case(evidence_mutation=mutation)
    with pytest.raises(AssessmentError, match=code):
        AssessmentResolver(ledger, reader).resolve(bound)


@pytest.mark.parametrize(("mutation", "reason"), [
    (lambda r: r.update(category="opinion"), "category_mismatch"),
    (lambda r: r.update(category="simulation"), "category_mismatch"),
    (lambda r: r.update(purpose="wrong"), "purpose_mismatch"),
    (lambda r: r["method"].update(sha256="d" * 64), "method_mismatch"),
    (lambda r: r["need"].update(revision=2), "need_revision_mismatch"),
])
def test_authentic_but_inapplicable_evidence_is_an_explicit_policy_gap(mutation, reason):
    bound, reader, ledger = resolution_case(evidence_mutation=mutation)
    result = AssessmentResolver(ledger, reader).resolve(bound)
    assert result.assessment.reviews[0].reason == reason
    assert result.assessment.needs[0].gap.reason == "no_matching_evidence"


def test_owner_declarations_and_reader_scope_are_checked_before_network():
    for kind, code in [("question", "question_declaration_mismatch"), ("need", "need_declaration_mismatch")]:
        bound, reader, ledger = resolution_case()
        ledger.records[kind] = None
        with pytest.raises(AssessmentError, match=code):
            AssessmentResolver(ledger, reader).resolve(bound)
        assert not reader.used
    bound, reader, ledger = resolution_case()
    reader.scope = OTHER
    with pytest.raises(AssessmentError, match="assessment_scope_mismatch"):
        AssessmentResolver(ledger, reader).resolve(bound)
    assert not ledger.calls


def test_transport_unavailability_propagates_without_an_assessment(monkeypatch):
    bound, reader, ledger = resolution_case()
    def unavailable(*_):
        raise AssessmentPeerUnavailable("peer_unavailable")
    monkeypatch.setattr(reader, "published", unavailable)
    with pytest.raises(AssessmentPeerUnavailable):
        AssessmentResolver(ledger, reader).resolve(bound)


def test_public_synthetic_payload_and_schema_are_strict_and_self_contained():
    bound, reader, _ = resolution_case()
    record = SyntheticEvidenceRecord.model_validate_json(reader.contents["evidence"])
    assert record.subject == bound.request.answers[0].artifact
    ReasoningResult.model_validate_json(reader.contents["answer"])


@pytest.mark.parametrize(("name", "change", "code"), [
    ("answer", "method", "answer_method_mismatch"),
    ("evidence", "method", "evidence_method_mismatch"),
    ("answer", "lineage", "evidence_lineage_mismatch"),
    ("evidence", "lineage", "evidence_lineage_mismatch"),
    ("answer", "duplicate", "evidence_lineage_mismatch"),
    ("evidence", "duplicate", "evidence_lineage_mismatch"),
    ("answer", "issuer", "untrusted_publisher"),
    ("evidence", "issuer", "untrusted_publisher"),
])
def test_valid_shape_cannot_hide_wrong_method_lineage_or_producer(name, change, code):
    bound, reader, ledger = resolution_case()
    proof = reader.proofs[name]
    declaration = proof.declaration
    if change == "method":
        declaration = declaration.model_copy(update={"transformation": declaration.transformation.model_copy(
            update={"sha256": "d" * 64})})
    elif change == "lineage":
        declaration = declaration.model_copy(update={"inputs": (declaration.inputs[0],)})
    elif change == "duplicate":
        declaration = declaration.model_copy(update={"inputs": declaration.inputs * 2})
    if change == "issuer":
        proof = proof.model_copy(update={"origin": proof.origin.model_copy(update={"actor_id": "untrusted"})})
    reader.proofs[name] = proof.model_copy(update={"declaration": declaration})
    with pytest.raises(AssessmentError, match=code):
        AssessmentResolver(ledger, reader).resolve(bound)


@pytest.mark.parametrize(("kind", "code"), [("answer", "answer_schema_mismatch"), ("receipt", "evidence_schema_mismatch")])
def test_arbitrary_schema_payloads_are_not_interpreted(kind, code):
    bound, reader, ledger = resolution_case()
    request = bound.request
    if kind == "answer":
        selection = request.answers[0].model_copy(update={"artifact": artifact("answer")})
        request = request.model_copy(update={"answers": (selection,)})
    else:
        request = request.model_copy(update={"receipts": (artifact("evidence"),)})
    bound = bound.configured.bind(request, bound.actor_id, SCOPE)
    with pytest.raises(AssessmentError, match=code):
        AssessmentResolver(ledger, reader).resolve(bound)


def test_duplicate_or_out_of_order_findings_fail_and_foreign_provenance_is_not_hidden():
    def duplicate(value):
        value["request"]["targets"] *= 2
        value["findings"] *= 2
    def foreign(value):
        value["excluded_context"] = [{"graph": {"scope": OTHER.model_dump(mode="json"), "graph_id": "domain"},
                                      "assertion_id": "foreign", "revision": 1}]
    for mutation in (duplicate, foreign):
        bound, reader, ledger = resolution_case(reason_mutation=mutation)
        with pytest.raises(AssessmentError, match="answer_findings_mismatch"):
            AssessmentResolver(ledger, reader).resolve(bound)


def test_authentic_wrong_context_is_retained_as_gap_after_reading_its_provenance():
    def wrong_context(value):
        value["context"] = artifact("wrong-context").model_dump(mode="json")
    bound, reader, ledger = resolution_case(evidence_mutation=wrong_context)
    proof = reader.proofs["evidence"]
    reader.proofs["evidence"] = proof.model_copy(update={"declaration": proof.declaration.model_copy(
        update={"inputs": (bound.request.answers[0].artifact, artifact("wrong-context"))})})
    result = AssessmentResolver(ledger, reader).resolve(bound)
    assert result.assessment.reviews[0].reason == "context_mismatch"
    assert not result.assessment.sufficient
    assert "wrong-context" in {ref.artifact_id for ref in result.inputs}


def test_knowledge_conflict_is_not_erased_by_a_negative_evidence_record():
    def conflict(result):
        result["findings"][0].update(negative=True, conflict=True, status="unknown")
    bound, reader, ledger = resolution_case(reason_mutation=conflict,
        evidence_mutation=lambda value: value.update(disposition="contradicted"))
    result = AssessmentResolver(ledger, reader).resolve(bound)
    assert result.assessment.disposition == "unknown"
    assert not result.assessment.sufficient
    assert result.assessment.needs[0].contradicting == bound.request.receipts
