"""Material preparation corrections do not rewrite prior samples or assert equivalence."""
from dataclasses import replace

import pytest
from amphora_research.material_state.corrections import MaterialStateCorrection
from amphora_research.material_state.preparation import PreparationHistory
from amphora_research.material_state.state import MaterialState

from .test_context import event, feature, identity


def test_material_correction_retains_original_preparation_and_future_policy():
    before = MaterialState(identity(),PreparationHistory((event(basis="proposed"),)),())
    after = replace(before,identity=replace(before.identity,reference=before.identity.reference.model_copy(update={"revision":2}),
        supersedes=before.identity.reference),preparation=PreparationHistory((event(basis="observed"),)),features=(feature(),))
    transition = MaterialStateCorrection(before,after)
    assert transition.policy == "future_campaigns_only" and transition.changed_fields == ("preparation","features")
    assert transition.before.preparation.posture == "proposed" and transition.after.preparation.posture == "observed"
    assert transition.before.features == ()
    with pytest.raises(ValueError,match="predecessor_mismatch"):
        MaterialStateCorrection(after,before)
