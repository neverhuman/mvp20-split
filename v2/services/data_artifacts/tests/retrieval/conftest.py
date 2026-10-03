"""Actual owner source/vector fixture for generation persistence tests."""

import hashlib
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_core import SchemaRef
from amphora_contracts_evidence import SourceSpan
from amphora_contracts_representations import (
    BuildIndexGeneration,
    EncodeSourceRequest,
    representation_vector_schema,
)
from amphora_data_artifacts.acquisition.provenance import SourceDocument
from amphora_data_artifacts.publication.model import ContentPolicy
from amphora_data_artifacts.representations.bindings.content_rule import VectorContentRule
from amphora_data_artifacts.representations.bindings.workflow import BindingWorkflow
from amphora_data_artifacts.representations.fixture import fixture_profile
from amphora_data_artifacts.representations.storage.registry import ProfileRegistry
from amphora_data_artifacts.retrieval.intents import GenerationIntents
from amphora_data_artifacts.retrieval.leases import GenerationLeases


@pytest.fixture
def generation(ingestion):
    e = ingestion
    p = replace(e.principal, actions=e.principal.actions | {"upload", "finalize", "representation_manage",
        "representation_read", "representation_encode", "manage_source_rights"})
    profile = fixture_profile()
    ref = ProfileRegistry(e.env.engine).register(p, profile)
    source = e.source(b"ABBA")
    e.ledger.register(p, source, SourceDocument(source.reference, b"ABBA"))
    schema = representation_vector_schema()
    policy = e.env.uploads.policy
    e.env.uploads.policy = ContentPolicy(policy.allowed | {("application/json", schema.schema_id, schema.version, schema.sha256)}, rules=policy.rules + (VectorContentRule(),))
    encoding = EncodeSourceRequest(wire_version="1", encoding_id="encoding", profile=ref,
        source=SourceSpan(source=source.reference, unit="byte", start=0, end=4, sha256=hashlib.sha256(b"ABBA").hexdigest()))
    result = BindingWorkflow(e.reads, e.env.uploads, e.env.storage).encode(p, encoding)
    assert result.outcome.state == "published"
    binding = result.outcome.binding
    request = BuildIndexGeneration(wire_version="1", corpus_id="corpus", generation_id="g1", profile=ref,
        bindings=(binding.reference,), expected_head=None)
    backend = SchemaRef(schema_id="fixture.projection-protocol", version="1", sha256="a" * 64)
    return SimpleNamespace(p=p, engine=e.env.engine, source=source, binding=binding, request=request,
        backend=backend, profile=profile, intents=GenerationIntents(e.env.engine, backend),
        leases=GenerationLeases(e.env.engine), ingestion=e)


class TestProjectionPort:
    """Test-only stored observations, never actual Qdrant or a production fallback."""
    __test__ = False

    def __init__(self, reference):
        self.reference = reference
        self.snapshots = {}
        self.calls = []
        self.after_build = lambda: None
        self.transform = lambda snapshot: snapshot

    def build(self, namespace, snapshot):
        self.calls.append(("build", namespace))
        self.snapshots[namespace] = snapshot
        self.after_build()

    def inspect(self, namespace):
        self.calls.append(("inspect", namespace))
        return self.transform(self.snapshots[namespace])


@pytest.fixture
def projection(generation):
    from amphora_data_artifacts.retrieval.publication import GenerationPublication

    e = generation
    encoded = EncodeSourceRequest(wire_version="1", encoding_id="second", profile=e.request.profile,
        source=SourceSpan(source=e.source.reference, unit="byte", start=0, end=2, sha256=hashlib.sha256(b"AB").hexdigest()))
    binding = BindingWorkflow(e.ingestion.reads, e.ingestion.env.uploads, e.ingestion.env.storage).encode(e.p, encoded).outcome.binding
    e.request = e.request.model_copy(update={"bindings": (e.binding.reference, binding.reference)})
    e.backend_port = TestProjectionPort(e.backend)
    e.publication = GenerationPublication(e.ingestion.reads, e.backend_port)
    e.intents.prepare(e.p, e.request)
    e.lease = e.leases.claim(e.p, "corpus", "g1")
    return e
