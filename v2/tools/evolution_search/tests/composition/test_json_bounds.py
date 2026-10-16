"""Schema-derived byte maxima must fail closed on unbounded shapes."""
import json
import pytest
from amphora_contracts_population import GenerationIdentity
from amphora_evolution_search.composition.json_bounds import bounded_json_bytes


def test_public_generation_header_has_finite_bound_without_dummy_references():
    assert 1000<bounded_json_bytes(GenerationIdentity.model_json_schema())<10000


def test_quotes_controls_and_unicode_fit_string_bound():
    schema={"type":"string","maxLength":8}
    for value in ('"'*8,'\\'*8,'\x00'*8,'😀'*8):
        assert len(json.dumps(value,ensure_ascii=False).encode())<=bounded_json_bytes(schema)


def test_closed_object_arrays_and_optional_union():
    schema={"type":"object","additionalProperties":False,"properties":{
        "values":{"type":"array","maxItems":3,"items":{"type":"integer","minimum":-100,"maximum":9}},
        "optional":{"anyOf":[{"type":"null"},{"const":"fixed"}]}}}
    assert bounded_json_bytes(schema)==len(b'{"optional":"fixed","values":[-100,-100,-100]}')


@pytest.mark.parametrize("schema",[{"type":"number"},{"type":"integer"},
    {"type":"string"},{"type":"array","items":{"const":1}},
    {"type":"object","properties":{}},{"$ref":"https://external/schema"},
    {"allOf":[{"const":1}]}])
def test_unsupported_or_unbounded_shape_rejects(schema):
    with pytest.raises(ValueError):bounded_json_bytes(schema)


def test_recursive_local_reference_rejects():
    with pytest.raises(ValueError,match="reference"):
        bounded_json_bytes({"$ref":"#/$defs/Loop","$defs":{"Loop":{"$ref":"#/$defs/Loop"}}})
