"""Public documents retain optional weaknesses without converting them to hard gates."""
from dataclasses import replace

import pytest
from amphora_contracts_research import EligibilityAssessment, EligibilityClaim, EligibilityProfile
from amphora_research.eligibility import wire
from amphora_research.eligibility.evidence import EligibilityError

from .test_policy import claim, policy


def test_context_flags_and_focus_survive_public_json():
    configured = wire.profile_from_wire(EligibilityProfile.model_validate_json(wire.profile_to_wire(policy()).model_dump_json()))
    assert configured == policy()
    claims = (claim(),replace(claim("accuracy","unknown",source="weak"),flags=("questionable",)),claim("model-context",kind="model"))
    decoded = tuple(wire.claim_from_wire(EligibilityClaim.model_validate_json(wire.claim_to_wire(item).model_dump_json())) for item in claims)
    assert decoded == claims
    result = wire.assess_to_wire(configured,decoded)
    assert result.disposition == "eligible" and result.focus == ("accuracy",)
    assert result.reviews[1].claim.flags == ("questionable",)
    assert result.reviews[2].reasons == ("undeclared_criterion",)
    assert EligibilityAssessment.model_validate_json(result.model_dump_json()) == result


def test_shape_valid_duplicate_requirement_does_not_create_extra_votes():
    profile = wire.profile_to_wire(policy())
    with pytest.raises(EligibilityError,match="duplicate_eligibility_requirement"):
        wire.profile_from_wire(profile.model_copy(update={"requirements":profile.requirements*2}))
