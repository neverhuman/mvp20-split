"""Compiler metadata is scoped, pinned and lazy; it grants no discovery or execution authority."""

import base64
import hashlib
from dataclasses import replace

import pytest
from amphora_campaign_runtime.api import create_app
from amphora_campaign_runtime.coordinator.advance import GraphAdvancer
from amphora_campaign_runtime.definitions.catalog import DefinitionCatalog
from amphora_campaign_runtime.definitions.reads import DefinitionReadError
from amphora_campaign_runtime.definitions.validation import ValidationUniverse
from amphora_campaign_runtime.lifecycle.access import RuntimeCredentials, RuntimePrincipal
from amphora_campaign_runtime.lifecycle.model import TransitionError
from amphora_contracts_core import SchemaRef, Scope
from fastapi.testclient import TestClient


def catalog_fixture(compiler_env, scope):
    universe = ValidationUniverse(scope, (compiler_env.tool,), tuple(compiler_env.schema_list))
    universes = {(scope.tenant_id, scope.project_id): universe}
    return DefinitionCatalog(universes), universes


def test_projection_preserves_exact_bytes_without_eager_schema_bodies(compiler_env):
    principal = RuntimePrincipal("reader", Scope(tenant_id="test", project_id="metadata"), frozenset({"read"}))
    catalog, configured = catalog_fixture(compiler_env, principal.scope)
    with pytest.raises(ValueError, match="catalog_scope_mismatch"):
        DefinitionCatalog({("wrong", "scope"): next(iter(configured.values()))})
    configured.clear()
    projected = catalog.universe(principal)
    assert projected.authority == "compiler_configuration"
    assert projected.reviewed_tools == (compiler_env.tool.lock,)
    assert len(projected.schemas) == 2 and "schema_bytes_base64" not in projected.model_dump_json()
    reference = projected.schemas[0]
    result = catalog.schema(principal, projected.universe_sha256, reference)
    body = base64.b64decode(result.schema_bytes_base64, validate=True)
    assert hashlib.sha256(body).hexdigest() == reference.sha256
    assert body == next(s.source_bytes for s in compiler_env.schema_list if s.identity.digest == reference.sha256)
    with pytest.raises(DefinitionReadError, match="universe_changed"):
        catalog.schema(principal, "0" * 64, reference)
    with pytest.raises(DefinitionReadError, match="schema_unavailable"):
        catalog.schema(principal, projected.universe_sha256, SchemaRef(schema_id="different", version="1", sha256=reference.sha256))
    with pytest.raises(DefinitionReadError, match="universe_unavailable"):
        catalog.universe(replace(principal, scope=Scope(tenant_id="foreign", project_id="foreign")))
    with pytest.raises(TransitionError, match="access_denied"):
        catalog.universe(replace(principal, actions=frozenset({"author"})))


def test_metadata_http_authentication_scope_and_universe_fencing(graph_env):
    g = graph_env
    e = g.env
    _, universes = catalog_fixture(g.source, e.principal.scope)
    credentials = RuntimeCredentials([("r" * 32, e.principal), ("f" * 32,
        replace(e.principal, scope=Scope(tenant_id="foreign", project_id="foreign")))])
    app = create_app(e.service, credentials, graphs=(g.admission, GraphAdvancer(e.engine)), authoring=True, universes=universes)
    headers = {"Authorization": "Bearer " + "r" * 32}
    with TestClient(app) as client:
        assert client.get("/v1/definition-universe").status_code == 401
        response = client.get("/v1/definition-universe", headers=headers)
        response.raise_for_status()
        universe = response.json()
        ref = universe["schemas"][0]
        query = {"schema_id": ref["schema_id"], "version": ref["version"], "universe_sha256": universe["universe_sha256"]}
        route = "/v1/definition-schemas/" + ref["sha256"]
        result = client.get(route, params=query, headers=headers)
        result.raise_for_status()
        assert hashlib.sha256(base64.b64decode(result.json()["schema_bytes_base64"])).hexdigest() == ref["sha256"]
        assert client.get(route, params={**query, "universe_sha256": "0" * 64}, headers=headers).status_code == 409
        assert client.get(route, params={**query, "schema_id": "unknown"}, headers=headers).status_code == 404
        assert client.get(route, params={**query, "url": "https://untrusted.invalid"}, headers=headers).status_code == 422
        assert client.get(route, params={**query, "version": "2"}, headers=headers).status_code == 422
        assert client.get(route, headers=headers).status_code == 422
        assert client.get("/v1/definition-universe", params={"extra": "value"}, headers=headers).status_code == 422
        foreign = {"Authorization": "Bearer " + "f" * 32}
        assert client.get("/v1/definition-universe", headers=foreign).status_code == 404
        assert client.get(route, params=query, headers=foreign).status_code == 404
