"""Measured, inferred and unknown morphology remain distinct attributable assertions."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef, SchemaRef

from ..observations import CategoryValue, CensoredValue, MissingValue, NumericValue, SeriesValue
from .validation import identifier, require


@dataclass(frozen=True, slots=True)
class FeatureEvidence:
    basis: str
    method: SchemaRef | None
    source: ArtifactRef | None

    def __post_init__(self):
        require(self.basis in ("measured","inferred","unknown"),"invalid_feature_basis")
        require(self.method is None or type(self.method) is SchemaRef,"feature_method_type")
        require(self.source is None or type(self.source) is ArtifactRef,"feature_source_type")
        if self.basis != "unknown":
            require(self.method is not None and self.source is not None,"feature_evidence_required")


@dataclass(frozen=True, slots=True)
class MaterialFeature:
    name: str
    value: NumericValue | CategoryValue | CensoredValue | MissingValue | SeriesValue
    evidence: FeatureEvidence

    def __post_init__(self):
        identifier(self.name)
        require(type(self.value) in (NumericValue,CategoryValue,CensoredValue,MissingValue,SeriesValue),"feature_value_required")
        require(type(self.evidence) is FeatureEvidence,"feature_attribution_required")
        require((self.evidence.basis == "unknown") == (type(self.value) is MissingValue),"feature_basis_value_mismatch")
        if type(self.value) is SeriesValue:
            require(self.value.reported_count > 0,"feature_series_has_no_reported_values")
