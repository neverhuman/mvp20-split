#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nomad_crystal360.atlas_artifacts import build_atlas_artifacts


ROOT = Path(__file__).resolve().parent
DEFAULT_NOMAD_ROOT = Path("/home/ubuntu/nomad")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the validated CrystalAtlas public-geometry predictor bank."
    )
    parser.add_argument("--nomad-root", type=Path, default=DEFAULT_NOMAD_ROOT)
    parser.add_argument(
        "--existing-dir", type=Path, default=ROOT / "artifacts" / "nomad_crystal360"
    )
    parser.add_argument(
        "--baseline-dir",
        type=Path,
        default=DEFAULT_NOMAD_ROOT / "artifacts" / "nomad_449_baseline",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "artifacts" / "nomad_crystal_atlas"
    )
    parser.add_argument("--jobs", type=int, default=112)
    parser.add_argument("--minimum-predictors", type=int, default=8_000)
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    manifest = build_atlas_artifacts(
        train_csv=args.nomad_root / "train.csv",
        test_csv=args.nomad_root / "test.csv",
        train_geometry_root=args.nomad_root / "train",
        test_geometry_root=args.nomad_root / "test",
        existing_dir=args.existing_dir,
        baseline_dir=args.baseline_dir,
        baseline_source=args.nomad_root / "nomad_449_baseline.py",
        output_dir=args.output_dir,
        lock_path=ROOT / "requirements-crystal360.lock",
        n_jobs=args.jobs,
        minimum_predictors=args.minimum_predictors,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
