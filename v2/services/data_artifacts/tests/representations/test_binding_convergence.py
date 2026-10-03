"""Actual source-independent rights, compute reuse and attributable alias convergence."""

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from threading import Event, Lock

import pytest
from amphora_data_artifacts.acquisition.provenance import SourceDocument
from amphora_data_artifacts.representations.bindings.workflow import BindingWorkflow, RecoveryBudget
from amphora_data_artifacts.representations.fixture import FixtureEncoder
from amphora_data_artifacts.source_rights.model import RightsError
from sqlalchemy import text

pytestmark = pytest.mark.postgres


def record(e, name, observations):
    folder = Path(__file__).absolute().parents[4] / ".test-results" / "representation-convergence"
    folder.mkdir(parents=True, exist_ok=True)
    body = {
        "timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scope": e.p.scope.model_dump(mode="json"),
        "observations": observations,
    }
    (folder / (name + ".json")).write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


def second_source(e):
    content = b"prefix ABBA suffix"
    original = e.e.source
    raw = e.e.e.publish(content)
    rights = original.rights.model_copy(update={"rights_id": "independent"})
    policy = e.e.e.workflow.rights.history(e.p, original.rights.rights_id, 1)
    e.e.e.workflow.rights.publish(e.p, policy.model_copy(update={"reference": rights}))
    source = original.model_copy(
        update={
            "reference": original.reference.model_copy(update={"source_id": "independent", "raw": raw}),
            "delivery": original.delivery.model_copy(update={"delivery_id": "independent"}),
            "rights": rights,
        }
    )
    e.e.e.ledger.register(e.p, source, SourceDocument(source.reference, content))
    request = e.request.model_copy(
        update={
            "encoding_id": "independent",
            "source": e.request.source.model_copy(update={"source": source.reference}),
        }
    )
    return source, request


def counts(e):
    with e.engine.connect() as connection:
        return {
            table: connection.execute(
                text(
                    "SELECT count(*) FROM artifacts."
                    + table
                    + " WHERE tenant_id=:tenant AND project_id=:project"
                ),
                e.p.bindings,
            ).scalar_one()
            for table in (
                "encoding_work",
                "encoding_results",
                "encoding_binding_jobs",
                "representation_bindings",
                "derivations",
            )
        }


def test_identical_content_keeps_independent_source_rights_and_lineage(flow):
    e = flow
    source2, request2 = second_source(e)
    first = e.workflow.encode(e.p, e.request).outcome.binding
    second = e.workflow.encode(e.p, request2).outcome.binding
    assert first.vector.sha256 == second.vector.sha256
    assert first.vector.artifact_id != second.vector.artifact_id
    assert first.reference != second.reference
    assert counts(e) == {
        "encoding_work": 1,
        "encoding_results": 1,
        "encoding_binding_jobs": 2,
        "representation_bindings": 2,
        "derivations": 2,
    }
    for binding, source in ((first, e.e.source), (second, source2)):
        receipt = e.workflow.derived.read(e.p, binding.vector.artifact_id)
        assert receipt.declaration.inputs == (source.reference.raw,)
    prior = e.e.e.workflow.rights.history(e.p, e.e.source.rights.rights_id, 1)
    denied = prior.model_copy(
        update={
            "reference": prior.reference.model_copy(update={"revision": 2}),
            "supersedes": prior.reference,
            "status": "revoked",
            "allowed_uses": (),
        }
    )
    e.e.e.workflow.rights.publish(e.p, denied)
    with pytest.raises(RightsError):
        e.e.e.reads.content(e.p, first.vector.artifact_id)
    with pytest.raises(RightsError):
        e.workflow.encode(e.p, e.request.model_copy(update={"encoding_id": "revoked-alias"}))
    _, content = e.e.e.reads.content(e.p, second.vector.artifact_id)
    assert content
    alias = request2.model_copy(update={"encoding_id": "permitted-alias"})
    assert e.workflow.encode(e.p, alias).outcome.binding == second
    assert e.workflow.encode(e.p, e.request).outcome.binding == first
    assert counts(e)["encoding_results"] == 1
    record(
        e,
        "independent_rights",
        {
            "first": first.model_dump(mode="json"),
            "second": second.model_dump(mode="json"),
            "revoked": denied.model_dump(mode="json"),
            "counts": counts(e),
            "first_bytes": "denied",
            "second_bytes": "allowed",
        },
    )


def test_different_publishers_share_compute_without_impersonating_commands(flow):
    e = flow
    first = e.workflow.encode(e.p, e.request).outcome.binding
    other = replace(e.p, actor_id="other-publisher")
    second = e.workflow.encode(other, e.request).outcome.binding
    assert first.reference != second.reference
    assert (
        first.vector.sha256 == second.vector.sha256 and first.vector.artifact_id != second.vector.artifact_id
    )
    for principal, binding in ((e.p, first), (other, second)):
        receipt = e.workflow.derived.read(principal, binding.vector.artifact_id)
        assert receipt.origin.actor_id == principal.actor_id
        assert e.workflow.requests.read(principal, e.request.encoding_id).outcome.binding == binding
    assert counts(e)["encoding_results"] == 1
    assert counts(e)["representation_bindings"] == 2
    record(
        e,
        "publishers",
        {
            "first": first.model_dump(mode="json"),
            "second": second.model_dump(mode="json"),
            "actors": [e.p.actor_id, other.actor_id],
            "counts": counts(e),
        },
    )


def test_concurrent_aliases_retain_pending_then_converge_once(flow, monkeypatch):
    e = flow
    entered, release = Event(), Event()
    lock = Lock()
    calls = []
    original = FixtureEncoder.encode

    def blocked(self, profile, source):
        with lock:
            calls.append(source.sha256)
        entered.set()
        assert release.wait(15), "test did not release the computation barrier"
        return original(self, profile, source)

    monkeypatch.setattr(FixtureEncoder, "encode", blocked)
    aliases = [e.request.model_copy(update={"encoding_id": "alias-" + str(i)}) for i in range(3)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        first = pool.submit(e.workflow.encode, e.p, e.request)
        try:
            assert entered.wait(10)
            others = [pool.submit(e.workflow.encode, e.p, request) for request in aliases]
            assert all(future.result(timeout=10).outcome.state == "pending" for future in others)
            assert len(calls) == 1
            assert counts(e)["representation_bindings"] == 0
        finally:
            release.set()
        published = first.result(timeout=15)
    replacement = BindingWorkflow(e.e.e.reads, e.uploads, e.storage)
    for request in aliases:
        assert replacement.encode(e.p, request).outcome == published.outcome
    assert len(calls) == 1
    assert counts(e) == {
        "encoding_work": 1,
        "encoding_results": 1,
        "encoding_binding_jobs": 1,
        "representation_bindings": 1,
        "derivations": 1,
    }


def test_new_source_revision_does_not_repin_published_or_pending_request(flow):
    e = flow
    e.workflow.budget = RecoveryBudget(1)
    assert e.workflow.encode(e.p, e.request).outcome.state == "pending"
    source2, request2 = second_source(e)
    old = e.e.source
    corrected = old.model_copy(
        update={
            "reference": old.reference.model_copy(update={"revision_id": "r2"}),
            "delivery": old.delivery.model_copy(update={"delivery_id": "revision2"}),
            "supersedes": old.reference,
        }
    )
    e.e.e.ledger.register(e.p, corrected, SourceDocument(corrected.reference, b"prefix ABBA suffix"))
    e.workflow.budget = RecoveryBudget()
    first = e.workflow.encode(e.p, e.request)
    alias = e.request.model_copy(update={"encoding_id": "old-pinned-alias"})
    assert e.workflow.encode(e.p, alias).outcome == first.outcome
    assert first.outcome.binding.source.source.revision_id == "r1"
    assert e.workflow.encode(e.p, request2).outcome.binding.source.source == source2.reference
