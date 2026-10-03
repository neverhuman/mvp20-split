"""Public synthesis documents retain bounded failures, alternatives and exact context."""
from dataclasses import replace

import pytest
from amphora_contracts_research import (
    RouteEvidenceRecord,
    RouteOptionRecord,
    SynthesisAssessment,
    SynthesisProfile,
)
from amphora_research.synthesis import wire
from amphora_research.synthesis.evidence import RouteEvidence, RouteProvenance, SearchRecord
from amphora_research.synthesis.validation import SynthesisError

from ..material_state.test_context import METHOD, artifact, q
from .test_policy import context, option, policy, route


def test_profiles_options_and_decisions_keep_alternatives_and_blockers():
    profile = wire.profile_to_wire(policy())
    restored = wire.profile_from_wire(SynthesisProfile.model_validate_json(profile.model_dump_json()))
    assert restored == policy()
    choices = (option("blocked","failed"),option("usable"))
    mapped = tuple(wire.option_from_wire(RouteOptionRecord.model_validate_json(wire.option_to_wire(item).model_dump_json())) for item in choices)
    assert mapped == choices
    result = wire.assess_to_wire(restored,mapped)
    assert [d.disposition for d in result.alternatives] == ["blocked","eligible"]
    assert result.alternatives[0].blockers == ("equipment",)
    assert SynthesisAssessment.model_validate_json(result.model_dump_json()) == result


def test_bounded_failed_search_and_unknown_scale_survive_json():
    value = RouteEvidence(replace(context(),scale=None,purity=None),None,"no_route_found",RouteProvenance(METHOD,METHOD,(),(artifact("search"),)),
                          (),SearchRecord(artifact("scope"),q("10","attempts")),("try_alternative",))
    restored = wire.evidence_from_wire(RouteEvidenceRecord.model_validate_json(wire.evidence_to_wire(value).model_dump_json()))
    assert restored == value and restored.context.scale is None


def test_shape_valid_forward_dependency_fails_domain_reconstruction():
    record = wire.evidence_to_wire(route())
    invalid = record.model_copy(update={"steps":(record.steps[0].model_copy(update={"requires":("future",)}),)})
    with pytest.raises(SynthesisError,match="route_step_dependency_unresolved"):
        wire.evidence_from_wire(invalid)
