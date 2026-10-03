"""Public schema oracles do not substitute for owner digest, scope or rights checks."""

import hashlib
import json
from pathlib import Path

import amphora_contracts_representations as contracts
import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

ROOT = Path(__file__).absolute().parents[1]
MODELS = {
    "generation-ref": contracts.IndexGenerationRef,
    "build-generation": contracts.BuildIndexGeneration,
    "index-manifest": contracts.IndexManifest,
    "generation": contracts.IndexGeneration,
    "generation-status": contracts.IndexGenerationStatus,
    "profile": contracts.EncodingProfile,
    "profile-ref": contracts.EncodingProfileRef,
    "encode-source": contracts.EncodeSourceRequest,
    "vector": contracts.RepresentationVector,
    "binding-ref": contracts.RepresentationBindingRef,
    "binding": contracts.RepresentationBinding,
    "encoding-status": contracts.EncodingStatus,
}


def example(name):
    return json.loads((ROOT / "examples" / (name + ".json")).read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", MODELS)
def test_examples_roundtrip_and_match_both_published_schema_modes(name):
    value = example(name)
    model = MODELS[name]
    assert json.loads(model.model_validate_json(json.dumps(value)).model_dump_json()) == value
    for mode in ("validation", "serialization"):
        schema = json.loads((ROOT.parent / "schemas/v1" / f"representations.{name}.{mode}.json").read_bytes())
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(value)


@pytest.mark.parametrize(
    "name,mutation",
    [
        ("generation-ref", lambda x: x.update(sha256="bad")),
        ("build-generation", lambda x: x.update(bindings=[])),
        ("build-generation", lambda x: x.update(bindings=x["bindings"] * 257)),
        ("build-generation", lambda x: x.update(namespace="caller-target")),
        ("build-generation", lambda x: x.update(verified=True)),
        ("build-generation", lambda x: x.update(actor_id="other")),
        ("build-generation", lambda x: x.pop("expected_head")),
        ("build-generation", lambda x: x.update(backend_profile={})),
        ("index-manifest", lambda x: x.update(watermark="bad")),
        ("index-manifest", lambda x: x.update(bindings=[])),
        ("generation", lambda x: x.update(scientifically_valid=True)),
        ("generation-status", lambda x: x.update(state="ready")),
        ("generation-status", lambda x: x.update(token="caller-authority")),
        ("profile", lambda x: x["space"].update(dimensions=True)),
        ("profile", lambda x: x["space"].update(dimensions=4097)),
        ("profile", lambda x: x["space"].update(dtype="float64")),
        ("profile", lambda x: x["space"].update(normalization="automatic")),
        ("profile", lambda x: x["space"].update(metric="similarity")),
        ("profile", lambda x: x["inputs"].update(role="auto")),
        ("profile", lambda x: x["encoder"].update(runtime=None)),
        ("profile", lambda x: x["pipeline"].pop("tokenizer")),
        ("profile", lambda x: x.update(applicability=[])),
        ("profile", lambda x: x.update(limitations=["x"] * 17)),
        ("profile-ref", lambda x: x.update(sha256="bad")),
        ("encode-source", lambda x: x.update(vector=[1, 2])),
        ("encode-source", lambda x: x.update(cache_hit=True)),
        ("encode-source", lambda x: x["source"].update(unit="character")),
        ("vector", lambda x: x.update(payload_hex="ABCD1234")),
        ("vector", lambda x: x.update(payload_hex="000000")),
        ("vector", lambda x: x.update(payload_hex="00000000" * 4097)),
        ("binding", lambda x: x.update(scientifically_valid=True)),
        ("encoding-status", lambda x: x["outcome"].update(state="accepted")),
        ("encoding-status", lambda x: x["outcome"].update(state="pending")),
        ("encoding-status", lambda x: x["outcome"].pop("binding")),
    ],
)
def test_untrusted_authority_and_invalid_shapes_rejected_in_python_and_json_schema(name, mutation):
    value = example(name)
    mutation(value)
    with pytest.raises(ValidationError):
        MODELS[name].model_validate_json(json.dumps(value))
    assert list(Draft202012Validator(MODELS[name].model_json_schema()).iter_errors(value))


def test_pending_has_no_binding_and_vector_schema_matches_published_bytes():
    value = example("encoding-status")
    value["outcome"] = {"state": "pending"}
    assert contracts.EncodingStatus.model_validate_json(json.dumps(value)).outcome.state == "pending"
    raw = (ROOT.parent / "schemas/v1/representations.vector.validation.json").read_bytes()
    assert contracts.representation_vector_schema().sha256 == hashlib.sha256(raw).hexdigest()
