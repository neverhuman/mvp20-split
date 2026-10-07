"""Explicit local supervisor/control commands; startup never migrates or admits work."""

import argparse
import json
from pathlib import Path
import urllib.error
import urllib.request

from ..profile import ProfileError
from ..persistence.state import LocalState
from .configuration import control_token, load_bindings
from .control import ControlServer
from .events import LifecycleEvents
from .routes import Routes
from .supervisor import Supervisor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["serve", "status", "start", "restart", "force-stop", "shutdown"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--owner")
    args = parser.parse_args()
    try:
        routes = Routes.ensure(args.root) if args.action == "serve" else Routes.load(args.root)
        if args.action == "serve":
            if args.manifest is None:
                parser.error("serve requires --manifest")
            bindings = load_bindings(args.root, args.manifest, routes)
            token = control_token(args.root, create=True)
            supervisor = Supervisor(bindings, LifecycleEvents(args.root / "logs"))
            # Serving holds the operation lease, excluding provisioning/migrations.
            # Control clients read atomic snapshots and never take this writer lease.
            with LocalState(args.root):
                server = ControlServer(routes.port("supervisor"), supervisor, token)
                try:
                    server.serve()
                finally:
                    # Unexpected supervisor exit is forced teardown, not graceful drain.
                    for process in supervisor.processes.values():
                        process.force_stop()
            return 0
        if args.action in {"status", "shutdown"}:
            path = "/" + args.action
        else:
            if args.owner is None:
                parser.error("owner command requires --owner")
            from ..installation import SERVING_HOSTS
            if args.owner not in SERVING_HOSTS:
                parser.error("unknown owner")
            path = "/owners/" + args.owner + "/" + args.action
        token = control_token(args.root)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        request = urllib.request.Request(routes.endpoint("supervisor") + path,
            method="GET" if args.action == "status" else "POST", headers={"Authorization":"Bearer " + token})
        with opener.open(request, timeout=30) as response:
            report = json.loads(response.read(65537))
        print(json.dumps(report, sort_keys=True))
        return 0
    except ProfileError as error:
        print(json.dumps({"status":"rejected", "reason":str(error)}))
        return 2
    except Exception:
        # Includes HTTP/driver errors: raw diagnostics must not expose credentials.
        print(json.dumps({"status":"rejected", "reason":"local_supervisor_unavailable"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
