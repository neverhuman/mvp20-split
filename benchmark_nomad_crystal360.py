#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nomad_crystal360.benchmark import run_benchmark


ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark 449, Crystal360, combined, and additive feature-family views."
    )
    parser.add_argument(
        "--artifact-dir", type=Path, default=ROOT / "artifacts" / "nomad_crystal360"
    )
    parser.add_argument("--max-iter", type=int, default=120)
    args = parser.parse_args()
    report = run_benchmark(args.artifact_dir, max_iter=args.max_iter)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
