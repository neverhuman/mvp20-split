#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nomad_crystal360.artifacts import build_artifacts


ROOT = Path(__file__).resolve().parent
DEFAULT_NOMAD_ROOT = Path("/home/ubuntu/nomad")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build and freeze the 360-column physically interpretable NOMAD feature pack."
    )
    parser.add_argument("--nomad-root", type=Path, default=DEFAULT_NOMAD_ROOT)
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=DEFAULT_NOMAD_ROOT / "artifacts" / "nomad_449_baseline",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "nomad_crystal360")
    parser.add_argument("--schema", type=Path, default=ROOT / "crystal360_schema.json")
    parser.add_argument("--lock-file", type=Path, default=ROOT / "requirements-crystal360.lock")
    parser.add_argument("--jobs", type=int, default=-1)
    args = parser.parse_args()

    manifest = build_artifacts(
        train_csv=args.nomad_root / "train.csv",
        test_csv=args.nomad_root / "test.csv",
        train_geometry_root=args.nomad_root / "train",
        test_geometry_root=args.nomad_root / "test",
        baseline_train_csv=args.baseline_dir / "train_features_449.csv",
        baseline_test_csv=args.baseline_dir / "test_features_449.csv",
        output_dir=args.output_dir,
        schema_path=args.schema,
        lock_path=args.lock_file,
        n_jobs=args.jobs,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
