from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from threading import Barrier

import pytest
from amphora_data_artifacts.publication.model import UploadError
from amphora_data_artifacts.source_rights.model import RightsError
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.postgres


def test_policy_history_replay_collision_and_atomic_head(ingestion):
    e = ingestion
    source = e.source()
    rights = e.workflow.rights
    admin = replace(e.principal, actions=frozenset({"manage_source_rights"}))
    first = rights.history(e.principal, "fixture", 1)
    second = first.model_copy(update={"reference": first.reference.model_copy(update={"revision": 2}),
                                      "supersedes": first.reference})

    def fail_head(_conn, _cursor, statement, _params, _context, _many):
        if statement.startswith("INSERT INTO artifacts.source_rights_heads"):
            raise RuntimeError("injected_head_failure")

    event.listen(e.env.engine, "before_cursor_execute", fail_head)
    try:
        with pytest.raises(RuntimeError, match="injected_head_failure"):
            rights.publish(admin, second)
    finally:
        event.remove(e.env.engine, "before_cursor_execute", fail_head)
    assert rights.history(e.principal, "fixture", 2) is None
    rights.publish(admin, second)
    assert rights.publish(admin, first) == first
    with pytest.raises(RightsError, match="rights_revision_conflict"):
        rights.publish(admin, second.model_copy(update={"allowed_uses": ("read",)}))
    fourth = second.model_copy(update={"reference": second.reference.model_copy(update={"revision": 4}),
                                      "supersedes": second.reference.model_copy(update={"revision": 3})})
    with pytest.raises(RightsError, match="rights_head_conflict"):
        rights.publish(admin, fourth)
    with pytest.raises(RightsError, match="rights_revision_stale"):
        e.workflow.prepare(e.principal, source)
    current = source.model_copy(update={"rights": second.reference})
    assert e.workflow.prepare(e.principal, current).content


def test_policy_scope_permissions_and_immutable_service_role(ingestion):
    e = ingestion
    source = e.source()
    rights = e.workflow.rights
    first = rights.history(e.principal, "fixture", 1)
    with pytest.raises(UploadError, match="access_denied"):
        rights.publish(e.principal, first)
    foreign = replace(e.principal, scope=e.principal.scope.model_copy(update={"project_id": "foreign"}),
                      actions=frozenset({"manage_source_rights", "source_history"}))
    with pytest.raises(RightsError, match="rights_scope_mismatch"):
        rights.publish(foreign, first)
    assert rights.history(foreign, "fixture", 1) is None
    snapshot = rights.capture(e.principal, declared=(source.rights,))
    with pytest.raises(RightsError, match="rights_scope_mismatch"):
        rights.recheck(foreign, snapshot)
    with pytest.raises(RightsError, match="rights_scope_mismatch"):
        rights.capture(foreign, declared=(source.rights,))
    with pytest.raises(RightsError, match="rights_use_denied"):
        rights.capture(e.principal, use="invented")
    for sql in ("UPDATE artifacts.source_rights_revisions SET canonical_bytes=decode('00','hex') WHERE false",
                "DELETE FROM artifacts.source_rights_revisions WHERE false"):
        with pytest.raises(DBAPIError) as error, e.env.engine.begin() as connection:
            connection.execute(text(sql))
        assert error.value.orig.sqlstate == "42501"


def test_concurrent_different_policy_revision_has_one_winner(ingestion):
    e = ingestion
    e.source()
    rights = e.workflow.rights
    first = rights.history(e.principal, "fixture", 1)
    admin = replace(e.principal, actions=frozenset({"manage_source_rights"}))
    barrier = Barrier(2)

    def publish(uses):
        record = first.model_copy(update={"reference": first.reference.model_copy(update={"revision": 2}),
            "supersedes": first.reference, "allowed_uses": uses})
        barrier.wait(timeout=5)
        try:
            rights.publish(admin, record)
            return "published"
        except RightsError as error:
            return str(error)

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(publish, [("read",), ("read", "process")])) == ["published", "rights_revision_conflict"]
