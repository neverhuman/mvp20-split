import hashlib
import json
import uuid
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_artifacts import parse_command
from amphora_contracts_core import ArtifactRef
from amphora_contracts_evidence import SourceRevision, prepared_schema
from amphora_data_artifacts.acquisition.ledger import AcquisitionLedger
from amphora_data_artifacts.acquisition.profiles import PreparedContentRule
from amphora_data_artifacts.acquisition.provenance import ProvenanceError
from amphora_data_artifacts.acquisition.workflow import AcquisitionWorkflow
from amphora_data_artifacts.publication.model import ContentPolicy, UploadError, UploadLimits
from amphora_data_artifacts.reads import ArtifactReads

pytestmark = pytest.mark.postgres


@pytest.fixture
def ingestion(upload_env):
    e = upload_env
    profiles = [prepared_schema(kind) for kind in ("document", "lab")]
    e.uploads.policy = ContentPolicy(e.uploads.policy.allowed | frozenset(
        ("application/json", ref.schema_id, ref.version, ref.sha256) for ref in profiles),
        rules=(PreparedContentRule("document"), PreparedContentRule("lab")))
    e.uploads.limits = UploadLimits(max_bytes=65536, scope_bytes=1048576)
    principal = replace(e.principal, actions=frozenset({"read", "acquire", "source_history"}))
    ledger = AcquisitionLedger(e.engine)
    reads = ArtifactReads(e.engine, e.storage, 65536)

    def publish(content, schema=None):
        envelope = json.loads(e.raw(content))
        if schema is not None:
            envelope["payload"]["content"].update(media_type="application/json",
                                                 schema_ref=schema.model_dump(mode="json"))
        receipt = e.uploads.begin(e.principal, parse_command("artifacts.begin_upload", json.dumps(envelope)))
        response = e.client.put(f"/v1/uploads/{receipt.upload_id}/content", content=content, headers=e.headers)
        assert response.status_code == 200
        response = e.client.post("/v1/artifacts/finalize", headers=e.headers, json={
            "identity": {"command_family": "artifacts.finalize", "command_id": uuid.uuid4().hex,
                         "actor_id": "worker", "scope": principal.scope.model_dump()},
            "payload": {"upload_id": receipt.upload_id, "content": receipt.content.model_dump(mode="json")}})
        assert response.status_code == 200, response.text
        return ArtifactRef.model_validate_json(json.dumps(response.json()["artifact"]))

    def source(content=b"research notes", format="utf8_document"):
        return SourceRevision.model_validate_json(json.dumps({"wire_version": "1",
            "reference": {"scope": principal.scope.model_dump(), "source_id": "source", "revision_id": "r1",
                          "raw": publish(content).model_dump(mode="json")},
            "delivery": {"issuer_id": "fixture", "delivery_id": "d1"},
            "method": {"connector_id": "fixture", "connector_version": "1",
                       "configuration_sha256": hashlib.sha256(b"{}").hexdigest(), "format": format},
            "rights": {"scope": principal.scope.model_dump(), "rights_id": "fixture", "revision": 1},
            "supersedes": None, "completeness": "complete"}))

    return SimpleNamespace(workflow=AcquisitionWorkflow(reads, ledger), ledger=ledger, reads=reads,
                           principal=principal, publish=publish, source=source, env=e)


@pytest.mark.parametrize("raw,format,disposition", [
    ("notes μ".encode(), "utf8_document", "normalized"),
    (b'{"value":"<0.5"}', "synthetic_lab_json", "quarantined"),
])
def test_finalized_ingestion_replays_across_owner_replacement(ingestion, raw, format, disposition):
    e = ingestion
    revision = e.source(raw, format)
    prepared = e.workflow.prepare(e.principal, revision)
    output = e.publish(prepared.content, prepared.output_schema)
    reference = e.workflow.retain(e.principal, revision, "trace", output)
    replacement = AcquisitionWorkflow(e.reads, AcquisitionLedger(e.env.engine))
    assert replacement.retain(e.principal, revision, "trace", output) == reference
    trace = e.ledger.trace_history(e.principal, "trace")
    assert trace.output == output and trace.disposition == disposition
    assert trace.source == revision.reference
    for field in trace.fields:
        for span in field.spans:
            assert prepared.source.extract(span) == raw[span.start:span.end]


def test_authority_and_scope_checked_before_delivery_write(ingestion):
    e = ingestion
    revision = e.source()
    for actions in ({"acquire"}, {"read"}):
        with pytest.raises(UploadError, match="access_denied"):
            e.workflow.prepare(replace(e.principal, actions=frozenset(actions)), revision)
    foreign = replace(e.principal, scope=e.principal.scope.model_copy(update={"project_id": "foreign"}))
    with pytest.raises(ProvenanceError, match="source_scope_mismatch"):
        e.workflow.prepare(foreign, revision)
    assert e.ledger.history(e.principal, "source", "r1") is None


@pytest.mark.parametrize("patch,code", [
    ({"artifact_id": "absent"}, "artifact_unavailable"),
    ({"media_type": "text/plain"}, "catalog_reference_mismatch"),
])
def test_raw_reference_must_match_finalized_catalog(ingestion, patch, code):
    e = ingestion
    revision = e.source()
    revision = revision.model_copy(update={"reference": revision.reference.model_copy(
        update={"raw": revision.reference.raw.model_copy(update=patch)})})
    with pytest.raises((ProvenanceError, UploadError), match=code):
        e.workflow.prepare(e.principal, revision)
    assert e.ledger.history(e.principal, "source", "r1") is None


def test_parser_failure_preserves_delivery_and_exact_retry(ingestion):
    e = ingestion
    revision = e.source(b"\xff")
    for _ in range(2):
        with pytest.raises(ProvenanceError):
            e.workflow.prepare(e.principal, revision)
    assert e.ledger.history(e.principal, "source", "r1") == revision
    changed = revision.model_copy(update={"reference": revision.reference.model_copy(
        update={"raw": e.publish(b"fixed")})})
    with pytest.raises(ProvenanceError, match="delivery_conflict"):
        e.workflow.prepare(e.principal, changed)


def test_wrong_or_unpublished_output_never_retains_trace(ingestion):
    e = ingestion
    revision = e.source()
    prepared = e.workflow.prepare(e.principal, revision)
    output = e.publish(b'{"wire_version":"1","text":"different"}', prepared.output_schema)
    with pytest.raises(ProvenanceError, match="prepared_output_mismatch"):
        e.workflow.retain(e.principal, revision, "trace", output)
    output = e.publish(prepared.content, prepared.output_schema)
    with pytest.raises(UploadError, match="artifact_unavailable"):
        e.workflow.retain(e.principal, revision, "trace", output.model_copy(update={"artifact_id": "absent"}))
    foreign = output.model_copy(update={"scope": output.scope.model_copy(update={"project_id": "foreign"})})
    with pytest.raises(ProvenanceError, match="artifact_scope_mismatch"):
        e.workflow.retain(e.principal, revision, "trace", foreign)
    assert e.ledger.trace_history(e.principal, "trace") is None
    e.workflow.retain(e.principal, revision, "trace", output)
    other = e.publish(prepared.content, prepared.output_schema)
    with pytest.raises(ProvenanceError, match="trace_identity_conflict"):
        e.workflow.retain(e.principal, revision, "trace", other)


def test_wrong_output_profile_and_corrupt_storage_are_not_trusted(ingestion):
    e = ingestion
    revision = e.source()
    prepared = e.workflow.prepare(e.principal, revision)
    output = e.publish(prepared.content)
    with pytest.raises(ProvenanceError, match="prepared_schema_mismatch"):
        e.workflow.retain(e.principal, revision, "trace", output)
    assert e.ledger.trace_history(e.principal, "trace") is None
    stored = e.reads.get(e.principal, revision.reference.raw.artifact_id)
    e.env.storage.path(stored.storage_key).write_bytes(b"corrupt")
    with pytest.raises(UploadError):
        e.workflow.prepare(e.principal, revision)
