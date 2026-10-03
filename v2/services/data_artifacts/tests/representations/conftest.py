"""Owner-local actual source, catalog, rights and vector publication fixtures."""

import hashlib
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_evidence import SourceSpan
from amphora_contracts_representations import EncodeSourceRequest, representation_vector_schema
from amphora_data_artifacts.acquisition.provenance import SourceDocument
from amphora_data_artifacts.publication.model import ContentPolicy
from amphora_data_artifacts.representations.bindings.content_rule import VectorContentRule
from amphora_data_artifacts.representations.bindings.source import SourcePreflight
from amphora_data_artifacts.representations.bindings.workflow import BindingWorkflow
from amphora_data_artifacts.representations.fixture import fixture_profile
from amphora_data_artifacts.representations.storage.registry import ProfileRegistry


@pytest.fixture
def source_setup(ingestion):
    e = ingestion
    principal = replace(
        e.principal,
        actions=e.principal.actions
        | {"representation_manage", "representation_read", "representation_encode", "manage_source_rights"},
    )
    registry = ProfileRegistry(e.env.engine)
    profile = fixture_profile()
    ref = registry.register(principal, profile)
    content = b"prefix ABBA suffix"
    source = e.source(content)
    e.ledger.register(e.principal, source, SourceDocument(source.reference, content))
    span = SourceSpan(
        source=source.reference, unit="byte", start=7, end=11, sha256=hashlib.sha256(b"ABBA").hexdigest()
    )
    request = EncodeSourceRequest(wire_version="1", encoding_id="encode", profile=ref, source=span)
    return SimpleNamespace(
        e=e,
        principal=principal,
        registry=registry,
        profile=profile,
        ref=ref,
        source=source,
        request=request,
        preflight=SourcePreflight(e.reads),
    )


@pytest.fixture
def flow(source_setup):
    e = source_setup
    principal = replace(e.principal, actions=e.principal.actions | {"upload", "finalize"})
    uploads = e.e.env.uploads
    ref = representation_vector_schema()
    policy = uploads.policy
    uploads.policy = ContentPolicy(
        policy.allowed | {("application/json", ref.schema_id, ref.version, ref.sha256)},
        rules=policy.rules + (VectorContentRule(),),
    )
    workflow = BindingWorkflow(e.e.reads, uploads, e.e.env.storage)
    return SimpleNamespace(
        e=e,
        p=principal,
        workflow=workflow,
        uploads=uploads,
        engine=e.e.env.engine,
        storage=e.e.env.storage,
        request=e.request,
    )
