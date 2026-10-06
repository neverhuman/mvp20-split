"""Workspace-only source audit; installed algorithm tests run without this audit."""

import hashlib
import json
from pathlib import Path

from amphora_evolution_search import CandidateScore, ObjectiveSpace

REPOSITORY = Path(__file__).absolute().parents[5]


def test_reviewed_frozen_sources_have_not_changed():
    path = REPOSITORY / "v2/docs/Build Plans/BP-08/BP-08.01 Reuse disposition.json"
    disposition = json.loads(path.read_bytes())
    assert len(disposition["sources"]) == 7
    for name, expected in disposition["sources"].items():
        assert name.startswith("v1/") and ".." not in Path(name).parts
        assert hashlib.sha256((REPOSITORY / name).read_bytes()).hexdigest() == expected


def test_reuse_lab_01_executable_selection_is_not_a_placeholder():
    # Observable mathematical behavior, no inference from a README's readiness claim.
    result = ObjectiveSpace(("minimize",)).select((CandidateScore("costly", (4.0,), 0.0),
                                                 CandidateScore("better", (2.0,), 0.0)), 1)
    assert result.selected == ("better",)
    assert {r.candidate_id: r.front for r in result.ranks} == {"better": 0, "costly": 1}


def test_reuse_lab_02_fixture_retains_synthetic_applicability():
    path = Path(__file__).parents[1] / "specification/synthetic_specification.json"
    fixture = json.loads(path.read_bytes())
    assert fixture["scope"]["tenant_id"] == "search-fixture"
    assert fixture["evaluator"]["tool"]["capability_id"] == "synthetic-objectives"
    assert fixture["implementations"][0]["name"] == "numeric-kernel-fixture"
    disposition = json.loads((REPOSITORY / "v2/docs/Build Plans/BP-08/BP-08.01 Reuse disposition.json").read_bytes())
    assert disposition["copied_sources"] == []
    assert disposition["scientific_claims"] == []
