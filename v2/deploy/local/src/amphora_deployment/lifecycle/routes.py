"""Persisted loopback endpoint allocation; never treats allocation as readiness."""

from contextlib import ExitStack
from dataclasses import dataclass
import socket

from ..installation import OWNERS
from ..persistence.state import LocalState
from ..profile import require


NAMES = tuple(sorted((*OWNERS, "gateway", "supervisor")))


@dataclass(frozen=True)
class Routes:
    ports: tuple[tuple[str, int], ...]

    @classmethod
    def from_record(cls, value):
        require(type(value) is dict and set(value) == {"profile", "host", "ports"}, "lifecycle_routes_shape")
        require(value["profile"] == "loopback-routes-v1" and value["host"] == "127.0.0.1", "lifecycle_routes_scope")
        ports = value["ports"]
        require(type(ports) is dict and set(ports) == set(NAMES), "lifecycle_routes_owners")
        require(all(type(p) is int and 1024 <= p <= 65535 for p in ports.values()) and
                len(set(ports.values())) == len(NAMES), "lifecycle_routes_ports")
        return cls(tuple(sorted(ports.items())))

    def port(self, name):
        require(name in NAMES, "lifecycle_route_owner")
        return dict(self.ports)[name]

    def endpoint(self, name):
        return "http://127.0.0.1:" + str(self.port(name))

    def to_record(self):
        return {"profile": "loopback-routes-v1", "host": "127.0.0.1", "ports": dict(self.ports)}

    @classmethod
    def load(cls, root):
        state = LocalState.snapshot(root)
        require(state.get("phase") == "stores_ready", "lifecycle_stores_required")
        return cls.from_record(state["routes"])

    @classmethod
    def ensure(cls, root):
        with LocalState(root) as state:
            require(state.record.get("phase") == "stores_ready", "lifecycle_stores_required")
            if "routes" in state.record:
                return cls.from_record(state.record["routes"])
            with ExitStack() as stack:
                ports = {}
                for owner in NAMES:
                    probe = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
                    probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
                    probe.bind(("127.0.0.1", 0))
                    ports[owner] = probe.getsockname()[1]
                result = cls.from_record({"profile": "loopback-routes-v1", "host": "127.0.0.1", "ports": ports})
                state.record["routes"] = result.to_record()
                state.save()
                return result
        # Reservations end here. Later bind conflicts must fail startup; never silently reroute.
