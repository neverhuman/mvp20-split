"""Reconstruct semantic policies and verify every declared content reference."""
from dataclasses import dataclass

from amphora_contracts_core import Scope
from amphora_contracts_research import (
    AssessObservationUseRequest,
    ConversionCatalogRecord,
    ConversionRuleRecord,
    InterpretationProfileRef,
    NormalizationProfile,
    NormalizeObservationRequest,
    ObservationUsePolicyRecord,
    ObservationUseProfile,
    ObservationUseRequirements,
)

from ..identity import require
from ..normalization.catalog import ConversionCatalog, ConversionRule
from ..quality.policy import ObservationUsePolicy, UseRequirements
from ..quantities import DecimalValue


def rule_to_wire(rule):
    return ConversionRuleRecord(**rule.descriptor())


def catalog_to_wire(catalog):
    return ConversionCatalogRecord(profile_id=catalog.profile_id,version=catalog.version,
        reference=catalog.reference,rules=tuple(rule_to_wire(rule) for rule in catalog.rules))


def catalog_from_wire(record):
    value = ConversionCatalog(record.profile_id,record.version,tuple(
        ConversionRule(rule.dimension,rule.source_unit,rule.target_unit,DecimalValue(rule.scale)) for rule in record.rules))
    require(value.reference == record.reference,"normalization_catalog_reference_mismatch")
    return value


def policy_to_wire(policy):
    return ObservationUsePolicyRecord(profile_id=policy.profile_id,version=policy.version,reference=policy.reference,
        action=policy.action,requirements=ObservationUseRequirements(**(policy.requirements.descriptor() | {"excluded_flags":policy.requirements.excluded_flags})),
        normalization=None if policy.normalization is None else catalog_to_wire(policy.normalization))


def policy_from_wire(record):
    requirements = record.requirements
    value = ObservationUsePolicy(record.profile_id,record.version,record.action,
        UseRequirements(requirements.available_value,requirements.passed_controls,requirements.bound_state,requirements.excluded_flags),
        None if record.normalization is None else catalog_from_wire(record.normalization))
    require(value.reference == record.reference,"observation_use_policy_reference_mismatch")
    return value


@dataclass(frozen=True, slots=True)
class InterpretationProfile:
    scope: Scope
    policy: ConversionCatalog | ObservationUsePolicy

    def __post_init__(self):
        require(type(self.scope) is Scope,"interpretation_scope_required")
        require(type(self.policy) in (ConversionCatalog,ObservationUsePolicy),"interpretation_policy_required")

    @property
    def kind(self):
        return "normalization" if type(self.policy) is ConversionCatalog else "observation-use"

    @property
    def reference(self):
        return InterpretationProfileRef(scope=self.scope,kind=self.kind,policy=self.policy.reference)

    def to_wire(self):
        if self.kind == "normalization":
            return NormalizationProfile(wire_version="1",kind=self.kind,scope=self.scope,catalog=catalog_to_wire(self.policy))
        return ObservationUseProfile(wire_version="1",kind=self.kind,scope=self.scope,policy=policy_to_wire(self.policy))

    @classmethod
    def from_wire(cls, record):
        if type(record) is NormalizationProfile:
            return cls(record.scope,catalog_from_wire(record.catalog))
        require(type(record) is ObservationUseProfile,"interpretation_profile_required")
        return cls(record.scope,policy_from_wire(record.policy))

    def bind(self, request):
        expected = NormalizeObservationRequest if self.kind == "normalization" else AssessObservationUseRequest
        require(type(request) is expected,"interpretation_request_kind_mismatch")
        # Revalidate objects even when a caller used Pydantic's unchecked model_copy.
        request = expected.model_validate_json(request.model_dump_json())
        require(request.profile == self.reference,"interpretation_profile_mismatch")
        if self.kind == "normalization":
            require(request.observation.scope == self.scope,"interpretation_input_scope_mismatch")
        else:
            require(request.experiment.scope == self.scope and all(item.scope == self.scope for item in request.observations),
                "interpretation_input_scope_mismatch")
            require(len({item.observation_id for item in request.observations}) == len(request.observations),
                "duplicate_observation_use_identity")
        return request
