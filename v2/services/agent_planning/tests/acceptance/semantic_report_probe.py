"""Write the complete reviewed fixture report under an isolated Planning install."""

import importlib.util
import json
import os
from pathlib import Path

from ..extraction.semantic_boundary import inspect
from ..extraction.semantic_review import ReviewedResponse, digest, report
from ..extraction.test_semantic_review import CASES, RECORDS, ROOT


def test_installed_semantic_report():
    assert all(importlib.util.find_spec(name) is None for name in
        ("amphora_data_artifacts", "amphora_research", "amphora_knowledge", "amphora_campaign_runtime"))
    responses = tuple(ReviewedResponse.bind(CASES[row["case_id"]], row) for row in RECORDS)
    result = {"pid": os.getpid(), "fixture_sha256": digest((ROOT / "semantic_fixtures/responses.json").read_bytes()),
        "corpus_sha256": digest((ROOT / "corpus/manifest.json").read_bytes()),
        "combined": report(tuple(CASES.values()), responses), "variants": {}, "boundaries": {}}
    for variant in ("faithful", "incorrect", "abstained"):
        selected = tuple(row for row in responses if row.response_id.endswith("-" + variant))
        result["variants"][variant] = report(tuple(CASES.values()), selected)
    for row in responses:
        boundary = inspect(row)
        result["boundaries"][row.response_id] = {"status": boundary["status"], "quotation": boundary["quotation"],
            "quotation_count": boundary["quotation_count"],
            "trace_authority": boundary["trace"]["authority"], "trace_validation": boundary["trace"]["validation"]}
    result["limits"] = ["Explicit coding-agent synthetic semantic review, not automatic entailment or domain-expert labels",
        "Generic fixture entity/predicate scaffolding; no domain-vocabulary, identity-resolution or accepted graph benchmark",
        "No Data/Knowledge/Research peer calls or acceptance; no scientific or live model quality claim",
        "All54 responses retained, including18 deliberately incorrect and18 abstentions"]
    Path(os.environ["AMPHORA_SEMANTIC_REPORT"]).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
