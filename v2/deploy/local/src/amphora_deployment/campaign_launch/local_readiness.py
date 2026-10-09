"""Installation preflight outside supervisor locks; no campaign or container creation."""
from ..profile import ProfileError
from ..scientific_workers.engine import ContainerEngine
from ..scientific_workers.ownership import require_released
from ..tool_catalog.availability import ExecutorBudget
from ..tool_catalog.dependencies import ToolDependencies
from .intent import LaunchError
from .ports import PeerUnavailable
from .capacity import AdmissionCapacity


class LocalLaunchReadiness:
    def __init__(self, installation, supervisor, stopped, *, engine=None):
        self.installation, self.supervisor, self.stopped = installation, supervisor, stopped
        self.engine = ContainerEngine() if engine is None else engine
        self.capacity = AdmissionCapacity(supervisor)

    def _available(self):
        if self.stopped.is_set():
            raise PeerUnavailable()

    def __call__(self, intent, tools):
        self._available()
        self.installation.pin_intent(intent)
        try:
            with self.supervisor.lock:
                if self.supervisor.closed or any(owner not in self.supervisor.processes
                    or self.supervisor.processes[owner].status()['state'] != 'running'
                    for owner in self.supervisor.bindings):
                    raise PeerUnavailable()
                self.supervisor.access.require_running()
                self.supervisor.workers.require_quiescent()
                self.capacity.require_idle()
            require_released(self.installation.root, self.installation.deployment_id)
            for slot in self.supervisor.workers.slots.values():
                self._available()
                slot.binding.recover()  # Verify installation/config pins, not a start.
                selected = slot.binding.scope
                if selected is not None and (selected.tenant != intent.request.identity.scope.tenant_id
                        or selected.project != intent.request.identity.scope.project_id):
                    raise LaunchError('launch_native_scope_mismatch')
            self._available()
            if not ExecutorBudget(len(self.installation.templates)).fits(self.engine.resources()):
                raise PeerUnavailable()
            access = self.supervisor.access.bindings
            for binding in self.installation.templates.values():
                self._available()
                binding.profile.verify()
                self.engine.verify_image(binding.profile)
                self._available()
                dependencies = ToolDependencies(binding.profile.certificate,
                    access['runtime'].port, access['artifact'].port,
                    access['runtime'].route.upstream_port, access['artifact'].route.upstream_port)
                if dependencies() is not True:
                    raise PeerUnavailable()
            self._available()
            self.capacity.offer()
        except ProfileError:
            raise PeerUnavailable() from None
