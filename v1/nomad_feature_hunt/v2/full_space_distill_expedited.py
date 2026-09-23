"""Expedited confirmation of the best completed two-sided distillation candidate.

This is a deliberately narrow checkpoint path: it never treats an incomplete
search as a fully verified distillation run.  It preregisters one candidate
from completed generations plus both controls, then evaluates all three on the
already-derived unused confirmation seeds with the frozen 400-tree model.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from .full_space_distill import (
    BANDGAP_TARGET,
    CONFIRM_TREES,
    DISCOVERY_FOLDS,
    EPSILON,
    FORMATION_TARGET,
    CampaignScheduler,
    Host,
    Settings,
    _execution_assignment,
    _json_command,
    _pair_from_dict,
    _score_pairs,
    _select_confirmed,
    atomic_json,
    canonical_hash,
    epsilon_select,
    save_frame,
    sha256_file,
    utc_now,
    verify_parent_lock,
)


def _completed_rows(settings: Settings) -> list[dict[str, Any]]:
    paths = sorted((settings.run_root / "search").glob("generation-*.json"))
    if not paths:
        raise RuntimeError("no completed search generation is available")
    return [row for path in paths for row in json.loads(path.read_text(encoding="utf-8"))["pairs"]]


def _checkpoint_candidate(rows: list[dict[str, Any]], compact: dict[str, Any]) -> dict[str, Any]:
    compact_counts = compact["target_mask_counts"]
    eligible = [
        row
        for row in rows
        if int(row["union_count"]) < int(compact["union_count"])
        and int(row["target_mask_counts"][BANDGAP_TARGET]) < int(compact_counts[BANDGAP_TARGET])
        and int(row["target_mask_counts"][FORMATION_TARGET]) < int(compact_counts[FORMATION_TARGET])
    ]
    if not eligible:
        raise RuntimeError("no completed candidate reduces both target masks and the union")
    return epsilon_select(eligible)


def run(settings: Settings) -> dict[str, Any]:
    protocol = json.loads((settings.run_root / "protocol.json").read_text(encoding="utf-8"))
    verify_parent_lock(settings, protocol)
    if sha256_file(settings.worker) != protocol["worker_sha256"]:
        raise RuntimeError("distillation worker changed after prepare")

    controls_payload = json.loads(
        (settings.run_root / "search/controls.json").read_text(encoding="utf-8")
    )["controls"]
    compact = controls_payload["compact-epsilon-control"]
    candidate_row = _checkpoint_candidate(_completed_rows(settings), compact)
    candidate = _pair_from_dict(candidate_row)
    controls = {
        name: _pair_from_dict(controls_payload[name])
        for name in ("accuracy-control", "compact-epsilon-control")
    }
    seeds = tuple(map(int, protocol["confirmation_seeds"]))

    preregistration = {
        "schema": "DistillExpeditedPreregistration.v1",
        "registered_at": utc_now(),
        "search_checkpoint_only": True,
        "completed_generations": len(
            list((settings.run_root / "search").glob("generation-*.json"))
        ),
        "candidate": candidate_row,
        "candidate_requirement": (
            "strictly fewer band-gap columns, formation columns, and union columns "
            "than the compact control"
        ),
        "controls": controls_payload,
        "confirmation_seeds": list(seeds),
        "folds_per_seed": DISCOVERY_FOLDS,
        "trees": CONFIRM_TREES,
        "runner_sha256": sha256_file(Path(__file__)),
        "test_labels_used": False,
    }
    preregistration["canonical_hash"] = canonical_hash(preregistration)
    atomic_json(settings.run_root / "expedited/preregistration.json", preregistration)

    assignment = _execution_assignment()
    atomic_json(settings.run_root / "receipts/expedited_scq_assignment.json", assignment)
    host = Host("local", "/usr/bin/python3", settings.bundle, settings.worker)
    smoke = _json_command(host, ["--smoke"], timeout=120)
    atomic_json(
        settings.run_root / "receipts/expedited_gpu_smoke.json",
        {**smoke, "assignment": assignment, "test_labels_used": False},
    )

    pairs = [candidate, controls["accuracy-control"], controls["compact-epsilon-control"]]
    scheduler = CampaignScheduler(settings, remote_host=None)
    summaries, ledger = _score_pairs(
        settings,
        scheduler,
        pairs,
        seeds=seeds,
        iterations=CONFIRM_TREES,
        stage="expedited-confirmation",
    )
    save_frame(ledger, settings.run_root / "expedited/fold_scores")

    control_ids = {name: pair.pair_id for name, pair in controls.items()}
    for row in summaries:
        row["candidate_class"] = next(
            (name for name, pair_id in control_ids.items() if row["pair_id"] == pair_id),
            "two-sided-reduced-candidate",
        )
    selected, fallback = _select_confirmed(summaries, control_ids)
    best = min(float(row["mean_rmsle"]) for row in summaries)
    for row in summaries:
        row["epsilon_feasible"] = float(row["mean_rmsle"]) <= best + EPSILON + 1e-15
        row["selected"] = row["pair_id"] == selected["pair_id"]

    curve = pd.DataFrame(
        {
            "pair_id": row["pair_id"],
            "candidate_class": row["candidate_class"],
            "mean_rmsle": row["mean_rmsle"],
            "union_count": row["union_count"],
            "bandgap_count": row["target_mask_counts"][BANDGAP_TARGET],
            "formation_count": row["target_mask_counts"][FORMATION_TARGET],
            "epsilon_feasible": row["epsilon_feasible"],
            "selected": row["selected"],
            "test_labels_used": False,
        }
        for row in summaries
    )
    save_frame(curve, settings.run_root / "expedited/score_curve")
    results = {
        "schema": "DistillExpeditedConfirmation.v1",
        "search_checkpoint_only": True,
        "candidates": summaries,
        "controls": control_ids,
        "best_confirmed_mean_rmsle": best,
        "selected": selected,
        "fallback_to_compact_control": fallback,
        "confirmation_seeds": list(seeds),
        "folds_per_seed": DISCOVERY_FOLDS,
        "trees": CONFIRM_TREES,
        "preregistration_sha256": sha256_file(settings.run_root / "expedited/preregistration.json"),
        "test_labels_used": False,
    }
    results["canonical_hash"] = canonical_hash(results)
    atomic_json(settings.run_root / "expedited/results.json", results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--parent-run", default="20260719-r1")
    arguments = parser.parse_args()
    results = run(Settings(arguments.run_id, parent_run=arguments.parent_run))
    print(json.dumps(results, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
