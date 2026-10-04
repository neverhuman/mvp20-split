"""Protect reviewed oracle/source identities and the evaluation split."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent / "corpus"
CATEGORIES = {"negation", "applicability", "correlation", "alias_collision", "contradiction",
              "retraction", "missing_context", "opinion_answer", "hostile_instructions"}


def test_reviewed_corpus_identity_split_and_oracle_completeness():
    manifest = json.loads((ROOT / "manifest.json").read_bytes())
    assert manifest["profile"] == "amphora-synthetic-extraction-corpus.v1"
    assert manifest["authority"] == "software_fixture_only"
    cases = manifest["cases"]
    assert len(cases) == 18 and len({case["case_id"] for case in cases}) == 18
    assert len({case["source_sha256"] for case in cases}) == 18
    for split in ("calibration", "held_out"):
        selected = [case for case in cases if case["split"] == split]
        assert len(selected) == 9 and {case["category"] for case in selected} == CATEGORIES
    for case in cases:
        for kind in ("source", "oracle"):
            raw = (ROOT / case[kind]).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == case[kind + "_sha256"]
            assert b"\r" not in raw
        oracle = json.loads((ROOT / case["oracle"]).read_bytes())
        assert oracle["case_id"] == case["case_id"] and oracle["category"] == case["category"]
        assert oracle["acceptance_authority"] == "none"
        for field in ("expected_meaning", "context_to_preserve", "permitted_alternatives", "hard_rejections"):
            assert oracle[field] and all(type(item) is str and item for item in oracle[field])
        # The fixture input is a source passage, never an oracle or prebuilt model response.
        source = (ROOT / case["source"]).read_text(encoding="utf-8")
        assert "expected_meaning" not in source and "hard_rejections" not in source
