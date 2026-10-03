"""Read exact committed observation transitions without authoring corrections or choosing heads."""
from amphora_contracts_research import ObservationCorrectionView

from . import wire
from .corrections import ObservationCorrection
from .identity import require
from .store import ObservationStore


class ObservationCorrectionViews:
    def __init__(self, engine):
        self.store = ObservationStore(engine)

    def read(self, scope, successor):
        after = self.store.read(scope,successor)
        if after is None:
            return None
        require(after.supersedes is not None,"observation_has_no_predecessor")
        before = self.store.read(scope,after.supersedes)
        require(before is not None,"observation_correction_predecessor_missing")
        correction = ObservationCorrection(wire.from_wire(before),wire.from_wire(after))
        return ObservationCorrectionView(wire_version="1",policy=correction.policy,before=before,after=after,
            changed_fields=correction.changed_fields)
