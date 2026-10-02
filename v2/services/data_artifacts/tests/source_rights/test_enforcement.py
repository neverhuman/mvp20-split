import json
import os
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from amphora_contracts_evidence import ObserveSourceIdentity
from amphora_contracts_research import IdentityResolution
from amphora_data_artifacts.access import Credentials
from amphora_data_artifacts.api import create_app
from amphora_data_artifacts.source_rights.model import RightsError
from fastapi.testclient import TestClient

pytestmark = pytest.mark.postgres


def revise(e, *, status="granted", uses=("read", "process"), expires_at=None):
    previous = e.workflow.rights.history(e.principal, "fixture", 1)
    record = previous.model_copy(update={"reference": previous.reference.model_copy(update={"revision": 2}),
        "supersedes": previous.reference, "status": status, "allowed_uses": uses, "expires_at": expires_at})
    admin = replace(e.principal, actions=frozenset({"manage_source_rights"}))
    return e.workflow.rights.publish(admin, record)


def retained(e, raw=b"notes", format="utf8_document"):
    source = e.source(raw, format)
    prepared = e.workflow.prepare(e.principal, source)
    output = e.publish(prepared.content, prepared.output_schema)
    trace = e.workflow.retain(e.principal, source, "trace", output)
    return source, output, trace


def test_revocation_blocks_bytes_and_new_use_but_preserves_history(ingestion):
    e = ingestion
    source, output, trace = retained(e)
    command = ObserveSourceIdentity(wire_version="1", observation_id="before", trace=trace)
    original = e.workflow.observe(e.principal, command)
    revise(e, status="revoked", uses=())
    for artifact in (source.reference.raw, output):
        with pytest.raises(RightsError, match="rights_revoked"):
            e.reads.content(e.principal, artifact.artifact_id)
        assert e.reads.get(e.principal, artifact.artifact_id).reference == artifact
    with pytest.raises(RightsError, match="rights_revoked"):
        e.workflow.prepare(e.principal, source)
    with pytest.raises(RightsError, match="rights_revoked"):
        e.workflow.retain(e.principal, source, "later", output)
    with pytest.raises(RightsError, match="rights_revoked"):
        e.workflow.observe(e.principal, command.model_copy(update={"observation_id": "after"}))
    assert e.workflow.observe(e.principal, command) == original
    assert e.ledger.trace_history(e.principal, "trace").output == output
    assert e.ledger.history(e.principal, "source", "r1") == source
    assert e.workflow.rights.history(e.principal, "fixture", 1).status == "granted"
    assert e.workflow.rights.history(e.principal, "fixture", 2).status == "revoked"


def test_unassociated_publication_does_not_infer_source_lineage_from_equal_bytes(ingestion, tmp_path):
    """Legacy identity semantics; new derivations need an explicit publication seam."""
    e = ingestion
    source, linked, _ = retained(e)
    payload = e.reads.content(e.principal, linked.artifact_id)[1]
    unassociated = e.publish(payload, linked.schema_ref)
    assert unassociated.artifact_id != linked.artifact_id and unassociated.sha256 == linked.sha256
    revise(e, status="revoked", uses=())
    with pytest.raises(RightsError, match="rights_revoked"):
        e.reads.content(e.principal, linked.artifact_id)
    assert e.reads.content(e.principal, unassociated.artifact_id)[1] == payload
    evidence = {"timestamp": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
        "tier": "actual PostgreSQL and Artifact owner publication/storage/rights; synthetic input",
        "source": source.reference.model_dump(mode="json"), "linked_output": linked.model_dump(mode="json"),
        "unassociated_output": unassociated.model_dump(mode="json"),
        "observations": {"linked_after_revocation": "rights_revoked", "unassociated_after_revocation": "readable",
            "matching_hash_implies_lineage": False},
        "implication": "General derived publication must declare and atomically retain exact input lineage; ordinary finalize cannot establish it."}
    destination = Path(os.environ.get("AMPHORA_DERIVED_LINEAGE_EVIDENCE", str(tmp_path / "lineage.json")))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


def test_expiry_uses_database_clock_and_read_only_disallows_processing(ingestion):
    e = ingestion
    source, output, _ = retained(e)
    expired = revise(e, expires_at=datetime.now(UTC) - timedelta(seconds=1))
    with pytest.raises(RightsError, match="rights_expired"):
        e.reads.content(e.principal, output.artifact_id)
    third = expired.model_copy(update={"reference": expired.reference.model_copy(update={"revision": 3}),
        "supersedes": expired.reference, "expires_at": None, "allowed_uses": ("read",)})
    e.workflow.rights.publish(replace(e.principal, actions=frozenset({"manage_source_rights"})), third)
    assert e.reads.content(e.principal, source.reference.raw.artifact_id)[1] == b"notes"
    with pytest.raises(RightsError, match="rights_use_denied"):
        e.workflow.prepare(e.principal, source)


def test_unknown_policy_is_never_inferred_from_historical_reference(ingestion):
    e = ingestion
    source = e.source()
    missing = source.model_copy(update={"rights": source.rights.model_copy(update={"rights_id": "unknown"})})
    with pytest.raises(RightsError, match="rights_unavailable"):
        e.workflow.prepare(e.principal, missing)
    assert e.ledger.history(e.principal, "source", "r1") is None


@pytest.mark.parametrize("revoke,reason", [(True, "rights_revoked"), (False, "rights_epoch_changed")])
def test_change_during_actual_storage_read_prevents_return(ingestion, monkeypatch, revoke, reason):
    e = ingestion
    source, _, _ = retained(e)
    verify = e.env.storage.verify

    def changed(key, descriptor):
        content = verify(key, descriptor)
        revise(e, status="revoked" if revoke else "granted", uses=() if revoke else ("read", "process"))
        return content

    monkeypatch.setattr(e.env.storage, "verify", changed)
    with pytest.raises(RightsError, match=reason):
        e.reads.content(e.principal, source.reference.raw.artifact_id)


def test_revocation_during_peer_lookup_prevents_result_commit(ingestion):
    e = ingestion
    _, _, trace = retained(e, b'{"candidate_id":"c","candidate_revision":"1","sample_id":"s","sample_revision":"1"}',
                            "synthetic_lab_json")

    class Peer:
        def resolve(self, query):
            revise(e, status="revoked", uses=())
            return IdentityResolution(wire_version="1", scope=query.scope, candidate=query.candidate, sample=query.sample,
                                      disposition="matched", reason="exact_identity_only", authority="identity_only")

    e.workflow.research = Peer()
    command = ObserveSourceIdentity(wire_version="1", observation_id="race", trace=trace)
    with pytest.raises(RightsError, match="rights_revoked"):
        e.workflow.observe(e.principal, command)
    assert e.workflow.observations.history(e.principal, "race").result is None


def test_derived_lineage_cannot_launder_revoked_source(ingestion, grant_source_rights):
    e = ingestion
    source, first_output, _ = retained(e)
    second = source.model_copy(update={"reference": source.reference.model_copy(update={
        "source_id": "derived", "raw": first_output}),
        "delivery": source.delivery.model_copy(update={"delivery_id": "derived"}),
        "rights": source.rights.model_copy(update={"rights_id": "independent"})})
    grant_source_rights(second.rights)
    prepared = e.workflow.prepare(e.principal, second)
    output = e.publish(prepared.content, prepared.output_schema)
    e.workflow.retain(e.principal, second, "derived-trace", output)
    revise(e, status="revoked", uses=())
    with pytest.raises(RightsError, match="rights_revoked"):
        e.reads.content(e.principal, output.artifact_id)
    with pytest.raises(RightsError, match="rights_revoked"):
        e.workflow.prepare(e.principal, second)
    # Equal bytes acquired under another artifact identity are not silently merged.
    independent = e.publish(b"notes")
    assert independent.sha256 == source.reference.raw.sha256
    assert e.reads.content(e.principal, independent.artifact_id)[1] == b"notes"


def test_public_rights_grant_and_revocation_fence_artifact_route(ingestion):
    e = ingestion
    source, _, _ = retained(e)
    admin = replace(e.principal, actions=e.principal.actions | {"manage_source_rights"})
    credentials = Credentials([("x" * 32, admin), ("y" * 32, e.principal)])
    previous = e.workflow.rights.history(e.principal, "fixture", 1)
    record = previous.model_copy(update={"reference": previous.reference.model_copy(update={"revision": 2}),
                                        "supersedes": previous.reference, "status": "revoked", "allowed_uses": ()})
    with TestClient(create_app(e.env.uploads, e.env.storage, credentials, acquisition=e.workflow)) as client:
        headers = {"Authorization": "Bearer " + "x" * 32}
        assert client.post("/v1/acquisition/rights", json=record.model_dump(mode="json"),
                           headers={"Authorization": "Bearer " + "y" * 32}).status_code == 403
        assert client.post("/v1/acquisition/rights", json=record.model_dump(mode="json"), headers=headers).status_code == 200
        assert client.get(f"/v1/artifacts/{source.reference.raw.artifact_id}/content", headers=headers).status_code == 403
        assert client.get("/v1/acquisition/rights/fixture/1", headers=headers).json()["status"] == "granted"
        assert client.get("/v1/acquisition/rights/absent/1", headers=headers).status_code == 404
