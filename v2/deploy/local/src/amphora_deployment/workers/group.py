"""Fixed worker slots beneath the supervisor's existing lifetime writer lease."""

from ..profile import require
from .recipes import NATIVE_RECIPES
from .turns import WorkerSlot


class WorkerGroup:
    def __init__(self, bindings):
        require(type(bindings) is dict and set(bindings) <= set(NATIVE_RECIPES), "worker_group_bindings")
        self.slots = {name: WorkerSlot(binding) for name, binding in sorted(bindings.items())}

    def status(self):
        return {name: slot.status() for name, slot in self.slots.items()}

    def command(self, name, action):
        require(name in self.slots and action in {"start", "quiesce", "recover", "force-stop"}, "worker_command")
        return getattr(self.slots[name], action.replace("-", "_"))()

    def tick(self):
        for slot in self.slots.values():
            slot.tick()

    def require_quiescent(self):
        for slot in self.slots.values():
            slot.require_quiescent()

    def quiesce(self):
        # Disable every slot before any observation that could fail.
        for slot in self.slots.values():
            with slot.lock:
                slot.enabled = False
        return self.status()

    def force_stop(self):
        # Attempt all owned handles even if one cleanup fails. No raw errors.
        failed = False
        for slot in self.slots.values():
            try:
                slot.force_stop()
            except Exception:  # noqa: BLE001 - attempt every handle, then report a safe aggregate error.
                failed = True
        require(not failed, "worker_forced_cleanup_incomplete")
