"""State transport preserves attributed preparation and exact revisions."""
from dataclasses import replace

import pytest
from amphora_contracts_research import MaterialStateRevision
from amphora_research.material_state import wire
from amphora_research.material_state.preparation import PreparationHistory
from amphora_research.material_state.state import MaterialState
from amphora_research.material_state.validation import MaterialStateError

from .test_context import event, feature, identity


def test_full_preparation_and_successor_round_trip():
    original = MaterialState(identity(),PreparationHistory((event(),)),(feature(),))
    second = replace(original,identity=identity(revision=2,prior=original.identity.reference),
        preparation=PreparationHistory((replace(event(),context=replace(event().context,duration=None,atmosphere="argon"),
            attribution=replace(event().attribution,equipment=("oven",))),)))
    for value in (original,second):
        result = MaterialStateRevision.model_validate_json(wire.to_wire(value).model_dump_json())
        assert wire.from_wire(result) == value


def test_shape_valid_duplicate_processing_is_rejected_by_owner():
    value = wire.to_wire(MaterialState(identity(),PreparationHistory((event(),)),()))
    duplicate = value.model_copy(update={"preparation":value.preparation*2})
    with pytest.raises(MaterialStateError,match="duplicate_processing_event"):
        wire.from_wire(duplicate)
