"""Expected campaign answers must satisfy the real action policy before paid runs."""

import json

import pytest
from amphora_agent_planning.providers.profiles import OutputProfiles
from openai_evaluation_bundle import ROOT, load_bundle


@pytest.mark.parametrize("case_id,posture", [("missing-tool", "missing"), ("contradiction", "contradictory")])
def test_campaign_oracle_is_feasible_only_with_supplied_typed_evidence_intent(case_id, posture):
    root = ROOT.with_name("openai-engineering-v4")
    _, _, batch, _ = load_bundle(None, root)
    task = next(t for t in batch.tasks if t.case_id == case_id)
    request = task.request.document()
    bodies = json.loads((root / "bodies.json").read_bytes())
    question = json.loads(bodies[request.context.objective.sha256])["question"]
    draft = {
        "schema_version": "1", "authority": "proposal_only", "scientific_authority": "not_established",
        "action": "request_evidence", "rationale": "Additional evidence is needed.",
        "decision_scope": request.decision_scope, "candidate": None, "alternatives": [],
        "evidence_requests": [],
        "unresolved": [{"question": None, "need": None, "posture": posture, "description": "Unresolved evidence."}],
    }
    # This was the v3 prompt's impossible expected shape. Keep the rejection policy.
    with pytest.raises(ValueError, match="campaign_evidence_payload"):
        OutputProfiles.parse(json.dumps(draft).encode(), task.binding)
    draft["evidence_requests"] = [{"question": question, "needs": [], "assessments": [], "producer": None,
                                   "expected_evidence": "A supported measurement or available capability.",
                                   "uncertainty": "The supplied evidence cannot establish the next step."}]
    draft["unresolved"][0]["question"] = question
    proposal = OutputProfiles.parse(json.dumps(draft).encode(), task.binding)
    parsed = json.loads(proposal.payload_json)
    assert parsed["action"] == "request_evidence" and parsed["candidate"] is None
    assert parsed["unresolved"][0]["posture"] == posture
    assert parsed["evidence_requests"][0]["question"] == question
    # The independently frozen rubric is not weakened to accept the earlier failure.
    draft["evidence_requests"][0]["question"]["scope"]["project_id"] = "foreign"
    with pytest.raises(ValueError, match="campaign_output_scope"):
        OutputProfiles.parse(json.dumps(draft).encode(), task.binding)


def test_followup_fits_revised_cumulative_cap_without_refunding_history():
    from run_openai_evaluation import GROUP_CEILING
    bundles = [load_bundle(None, ROOT.with_name("openai-engineering-" + v)) for v in ("v1", "v2", "v3", "v4")]
    assert sum(b[2].accounting_units for b in bundles) == 1253376000
    assert bundles[3][2].accounting_units == 258048000

    assert 1253376000 <= GROUP_CEILING == 1700000000
