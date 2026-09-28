"""Local artifact service executable and bounded maintenance commands."""

import argparse
import json
import sys

import uvicorn

from .hosting import Host
from .maintenance.cleanup import Cleanup
from .maintenance.reconcile import Reconciler
from .retention.reservations import Reservations


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["serve", "cleanup", "reconcile", "check"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--port", type=int, default=8081)
    parser.add_argument("--actor")
    parser.add_argument("--tenant")
    parser.add_argument("--project")
    parser.add_argument("--after", default="")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or not 1 <= args.limit <= 100:
        parser.error("Port or maintenance bound invalid")
    try:
        host = Host.load(args.config)
    except Exception:
        print("Artifact configuration or database readiness check failed; no service started.", file=sys.stderr)
        return 2
    try:
        if args.action == "serve":
            uvicorn.run(host.app(), host="127.0.0.1", port=args.port, access_log=False)
        elif args.action == "check":
            print("Artifact configuration and service role ready")
        else:
            matches = [p for p in host.principals if (p.actor_id, p.scope.tenant_id, p.scope.project_id)
                       == (args.actor, args.tenant, args.project)]
            if len(matches) != 1:
                raise ValueError("Select exactly one configured principal")
            runner = Cleanup(host.uploads, host.storage) if args.action == "cleanup" else Reconciler(
                Reservations(host.uploads, host.outcomes))
            print(json.dumps(runner.sweep(matches[0], limit=args.limit, after=args.after)))
    except Exception:
        print("Artifact operation failed; retained state remains authoritative.", file=sys.stderr)
        return 2
    finally:
        host.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
