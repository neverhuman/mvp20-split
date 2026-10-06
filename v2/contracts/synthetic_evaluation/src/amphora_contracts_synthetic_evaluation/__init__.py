"""Synthetic engineering result transport; no cache or scientific authority."""
from typing import Annotated, Literal

from amphora_contracts_core import Digest, Scope, WireModel
from amphora_contracts_evaluation_identity import EvaluationMethod
from pydantic import Field


class SyntheticEvaluationReceipt(WireModel):
    wire_version: Literal['1']
    authority: Literal['synthetic_evaluation']
    scope: Scope
    input_sha256: Digest
    canonical_sha256: Digest
    method: EvaluationMethod
    objective_id: Literal['synthetic-digest-score']
    unit: Literal['1']
    value: Annotated[int, Field(ge=0, le=16777215)]
