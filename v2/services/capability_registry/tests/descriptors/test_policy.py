"""Selection observations retain independent structural/scientific/operational meaning."""

import copy
import json
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from amphora_capability_registry.descriptors.assessments import CapacityObservation
from amphora_capability_registry.descriptors.identity import ReleaseDocument
from amphora_capability_registry.descriptors.policy import (
    EligibilityEvaluator,
    EvaluationPolicy,
    PermissionPolicy,
)
from amphora_capability_registry.descriptors.requirements import CapabilityNeed, ResourceAllowance
from amphora_contracts_core import Scope
from amphora_contracts_tools import EligibilityDecision, ReleaseDescriptor
from export_schemas import ROOT

CASES = json.loads((ROOT / "contracts/fixtures/v1/tool_releases.json").read_text())
NOW = datetime(2026, 9, 28, 12, tzinfo=UTC)


@pytest.fixture
def case():
    raw = copy.deepcopy(CASES[0]["descriptor"])
    descriptor = ReleaseDescriptor.model_validate_json(json.dumps(raw))
    scope = Scope(tenant_id="internal", project_id="synthetic")
    need = CapabilityNeed.for_tool(scope, "synthetic-tests", descriptor.tool)
    resources = ResourceAllowance("x86_64", "windows", 2000, 128, 0, 60, 4, 64)
    policy = EvaluationPolicy(scope, resources, PermissionPolicy())

    def evaluate(raw=raw, need=need, policy=policy, capacity=None, *, unobserved=False, now=NOW):
        descriptor = ReleaseDescriptor.model_validate_json(json.dumps(raw))
        observation = capacity
        if observation is None and not unobserved:
            observation = CapacityObservation(scope, ReleaseDocument.from_descriptor(descriptor).digest,
                                              1, 1, NOW - timedelta(seconds=1), NOW + timedelta(seconds=30))
        return EligibilityEvaluator().evaluate(descriptor, need, policy, observation, now=now).to_wire()
    return SimpleNamespace(raw=raw, descriptor=descriptor, scope=scope, need=need, policy=policy, evaluate=evaluate)


def test_synthetic_candidate_roundtrip_and_policy_fingerprint(case):
    result = case.evaluate()
    assert result.status == "candidate"
    assert result.observations.scientific.reason_codes == ("synthetic_fixture_only",)
    assert result.admission.status == "allowed"
    assert EligibilityDecision.model_validate_json(result.model_dump_json()) == result
    changed = replace(case.policy, resources=replace(case.policy.resources, memory_mib=256))
    assert changed.digest != case.policy.digest
    assert replace(case.policy, permissions=PermissionPolicy(("a.invalid", "b.invalid"))).digest == replace(
        case.policy, permissions=PermissionPolicy(("b.invalid", "a.invalid"))).digest


@pytest.mark.parametrize("fault", ["real_context", "missing_context", "unreviewed_method"])
def test_healthy_replica_cannot_make_scientifically_ineligible_release_eligible(case, fault):
    need = case.need
    if fault == "real_context":
        need = replace(need, context="biological-research")
    elif fault == "missing_context":
        case.raw["tool"]["applicability"] = ["other-fixture"]
    else:
        case.raw["authority_ceiling"] = "evidence_proposal"
    result = case.evaluate(need=need)
    assert result.status == "rejected"
    assert result.observations.structural.status == "valid"
    assert result.observations.scientific.status in {"ineligible", "unreviewed"}
    assert result.observations.capacity.status == "available"
    assert result.admission.status == "allowed"


@pytest.mark.parametrize("fault,reason", [("effect", "effect_class_unsupported"), ("egress", "egress_forbidden"),
    ("memory", "resource_limit_memory_mib"), ("representation", "representation_incompatible"),
    ("unit", "unit_incompatible"), ("schema", "schema_incompatible")])
def test_compatibility_and_permissions_do_not_relabel_science_or_health(case, fault, reason):
    if fault == "effect":
        case.raw["tool"]["side_effects"] = "external"
    elif fault == "egress":
        case.raw["egress"] = {"mode": "allowlist", "hosts": ["unapproved.invalid"]}
    elif fault == "memory":
        case.raw["resources"]["memory_mib"] = 256
    elif fault == "schema":
        case.raw["tool"]["inputs"][0]["schema_ref"]["sha256"] = "e" * 64
    else:
        case.raw["tool"]["inputs"][0][fault] = "different"
    result = case.evaluate()
    assert result.status == "rejected" and reason in result.admission.reason_codes
    assert result.observations.scientific.status == "eligible" and result.observations.capacity.status == "available"


def test_explicit_egress_policy_is_a_separate_pinned_choice(case):
    case.raw["egress"] = {"mode": "allowlist", "hosts": ["approved.invalid"]}
    assert case.evaluate().admission.status == "denied"
    permitted = replace(case.policy, permissions=PermissionPolicy(("approved.invalid",)))
    assert case.evaluate(policy=permitted).status == "candidate"
    assert permitted.digest != case.policy.digest


@pytest.mark.parametrize("fault", ["duplicate_port", "unit_whitespace", "checkpoint", "empty_output"])
def test_structural_conflicts_prevent_selection_without_hiding_observed_capacity(case, fault):
    if fault == "duplicate_port":
        case.raw["tool"]["inputs"].append(copy.deepcopy(case.raw["tool"]["inputs"][0]))
    elif fault == "unit_whitespace":
        case.raw["tool"]["inputs"][0]["unit"] = " "
    elif fault == "checkpoint":
        case.raw["checkpoint"] = {"mode": "opaque_artifact", "readable_schema_sha256": ["a" * 64]}
    else:
        case.raw["tool"]["outputs"] = []
    result = case.evaluate()
    assert result.status == "rejected" and result.observations.structural.status == "invalid"
    assert result.observations.scientific.status == "unreviewed" and result.observations.capacity.status == "available"
    assert "descriptor_invalid" in result.admission.reason_codes


@pytest.mark.parametrize("fault", ["expired", "future", "scope", "release", "inconsistent", "unobserved", "busy", "unhealthy"])
def test_capacity_uncertainty_or_exhaustion_never_infers_suitability(case, fault):
    if fault == "unobserved":
        result = case.evaluate(unobserved=True)
    else:
        values = {"scope": case.scope, "descriptor_sha256": ReleaseDocument.from_descriptor(case.descriptor).digest,
                  "healthy_replicas": 1, "free_slots": 1, "sampled_at": NOW - timedelta(seconds=1), "expires_at": NOW + timedelta(seconds=30)}
        if fault == "expired":
            values["expires_at"] = NOW
        elif fault == "future":
            values["sampled_at"] = NOW + timedelta(seconds=1)
        elif fault == "scope":
            values["scope"] = Scope(tenant_id="other", project_id="other")
        elif fault == "release":
            values["descriptor_sha256"] = "e" * 64
        elif fault == "inconsistent":
            values["free_slots"] = 3
        elif fault == "busy":
            values["free_slots"] = 0
        else:
            values.update(healthy_replicas=0, free_slots=0)
        result = case.evaluate(capacity=CapacityObservation(**values))
    assert result.status == "rejected" and result.observations.capacity.status in {"unknown", "unavailable"}
    assert result.observations.scientific.status == "eligible" and result.admission.status == "allowed"


def test_wrong_policy_scope_and_naive_clock_fail_before_observation(case):
    with pytest.raises(ValueError, match="policy_scope_mismatch"):
        case.evaluate(policy=replace(case.policy, scope=Scope(tenant_id="other", project_id="other")))
    with pytest.raises(ValueError, match="timezone-aware"):
        case.evaluate(now=NOW.replace(tzinfo=None))


@pytest.mark.parametrize("fault", ["bool", "negative", "no_replica", "unbounded", "digest"])
def test_capacity_constructor_rejects_impossible_observations(case, fault):
    values = {"scope": case.scope, "descriptor_sha256": "a" * 64, "healthy_replicas": 1, "free_slots": 1,
              "sampled_at": NOW, "expires_at": NOW + timedelta(seconds=30)}
    if fault == "bool":
        values["free_slots"] = True
    elif fault == "negative":
        values["free_slots"] = -1
    elif fault == "no_replica":
        values["healthy_replicas"] = 0
    elif fault == "unbounded":
        values["expires_at"] = NOW + timedelta(hours=1)
    else:
        values["descriptor_sha256"] = "latest"
    with pytest.raises(ValueError):
        CapacityObservation(**values)
