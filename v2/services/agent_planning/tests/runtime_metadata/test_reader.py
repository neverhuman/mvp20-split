import base64
import copy
import hashlib
import json
from pathlib import Path

import pytest
from amphora_agent_planning.metadata_reads import MetadataTransport, MetadataWindow
from amphora_agent_planning.runtime_metadata import (
    ReviewedUniverse,
    RuntimeMetadataReader,
    SchemaObservation,
)
from amphora_contracts_graph_runtime import DefinitionSchema, DefinitionUniverse

from ..campaign_context.test_selection import SCOPE, request
from ..metadata_reads.test_transport import server  # noqa: F401
from ..registry_access.test_discovery import Scripted


def values():
    return json.loads((Path(__file__).parent / "fixtures/universe.json").read_bytes())


def universe(raw=None):
    return DefinitionUniverse.model_validate_json(json.dumps(values()["universe"] if raw is None else raw))


def schema(index=0, raw=None):
    return DefinitionSchema.model_validate_json(json.dumps(values()["schemas"][index] if raw is None else raw))


def selected():
    return ReviewedUniverse.bind(universe(), request())


def test_installed_runtime_literal_digest_matches_without_private_import():
    chosen = selected()
    assert chosen.sha256 == "29bb4caf3131059b7bd6cf57af526ced9033b22df8cc76494dc729c7a85a23eb"
    raw = values()["universe"]
    raw["reviewed_tools"].reverse()
    raw["schemas"].reverse()
    assert ReviewedUniverse.bind(universe(raw), request()).sha256 == chosen.sha256
    assert chosen.document().authority == "compiler_configuration"


@pytest.mark.parametrize("fault,code", [("scope", "scope"), ("digest", "universe"), ("changed-lock", "universe"),
    ("expected", "universe"), ("duplicate-tool", "duplicate_tool"), ("duplicate-schema", "duplicate_schema"),
    ("duplicate-port", "duplicate_port")])
def test_universe_cannot_change_scope_pin_or_membership(fault, code):
    raw = values()["universe"]
    expected = None
    if fault == "scope":
        raw["scope"]["project_id"] = "other"
    elif fault == "digest":
        raw["universe_sha256"] = "f" * 64
    elif fault == "changed-lock":
        raw["reviewed_tools"][0]["descriptor_sha256"] = "f" * 64
    elif fault == "expected":
        expected = "f" * 64
    elif fault == "duplicate-tool":
        raw["reviewed_tools"].append(copy.deepcopy(raw["reviewed_tools"][0]))
    elif fault == "duplicate-schema":
        raw["schemas"].append(copy.deepcopy(raw["schemas"][0]))
    else:
        raw["reviewed_tools"][0]["output_schemas"] *= 2
    with pytest.raises(ValueError, match="runtime_metadata_" + code):
        ReviewedUniverse.bind(universe(raw), request(), expected)


def test_exact_original_schema_bytes_including_whitespace_and_boolean():
    chosen = selected()
    for index, expected in enumerate((b'{ "type": "number" }\n', b'true')):
        response = schema(index)
        observed = SchemaObservation.bind(chosen, response.reference, response)
        assert observed.body == expected and observed.document() == response
    assert b'{"type":"number"}' != SchemaObservation.bind(chosen, schema().reference, schema()).body


@pytest.mark.parametrize("fault,code", [("scope", "identity"), ("universe", "identity"), ("reference", "identity"),
                                        ("body", "digest"), ("unselected", "unselected")])
def test_schema_is_exactly_selected_and_content_addressed(fault, code):
    chosen, response = selected(), schema()
    reference = response.reference
    if fault == "scope":
        response = response.model_copy(update={"scope": SCOPE.model_copy(update={"project_id": "other"})})
    elif fault == "universe":
        response = response.model_copy(update={"universe_sha256": "f" * 64})
    elif fault == "reference":
        response = response.model_copy(update={"reference": schema(1).reference})
    elif fault == "body":
        response = response.model_copy(update={"schema_bytes_base64": base64.b64encode(b"false").decode()})
    else:
        reference = reference.model_copy(update={"schema_id": "unselected"})
    with pytest.raises(ValueError, match="runtime_schema_" + code):
        SchemaObservation.bind(chosen, reference, response)


@pytest.mark.parametrize("body", [b'{"type":"string","type":"number"}', b'{"x":NaN}', b'{"x":1e999}', b'[]', b'123', b'\xff'])
def test_even_digest_matching_schema_must_be_strict_json_metadata(body):
    from amphora_agent_planning.runtime_metadata.universe import canonical
    raw = values()["universe"]
    ref = {"schema_id": "bad-json", "version": "1", "sha256": hashlib.sha256(body).hexdigest()}
    raw["schemas"], raw["reviewed_tools"] = [ref], []
    raw["universe_sha256"] = hashlib.sha256(canonical({"profile": "amphora-authoring-universe-v1",
        "compiler": "amphora-deterministic-compiler-v3", "scope": raw["scope"], "tools": [], "schemas": [ref]})).hexdigest()
    chosen = ReviewedUniverse.bind(universe(raw), request())
    response = schema(raw={"scope": raw["scope"], "universe_sha256": chosen.sha256, "reference": ref,
                           "schema_bytes_base64": base64.b64encode(body).decode()})
    with pytest.raises(ValueError, match="runtime_schema_document"):
        SchemaObservation.bind(chosen, response.reference, response)


def test_universe_and_selected_schema_http_share_budget_and_exact_queries(server):  # noqa: F811
    host, _ = server
    transport = MetadataTransport("runtime", f"http://127.0.0.1:{host.server_port}", "t" * 32)
    reader, window = RuntimeMetadataReader(transport), MetadataWindow("runtime")
    host.body = universe().model_dump_json().encode()
    chosen = reader.universe(request(), window=window)
    host.body = schema().model_dump_json().encode()
    result = reader.schemas(chosen, (schema().reference,), window)
    assert result.records[0].body == b'{ "type": "number" }\n' and not result.failures
    assert window.calls == 2 and result.calls == 1
    assert host.calls[0] == ("/v1/definition-universe", "Bearer " + "t" * 32)
    assert host.calls[1][0] == "/v1/definition-schemas/" + schema().reference.sha256 + "?schema_id=fixture.schema-0&version=1&universe_sha256=" + chosen.sha256


def test_selected_schemas_survive_an_independent_missing_schema():
    chosen = selected()
    result = RuntimeMetadataReader(Scripted(ValueError("metadata_missing"), schema(1))).schemas(chosen, chosen.document().schemas)
    assert result.records[0].document() == schema(1) and result.failures[0].reference == schema().reference
    assert result.failures[0].code == "metadata_missing" and result.calls == 2


@pytest.mark.parametrize("reason", ["metadata_unavailable", "metadata_deadline", "metadata_call_limit", "metadata_byte_limit"])
def test_global_failures_stop_calls_and_mark_each_remaining_selected_schema(reason):
    chosen = selected()
    transport = Scripted(ValueError(reason))
    result = RuntimeMetadataReader(transport).schemas(chosen, chosen.document().schemas)
    assert not result.records and len(result.failures) == 2 and {f.code for f in result.failures} == {reason}
    assert len(transport.paths) == 1


@pytest.mark.parametrize("response", [schema().model_copy(update={"universe_sha256": "f" * 64}),
                                    schema().model_copy(update={"schema_version": "bad"})], ids=["wrong-pin", "invalid-wire"])
def test_invalid_response_is_explicit_and_does_not_replace_pins(response):
    chosen = selected()
    result = RuntimeMetadataReader(Scripted(response, schema(1))).schemas(chosen, chosen.document().schemas)
    assert result.failures[0].code == "runtime_schema_invalid" and len(result.records) == 1
    assert result.universe == chosen


def test_selection_and_programming_errors_reject_before_or_outside_peer_gap_handling():
    chosen = selected()
    for refs in ([schema().reference], (schema().reference,) * 2, (schema().reference.model_copy(update={"schema_id": "other"}),)):
        with pytest.raises(ValueError, match="runtime_schema_selection"):
            RuntimeMetadataReader(None).schemas(chosen, refs)
    assert RuntimeMetadataReader(None).schemas(chosen, ()).records == ()
    with pytest.raises(ValueError, match="implementation_bug"):
        RuntimeMetadataReader(Scripted(ValueError("implementation_bug"))).schemas(chosen, (schema().reference,))
    with pytest.raises(ValueError, match="metadata_window"):
        RuntimeMetadataReader(None).universe(request(), window=MetadataWindow("registry"))
    with pytest.raises(ValueError, match="metadata_window"):
        RuntimeMetadataReader(None).schemas(chosen, (), MetadataWindow("registry"))
