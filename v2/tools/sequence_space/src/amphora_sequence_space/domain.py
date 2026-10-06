"""DNA fixture legality is separate from polymer or numeric operations."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_candidate_spaces import (
    ProposedDesignChange,
    SequenceDesign,
    SequenceMoveRequest,
)

from .profile import OPERATOR, PROFILE, canonical


class SequenceDesignError(ValueError):
    pass


@dataclass(frozen=True)
class SequenceSpace:
    record: SequenceDesign

    def __post_init__(self):
        record = SequenceDesign.model_validate_json(self.record.model_dump_json())
        object.__setattr__(self, "record", record)
        if record.profile != PROFILE:
            raise SequenceDesignError("sequence_profile_mismatch")

    def apply(self, request: SequenceMoveRequest) -> ProposedDesignChange:
        request = SequenceMoveRequest.model_validate_json(request.model_dump_json())
        if request.source != self.record or request.operator != OPERATOR:
            raise SequenceDesignError("sequence_move_binding_mismatch")
        position = request.move.position
        if position >= len(self.record.sequence):
            raise SequenceDesignError("sequence_position_outside_source")
        sequence = (
            self.record.sequence[:position]
            + request.move.base
            + self.record.sequence[position + 1 :]
        )
        result = SequenceSpace(
            self.record.model_copy(update={"sequence": sequence})
        ).record
        return ProposedDesignChange(
            wire_version="1",
            source_sha256=hashlib.sha256(canonical(self.record)).hexdigest(),
            operator=OPERATOR,
            move=request.move,
            result=result,
        )
