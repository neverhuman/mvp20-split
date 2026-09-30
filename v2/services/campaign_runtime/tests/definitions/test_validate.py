"""Actual PostgreSQL validation evidence, interrupted receipt recovery and immutable replay."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.definitions import validation_storage
from amphora_campaign_runtime.definitions.reads import DefinitionReadError, DefinitionReads
from amphora_campaign_runtime.definitions.validate import DefinitionValidator
from amphora_campaign_runtime.definitions.validation import ValidationUniverse
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_graph_runtime import parse_authoring_command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .test_commands import bindings, command, owner


def setup(e):
    saves = owner(e)
    e.principal = replace(e.principal, actions=e.principal.actions | {"validate"})
    saves.save(e.principal, command(e))
    universe = ValidationUniverse(e.principal.scope, (), ())
    key = (e.principal.scope.tenant_id, e.principal.scope.project_id)
    return saves, DefinitionValidator(e.engine, {key: universe}), universe


def request(e, key="validate-1", digest=None, revision=1):
    draft = DefinitionReads(e.engine).revision(e.principal, "draft", revision)
    return parse_authoring_command("definition.validate", json.dumps({"identity": {
        "scope": e.principal.scope.model_dump(), "actor_id": e.principal.actor_id,
        "command_family": "definition.validate", "command_id": key}, "payload": {
        "draft_id": "draft", "revision": revision, "content_sha256": digest or draft.head.content_sha256}}))


def test_validation_pins_old_revision_and_replays_without_current_universe(fixture_env):
    e = fixture_env
    saves, validator, universe = setup(e)
    validate = request(e)
    # Validation of an immutable older revision is legal; activation must separately guard head.
    saves.save(e.principal, command(e, "newer", 1, "Newer"))
    receipt = validator.validate(e.principal, validate)
    assert receipt.outcome.status == "accepted" and receipt.outcome.committed.kind == "draft_validation"
    reads = DefinitionReads(e.engine)
    result = reads.validation(e.principal, receipt.outcome.committed.object_id)
    assert result.revision == 1 and result.structurally_valid and result.universe_sha256 == universe.sha256
    replacement = DefinitionValidator(e.engine, {})
    assert replacement.validate(e.principal, validate) == receipt
    assert reads.receipt(e.principal, "definition.validate", "validate-1") == receipt
    with e.engine.connect() as conn:
        material = conn.execute(text("SELECT material FROM runtime.definition_universes WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one()
    restored = ValidationUniverse.restore(material, result.universe_sha256)
    from amphora_campaign_runtime.definitions.revisions import DraftVersion
    assert restored.validate(DraftVersion.from_wire(reads.revision(e.principal, "draft", 1))).to_wire(result.validation_id) == result
    for table in ("definition_universes", "definition_validations"):
        with pytest.raises(DBAPIError), e.engine.begin() as conn:
            conn.execute(text(f"DELETE FROM runtime.{table}"))


def test_validation_denial_and_mismatch_do_not_create_evidence(fixture_env):
    e = fixture_env
    _, validator, _ = setup(e)
    denied = replace(e.principal, actions=frozenset({"read", "author"}))
    with pytest.raises(TransitionError, match="access_denied"):
        validator.validate(denied, request(e))
    with pytest.raises(DefinitionReadError, match="unavailable"):
        DefinitionReads(e.engine).receipt(e.principal, "definition.validate", "validate-1")
    bad = request(e, digest="0" * 64)
    receipt = validator.validate(e.principal, bad)
    assert receipt.outcome.reason_code == "draft_content_mismatch"
    assert validator.validate(e.principal, bad) == receipt
    missing = DefinitionValidator(e.engine, {}).validate(e.principal, request(e, "missing"))
    assert missing.outcome.reason_code == "validation_universe_unavailable"
    with e.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.definition_validations WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 0


def test_validation_receipt_failure_rolls_back_evidence_and_retry_recovers(fixture_env, monkeypatch):
    e = fixture_env
    _, validator, _ = setup(e)
    original = validation_storage.persist

    def fail(*args):
        original(*args)
        raise RuntimeError("validation_before_receipt")

    monkeypatch.setattr(validation_storage, "persist", fail)
    validate = request(e)
    with pytest.raises(RuntimeError, match="validation_before_receipt"):
        validator.validate(e.principal, validate)
    assert DefinitionReads(e.engine).receipt(e.principal, "definition.validate", "validate-1").outcome.status == "pending"
    with e.engine.connect() as conn:
        for table in ("definition_universes", "definition_validations"):
            assert conn.execute(text(f"SELECT count(*) FROM runtime.{table} WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 0
    monkeypatch.setattr(validation_storage, "persist", original)
    assert validator.validate(e.principal, validate).outcome.status == "accepted"


def test_structurally_invalid_draft_records_failed_validation(fixture_env):
    e = fixture_env
    saves, validator, _ = setup(e)
    payload = json.loads(command(e, "invalid", 1).canonical_bytes)
    payload["payload"]["definition"]["body"]["nodes"].append({"kind": "finish", "node_id": "second", "outputs": []})
    saves.save(e.principal, parse_authoring_command("definition.save", json.dumps(payload)))
    receipt = validator.validate(e.principal, request(e, revision=2))
    assert receipt.outcome.status == "accepted"
    result = DefinitionReads(e.engine).validation(e.principal, receipt.outcome.committed.object_id)
    assert not result.structurally_valid and result.plan_sha256 is None and result.findings
    assert result.scientific_acceptance == "not_established"


def test_concurrent_validation_replay_commits_one_record(fixture_env):
    e = fixture_env
    _, validator, _ = setup(e)
    validate = request(e)
    barrier = Barrier(2)

    def run(_):
        barrier.wait(timeout=5)
        return validator.validate(e.principal, validate)

    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(run, range(2)))
    assert receipts[0] == receipts[1] and receipts[0].outcome.status == "accepted"
    # A separate command can record its own result while sharing retained material.
    validator.validate(e.principal, request(e, "second"))
    with e.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.definition_universes WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 1
        assert conn.execute(text("SELECT count(*) FROM runtime.definition_validations WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 2
