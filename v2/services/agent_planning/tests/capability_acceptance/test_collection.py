import pytest

from amphora_agent_planning.capability_acceptance.collection import AcceptanceCollector
from ..registry_access.test_discovery import Scripted
from .test_review import case, evidence


@pytest.mark.parametrize('fault', ['untyped', 'ambiguous', 'oversized', 'foreign_scope'])
def test_unusable_evidence_never_starts_peer_reads(fault):
    capability, release, report = case()
    specification, _ = evidence(capability, release, report)
    reference = specification.acceptance_evidence[0]
    if fault == 'untyped': reference = reference.model_copy(update={'schema_ref': reference.schema_ref.model_copy(update={'sha256': 'f' * 64})})
    if fault == 'oversized': reference = reference.model_copy(update={'size_bytes': 65537})
    if fault == 'foreign_scope': reference = reference.model_copy(update={'scope': reference.scope.model_copy(update={'project_id': 'foreign'})})
    refs = (reference, reference.model_copy(update={'artifact_id': 'second'})) if fault == 'ambiguous' else (reference,)
    specification = specification.model_copy(update={'acceptance_evidence': refs})
    registry = Scripted()
    with pytest.raises(ValueError): AcceptanceCollector(registry, None).collect(capability, specification)
    assert registry.paths == []


@pytest.mark.parametrize('fault', ['lock', 'retired', 'processing_denied', 'metadata', 'content', 'deadline'])
def test_unavailable_or_changed_peer_evidence_never_returns_acceptance(fault):
    capability, release, report = case()
    specification, retained = evidence(capability, release, report)
    if fault == 'lock': release = release.model_copy(update={'lock': release.lock.model_copy(update={'descriptor_sha256': 'f' * 64})})
    if fault == 'retired': release = release.model_copy(update={'status': 'retired'})
    class Data:
        calls = []
        def artifact(self, ref, budget):
            budget.start(); self.calls.append('metadata')
            return ref.model_copy(update={'sha256': 'f' * 64}) if fault == 'metadata' else ref
        def content(self, ref, budget):
            budget.start(); self.calls.append('processing')
            if fault == 'processing_denied': raise ValueError('source_access_denied')
            if fault == 'deadline': budget.deadline = 0
            return b'wrong bytes' if fault == 'content' else retained[0].body
    data = Data()
    with pytest.raises(ValueError): AcceptanceCollector(Scripted(release), data).collect(capability, specification)
    if fault in {'lock', 'retired'}: assert data.calls == []
    elif fault == 'metadata': assert data.calls == ['metadata']
    else: assert data.calls == ['metadata', 'processing']
