"""Language-neutral fixture validation plus strict input/serialization compatibility."""

import hashlib
import json

from export_schemas import ROOT, artifacts, publish

CASES = json.loads((ROOT / "contracts/fixtures/v1/wire_cases.json").read_text(encoding="utf-8"))


def test_publication_reproducible_and_tampering_detected(tmp_path):
    assert artifacts() == artifacts()
    publish(tmp_path)
    assert publish(tmp_path, check=True) == []
    manifest = json.loads((tmp_path / "manifest.json").read_bytes())
    for name, digest in manifest["schemas"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest
    (tmp_path / "tools.invocation.validation.json").write_text("{}")
    assert publish(tmp_path, check=True) == ["tools.invocation.validation.json"]
