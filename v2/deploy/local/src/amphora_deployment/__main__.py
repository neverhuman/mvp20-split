"""Local validation/probes and declarative ordering; never installs or invokes models."""

import argparse
import json
import os
from pathlib import Path

from .observations import HostObservation
from .profile import DeploymentProfile, ProfileError
from .readiness import assess
from .replacement import CampaignCut


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    for name in ("validate", "preflight"):
        actions.add_parser(name).add_argument("--profile", type=Path, required=True)
    order = actions.add_parser("replacement-order")
    order.add_argument("--admissions-paused", action="store_true")
    for name in ("active-campaigns", "inflight-attempts", "pending-retentions"):
        order.add_argument("--" + name, type=int, required=True)
    args = parser.parse_args()
    try:
        if args.action == "replacement-order":
            report = CampaignCut(args.admissions_paused, args.active_campaigns, args.inflight_attempts, args.pending_retentions).plan()
        else:
            with args.profile.open("rb") as stream:
                profile = DeploymentProfile.from_bytes(stream.read(65537))
            if args.action == "validate":
                report = {"status": "profile_valid", "profile_id": profile.profile_id, "readiness_assessed": False}
            else:
                observed = HostObservation.inspect(profile)
                report = {**assess(profile, observed, os.environ).to_record(), "observation": observed.to_record()}
    except ProfileError as error:
        print(json.dumps({"status": "rejected", "reason": str(error)}))
        return 2
    except OSError:
        print(json.dumps({"status": "rejected", "reason": "profile_or_probe_unavailable"}))
        return 2
    print(json.dumps(report, sort_keys=True))
    return 3 if report["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
