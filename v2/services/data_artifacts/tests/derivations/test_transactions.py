import copy
import json

import pytest
from amphora_contracts_core import ArtifactRef
from sqlalchemy import event, text

pytestmark = pytest.mark.postgres


def count(d, table):
    with d.e.env.engine.connect() as connection:
        return connection.execute(text("SELECT count(*) FROM artifacts." + table +
            " WHERE tenant_id=:tenant AND project_id=:project"), d.principal.bindings).scalar_one()


def test_http_publication_inherits_transitive_rights_and_replays_history(derived_env):
    d = derived_env
    source, converted = d.linked_source()
    raw = d.begin([converted])
    final = d.stream(raw)
    result = d.client.post("/v1/artifacts/finalize", json=final, headers=d.headers)
    assert result.status_code == 200, result.text
    artifact = ArtifactRef.model_validate_json(json.dumps(result.json()["artifact"]))
    path = f"/v1/artifacts/{artifact.artifact_id}"
    metadata = d.client.get(path + "/derivation", headers=d.headers)
    assert metadata.status_code == 200
    assert metadata.json()["declaration"]["inputs"] == [converted.model_dump(mode="json")]
    assert d.client.get(path + "/content", headers=d.headers).content == b"derived"
    d.revoke(source)
    assert d.client.get(path + "/content", headers=d.headers).json()["reason_code"] == "rights_revoked"
    assert d.client.get(path + "/derivation", headers=d.headers).json() == metadata.json()
    assert d.client.post("/v1/artifacts/finalize", json=final, headers=d.headers).json() == result.json()
    begin_replay = d.client.post("/v1/derived-uploads", json=raw, headers=d.headers)
    assert begin_replay.status_code == 200
    history = d.client.get("/v1/commands/artifacts.begin_derived_upload/" + raw["identity"]["command_id"], headers=d.headers)
    assert history.json()["outcome"]["receipt"] == begin_replay.json()
    assert count(d, "derivations") == count(d, "derivation_inputs") == count(d, "derived_uploads") == 1


@pytest.mark.parametrize("kind,reason", [("missing", "derivation_input_unavailable"), ("digest", "derivation_input_mismatch")])
def test_false_input_identity_never_reserves_capacity(derived_env, kind, reason):
    d = derived_env
    original = d.e.publish(b"input")
    raw = d.begin([original])
    ref = raw["payload"]["declaration"]["inputs"][0]
    ref["artifact_id" if kind == "missing" else "sha256"] = "absent" if kind == "missing" else "d" * 64
    before = count(d, "uploads")
    response = d.client.post("/v1/derived-uploads", json=raw, headers=d.headers)
    assert response.json()["reason_code"] == reason
    assert count(d, "uploads") == before
    assert count(d, "derived_uploads") == 0
    assert d.client.post("/v1/derived-uploads", json=raw, headers=d.headers).json() == response.json()


def test_begin_identity_collision_does_not_replace_declaration(derived_env):
    d = derived_env
    original = d.e.publish(b"input")
    raw = d.begin([original])
    assert d.client.post("/v1/derived-uploads", json=raw, headers=d.headers).status_code == 200
    changed = copy.deepcopy(raw)
    changed["payload"]["declaration"]["transformation"]["sha256"] = "e" * 64
    assert d.client.post("/v1/derived-uploads", json=changed, headers=d.headers).json()["reason_code"] == "command_identity_conflict"
    assert count(d, "derived_uploads") == 1


@pytest.mark.parametrize("revoked,reason", [(True, "rights_revoked"), (False, "rights_epoch_changed")])
def test_rights_change_during_verification_never_exposes_output(derived_env, monkeypatch, revoked, reason):
    d = derived_env
    source, converted = d.linked_source()
    final = d.stream(d.begin([converted]))
    before = count(d, "catalog")
    verify = d.e.env.storage.verify

    def changing(key, descriptor):
        payload = verify(key, descriptor)
        d.revoke(source, status="revoked" if revoked else "granted", uses=() if revoked else ("read", "process"))
        return payload

    monkeypatch.setattr(d.e.env.storage, "verify", changing)
    response = d.client.post("/v1/artifacts/finalize", json=final, headers=d.headers)
    assert response.json()["reason_code"] == reason
    assert count(d, "catalog") == before
    assert count(d, "derivations") == count(d, "derivation_inputs") == 0


def test_injected_lineage_failure_rolls_back_catalog_and_terminal_receipt(derived_env):
    d = derived_env
    original = d.e.publish(b"input")
    final = d.stream(d.begin([original]))
    before = {name: count(d, name) for name in ("catalog", "audit_events", "outbox")}

    def fail(_conn, _cursor, statement, _parameters, _context, _many):
        if statement.startswith("INSERT INTO artifacts.derivation_inputs"):
            raise RuntimeError("injected lineage failure")

    event.listen(d.e.env.engine, "before_cursor_execute", fail)
    try:
        with pytest.raises(RuntimeError, match="injected lineage failure"):
            d.client.post("/v1/artifacts/finalize", json=final, headers=d.headers)
    finally:
        event.remove(d.e.env.engine, "before_cursor_execute", fail)
    assert {name: count(d, name) for name in before} == before
    assert count(d, "derivations") == count(d, "derivation_inputs") == 0
    history = d.client.get("/v1/commands/artifacts.finalize/" + final["identity"]["command_id"], headers=d.headers)
    assert history.json()["outcome"]["status"] == "pending"
    assert d.client.post("/v1/artifacts/finalize", json=final, headers=d.headers).status_code == 200
