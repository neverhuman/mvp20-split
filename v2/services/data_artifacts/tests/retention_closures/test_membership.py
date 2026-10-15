import hashlib
import json

import pytest
from amphora_contracts_core import ArtifactRef
from amphora_data_artifacts.publication.model import UploadError
from amphora_data_artifacts.retention_closures.model import ProtectedClosure


def reference(name="root", tenant="tenant"):
    return ArtifactRef(artifact_id=name, scope={"tenant_id": tenant, "project_id": "project"},
        sha256="a" * 64, size_bytes=4, media_type="application/octet-stream",
        schema_ref={"schema_id": "bytes", "version": "1", "sha256": "b" * 64})


def test_membership_digest_pins_complete_sorted_metadata():
    root, leaf = reference("root"), reference("leaf")
    closure = ProtectedClosure(root, (leaf, root))
    body = json.dumps([r.model_dump(mode="json") for r in closure.members], sort_keys=True,
                      separators=(",", ":"), ensure_ascii=False).encode()
    assert closure.digest == hashlib.sha256(b"amphora.artifact-retention/derived-closure-v1\0" + body).hexdigest()
    changed = leaf.model_copy(update={"size_bytes": 5})
    assert ProtectedClosure(root, (changed, root)).digest != closure.digest


@pytest.mark.parametrize("members", [(), (reference(), reference()), (reference("root"), reference("leaf")),
    (reference("leaf"),), (reference("leaf", "foreign"), reference("root"))])
def test_invalid_membership_is_not_a_protection_claim(members):
    with pytest.raises(UploadError):
        ProtectedClosure(reference(), members)


def test_maximum_membership_and_one_over():
    members = tuple(reference(f"item-{i:04}") for i in range(4096))
    assert len(ProtectedClosure(members[0], members).members) == 4096
    with pytest.raises(UploadError, match="retention_closure_limit"):
        ProtectedClosure(members[0], (*members, reference("overflow")))
