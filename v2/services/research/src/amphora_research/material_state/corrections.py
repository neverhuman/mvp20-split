"""Material corrections retain both exact preparations and never imply sample equivalence."""
from dataclasses import dataclass
from typing import ClassVar

from .state import MaterialState
from .validation import require


@dataclass(frozen=True, slots=True)
class MaterialStateCorrection:
    before: MaterialState
    after: MaterialState
    policy: ClassVar[str] = "future_campaigns_only"

    def __post_init__(self):
        require(type(self.before) is MaterialState and type(self.after) is MaterialState,"material_correction_records_required")
        require(self.after.identity.supersedes == self.before.identity.reference,"material_correction_predecessor_mismatch")

    @property
    def changed_fields(self):
        changed = ["candidate"] if self.before.identity.candidate != self.after.identity.candidate else []
        changed.extend(name for name in ("preparation","features") if getattr(self.before,name) != getattr(self.after,name))
        return tuple(changed)
