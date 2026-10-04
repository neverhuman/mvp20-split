"""Close named binding acceptance gaps with actual retained owner state."""

import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from amphora_data_artifacts.publication.model import ContentPolicy, UploadError
from amphora_data_artifacts.representations.bindings import leases
from amphora_data_artifacts.representations.bindings.workflow import (
    BindingWorkflow,
    RecoveryBudget,
)
from sqlalchemy import text

from .test_binding_workflow import encode, stopped_at_upload

pytestmark = pytest.mark.postgres


def test_publication_between_claim_reads_returns_original_binding(flow, monkeypatch):
    e = flow
    e.workflow.budget = RecoveryBudget(1)
    assert encode(e).outcome.state == "pending"
    e.workflow.budget = RecoveryBudget()
    identity = e.e.preflight.load(e.p, e.request).identity
    original = leases.published
    main_thread = threading.get_ident()
    observed, release = threading.Event(), threading.Event()

    def paused(*args):
        result = original(*args)
        if threading.get_ident() != main_thread and not observed.is_set():
            assert result is None
            observed.set()
            assert release.wait(15)
        return result

    monkeypatch.setattr(leases, "published", paused)
    with ThreadPoolExecutor(max_workers=1) as pool:
        contender = pool.submit(e.workflow.claims.claim, e.p, identity.binding_id)
        try:
            assert observed.wait(15)
            winner = encode(e)
            assert winner.outcome.state == "published"
        finally:
            release.set()
        assert contender.result(timeout=15) == winner.outcome.binding
    assert encode(e) == winner


@pytest.mark.parametrize("stage", ["begin", "finalize"])
def test_lost_rejection_is_recovered_before_numbered_retry(flow, monkeypatch, stage):
    e = flow
    policy = e.uploads.policy
    if stage == "begin":
        e.uploads.policy = ContentPolicy(frozenset())
        target, method = e.workflow.derived, "begin"
    else:
        prefix = stopped_at_upload(e)
        e.uploads.limits = replace(e.uploads.limits, attempts=1)
        attempt = e.uploads.start(e.p, prefix.upload_id)
        e.uploads.finish(e.p, attempt, verified=False, actual_bytes=0)
        target, method = e.workflow.finalizer, "finalize"
    original = getattr(target, method)

    def lost(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except UploadError as error:
            raise OSError("lost terminal rejection") from error

    monkeypatch.setattr(target, method, lost)
    with pytest.raises(OSError, match="lost terminal rejection"):
        encode(e)
    e.uploads.policy = policy
    e.workflow = BindingWorkflow(e.e.e.reads, e.uploads, e.storage)
    with pytest.raises(UploadError):
        encode(e)
    result = encode(e)
    assert result.outcome.state == "published"
    with e.engine.connect() as c:
        attempts = (
            c.execute(
                text(
                    "SELECT DISTINCT attempt FROM artifacts.encoding_binding_events "
                    "WHERE tenant_id=:tenant AND project_id=:project ORDER BY attempt"
                ),
                e.p.bindings,
            )
            .scalars()
            .all()
        )
        assert attempts == [1, 2]
    assert encode(e) == result


def test_writer_constructor_failure_settles_capacity_before_retry(flow, monkeypatch):
    e = flow
    original = e.storage.writer

    def unavailable(_attempt):
        raise OSError("writer construction unavailable")

    monkeypatch.setattr(e.storage, "writer", unavailable)
    with pytest.raises(OSError, match="writer construction unavailable"):
        encode(e)
    with e.engine.connect() as c:
        assert (
            c.execute(
                text(
                    "SELECT active_streams FROM artifacts.capacity WHERE tenant_id=:tenant AND project_id=:project"
                ),
                e.p.bindings,
            ).scalar_one()
            == 0
        )
    assert (
        e.workflow.requests.read(e.p, e.request.encoding_id).outcome.state == "pending"
    )
    monkeypatch.setattr(e.storage, "writer", original)
    e.workflow = BindingWorkflow(e.e.e.reads, e.uploads, e.storage)
    recovered = encode(e)
    assert recovered.outcome.state == "published"
    assert encode(e) == recovered
