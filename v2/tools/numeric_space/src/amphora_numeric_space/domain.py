"""Finite numeric legality and one explicit, bounded coordinate move."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_candidate_spaces import (
    NumericDesign,
    NumericMoveRequest,
    ProposedDesignChange,
)

from .profile import OPERATOR, PROFILE, canonical


class NumericDesignError(ValueError):
    pass


@dataclass(frozen=True)
class NumericSpace:
    record: NumericDesign

    def __post_init__(self):
        record = NumericDesign.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", record)
        if record.profile != PROFILE:
            raise NumericDesignError("numeric_profile_mismatch")
        keys = [item.coordinate_id for item in record.coordinates]
        if len(set(keys)) != len(keys):
            raise NumericDesignError("numeric_duplicate_coordinate")
        for item in record.coordinates:
            if not item.unit.strip() or not item.lower <= item.value <= item.upper:
                raise NumericDesignError("numeric_coordinate_invalid")

    def apply(self, request: NumericMoveRequest) -> ProposedDesignChange:
        request = NumericMoveRequest.model_validate_json(request.model_dump_json())
        if request.source != self.record or request.operator != OPERATOR:
            raise NumericDesignError("numeric_move_binding_mismatch")
        values = self.record.model_dump(mode="json")
        target = next(
            (
                item
                for item in values["coordinates"]
                if item["coordinate_id"] == request.move.coordinate_id
            ),
            None,
        )
        if target is None:
            raise NumericDesignError("numeric_coordinate_missing")
        target["value"] = request.move.value
        result = NumericSpace(
            NumericDesign.model_validate_json(json.dumps(values, allow_nan=False))
        ).record
        return ProposedDesignChange(
            wire_version="1",
            source_sha256=hashlib.sha256(canonical(self.record)).hexdigest(),
            operator=OPERATOR,
            move=request.move,
            result=result,
        )
