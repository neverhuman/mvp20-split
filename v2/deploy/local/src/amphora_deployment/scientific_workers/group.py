"""Fixed scientific slots; adoption is explicit inside the installation writer lease."""

from ..profile import require
from .monitor import ScientificSlot
from .profiles import PROFILES


class ScientificGroup:
    def __init__(self, bindings):
        require(type(bindings) is dict and set(bindings) <= set(PROFILES), 'container_group_bindings')
        self.slots = {name: ScientificSlot(binding) for name, binding in bindings.items()}

    def adopt(self):
        for slot in self.slots.values():
            slot.adopt()

    def status(self):
        return {name: slot.status() for name, slot in self.slots.items()}

    def command(self, name, action):
        require(name in self.slots and action in {'start', 'quiesce', 'recover'}, 'container_command')
        return getattr(self.slots[name], action)()

    def quiesce(self):
        for slot in self.slots.values():
            slot.quiesce()

    def require_quiescent(self):
        for slot in self.slots.values():
            slot.require_quiescent()

    def detach(self):
        self.quiesce()
        failed = False
        for slot in self.slots.values():
            try:
                slot.detach()
            except Exception:  # noqa: BLE001 - join every owned monitor before safe aggregate error.
                failed = True
        require(not failed, 'container_monitor_cleanup_incomplete')
