"""Actual owned origin; raw captures stay raw and publication remains separate."""

from dataclasses import replace

import pytest
from amphora_agent_planning.providers.capture import (
    CapturedOutput,
    Observation,
    unknown_usage,
)
from amphora_agent_planning.publication.attempt import PublicationAttempt
from amphora_agent_planning.supervision_publication import (
    CaptureArtifact,
    CaptureIdentity,
    CaptureOrigin,
)
from amphora_contracts_core import ArtifactRef

from ..supervision_execution.test_worker import setup

pytestmark = pytest.mark.postgres


@pytest.fixture
def origin(stored):
    worker, _, _, intake = setup(stored)
    result = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    record = worker.preparations.read(stored.principal, intake.planning.document().reference).record
    return CaptureOrigin.bind(intake, stored.principal, record, result.latest.observation)


def reference(origin, artifact):
    return ArtifactRef(scope=origin.scope, artifact_id='captured-by-data',
        **artifact.content.model_dump(mode='python'))


def test_exact_opaque_bytes_derivation_response_and_command(stored, origin):
    artifact = CaptureArtifact.bind(origin)
    assert artifact.body == origin.observation.capture.content
    assert artifact.content.media_type == 'application/octet-stream'
    assert len(artifact.declaration.inputs) == 5
    assert {ref.artifact_id for ref in artifact.declaration.inputs} == {
        row['identity']['artifact_id'] for row in origin.packet.preparation.packet.context()['slices']}
    identity = CaptureIdentity.bind(stored.principal, origin, 'publisher-v1')
    ref = reference(origin, artifact)
    response = identity.response(stored.principal, origin, ref)
    assert response.observation == origin.observation.document() and response.capture == ref
    assert response.request_sha256 == origin.packet.context.snapshot.sha256
    command = identity.command(stored.principal, origin, ref)
    assert command.identity.command_id == identity.publication_id
    attempt = PublicationAttempt.first(identity)
    assert attempt.begin_command(identity, artifact).identity.scope == origin.scope
    changed = CaptureIdentity.bind(stored.principal, origin, 'publisher-v2')
    assert changed.publication_id == identity.publication_id and changed.sha256 != identity.sha256
    late = CaptureIdentity.bind(stored.principal, replace(origin, kind='late'), 'publisher-v1')
    assert late.publication_id != identity.publication_id
    with pytest.raises(ValueError, match='capture_observation_kind'):
        CaptureIdentity.bind(stored.principal, replace(origin, kind='invented'), 'publisher-v1')


@pytest.mark.parametrize('raw,complete', [(b'\xff\x00broken{', False), (b'bad json', True), (b'', False)])
def test_failed_capture_preserves_prefix_and_empty_has_no_artifact(stored, origin, raw, complete):
    from amphora_agent_planning.context import AttemptBinding
    binding = AttemptBinding(origin.packet.context.snapshot.planning, 1)
    observed = Observation.record(binding, CapturedOutput(raw, complete), 'unknown', 'fixture_unknown', unknown_usage())
    value = CaptureOrigin.bind(origin.packet.context.snapshot, stored.principal, origin.packet.preparation, observed)
    identity = CaptureIdentity.bind(stored.principal, value, 'publisher')
    if raw:
        artifact = CaptureArtifact.bind(value)
        assert artifact.body == raw
        response = identity.response(stored.principal, value, reference(value, artifact))
    else:
        with pytest.raises(ValueError, match='capture_publication_nonempty'):
            CaptureArtifact.bind(value)
        response = identity.response(stored.principal, value)
    assert response.observation.proposal is None and response.observation.captured_bytes == len(raw)


def test_substituted_artifact_and_forged_origin_fail(stored, origin):
    artifact = CaptureArtifact.bind(origin)
    identity = CaptureIdentity.bind(stored.principal, origin, 'publisher')
    with pytest.raises(ValueError, match='capture_reference_required'):
        identity.response(stored.principal, origin)
    ref = reference(origin, artifact)
    for field, changed in [('sha256', 'f' * 64), ('size_bytes', 1), ('media_type', 'application/json')]:
        with pytest.raises(ValueError, match='capture_publication_reference'):
            identity.response(stored.principal, origin, ref.model_copy(update={field: changed}))
    corrupt = replace(origin.observation, capture=CapturedOutput(b'changed', True))
    with pytest.raises(ValueError, match='capture_digest_mismatch'):
        CaptureIdentity.bind(stored.principal, replace(origin, observation=corrupt), 'publisher')


@pytest.mark.parametrize('extra_count', [123, 124])
def test_direct_parent_limit_never_truncates_original_packet(stored, extra_count):
    worker, _, _, intake = setup(stored, extra_count=extra_count, maximum=1000000)
    result = worker.run(stored.principal, intake.planning.document().reference.engagement_id)
    assert result.stop_reason == 'abstained'
    record = worker.preparations.read(stored.principal, intake.planning.document().reference).record
    value = CaptureOrigin.bind(intake, stored.principal, record, result.latest.observation)
    if extra_count == 123:
        assert len(CaptureArtifact.bind(value).declaration.inputs) == 128
    else:
        with pytest.raises(ValueError, match='capture_derivation_input_limit'):
            CaptureArtifact.bind(value)
