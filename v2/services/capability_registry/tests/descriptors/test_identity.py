"""Independent canonical fixtures and full immutable-registration comparisons."""

import copy
import json
from dataclasses import replace

import pytest
from amphora_capability_registry.descriptors.identity import ReleaseConflict, ReleaseDocument
from amphora_contracts_tools import LockEntry, ReleaseDescriptor
from export_schemas import ROOT

CASES = json.loads((ROOT / "contracts/fixtures/v1/tool_releases.json").read_text())


def document(value):
    return ReleaseDocument.from_descriptor(ReleaseDescriptor.model_validate_json(json.dumps(value)))


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["name"])
def test_exact_canonical_bytes_digest_and_public_lock(case):
    owner = document(case["descriptor"])
    assert owner.canonical_bytes == case["canonical_utf8"].encode()
    assert owner.digest == case["sha256"]
    expected = LockEntry.model_validate_json(json.dumps(case["lock"]))
    assert owner.to_lock() == expected
    owner.verify_lock(expected)
    reordered = dict(reversed(list(case["descriptor"].items())))
    owner.require_identical_registration(document(reordered))


@pytest.mark.parametrize("fault", ["metadata", "image", "schema", "egress"])
def test_existing_semantic_release_cannot_replace_declared_bytes(fault):
    original = document(CASES[0]["descriptor"])
    value = copy.deepcopy(CASES[0]["descriptor"])
    if fault == "metadata":
        value["tool"]["purpose"] = "Changed purpose"
    elif fault == "image":
        value["tool"]["binding"]["image_sha256"] = "d" * 64
    elif fault == "schema":
        value["tool"]["outputs"][0]["schema_ref"]["sha256"] = "d" * 64
    else:
        value["egress"] = {"mode": "allowlist", "hosts": ["example.invalid"]}
    proposed = document(value)
    assert proposed.identity.semantic_key == original.identity.semantic_key
    with pytest.raises(ReleaseConflict, match="immutable_release_conflict"):
        original.require_identical_registration(proposed)
    # Deliberately forged digest simulates corrupted input; equality still checks actual bytes.
    with pytest.raises(ReleaseConflict, match="immutable_release_conflict"):
        original.require_identical_registration(replace(proposed, digest=original.digest))


def test_changed_release_key_is_not_an_idempotent_registration():
    original = document(CASES[0]["descriptor"])
    proposed = document(CASES[1]["descriptor"])
    with pytest.raises(ReleaseConflict, match="release_identity_mismatch"):
        original.require_identical_registration(proposed)


@pytest.mark.parametrize("fault", ["descriptor", "port", "checkpoint"])
def test_lock_verification_checks_all_pins(fault):
    owner = document(CASES[0]["descriptor"])
    lock = copy.deepcopy(CASES[0]["lock"])
    if fault == "descriptor":
        lock["descriptor_sha256"] = "d" * 64
    elif fault == "port":
        lock["output_schemas"][0]["schema_ref"]["sha256"] = "d" * 64
    else:
        lock["checkpoint_schema"] = lock["input_schemas"][0]["schema_ref"]
    with pytest.raises(ReleaseConflict, match="release_lock_mismatch"):
        owner.verify_lock(LockEntry.model_validate_json(json.dumps(lock)))


def test_checkpoint_schema_participates_in_lock_identity():
    value = copy.deepcopy(CASES[0]["descriptor"])
    schema = value["tool"]["inputs"][0]["schema_ref"]
    value["tool"]["checkpoint_schema"] = schema
    value["checkpoint"] = {"mode": "opaque_artifact", "readable_schema_sha256": [schema["sha256"]]}
    owner = document(value)
    assert owner.to_lock().checkpoint_schema.model_dump() == schema
    assert owner.digest != CASES[0]["sha256"]
