"""Defensive workflow probes over real journals; scripted transport is not actual-peer evidence."""
import json

import pytest
from amphora_contracts_artifacts import DerivationReceipt, FinalizedReceipt, UploadContentReceipt
from amphora_research.scientific_publication.artifact import ScientificPublicationError
from amphora_research.scientific_publication.workflow import ScientificPublicationWorkflow

from .test_publication import finalizing, publication, terminal, uploaded

pytestmark = pytest.mark.postgres


class Reader:
    def __init__(self, scope):
        self.scope = scope
    def read(self, reference):
        assert reference.scope == self.scope


def scripted_client(monkeypatch, store, initial):
    calls = []
    class Client:
        def __init__(self, *args):
            pass
        def begin_derived(self, content, declaration, identity, **kwargs):
            kwargs["guard"]()
            calls.append(("begin",identity))
            return uploaded(store.read(initial))
        def stream(self, upload, body, **kwargs):
            kwargs["guard"]()
            calls.append(("stream",upload.upload_id))
            return UploadContentReceipt(upload_id=upload.upload_id,attempt_id="stream",generation=1)
        def finalize(self, upload, identity, **kwargs):
            kwargs["guard"]()
            calls.append(("finalize",identity))
            return FinalizedReceipt.model_validate_json(json.dumps(terminal(store.read(initial))["finalized"]))
        def derivation(self, reference):
            calls.append(("derivation",reference.artifact_id))
            return DerivationReceipt.model_validate_json(json.dumps(terminal(store.read(initial))["derivation"]))
    monkeypatch.setattr("amphora_research.scientific_publication.workflow.ArtifactClient",Client)
    return calls


def test_terminal_committed_between_initial_read_and_lease_needs_no_peer_effect(ledger,monkeypatch):
    store,initial = publication(ledger)
    acquire = store.acquire
    results = []
    def raced_acquire(selected):
        competing = acquire(selected)
        progress = finalizing(store,competing)
        results.append(store.advance(competing,progress.position,"published",terminal(progress)))
        store.release(competing)
        return acquire(selected)
    calls = scripted_client(monkeypatch,store,initial)
    with monkeypatch.context() as patch:
        patch.setattr(store,"acquire",raced_acquire)
        result = ScientificPublicationWorkflow(store,None,None,"publisher").submit(initial.artifact)
    assert result == results[0] == store.read(initial)
    assert calls == []
    # The lease taken after the competing terminal was released by the workflow.
    available = store.acquire(initial)
    assert available is not None
    store.release(available)


def test_stalled_adapter_budget_leaves_durable_stage_and_allows_healthy_retry(ledger,monkeypatch):
    store,initial = publication(ledger)
    calls = scripted_client(monkeypatch,store,initial)
    workflow = ScientificPublicationWorkflow(store,Reader(initial.scope),None,"publisher")
    def stalled(lease, position, action, data=None):
        assert position == 0 and action == "begun"
        return store.read(initial)
    with monkeypatch.context() as patch:
        patch.setattr(store,"advance",stalled)
        with pytest.raises(ScientificPublicationError,match="science_publication_progress_limit"):
            workflow.submit(initial.artifact)
    assert len(calls) == 12 and len(set(calls)) == 1
    assert store.read(initial) == initial
    recovered = workflow.submit(initial.artifact)
    assert recovered.stage == "published" and recovered.ordinal == 1
    assert len({identity for kind,identity in calls if kind == "begin"}) == 1
    prior_calls = list(calls)
    assert workflow.submit(initial.artifact) == recovered and calls == prior_calls


@pytest.mark.parametrize("lost",[True,False])
def test_release_failure_preserves_committed_publication_and_effect_free_replay(ledger,monkeypatch,lost):
    store,initial = publication(ledger)
    calls = scripted_client(monkeypatch,store,initial)
    workflow = ScientificPublicationWorkflow(store,Reader(initial.scope),None,"publisher")
    release = store.release
    def failed_release(lease):
        release(lease)
        if lost:
            release(lease)  # Real guard detects that this holder no longer owns a lease.
        else:
            raise ScientificPublicationError("injected_release_failure")
    with monkeypatch.context() as patch:
        patch.setattr(store,"release",failed_release)
        if lost:
            observed = workflow.submit(initial.artifact)
            assert observed.stage == "published"
        else:
            with pytest.raises(ScientificPublicationError,match="injected_release_failure"):
                workflow.submit(initial.artifact)
    committed = store.read(initial)
    assert committed.stage == "published" and committed.failure is None
    assert [kind for kind,_ in calls].count("finalize") == 1
    prior_calls = list(calls)
    assert workflow.submit(initial.artifact) == committed and calls == prior_calls
