"""Local runtime executable with explicit configuration and scoped maintenance."""

import argparse
import json
import sys
from dataclasses import asdict

import uvicorn

from .completion.recovery import StaleIntents
from .hosting import Host
from .lifecycle.settlement import BudgetSettlement


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["serve", "check", "settle", "reconcile-intents"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--actor")
    parser.add_argument("--tenant")
    parser.add_argument("--project")
    parser.add_argument("--run")
    parser.add_argument("--after", default="")
    parser.add_argument("--limit", type=int, default=100)
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
            print("Runtime fixture configuration and service role ready")
        else:
            matches = [p for p in host.principals if (p.actor_id, p.scope.tenant_id, p.scope.project_id)
                       == (args.actor, args.tenant, args.project)]
            if len(matches) != 1 or not args.run:
                raise ValueError("Select a run and exactly one configured principal")
            if args.action == "reconcile-intents":
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
