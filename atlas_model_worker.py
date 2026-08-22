#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

from nomad_crystal360.atlas_worker import environment_identity, run_job


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute one immutable CrystalAtlas model job.")
    parser.add_argument("--identity", action="store_true")
    parser.add_argument("--bundle", type=Path)
    parser.add_argument("--job-base64")
    args = parser.parse_args()
    if args.identity:
        print(json.dumps(environment_identity(), sort_keys=True))
        return
    if args.bundle is None or not args.job_base64:
        parser.error("--bundle and --job-base64 are required for a model job")
    job = json.loads(base64.b64decode(args.job_base64).decode("utf-8"))
    print(json.dumps(run_job(args.bundle, job), separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
