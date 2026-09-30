"""Actual owner-role transactions; immutable revisions, optimistic race and lost-ack replay."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_campaign_runtime.definitions import storage
from amphora_campaign_runtime.definitions.commands import DefinitionCommands
from amphora_campaign_runtime.definitions.reads import DefinitionReads
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_campaign_runtime.persistence.commands import CommandConflict
from amphora_contracts_graph_runtime import parse_authoring_command
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from .test_revisions import save


def command(e, key="save-1", revision=0, title="Draft"):
    payload = json.loads(save(revision, title).model_dump_json())
    payload["definition"]["scope"] = e.principal.scope.model_dump()
    return parse_authoring_command("definition.save", json.dumps({"identity": {"scope": e.principal.scope.model_dump(),
        "actor_id": e.principal.actor_id, "command_family": "definition.save", "command_id": key}, "payload": payload}))


def owner(e):
    e.principal = replace(e.principal, actions=e.principal.actions | {"author", "read"})
    return DefinitionCommands(e.engine)


def bindings(e):
    return {"tenant": e.principal.scope.tenant_id, "project": e.principal.scope.project_id, "draft": "draft"}


def test_save_replay_and_role_preserve_old_revision(fixture_env):
    e = fixture_env
    service = owner(e)
    first = command(e)
    receipt = service.save(e.principal, first)
    assert receipt.outcome.status == "accepted" and receipt.outcome.committed.revision == 1
    assert service.save(e.principal, first) == receipt
    second = service.save(e.principal, command(e, "save-2", 1, "Updated"))
    assert second.outcome.committed.revision == 2
    assert service.save(e.principal, first) == receipt
    with e.engine.connect() as conn:
        current = storage.head(conn, bindings(e))
        assert current.revision == 2 and current.content.title == "Updated"
        assert conn.execute(text("SELECT count(*) FROM runtime.definition_audit WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 2
    with pytest.raises(CommandConflict):
        service.save(e.principal, command(e, title="Changed under same command"))
    for statement in ("UPDATE runtime.definition_revisions SET content_sha256=content_sha256",
                      "DELETE FROM runtime.definition_audit", "UPDATE runtime.definition_heads SET draft_id=draft_id"):
        with pytest.raises(DBAPIError), e.engine.begin() as conn:
            conn.execute(text(statement))


def test_concurrent_same_base_has_one_winner_and_terminal_loser(fixture_env):
    e = fixture_env
    service = owner(e)
    service.save(e.principal, command(e))
    barrier = Barrier(2)
    requests = [command(e, "edit-a", 1, "A"), command(e, "edit-b", 1, "B")]

    def edit(request):
        barrier.wait(timeout=5)
        return service.save(e.principal, request)

    with ThreadPoolExecutor(max_workers=2) as pool:
        receipts = list(pool.map(edit, requests))
    assert sorted(r.outcome.status for r in receipts) == ["accepted", "rejected"]
    loser = next(r for r in receipts if r.outcome.status == "rejected")
    assert loser.outcome.reason_code == "draft_revision_conflict"
    service.save(e.principal, command(e, "later", 2, "Later"))
    assert [service.save(e.principal, c) for c in requests] == receipts


def test_failure_before_receipt_rolls_back_head_revision_and_audit(fixture_env, monkeypatch):
    e = fixture_env
    service = owner(e)
    original = storage.persist

    def fail_after_write(*args):
        original(*args)
        raise RuntimeError("controlled_before_receipt")

    monkeypatch.setattr(storage, "persist", fail_after_write)
    request = command(e)
    with pytest.raises(RuntimeError, match="controlled_before_receipt"):
        service.save(e.principal, request)
    assert DefinitionReads(e.engine).receipt(e.principal, "definition.save", "save-1").outcome.status == "pending"
    with e.engine.connect() as conn:
        assert storage.head(conn, bindings(e)) is None
        assert conn.execute(text("SELECT count(*) FROM runtime.definition_revisions WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 0
    monkeypatch.setattr(storage, "persist", original)
    assert service.save(e.principal, request).outcome.committed.revision == 1


def test_denial_precedes_registration(fixture_env):
    e = fixture_env
    service = DefinitionCommands(e.engine)
    with pytest.raises(TransitionError, match="access_denied"):
        service.save(e.principal, command(e))
    with e.engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM runtime.commands WHERE tenant_id=:tenant AND project_id=:project"), bindings(e)).scalar_one() == 0
