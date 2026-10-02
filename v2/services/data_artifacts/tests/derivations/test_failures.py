import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from threading import Barrier

import pytest
from amphora_contracts_artifacts import parse_command
from amphora_contracts_core import ArtifactRef
from amphora_data_artifacts.derivations.publication import DerivedPublications
from amphora_data_artifacts.publication.finalize import Finalizer
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def published(d, inputs):
    final = d.stream(d.begin(inputs))
    response = d.client.post("/v1/artifacts/finalize", json=final, headers=d.headers)
    assert response.status_code == 200, response.text
    return ArtifactRef.model_validate_json(json.dumps(response.json()["artifact"]))


def independent_source(d):
    source = d.e.source(b"independent")
    source = source.model_copy(update={
        "reference": source.reference.model_copy(update={"source_id": "second"}),
        "delivery": source.delivery.model_copy(update={"delivery_id": "second"}),
        "rights": source.rights.model_copy(update={"rights_id": "second"})})
    policy = d.e.workflow.rights.history(d.principal, "fixture", 1).model_copy(update={"reference": source.rights})
    d.e.workflow.rights.publish(replace(d.principal, actions=frozenset({"manage_source_rights"})), policy)
    d.e.workflow.prepare(d.principal, source)
    return source


@pytest.mark.parametrize("expired", [False, True])
def test_every_independent_source_controls_new_consumption(derived_env, expired):
    d = derived_env
    _, first = d.linked_source()
    second = independent_source(d)
    output = published(d, [first, second.reference.raw])
    chained = published(d, [output, first])  # Shared ancestor is traversed only once.
    path = f"/v1/artifacts/{chained.artifact_id}"
    assert d.client.get(path + "/content", headers=d.headers).status_code == 200
    if expired:
        d.revoke(second, status="granted", uses=("read", "process"), expires_at=datetime.now(UTC) - timedelta(seconds=1))
    else:
        d.revoke(second)
    reason = "rights_expired" if expired else "rights_revoked"
    assert d.client.get(path + "/content", headers=d.headers).json()["reason_code"] == reason
    assert d.client.get(path + "/derivation", headers=d.headers).status_code == 200
    assert d.client.post("/v1/derived-uploads", json=d.begin([chained]), headers=d.headers).json()["reason_code"] == reason


def test_read_permission_does_not_allow_new_processing(derived_env):
    d = derived_env
    source, converted = d.linked_source()
    d.revoke(source, status="granted", uses=("read",))
    assert d.client.get(f"/v1/artifacts/{converted.artifact_id}/content", headers=d.headers).status_code == 200
    response = d.client.post("/v1/derived-uploads", json=d.begin([converted]), headers=d.headers)
    assert response.json()["reason_code"] == "rights_use_denied"


def test_concurrent_begin_and_finalize_share_one_identity(derived_env):
    d = derived_env
    source = d.e.publish(b"input")
    raw = d.begin([source])
    command = parse_command("artifacts.begin_derived_upload", json.dumps(raw))
    barrier = Barrier(2)

    def begin(_):
        barrier.wait(timeout=5)
        return DerivedPublications(d.e.env.uploads).begin(d.principal, command)

    with ThreadPoolExecutor(max_workers=2) as pool:
        left, right = list(pool.map(begin, range(2)))
    assert left == right
    final = d.stream(raw)
    barrier = Barrier(2)

    def finish(index):
        barrier.wait(timeout=5)
        envelope = {**final, "identity": {**final["identity"], "command_id": f"final-{index}"}}
        return Finalizer(d.e.env.uploads, d.e.env.storage).finalize(d.principal, parse_command("artifacts.finalize", json.dumps(envelope)))

    with ThreadPoolExecutor(max_workers=2) as pool:
        left, right = list(pool.map(finish, range(2)))
    assert left == right
    with d.e.env.engine.connect() as connection:
        assert connection.execute(text("SELECT count(*) FROM artifacts.derivations WHERE tenant_id=:tenant AND project_id=:project"),
                                  d.principal.bindings).scalar_one() == 1


@pytest.mark.parametrize("table", ["derived_uploads", "derivations", "derivation_inputs"])
@pytest.mark.parametrize("operation", ["update", "delete"])
def test_service_role_cannot_rewrite_lineage(derived_env, table, operation):
    d = derived_env
    statement = f"UPDATE artifacts.{table} SET tenant_id=tenant_id WHERE false" if operation == "update" else f"DELETE FROM artifacts.{table} WHERE false"
    with pytest.raises(DBAPIError) as error, d.e.env.engine.begin() as connection:
        connection.execute(text(statement))
    assert error.value.orig.sqlstate == "42501"


def test_defensive_cycle_detection_blocks_payload_without_erasing_metadata(derived_env):
    d = derived_env
    root = d.e.publish(b"input")
    first = published(d, [root])
    second = published(d, [first])
    # Test-only corruption: normal finalized publication can only name existing inputs.
    with d.e.env.engine.begin() as connection:
        connection.execute(text("INSERT INTO artifacts.derivation_inputs "
            "(tenant_id,project_id,artifact_id,input_artifact_id,ordinal) VALUES (:tenant,:project,:first,:second,1)"),
            d.principal.bindings | {"first": first.artifact_id, "second": second.artifact_id})
    path = f"/v1/artifacts/{second.artifact_id}"
    assert d.client.get(path + "/content", headers=d.headers).json()["reason_code"] == "rights_lineage_cycle"
    assert d.client.get(path + "/derivation", headers=d.headers).status_code == 200


def test_foreign_declared_scope_never_begins_upload(derived_env):
    d = derived_env
    source = d.e.publish(b"input")
    raw = d.begin([source])
    raw["payload"]["declaration"]["inputs"][0]["scope"]["project_id"] = "foreign"
    assert d.client.post("/v1/derived-uploads", json=raw, headers=d.headers).status_code == 422
