"""Explicit local supervisor/control commands; startup never migrates or admits work."""

import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path

from ..persistence.state import LocalState
from ..profile import ProfileError
from .configuration import control_token, load_bindings
from .control import ControlServer
from .events import LifecycleEvents
from .routes import Routes
from .supervisor import Supervisor


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["serve", "status", "readiness", "start", "restart", "drain", "force-stop", "shutdown", "quiesce", "recover"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--owner")
    parser.add_argument("--workers-manifest", type=Path)
    parser.add_argument("--worker")
    parser.add_argument('--tool-access-manifest', type=Path)
    parser.add_argument('--tool-access', choices=['runtime', 'artifact'])
    parser.add_argument('--scientific-manifest', type=Path)
    parser.add_argument('--scientific-worker')
    args = parser.parse_args()
    try:
        routes = Routes.ensure(args.root) if args.action == "serve" else Routes.load(args.root)
        if args.action == "readiness":
            if args.manifest is None:
                parser.error("readiness requires --manifest")
            from .health import observe
            report = observe(load_bindings(args.root, args.manifest, routes))
            print(json.dumps(report, sort_keys=True))
            return 0 if report["infrastructure"] == "available" else 3
        if args.action == "serve":
            if args.manifest is None:
                parser.error("serve requires --manifest")
            bindings = load_bindings(args.root, args.manifest, routes)
            token = control_token(args.root, create=True)
            from ..workers.configuration import load_workers
            workers = {} if args.workers_manifest is None else load_workers(args.workers_manifest, bindings)
            from ..tool_access.configuration import load_access
            access = {} if args.tool_access_manifest is None else load_access(args.tool_access_manifest,
                LocalState.snapshot(args.root)['deployment_id'], routes, bindings)
            # Serving holds the operation lease, excluding provisioning/migrations.
            # Control clients read atomic snapshots and never take this writer lease.
            with LocalState(args.root) as state:
                from ..scientific_workers.configuration import load_scientific
                scientific = load_scientific(args.scientific_manifest, state.root, state.identity, access)
                supervisor = Supervisor(bindings, LifecycleEvents(args.root / "logs"),
                                        workers=workers, access=access, scientific=scientific)
                try:
                    server = ControlServer(routes.port("supervisor"), supervisor, token)
                    supervisor.scientific.adopt()
                    server.serve()
                finally:
                    # Unexpected supervisor exit is forced teardown, not graceful drain.
                    supervisor.scientific.quiesce()
                    try:
                        supervisor.workers.force_stop()
                    finally:
                        try:
                            supervisor.scientific.detach()
                        finally:
                            try:
                                supervisor.access.close()
                            finally:
                                for process in supervisor.processes.values():
                                    process.force_stop()
            return 0
        if args.action in {"status", "shutdown"}:
            path = "/" + args.action
        elif args.scientific_worker is not None:
            from ..scientific_workers.profiles import PROFILES
            if args.owner is not None or args.worker is not None or args.tool_access is not None or args.scientific_worker not in PROFILES or args.action not in {'start', 'quiesce', 'recover'}:
                parser.error('invalid scientific worker command')
            path = '/scientific-workers/' + args.scientific_worker + '/' + args.action
        elif args.tool_access is not None:
            if args.owner is not None or args.worker is not None or args.action not in {'start', 'restart', 'drain'}:
                parser.error('invalid tool access command')
            path = '/tool-access/' + args.tool_access + '/' + args.action
        elif args.worker is not None:
            from ..workers.recipes import NATIVE_RECIPES
            if args.owner is not None or args.worker not in NATIVE_RECIPES or args.action not in {"start", "quiesce", "recover", "force-stop"}:
                parser.error("invalid worker command")
            path = "/workers/" + args.worker + "/" + args.action
        else:
            if args.action in {"quiesce", "recover"}:
                parser.error("worker command requires --worker")
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
    except Exception:  # noqa: BLE001 - HTTP and driver diagnostics can contain credentials.
        # Includes HTTP/driver errors: raw diagnostics must not expose credentials.
        print(json.dumps({"status":"rejected", "reason":"local_supervisor_unavailable"}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
