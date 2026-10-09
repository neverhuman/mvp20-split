"""One background coordinator owned by the existing installation supervisor."""
import threading

from ..profile import require
from .coordinator import LaunchCoordinator
from .local_readiness import LocalLaunchReadiness
from .managed_workers import ManagedLaunchWorkers
from .preflight import LaunchPreflight
from .runtime_peer import LoopbackPeer, RuntimePeer


class LaunchHost:
    def __init__(self, installation, supervisor, routes):
        self.installation, self.supervisor = installation, supervisor
        self.stop = threading.Event()
        self.thread = None
        self.failure = False
        self.api, self.api_thread = None, None
        self.api_stop = threading.Event()
        peers = {}
        for owner in ('runtime', 'artifact', 'registry'):
            binding = supervisor.bindings[owner]
            token = binding.environment['AMPHORA_' + owner.upper() + '_OPERATOR_TOKEN']
            factory = RuntimePeer if owner == 'runtime' else LoopbackPeer
            peers[owner] = factory(routes.port(owner), token, stopped=self.stop)
        workers = ManagedLaunchWorkers(supervisor, installation.store,
            lambda supervisor, bindings: installation.catalog(supervisor, bindings, routes))
        preflight = LaunchPreflight(installation.policy, peers['runtime'], peers['artifact'], peers['registry'],
            installation.executors, LocalLaunchReadiness(installation, supervisor, self.stop))
        self.coordinator = LaunchCoordinator(installation.journal, preflight, peers['runtime'], workers)

    def attach_api(self, port, token):
        from .http import LaunchServer
        require(self.thread is None and self.api is None, 'launch_listener_already_attached')
        self.api = LaunchServer(port, token, self.installation.manifest.actor_id,
            self.installation.policy, self.installation.journal,
            lambda: not self.stop.is_set() and not self.failure and not self.supervisor.closed, self.api_stop,
            recover=self.coordinator.request_recovery)

    def start(self):
        require(self.thread is None and not self.stop.is_set(), 'launch_host_already_started')
        self.thread = threading.Thread(target=self._run, name='amphora-campaign-launch')
        self.thread.start()
        if self.api is not None:
            self.api_thread = threading.Thread(target=self.api.serve, name='amphora-campaign-launch-api')
            self.api_thread.start()

    def _run(self):
        while not self.stop.is_set():
            try:
                self.coordinator.tick()
            except Exception:  # Private journal/transport details never enter control output.
                self.failure = True
                self.stop.set()
                return
            self.stop.wait(1)

    def quiesce(self):
        self.stop.set()
        self.api_stop.set()

    def require_stopped(self):
        require(self.thread is None or not self.thread.is_alive(), 'launch_host_requires_drain')
        require(self.api_thread is None or not self.api_thread.is_alive(), 'launch_listener_requires_drain')

    def close(self):
        self.quiesce()
        if self.api_thread is not None:
            self.api_thread.join(10)
        elif self.api is not None:
            self.api.server_close()
        if self.thread is not None:
            self.thread.join(15)
        self.require_stopped()
