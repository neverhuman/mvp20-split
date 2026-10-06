import json

import pytest
from amphora_agent_planning.openai_provider.format import response_format
from amphora_agent_planning.openai_provider.http import OpenAIHTTP
from amphora_contracts_planning import (
    ExtractionDraft,
    campaign_draft_schema,
    extraction_draft_schema,
)
from jsonschema import Draft202012Validator, ValidationError
from openai_evaluation_bundle import ROOT, load_bundle


def test_strict_schema_preserves_fields_and_requires_explicit_default_values():
    schema = response_format(extraction_draft_schema())
    assert schema["strict"] and schema["type"] == "json_schema"
    original = ExtractionDraft.model_json_schema()
    projected = schema["schema"]
    Draft202012Validator.check_schema(projected)
    assert set(projected["properties"]) == set(original["properties"])
    for name, definition in projected["$defs"].items():
        if definition.get("type") == "object":
            assert set(definition["properties"]) == set(original["$defs"][name]["properties"])
            assert set(definition["required"]) == set(definition["properties"])
            assert definition["additionalProperties"] is False
    quote = projected["$defs"]["SourceQuotation"]
    assert set(quote["required"]) == {"span", "text"}
    # The exact extra wrapper seen in the live failure is rejected structurally.
    with pytest.raises(ValidationError):
        Draft202012Validator(quote).validate({"citation": {"span": {}, "text": "Synthetic."}})
    assert response_format(campaign_draft_schema()) == {"type": "json_object"}


def test_frozen_strict_packets_fit_cap_and_preserve_predecessors():
    bundles = [load_bundle(None, ROOT.with_name("openai-engineering-" + v)) for v in ("v1", "v2", "v3", "v4", "v5")]
    assert sum(b[2].accounting_units for b in bundles) == 1658880000
    _, protocol, batch, provider = bundles[-1]
    assert protocol.manifest.adapter_revision == "openai-responses-synthetic-v3"
    for task in batch.tasks:
        body = json.loads(provider.prepared[task.request.sha256].body)
        assert len(provider.prepared[task.request.sha256].body) + 1024 <= 32768
        expected = "json_schema" if task.request.document().purpose == "knowledge_decomposition" else "json_object"
        assert body["text"]["format"]["type"] == expected
    assert all(json.loads(p.body)["text"]["format"] == {"type": "json_object"}
               for p in bundles[-2][3].prepared.values())


def test_transport_limit_is_explicit_and_remains_bounded():
    with pytest.raises(ValueError, match="openai_http_body"):
        OpenAIHTTP("fixture").send(b"x" * 16385)
    with pytest.raises(ValueError, match="openai_http_limit"):
        OpenAIHTTP("fixture", maximum_body_bytes=999999)
    with pytest.raises(ValueError, match="openai_http_body"):
        OpenAIHTTP("fixture", maximum_body_bytes=32768).send(b"x" * 32769)
