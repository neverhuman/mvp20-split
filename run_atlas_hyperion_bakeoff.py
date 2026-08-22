#!/usr/bin/env python3
"""Build, execute, freeze, and separately score the Atlas/Hyperion bake-off."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nomad_crystal360.bakeoff import (
    CHUNK_WIDTH,
    IMPORTANCE_PERCENTILES,
    SELECTION_FOLDS,
    SWEEP_SEEDS,
    build_public_bundle,
    make_importance_jobs,
    percentile_feature_count,
    percentile_label,
    score_frozen_submission_once,
    verify_public_bundle,
)
from nomad_crystal360.bakeoff_run import run_bakeoff, stage_remote_bundle


ROOT = Path(__file__).resolve().parent
DEFAULT_ATLAS = ROOT / "artifacts" / "nomad_crystal_atlas"
DEFAULT_BASELINE = ROOT / "artifacts" / "nomad_crystal360"
DEFAULT_ROOT = ROOT / "artifacts" / "atlas_hyperion_bakeoff"
DEFAULT_WORKER = ROOT / "atlas_bakeoff_worker.py"
DEFAULT_REMOTE_BUNDLE = Path("/home/ubuntu/atlas-hyperion-bakeoff/bundle")


def prepare(args: argparse.Namespace) -> None:
    if not args.atlas_only and args.hyperion_manifest is None:
        raise ValueError("--hyperion-manifest is required unless --atlas-only is set")
    manifest = build_public_bundle(
        atlas_dir=args.atlas_dir,
        row_id_dir=args.row_id_dir,
        hyperion_manifest=None if args.atlas_only else args.hyperion_manifest,
        output_dir=args.bundle_dir,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


def validate(args: argparse.Namespace) -> None:
    manifest = verify_public_bundle(args.bundle_dir)
    jobs = make_importance_jobs(manifest["predictors"])
    print(
        json.dumps(
            {
                "bundle_sha256": manifest["bundle_sha256"],
                "bundle_mode": manifest.get("bundle_mode", "atlas_hyperion"),
                "train_rows": manifest["train_rows"],
                "test_rows": manifest["test_rows"],
                "predictors": manifest["predictors"],
                "importance_jobs": len(jobs),
                "importance_jobs_by_target": {
                    target: sum(job["target"] == target for job in jobs)
                    for target in manifest["targets"]
                },
                "importance_observations_per_target_feature": len(SWEEP_SEEDS)
                * SELECTION_FOLDS,
                "ranking_fit_width": CHUNK_WIDTH,
                "percentile_feature_counts": {
                    percentile_label(value): percentile_feature_count(
                        manifest["predictors"], value
                    )
                    for value in IMPORTANCE_PERCENTILES
                },
                "test_targets_staged": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


def stage(args: argparse.Namespace) -> None:
    stage_remote_bundle(
        bundle=args.bundle_dir,
        worker=args.worker,
        remote_host=args.remote_host,
        remote_bundle=args.remote_bundle,
    )
    print(
        json.dumps(
            {
                "remote_host": args.remote_host,
                "remote_bundle": str(args.remote_bundle),
                "test_targets_staged": False,
            },
            indent=2,
        )
    )


def run(args: argparse.Namespace) -> None:
    freeze = run_bakeoff(
        bundle=args.bundle_dir,
        output_dir=args.output_dir,
        worker=args.worker,
        remote_host=args.remote_host,
        remote_bundle=args.remote_bundle,
        local_python=args.local_python,
        remote_python=args.remote_python,
        stage_remote=not args.no_stage,
    )
    print(freeze.read_text(encoding="utf-8"))


def score(args: argparse.Namespace) -> None:
    receipt = score_frozen_submission_once(
        output_dir=args.output_dir,
        labeled_test_dir=args.labeled_test_dir,
        benchmark_scores=args.benchmark_scores,
    )
    print(receipt.read_text(encoding="utf-8"))


def _bundle_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_ROOT / "bundle")


def _remote_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--remote-host", default="xbabe1")
    parser.add_argument("--remote-bundle", type=Path, default=DEFAULT_REMOTE_BUNDLE)
    parser.add_argument("--worker", type=Path, default=DEFAULT_WORKER)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare", help="validate and build public bundle")
    prepare_parser.add_argument("--atlas-dir", type=Path, default=DEFAULT_ATLAS)
    prepare_parser.add_argument("--row-id-dir", type=Path, default=DEFAULT_BASELINE)
    prepare_parser.add_argument("--hyperion-manifest", type=Path)
    prepare_parser.add_argument(
        "--atlas-only",
        action="store_true",
        help="stage only the frozen 9,969-column Atlas matrices",
    )
    _bundle_argument(prepare_parser)
    prepare_parser.set_defaults(function=prepare)

    validate_parser = subparsers.add_parser("validate", help="verify bundle and job coverage")
    _bundle_argument(validate_parser)
    validate_parser.set_defaults(function=validate)

    stage_parser = subparsers.add_parser("stage", help="stage the public bundle on the 4090 host")
    _bundle_argument(stage_parser)
    _remote_arguments(stage_parser)
    stage_parser.set_defaults(function=stage)

    run_parser = subparsers.add_parser("run", help="run and freeze the dual-GPU bake-off")
    _bundle_argument(run_parser)
    _remote_arguments(run_parser)
    run_parser.add_argument("--output-dir", type=Path, default=DEFAULT_ROOT / "run")
    run_parser.add_argument("--local-python", default="/usr/bin/python3")
    run_parser.add_argument("--remote-python", default="python3")
    run_parser.add_argument("--no-stage", action="store_true")
    run_parser.set_defaults(function=run)

    score_parser = subparsers.add_parser(
        "score-informational", help="score the frozen submission once on reused test labels"
    )
    score_parser.add_argument("--output-dir", type=Path, default=DEFAULT_ROOT / "run")
    score_parser.add_argument("--labeled-test-dir", type=Path, default=DEFAULT_BASELINE)
    score_parser.add_argument(
        "--benchmark-scores",
        type=Path,
        default=DEFAULT_BASELINE / "benchmark_labeled_test_informational.csv",
    )
    score_parser.set_defaults(function=score)

    args = parser.parse_args()
    args.function(args)


if __name__ == "__main__":
    main()
