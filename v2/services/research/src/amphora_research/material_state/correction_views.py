"""Read exact material-state transitions; no nominal-design equivalence or current selection."""
from amphora_contracts_research import MaterialStateCorrectionView

from . import wire
from .corrections import MaterialStateCorrection
from .store import MaterialStateStore
from .validation import require


class MaterialStateCorrectionViews:
    def __init__(self, engine):
        self.store = MaterialStateStore(engine)

    def read(self, scope, successor):
        after = self.store.read(scope,successor)
        if after is None:
            return None
        require(after.supersedes is not None,"material_state_has_no_predecessor")
        before = self.store.read(scope,after.supersedes)
        require(before is not None,"material_correction_predecessor_missing")
        correction = MaterialStateCorrection(wire.from_wire(before),wire.from_wire(after))
        return MaterialStateCorrectionView(wire_version="1",policy=correction.policy,before=before,after=after,
            changed_fields=correction.changed_fields)
