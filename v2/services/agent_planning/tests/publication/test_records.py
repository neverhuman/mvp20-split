import hashlib
import json
from dataclasses import replace

import pytest
from amphora_agent_planning.access import Principal
from amphora_agent_planning.publication import (
    PublicationAttempt,
    PublicationIdentity,
    TraceArtifact,
    content_schema,
)
from amphora_agent_planning.publication.records import PayloadRecord, PublicationEvent, encode
from amphora_agent_planning.publication.review_record import ReviewRecord

from .test_values import prepared


def test_historical_metadata_rebuilds_identical_payload_without_source_payload_cache():
    identity, projection, review, artifact = prepared()
    record = ReviewRecord.from_review(review)
    assert record.document()["task_sha256"] == review.task.sha256
    assert "source_text" not in record.document() and "trusted_instructions" not in record.document()
    assert TraceArtifact.restore(identity, projection, review.task, record) == artifact
    payload = PayloadRecord(artifact, record)
    row = {"trace_bytes": artifact.body, "review_bytes": record.canonical,
           "manifest_bytes": payload.manifest, "payload_sha256": payload.sha256}
    assert PayloadRecord.from_row(row, identity, projection, review.task, content_schema()) == payload
    for key, value in (("trace_bytes", artifact.body + b" "), ("manifest_bytes", payload.manifest + b" "),
                       ("payload_sha256", "f" * 64)):
        with pytest.raises(ValueError, match="stored_publication_payload"):
            PayloadRecord.from_row({**row, key: value}, identity, projection, review.task, content_schema())


@pytest.mark.parametrize("raw", [b"", b"x" * 4194305, b'{"x":1,"x":2}', b'{"x":NaN}', b"[]"],
                         ids=["empty", "size", "duplicate", "nonfinite", "shape"])
def test_historical_review_rejects_unbounded_or_ambiguous_wire(raw):
    with pytest.raises(ValueError):
        ReviewRecord.from_bytes(raw)


def test_stored_identity_does_not_fabricate_write_authority_or_accept_noncanonical_bytes():
    identity, _, _, _ = prepared()
    reader = Principal(identity.actor_id, identity.trace().scope, frozenset({"read_attempts"}))
    assert PublicationIdentity.restore(identity.canonical, reader) == identity
    with pytest.raises(ValueError, match="publication_identity_canonical"):
        PublicationIdentity.restore(identity.canonical + b" ", reader)
    with pytest.raises(ValueError, match="publication_actor_binding"):
        PublicationIdentity.restore(identity.canonical, replace(reader, actor_id="other"))
    for raw in (b"", b"[]", b'{"format":"future"}'):
        with pytest.raises(ValueError):
            PublicationIdentity.restore(raw, reader)


@pytest.mark.parametrize("field,value", [("position", True), ("position", 2), ("ordinal", True),
    ("ordinal", 2), ("action", "streaming"), ("data", {}), ("format", "future"), ("extra", True)])
def test_hash_valid_but_invalid_initial_events_cannot_be_replayed(field, value):
    identity, _, _, artifact = prepared()
    initial = PublicationEvent.record(1, PublicationAttempt.first(identity), "prepared", None)
    raw = json.loads(initial.canonical)
    raw[field] = value
    event = PublicationEvent(encode(raw))
    assert event.sha256 == hashlib.sha256(event.canonical).hexdigest()  # Hash alone is not validity.
    with pytest.raises(ValueError):
        event.apply(None, identity, artifact, 1)


def test_unsupported_or_out_of_order_event_does_not_authorize_an_effect():
    identity, _, _, artifact = prepared()
    first = PublicationAttempt.first(identity)
    for action, data in (("prepared", None), ("invented", None), ("streaming", None),
                          ("replacement", {}), ("finalized", {"receipt": {}}),
                          ("rejected", {"reason": "x", "extra": True})):
        event = PublicationEvent.record(2, first, action, data)
        with pytest.raises(ValueError):
            event.apply(first, identity, artifact, 2)
    with pytest.raises(ValueError, match="publication_event_limit"):
        PublicationEvent.record(65, first, "prepared", None)
    with pytest.raises(ValueError, match="publication_event_size"):
        PublicationEvent.record(2, first, "rejected", {"reason": "x" * 262144})
