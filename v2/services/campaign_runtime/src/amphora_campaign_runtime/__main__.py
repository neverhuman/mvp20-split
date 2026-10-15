"""Local runtime executable with explicit configuration and scoped maintenance."""

import argparse
import json
import sys
from dataclasses import asdict

import uvicorn

from .completion.recovery import StaleIntents
from .coordinator.polling import GraphPoller
from .hosting import Host
from .lifecycle.settlement import BudgetSettlement
from .resource_profiles.preflight import require_supported_resources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["serve", "check", "resource-preflight", "settle", "reconcile-intents", "deliver", "coordinate"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--target-release")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--actor")
    parser.add_argument("--tenant")
    parser.add_argument("--project")
    parser.add_argument("--run")
    parser.add_argument("--after", default="")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--time-budget", type=float, default=20)
    parser.add_argument("--poll-interval", type=float, default=1)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535 or not 1 <= args.limit <= 100:
        parser.error("Invalid loopback port")
    try:
        host = Host.load(args.config)
    except Exception:
        print("Runtime configuration or database readiness check failed; no service started.", file=sys.stderr)
        return 2
    try:
        if args.action == "serve":
            uvicorn.run(host.app(), host="127.0.0.1", port=args.port, access_log=False)
        elif args.action == "check":
            print("Runtime configuration and service role ready")
        elif args.action == "resource-preflight":
            with host.admission.commands.engine.connect() as conn:
                require_supported_resources(conn, args.target_release)
            print("Runtime active resource profiles supported")
        else:
            matches = [p for p in host.principals if (p.actor_id, p.scope.tenant_id, p.scope.project_id)
                       == (args.actor, args.tenant, args.project)]
            if len(matches) != 1 or (args.action not in {"deliver", "coordinate"} and not args.run):
                raise ValueError("Select a run and exactly one configured principal")
            if args.action == "coordinate":
                if host.graphs is None:
                    raise ValueError("Configured graph host required")
                poller = GraphPoller(host.admission.commands.engine, host.graphs[1])
                print(json.dumps(poller.sweep(matches[0], seconds=args.time_budget, interval=args.poll_interval)))
            elif args.action == "deliver":
                print(json.dumps(host.delivery.sweep(matches[0], limit=args.limit, max_seconds=args.time_budget)))
            elif args.action == "reconcile-intents":
                result = StaleIntents(host.admission.commands.engine).sweep(matches[0], args.run, after=args.after, limit=args.limit)
                print(json.dumps(result))
            else:
                result = BudgetSettlement(host.admission.commands.engine).sweep(matches[0], args.run)
                print(json.dumps(asdict(result)))
    except Exception:
        print("Runtime operation failed; durable state remains authoritative.", file=sys.stderr)
        return 2
    finally:
        host.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
