"""Real Data and Knowledge publication, with a Research-owned resolver and identity ledger."""

import hashlib
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pytest
from amphora_contracts_knowledge import reasoning_artifact_schema, reasoning_artifact_schema_document
from amphora_contracts_research import (
    EvidenceAssessmentProfile,
    EvidenceAssessmentRequest,
    EvidenceNeed,
    ResearchQuestion,
    synthetic_evidence_schema,
    synthetic_evidence_schema_document,
)
from amphora_research.assessment.boundary import ConfiguredAssessment
from amphora_research.assessment.policy import AssessmentError
from amphora_research.assessment.reader import AssessmentDataReader, AssessmentPeerUnavailable
from amphora_research.assessment.resolution import AssessmentResolver
from amphora_research.assessment.store import AssessmentStore
from postgres_fixture import knowledge_owner, owned_state

from .live_peers import Owner, owned_script

pytestmark = pytest.mark.postgres


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def publish(data, scope, content, schema, *, inputs=None, method=None):
    descriptor = {"sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content),
                  "media_type": "application/octet-stream" if schema["schema_id"] == "fixture.bytes" else "application/json",
                  "schema_ref": schema}
    def command(family, payload):
        return {"identity": {"command_family": family, "command_id": uuid.uuid4().hex,
                             "actor_id": "fixture", "scope": scope}, "payload": payload}
    if inputs is None:
        started = data.request("/v1/uploads", command("artifacts.begin_upload", {"content": descriptor}))
    else:
        started = data.request("/v1/derived-uploads", command("artifacts.begin_derived_upload", {
            "content": descriptor, "declaration": {"schema_version": "1", "transformation": method, "inputs": inputs}}))["upload"]
    data.request(f"/v1/uploads/{started['upload_id']}/content", content=content, method="PUT")
    return data.request("/v1/artifacts/finalize", command("artifacts.finalize", {
        "upload_id": started["upload_id"], "content": descriptor}))["artifact"]


def test_actual_knowledge_output_and_evidence_require_authenticated_applicable_producers(ledger, tmp_path):
    store, scope_model = ledger
    scope = scope_model.model_dump(mode="json")
    state = owned_state()
    knowledge_owner(state)
    url = store.engine.url
    environment = dict(os.environ, DATA_DB=url.set(username="artifact_service").render_as_string(hide_password=False),
        KNOWLEDGE_DB=url.set(username="knowledge_service").render_as_string(hide_password=False),
        RESEARCH_DB=url.render_as_string(hide_password=False), DATA_TOKEN="d" * 32, READ_TOKEN="b" * 32,
        PUBLISH_TOKEN="p" * 32, KNOWLEDGE_TOKEN="k" * 32, RESEARCH_TOKEN="r" * 32)
    for label, module, role in [("DATA", "amphora_data_artifacts", "artifact_migrator"),
                                 ("KNOWLEDGE", "amphora_knowledge", "knowledge_migrator")]:
        environment["PEER_MIGRATION"] = url.set(username=role).render_as_string(hide_password=False)
        owned_script(os.environ.get(f"AMPHORA_TEST_{label}_PYTHON", sys.executable),
            f"import os; from {module}.persistence.migrate import upgrade; upgrade(os.environ['PEER_MIGRATION'])", environment)
    schemas = []
    for name, reference, document in [("reasoning", reasoning_artifact_schema(), reasoning_artifact_schema_document()),
                                       ("evidence", synthetic_evidence_schema(), synthetic_evidence_schema_document())]:
        (tmp_path / (name + ".json")).write_bytes(document)
        schemas.append({"media_type": "application/json", **reference.model_dump(mode="json"), "schema_path": name + ".json"})
    raw_schema = {"schema_id": "fixture.bytes", "version": "1",
                  "sha256": hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()}
    (tmp_path / "bytes").mkdir()
    data_config = tmp_path / "data.json"
    data_config.write_text(json.dumps({"database_url_env": "DATA_DB", "storage_root": str(tmp_path / "bytes"),
        "acquisition": True, "profiles": [{"media_type": "application/octet-stream", **raw_schema}, *schemas],
        "principals": [{"token_env": "DATA_TOKEN", "actor_id": "fixture", "scope": scope,
                        "actions": ["read", "source_history", "upload", "finalize", "acquire", "manage_source_rights"]},
                       {"token_env": "READ_TOKEN", "actor_id": "reader", "scope": scope, "actions": ["read", "source_history"]},
                       {"token_env": "PUBLISH_TOKEN", "actor_id": "knowledge-publisher", "scope": scope,
                        "actions": ["read", "upload", "finalize"]}]}))
    owners = []
    try:
        data = Owner("amphora_data_artifacts", data_config, environment, "d" * 32,
                     os.environ.get("AMPHORA_TEST_DATA_PYTHON"))
        owners.append(data)
        raw = b"Synthetic research support."
        context = publish(data, scope, raw, raw_schema)
        rights = {"wire_version": "1", "reference": {"scope": scope, "rights_id": "rights", "revision": 1},
                  "supersedes": None, "status": "granted", "allowed_uses": ["read", "process"],
                  "expires_at": None, "retention": "retain_audit_payload"}
        data.request("/v1/acquisition/rights", rights)
        source_ref = {"scope": scope, "source_id": "source", "revision_id": "1", "raw": context}
        source = {"wire_version": "1", "reference": source_ref, "delivery": {"issuer_id": "fixture", "delivery_id": "one"},
                  "method": {"connector_id": "fixture", "connector_version": "1", "configuration_sha256": "a" * 64,
                             "format": "utf8_document"}, "rights": rights["reference"], "supersedes": None, "completeness": "complete"}
        prepared = data.request("/v1/acquisition/prepare", source)
        converted = publish(data, scope, prepared["content_json_utf8"].encode(), prepared["schema_ref"])
        trace = data.request("/v1/acquisition/retain", {"wire_version": "1", "source": source, "trace_id": "trace", "output": converted})
        question = {"wire_version": "1", "reference": {"scope": scope, "question_id": "q", "revision": 1},
                    "objective": "Synthetic measurement criterion", "applicability": context,
                    "criteria": [{"criterion_id": "c", "description": "Declared synthetic need"}], "supersedes": None}
        need = {"wire_version": "1", "reference": {"scope": scope, "need_id": "n", "revision": 1},
                "question": question["reference"], "criterion_ids": ["c"], "method": raw_schema,
                "required_context": context, "supersedes": None}
        for model, record in [(ResearchQuestion, question), (EvidenceNeed, need)]:
            store.publish(scope_model, model.model_validate_json(json.dumps(record)))
        research_config = tmp_path / "research.json"
        research_config.write_text(json.dumps({"database_url_env": "RESEARCH_DB", "principals": [
            {"token_env": "RESEARCH_TOKEN", "actor_id": "reader", "scope": scope, "actions": ["read_declarations"]}]}))
        research = Owner("amphora_research", research_config, environment, "r" * 32)
        owners.append(research)
        vocabulary = {"wire_version": "1", "vocabulary_id": "fixture", "version": "1", "entity_types": ["concept"],
                      "predicates": [{"predicate_id": "supports", "description": "Synthetic support",
                                      "subject_types": ["concept"], "object_types": ["concept"]}]}
        policy = {"policy_id": "synthetic-structural", "version": "1", "authority": "structural_only",
                  "max_entities": 4096, "max_assertions": 8192, "max_aliases": 4096, "max_retractions": 8192}
        graph = {"scope": scope, "graph_id": "domain"}
        rules = {"wire_version": "1", "graph": graph, "rule_set_id": "rules", "version": "1",
                 "authority": "synthetic_logical_entailment", "context": context,
                 "limits": {"depth": 32, "work": 100000, "facts": 8192}, "rules": []}
        knowledge_config = tmp_path / "knowledge.json"
        knowledge_config.write_text(json.dumps({"database_url_env": "KNOWLEDGE_DB", "vocabulary": vocabulary, "policy": policy,
            "reasoning": [rules], "publication": {"actor_id": "knowledge-publisher", "issuer_id": "logical", "token_env": "PUBLISH_TOKEN"},
            "principals": [{"token_env": "KNOWLEDGE_TOKEN", "actor_id": "author", "scope": scope,
                            "actions": ["read_graph", "propose_graph", "reason_graph", "publish_reasoning"]}],
            "data": {"endpoint": data.endpoint, "token_env": "READ_TOKEN"},
            "research": {"endpoint": research.endpoint, "token_env": "RESEARCH_TOKEN"}}))
        knowledge = Owner("amphora_knowledge", knowledge_config, environment, "k" * 32,
                          os.environ.get("AMPHORA_TEST_KNOWLEDGE_PYTHON"))
        owners.append(knowledge)
        grounding = {"spans": [{"source": source_ref, "unit": "byte", "start": 0, "end": len(raw),
                                 "sha256": hashlib.sha256(raw).hexdigest()}], "conversion_traces": [trace], "interpretation_artifacts": []}
        entities = [{"reference": {"graph": graph, "entity_id": name, "revision": 1}, "entity_type": "concept",
                     "label": name, "context": context, "supersedes": None} for name in ("a", "b")]
        target = {"subject": entities[0]["reference"], "predicate": "supports", "object": entities[1]["reference"], "polarity": "affirmed"}
        assertion = {"reference": {"graph": graph, "assertion_id": "claim", "revision": 1}, **target,
                     "statement": "Synthetic claim", "posture": "hypothesis", "applicability": context,
                     "grounding": grounding, "research_links": [], "supersedes": None}
        proposal = {"wire_version": "1", "graph": graph, "change_id": "initial", "base": None,
                    "vocabulary": {"vocabulary_id": "fixture", "version": "1", "sha256": digest(vocabulary)},
                    "policy": {"policy_id": policy["policy_id"], "version": "1", "sha256": digest(policy)},
                    "description": "Synthetic graph", "rationale": "Research resolution compatibility", "grounding": grounding,
                    "operations": [*[{"operation": "add_entity", "entity": entity} for entity in entities],
                                   {"operation": "add_assertion", "assertion": assertion}]}
        accepted = knowledge.request("/v1/graph-proposals", proposal)
        assert accepted["decision"]["outcome"] == "accepted"
        reason = {"wire_version": "1", "request_id": "reason", "snapshot": accepted["decision"]["head"]["snapshot"],
                  "rule_set": {"graph": graph, "rule_set_id": "rules", "version": "1", "sha256": digest(rules)},
                  "context": context, "subject": context, "purpose": "fixture.measurement", "targets": [target]}
        assert knowledge.request("/v1/graph-reasoning", reason)["decision"]["outcome"] == "evaluated"
        result = knowledge.request("/v1/reasoning-publications", {"wire_version": "1", "graph": graph,
            "publication_id": "publish", "reasoning_request_id": "reason"})
        assert result["outcome"]["status"] == "published"
        answer = result["outcome"]["derivation"]["artifact"]
        profile = EvidenceAssessmentProfile.model_validate_json(json.dumps({"wire_version": "1", "profile_id": "assessment",
            "version": "1", "authority": "synthetic", "purpose": reason["purpose"], "question": question, "subject": context,
            "targets": [{"criterion_id": "c", "target_sha256": digest(target)}], "answer_publishers": ["knowledge-publisher"],
            "requirements": [{"need": need, "categories": ["observation"], "issuers": ["fixture"]}]}))
        configured = ConfiguredAssessment.from_wire(profile)
        request = {"wire_version": "1", "assessment_id": "assessment", "profile": configured.reference.model_dump(mode="json"),
                   "question": question["reference"], "answers": [{"criterion_id": "c", "artifact": answer}], "receipts": []}
        def resolve(receipts, token="b" * 32):
            selected = EvidenceAssessmentRequest.model_validate_json(json.dumps(request | {
                "receipts": receipts, "assessment_id": digest(receipts)}))
            bound = configured.bind(selected, "reader", scope_model)
            journal = AssessmentStore(store.engine)
            journal.begin(bound)
            resolved = AssessmentResolver(store, AssessmentDataReader(data.endpoint, token, scope_model)).resolve(bound)
            terminal = journal.complete(bound, resolved)
            assert AssessmentStore(store.engine).read(scope_model, selected.assessment_id, "reader") == terminal
            return terminal.resolved
        assert resolve([]).assessment.needs[0].gap.reason == "no_matching_evidence"
        observations = []
        for category in ("opinion", "observation"):
            record = {"wire_version": "1", "authority": "synthetic", "need": need["reference"], "criterion_id": "c",
                      "subject": answer, "method": raw_schema, "context": context, "category": category,
                      "issuer": "fixture", "purpose": reason["purpose"], "disposition": "supported"}
            receipt = publish(data, scope, encoded(record), synthetic_evidence_schema().model_dump(mode="json"),
                inputs=[answer, context], method={"transformation_id": raw_schema["schema_id"], "version": "1", "sha256": raw_schema["sha256"]})
            assessment = resolve([receipt]).assessment
            assert assessment.sufficient is (category == "observation")
            assert assessment.scientifically_established is False
            observations.append(assessment.model_dump(mode="json"))
        with pytest.raises(AssessmentError, match="peer_access_denied"):
            resolve([receipt], token="z" * 32)
        rights2 = rights | {"reference": rights["reference"] | {"revision": 2}, "supersedes": rights["reference"],
                           "status": "revoked", "allowed_uses": []}
        data.request("/v1/acquisition/rights", rights2)
        with pytest.raises(AssessmentError, match="peer_access_denied"):
            resolve([receipt])
        data.stop()
        with pytest.raises(AssessmentPeerUnavailable):
            resolve([receipt])
        assert store.engine.pool.checkedout() == 0
        evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "scope": scope,
                    "answer": answer, "assessments": observations, "actual_processes": ["Data", "Knowledge", "Research"],
                    "cases": ["real_logical_output", "explicit_missing_evidence", "opinion_insufficient", "matching_observation",
                              "wrong_token_denied", "revoked_source_denied", "data_outage_retryable", "no_idle_research_transaction", "durable_assessment_replacement_read"]}
        path = Path(os.environ.get("AMPHORA_RESEARCH_RESOLUTION_EVIDENCE", str(Path(__file__).absolute().parents[4] /
                                                                                 ".test-results/research-resolution-live.json")))
        path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    finally:
        for owner in reversed(owners):
            owner.stop()
