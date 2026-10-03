"""Actual source/catalog/rights preflight; no binding publication or fake-source authority."""

import hashlib
from dataclasses import replace
from types import SimpleNamespace

import pytest
from amphora_contracts_evidence import SourceSpan
from amphora_contracts_representations import EncodeSourceRequest
from amphora_data_artifacts.acquisition.provenance import SourceDocument
from amphora_data_artifacts.representations.bindings.source import SourcePreflight
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
