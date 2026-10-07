"""Fresh local executor capacity observation; not reservation or scientific eligibility."""

import time
from dataclasses import dataclass

from ..profile import require
from ..scientific_workers.engine import ContainerEngine


@dataclass(frozen=True)
class ExecutorBudget:
    slots: int

    def __post_init__(self):
        require(type(self.slots) is int and 1 <= self.slots <= 5, 'catalog_executor_count')

    def fits(self, resources):
        # These are the closed container profile ceilings, not free physical resources.
        return resources['cpus'] >= 2 * self.slots and resources['memory'] >= 1024**3 * self.slots


@dataclass(frozen=True)
class CapacityObservation:
    available: bool
    checked_at: float
    reason: str

    def fresh(self, now=None):
        age = (time.monotonic() if now is None else now) - self.checked_at
        return self.available and 0 <= age <= 5


class CapacityProbe:
    """Background-only, serialized per slot. Dependency probe must perform fresh I/O.

    Local slot state is rechecked after potentially slow image/daemon/dependency
    checks. It can change immediately afterwards; Runtime still owns claims/fences.
    Exceptions produce unavailable observations, never credential-bearing diagnostics.
    """

    def __init__(self, slot, budget, dependencies, *, engine=None):
        require(callable(dependencies), 'catalog_dependency_probe')
        self.slot, self.budget, self.dependencies = slot, budget, dependencies
        self.engine = ContainerEngine() if engine is None else engine

    def observe(self):
        started = time.monotonic()
        try:
            if not self.slot.offers_capacity():
                return self._result(False, 'slot_not_offering')
            binding = self.slot.binding
            record = binding.journal.read()
            if record is not None and record['phase'] != 'released':
                return self._result(False, 'unresolved_container_turn')
            binding.profile.verify()
            self.engine.verify_image(binding.profile)
            if not self.budget.fits(self.engine.resources()):
                return self._result(False, 'executor_budget_unavailable')
            if self.dependencies() is not True:
                return self._result(False, 'dependencies_unavailable')
            # Disk/config and local acceptance may change during dependency I/O.
            binding.profile.verify()
            if not self.slot.offers_capacity():
                return self._result(False, 'slot_not_offering')
            observed = CapacityObservation(True, started, 'verified_local_executor')
            return observed if observed.fresh() else self._result(False, 'stale_observation')
        except Exception:  # noqa: BLE001 - private Docker/credential/HTTP errors never enter status.
            return self._result(False, 'observation_unavailable')

    @staticmethod
    def _result(available, reason):
        return CapacityObservation(available, time.monotonic(), reason)
