"""Actual source/catalog/rights preflight; no binding publication or fake-source authority."""

import hashlib
from dataclasses import replace

import pytest
from amphora_contracts_core import SchemaRef
from amphora_contracts_evidence import SourceSpan
from amphora_data_artifacts.acquisition.provenance import ProvenanceError, SourceDocument
from amphora_data_artifacts.publication.model import UploadError
from amphora_data_artifacts.representations.fixture import FixtureEncoder
from amphora_data_artifacts.representations.payloads import EncodedRepresentation
from amphora_data_artifacts.representations.storage.leases import WorkLeases
from amphora_data_artifacts.representations.storage.results import EncodingResults
from amphora_data_artifacts.representations.validation import RepresentationError
from amphora_data_artifacts.source_rights.model import RightsError

pytestmark = pytest.mark.postgres


def revise_rights(env, *, status="granted", uses=("read", "process")):
    prior = env.e.workflow.rights.history(env.principal, env.source.rights.rights_id, 1)
    changed = prior.model_copy(
        update={
            "reference": prior.reference.model_copy(update={"revision": 2}),
            "supersedes": prior.reference,
            "status": status,
            "allowed_uses": uses,
        }
    )
    env.e.workflow.rights.publish(env.principal, changed)


def test_exact_original_span_and_cached_retired_profile_are_reusable(source_setup):
    s = source_setup
    selected = s.preflight.load(s.principal, s.request)
    assert selected.input.content == b"ABBA" and selected.cached is None
    assert selected.rights.use == "process" and selected.rights.artifacts == (
        s.source.reference.raw.artifact_id,
    )
    inactive = replace(s.profile, version="retired", encoder=replace(s.profile.encoder, revision="retired"))
    ref = s.registry.register(s.principal, inactive)
    request = s.request.model_copy(update={"profile": ref})
    with pytest.raises(RepresentationError, match="encoder_unavailable"):
        s.preflight.load(s.principal, request)
    lease = WorkLeases(s.e.env.engine).claim(s.principal, ref, selected.input)
    retained = EncodedRepresentation.prepare(
        inactive, selected.input, FixtureEncoder().encode(s.profile, selected.input)
    )
    EncodingResults(s.e.env.engine).complete(s.principal, lease, retained)
    recovered = s.preflight.load(s.principal, request)
    assert recovered.cached == retained and recovered.work == lease.work


def test_current_rights_deny_before_cache_read(source_setup, monkeypatch):
    s = source_setup
    revise_rights(s, status="revoked", uses=())

    def forbidden(*_args):
        raise AssertionError("Cache must not be touched before current source authorization")

    monkeypatch.setattr(s.preflight.results, "read", forbidden)
    with pytest.raises(RightsError, match="rights_revoked"):
        s.preflight.load(s.principal, s.request)


def test_read_only_rights_do_not_authorize_encoding(source_setup):
    s = source_setup
    revise_rights(s, uses=("read",))
    with pytest.raises(RightsError, match="rights_use_denied"):
        s.preflight.load(s.principal, s.request)


def test_rights_change_after_source_read_is_fenced(source_setup, monkeypatch):
    s = source_setup
    original = s.e.reads.content

    def changed(*args):
        result = original(*args)
        revise_rights(s)
        return result

    monkeypatch.setattr(s.e.reads, "content", changed)
    with pytest.raises(RightsError, match="rights_epoch_changed"):
        s.preflight.load(s.principal, s.request)


def test_later_source_revision_does_not_repin_existing_source_request(source_setup):
    s = source_setup
    raw = s.e.publish(b"changed scientific information")
    later = s.source.model_copy(
        update={
            "reference": s.source.reference.model_copy(update={"revision_id": "r2", "raw": raw}),
            "supersedes": s.source.reference,
            "delivery": s.source.delivery.model_copy(update={"delivery_id": "d2"}),
        }
    )
    s.e.ledger.register(
        s.e.principal, later, SourceDocument(later.reference, b"changed scientific information")
    )
    selected = s.preflight.load(s.principal, s.request)
    assert selected.identity.source.source == s.source.reference and selected.input.content == b"ABBA"


def test_unknown_source_wrong_artifact_and_span_digest_fail(source_setup):
    s = source_setup
    for ref in (
        s.source.reference.model_copy(update={"revision_id": "missing"}),
        s.source.reference.model_copy(
            update={"raw": s.source.reference.raw.model_copy(update={"sha256": "a" * 64})}
        ),
    ):
        with pytest.raises(RepresentationError, match="source_reference"):
            s.preflight.load(
                s.principal,
                s.request.model_copy(update={"source": s.request.source.model_copy(update={"source": ref})}),
            )
    with pytest.raises(ProvenanceError, match="span_digest_mismatch"):
        s.preflight.load(
            s.principal,
            s.request.model_copy(update={"source": s.request.source.model_copy(update={"sha256": "a" * 64})}),
        )


def test_grants_and_unavailable_context_are_checked_before_source_io(source_setup, monkeypatch):
    s = source_setup

    def forbidden(*_args):
        raise AssertionError("Source I/O must not precede prerequisite validation")

    monkeypatch.setattr(s.e.reads, "content", forbidden)
    for grant in ("read", "source_history", "representation_read", "representation_encode"):
        with pytest.raises(UploadError, match="access_denied"):
            s.preflight.load(replace(s.principal, actions=s.principal.actions - {grant}), s.request)
    contextual = replace(
        s.profile,
        version="context",
        inputs=replace(
            s.profile.inputs,
            context_schema=SchemaRef(schema_id="fixture.context", version="1", sha256="c" * 64),
        ),
    )
    ref = s.registry.register(s.principal, contextual)
    with pytest.raises(RepresentationError, match="context_unavailable"):
        s.preflight.load(s.principal, s.request.model_copy(update={"profile": ref}))


def test_split_utf8_span_is_not_silently_repaired(source_setup):
    s = source_setup
    content = "\u00e9".encode("utf-8")
    raw = s.e.publish(content)
    later = s.source.model_copy(
        update={
            "reference": s.source.reference.model_copy(update={"revision_id": "r2", "raw": raw}),
            "supersedes": s.source.reference,
            "delivery": s.source.delivery.model_copy(update={"delivery_id": "d2"}),
        }
    )
    s.e.ledger.register(s.e.principal, later, SourceDocument(later.reference, content))
    span = SourceSpan(
        source=later.reference, unit="byte", start=0, end=1, sha256=hashlib.sha256(content[:1]).hexdigest()
    )
    with pytest.raises(RepresentationError, match="input_utf8"):
        s.preflight.load(s.principal, s.request.model_copy(update={"source": span}))


def test_cache_errors_other_than_missing_work_are_not_hidden(source_setup, monkeypatch):
    s = source_setup

    def corrupt(*_args):
        raise RepresentationError("representation_work_conflict")

    monkeypatch.setattr(s.preflight.results, "read", corrupt)
    with pytest.raises(RepresentationError, match="work_conflict"):
        s.preflight.load(s.principal, s.request)
