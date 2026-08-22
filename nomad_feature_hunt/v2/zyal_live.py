from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import traceback
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd

from nomad_crystal360.io import load_structures
from nomad_feature_hunt.ledger import HashChain, atomic_json, sha256_file

from .compiler import TrustedCompiler
from .execution import deterministic_real_sample, quarantine_columns, run_invariance_tests
from .kernels import KERNEL_OPERATIONS, PrimitiveCache
from .novelty import numeric_signature
from .schemas import FAMILY_FIELDS, OUTPUT_FIELDS, SPEC_FIELDS, SchemaError
from .scoring import FamilyCandidate, categorical_discovery_feedback, score_discovery
from .security import plugin_sandbox_command
from .zyal_epochs import (
    CAMPAIGN_VERSION,
    GENETIC_GENERATIONS,
    GENETIC_POPULATION,
    PLUGIN_LIMIT_BYTES,
    TARGETS,
    CampaignError,
    CampaignStore,
    Settings,
    build_epoch_prompt,
    controller_feature_id,
    dispatch_role_wave,
    epoch_role_specs,
    validate_genetic_history,
    write_receipt,
)


AGGREGATIONS = ("raw", "per-atom", "volume-normalized")
_EXECUTION_CONTEXT: dict[str, Any] = {}


def _emit(event: str, **payload: Any) -> None:
    print(json.dumps({"event": event, **payload}, sort_keys=True), flush=True)


def _seal_phase(
    settings: Settings,
    store: CampaignStore,
    phase: str,
    payload: Mapping[str, Any],
) -> Path:
    path = settings.run_root / f"receipts/phases/{phase}.json"
    reconciled = store.phase_complete(phase)
    atomic_json(path, dict(payload))
    store.complete_phase(phase, path)
    HashChain(settings.events_path).append(
        "phase_reconciled" if reconciled else "phase_complete",
        {"phase": phase, "receipt_sha256": sha256_file(path)},
    )
    return path


def _role_statuses(store: CampaignStore, epoch: int) -> dict[str, str]:
    with store.connect() as connection:
        rows = connection.execute(
            "SELECT role_id,status FROM roles WHERE epoch=?", (epoch,)
        ).fetchall()
    return {str(row["role_id"]): str(row["status"]) for row in rows}


def _pending_roles(
    store: CampaignStore, epoch: int, role_classes: set[str]
) -> list[dict[str, Any]]:
    statuses = _role_statuses(store, epoch)
    return [
        role
        for role in epoch_role_specs(epoch)
        if role["class"] in role_classes and statuses.get(str(role["id"])) == "pending"
    ]


def _kernel_config(kernel: str, epoch: int, role_index: int, parameter_index: int) -> dict[str, Any]:
    position = (epoch - 1) * 72 + role_index * 3 + parameter_index + 1
    unit = min(position / 850.0, 0.97)
    if kernel == "symmetry":
        return {"symprec": round(0.00001 + 0.09 * unit, 7)}
    if kernel == "reciprocal":
        return {
            "hmax": 1 + (position % 4),
            "weight": ("Z", "atomic_mass", "X", "atomic_radius")[position % 4],
            "debye_waller_b": round(2.8 * unit, 4),
        }
    if kernel in {"orbital_local", "periodic_graph", "entropy_transport"}:
        return {"cutoff": round(1.1 + 10.5 * unit, 4)}
    if kernel == "electrostatic":
        return {
            "bond_valence_b": round(0.1 + 0.85 * unit, 4),
            "screening_length": round(0.5 + 18.0 * unit, 4),
            "charge_scale": round(0.5 + 0.95 * unit, 4),
            "qeq_screening_length": round(0.5 + 17.0 * unit, 4),
        }
    if kernel == "local_density":
        return {
            "cutoff": round(1.1 + 10.0 * unit, 4),
            "radial_centers": [
                round(0.5 + 2.0 * unit, 4),
                round(3.0 + 3.0 * unit, 4),
                round(7.0 + 4.0 * unit, 4),
            ],
            "width": round(0.05 + 1.8 * unit, 4),
        }
    if kernel == "canonical_topology":
        return {"grid": 3 + (position % 6), "void_threshold": round(0.1 + 4.5 * unit, 4)}
    if kernel == "thermodynamics":
        return {"pair_cutoff": round(1.5 + 10.0 * unit, 4), "redox_scale": round(0.5 + 0.95 * unit, 4)}
    if kernel == "mechanics":
        return {"bond_cutoff": round(1.5 + 6.0 * unit, 4), "stiffness_exponent": round(2.0 + 3.8 * unit, 4)}
    raise ValueError(f"unsupported kernel: {kernel}")


def _cards(settings: Settings, epoch: int) -> dict[tuple[str, str], dict[str, Any]]:
    cards: dict[tuple[str, str], dict[str, Any]] = {}
    for path in sorted((settings.run_root / f"families/epoch-{epoch:02d}").glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        cards[(str(value["domain"]), str(value["family_slug"]))] = value
    return cards


def _dispatch_architects(settings: Settings, store: CampaignStore, epoch: int) -> None:
    roles = _pending_roles(store, epoch, {"domain_architect"})
    if not roles:
        return
    prior = []
    for path in sorted((settings.run_root / "families").glob("epoch-*/*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        if int(str(path.parent.name).split("-")[-1]) < epoch:
            prior.append(str(value["family_slug"]))
    context = {
        "baseline_columns": 10_800,
        "graduated_zyal_columns": 831,
        "prior_family_slug_sha256": sha256_file(settings.run_root / "novelty/baseline_registry.jsonl"),
        "recent_prior_family_slugs": prior[-120:],
        "epoch_direction": "invent measurable mechanisms distinct from every listed prior family",
    }
    prompts = {str(role["id"]): build_epoch_prompt(role, context) for role in roles}
    result = dispatch_role_wave(
        settings, store, roles, prompts, epoch=epoch, wave_id="architects-10"
    )
    _emit("architect_wave_complete", epoch=epoch, result=result)


def _builder_prompt(
    role: Mapping[str, Any], cards: Sequence[Mapping[str, Any]], epoch: int, role_index: int
) -> str:
    if len(cards) < 2:
        return build_epoch_prompt(
            role,
            {
                "assigned_family_cards": list(cards),
                "instruction": "No two current-epoch cards are available; return the strict schema without inventing IDs.",
            },
        )
    assignments = []
    for side, card in enumerate(cards[:2]):
        kernel = str(card["kernel"])
        assignments.append(
            {
                "spec_index": side + 1,
                "family_slug": card["family_slug"],
                "domain": card["domain"],
                "kernel": kernel,
                "spec_slug": f"e{epoch:02d}-{str(role['domain']).lower()}-builder-{'ab'[side]}",
                "name_prefix": "ab"[side],
                "parameter_sets": [
                    {
                        "id": f"p{index + 1}",
                        "values": _kernel_config(kernel, epoch, role_index * 2 + side, index),
                        "physical_justification": "Controller-preregistered distinct physical resolution.",
                    }
                    for index in range(3)
                ],
            }
        )
    kernel = str(cards[0]["kernel"])
    operations = list(KERNEL_OPERATIONS[kernel])[:8]
    context = {
        "assigned_family_cards": list(cards[:2]),
        "assignments": assignments,
        "operation_registry": operations,
        "output_blueprint": [
            {
                "index": index + 1,
                "operation": operation,
                "parameter_set": f"p{index % 3 + 1}",
                "aggregation": "raw",
            }
            for index, operation in enumerate(operations)
        ],
        "aggregations": ["raw"],
        "compact_output_rules": [
            "exactly 8 outputs per spec",
            "use assignments and output_blueprint exactly",
            "equation at most 40 characters",
            "unit at most 12 characters",
            "physical_interpretation at most 12 words",
            "emit minified strict JSON without markdown",
        ],
        "missingness_policy": "replace nonfinite kernel values with zero and preserve a missingness indicator",
    }
    return build_epoch_prompt(role, context)


def _dispatch_builders(settings: Settings, store: CampaignStore, epoch: int) -> None:
    roles = _pending_roles(store, epoch, {"domain_spec_builder"})
    if not roles:
        return
    cards = _cards(settings, epoch)
    prompts = {}
    for index, role in enumerate(roles):
        assigned = [
            card for (domain, _slug), card in sorted(cards.items()) if domain == role["domain"]
        ][:2]
        prompts[str(role["id"])] = _builder_prompt(role, assigned, epoch, index)
    result = dispatch_role_wave(
        settings, store, roles, prompts, epoch=epoch, wave_id="domain-builders-10"
    )
    _emit("builder_wave_complete", epoch=epoch, result=result)


def _base_specs(settings: Settings, epoch: int) -> list[Path]:
    return sorted((settings.run_root / f"specs/epoch-{epoch:02d}").glob("*.json"))


def _expand_specs(settings: Settings, epoch: int) -> dict[str, list[Path]]:
    output_dir = settings.run_root / f"specs/epoch-{epoch:02d}/controller-expanded"
    output_dir.mkdir(parents=True, exist_ok=True)
    groups: dict[str, list[Path]] = {}
    derivations = []
    for source_path in _base_specs(settings, epoch):
        source = json.loads(source_path.read_text(encoding="utf-8"))
        parameters = list(source.get("parameter_sets", []))[:3]
        operations = list(KERNEL_OPERATIONS[str(source["kernel"])])[:8]
        exemplars = {
            str(output["operation"]): output
            for output in source.get("outputs", [])
            if isinstance(output, dict)
        }
        if len(parameters) < 3 or not all(operation in exemplars for operation in operations):
            continue
        group_paths = []
        for aggregation in AGGREGATIONS:
            suffix = {"raw": "raw", "per-atom": "per-atom", "volume-normalized": "per-volume"}[
                aggregation
            ]
            spec_slug = f"{source['spec_slug']}-{suffix}"
            spec = {field: source[field] for field in SPEC_FIELDS if field in source}
            spec["spec_slug"] = spec_slug
            spec["aggregations"] = [aggregation]
            outputs = []
            for parameter in parameters:
                parameter_id = str(parameter["id"])
                for operation in operations:
                    exemplar = exemplars[operation]
                    name = f"{operation}-{parameter_id}-{suffix}"
                    equation = str(exemplar["equation"])
                    unit = str(exemplar["unit"])
                    if aggregation == "per-atom":
                        equation = f"({equation})/Nprim"
                        unit = f"{unit}/atom"
                    elif aggregation == "volume-normalized":
                        equation = f"({equation})/Vprim"
                        unit = f"{unit}/A3"
                    outputs.append(
                        {
                            "name": name,
                            "operation": operation,
                            "parameter_set": parameter_id,
                            "aggregation": aggregation,
                            "equation": equation,
                            "unit": unit,
                            "physical_interpretation": (
                                f"{exemplar['physical_interpretation']} at {parameter_id}; {aggregation}."
                            ),
                            "feature_id": controller_feature_id(
                                epoch,
                                str(source["domain"]),
                                str(source["family_slug"]),
                                spec_slug,
                                name,
                            ),
                        }
                    )
            spec["outputs"] = outputs
            family = str(source["family_slug"])
            spec_id = f"v2.1.e{epoch:02d}.{str(source['domain']).lower()}.{family}.{spec_slug}"
            spec["spec_id"] = spec_id
            spec["source_role_id"] = source["source_role_id"]
            path = output_dir / f"{spec_id}.json"
            atomic_json(path, spec)
            group_paths.append(path)
        groups[str(source["spec_id"])] = group_paths
        derivations.append(
            {
                "source_spec_id": source["spec_id"],
                "source_sha256": sha256_file(source_path),
                "derived_specs": {
                    str(path.relative_to(settings.run_root)): sha256_file(path)
                    for path in group_paths
                },
            }
        )
    atomic_json(
        settings.run_root / f"receipts/features/epoch-{epoch:02d}-controller-expansion.json",
        {
            "epoch": epoch,
            "source_specs": len(derivations),
            "aggregations": list(AGGREGATIONS),
            "max_outputs_per_derived_spec": 24,
            "derivations": derivations,
        },
    )
    return groups


def _compile(settings: Settings, store: CampaignStore, epoch: int) -> dict[str, Any]:
    cards = _cards(settings, epoch)
    paths = sorted(
        (settings.run_root / f"specs/epoch-{epoch:02d}/controller-expanded").glob("*.json")
    )
    if not paths:
        raise CampaignError(f"epoch {epoch} produced no controller-expanded executable specs")
    train = pd.read_csv(settings.run_root / "inputs/public/train.csv")
    sample_ids = deterministic_real_sample(train["id"].tolist(), 16, seed=4219 + epoch)
    sample = train[train["id"].isin(sample_ids)].copy()
    sample["_order"] = sample["id"].map({value: index for index, value in enumerate(sample_ids)})
    sample = sample.sort_values("_order").drop(columns="_order")
    structures = load_structures(sample, settings.run_root / "inputs/public/train_geometry")
    compiler = TrustedCompiler(PrimitiveCache(settings.run_root / f"cache/primitives/epoch-{epoch:02d}"))
    registry = []
    failures = []
    smoke = []
    for path in paths:
        raw_spec = json.loads(path.read_text(encoding="utf-8"))
        raw_card = cards.get((str(raw_spec["domain"]), str(raw_spec["family_slug"])))
        if raw_card is None:
            failures.append({"spec": path.name, "error": "unresolved FamilyCard"})
            continue
        card = {field: raw_card[field] for field in FAMILY_FIELDS}
        spec = {field: raw_spec[field] for field in SPEC_FIELDS}
        spec["outputs"] = [
            {field: output[field] for field in OUTPUT_FIELDS} for output in raw_spec["outputs"]
        ]
        try:
            compiled = compiler.compile(card, spec, source_role_id=raw_spec["source_role_id"])
            for column, output in zip(compiled.columns, raw_spec["outputs"], strict=True):
                column["feature_id"] = output["feature_id"]
                column["campaign_version"] = CAMPAIGN_VERSION
                column["epoch"] = epoch
                column["family_id"] = raw_card["family_id"]
                column["spec_id"] = raw_spec["spec_id"]
            first = compiler.compute_matrix(compiled, structures, sample_ids)
            second = compiler.compute_matrix(compiled, structures, sample_ids)
            invariance = run_invariance_tests(
                structures, lambda transformed, item=compiled: compiler.compute_family(item, transformed)
            )
            passed = {
                column["feature_id"]: first.equals(second)
                and all(invariance[name].get(column["feature_id"], False) for name in invariance)
                for column in compiled.columns
            }
            smoke.append(
                {
                    "spec_id": raw_spec["spec_id"],
                    "structures": 16,
                    "deterministic": first.equals(second),
                    "passed_columns": sum(passed.values()),
                    "failed_columns": [feature_id for feature_id, valid in passed.items() if not valid],
                }
            )
            for column in compiled.columns:
                column["smoke_valid"] = passed[column["feature_id"]]
                registry.append(column)
        except (SchemaError, ValueError) as error:
            failures.append({"spec": path.name, "error": str(error)})
    registry_path = settings.run_root / f"novelty/epoch-{epoch:02d}-compiled-registry.jsonl"
    registry_path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in registry),
        encoding="utf-8",
    )
    with store.connect() as connection:
        for card in cards.values():
            connection.execute(
                "INSERT OR REPLACE INTO families VALUES(?,?,?,1)",
                (card["family_id"], epoch, card["domain"]),
            )
        for row in registry:
            connection.execute(
                "INSERT OR REPLACE INTO columns VALUES(?,?,?,?,0,0,0,?)",
                (
                    row["feature_id"],
                    epoch,
                    row["domain"],
                    row["family_id"],
                    None if row["smoke_valid"] else "smoke_invariance_or_determinism",
                ),
            )
    receipt = {
        "epoch": epoch,
        "static_checks_passed": not failures,
        "plugin_limit_bytes": PLUGIN_LIMIT_BYTES,
        "individual_column_quarantine": True,
        "compiled_specs": len(smoke),
        "compiled_columns": len(registry),
        "smoke_structures": 16,
        "smoke_reports": smoke,
        "compile_failures": failures,
        "registry_sha256": sha256_file(registry_path),
    }
    _seal_phase(settings, store, f"epoch-{epoch:02d}-compilation", receipt)
    _emit(
        "compilation_complete",
        epoch=epoch,
        specs=len(smoke),
        columns=len(registry),
        smoke_valid=sum(bool(row["smoke_valid"]) for row in registry),
        failures=len(failures),
    )
    return receipt


def _signature_lookups(settings: Settings, epoch: int) -> tuple[dict[str, str], dict[str, str]]:
    atlas = {}
    for line in (settings.run_root / "novelty/atlas_registry.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        atlas[str(row["numeric_signature"])] = str(row["name"])
    earlier = {}
    for prior_epoch in range(1, epoch):
        for receipt_path in sorted(
            (settings.run_root / f"matrices/validated/epoch-{prior_epoch:02d}").glob("*/receipt.json")
        ):
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            train = pd.read_parquet(receipt_path.parent / "train.parquet")
            test = pd.read_parquet(receipt_path.parent / "test.parquet")
            for feature_id in receipt["accepted_columns"]:
                earlier[
                    numeric_signature(pd.concat([train[feature_id], test[feature_id]], ignore_index=True).to_numpy(float))
                ] = feature_id
    return atlas, earlier


def _execute_spec_group(paths: Sequence[str]) -> dict[str, Any]:
    context = _EXECUTION_CONTEXT
    root = Path(context["root"])
    cards = context["cards"]
    cache = PrimitiveCache(root / "cache/execution")
    compiler = TrustedCompiler(cache)
    local_seen = dict(context["earlier"])
    completed = []
    failures = []
    for path_string in paths:
        path = Path(path_string)
        try:
            started = time.perf_counter()
            raw_spec = json.loads(path.read_text(encoding="utf-8"))
            raw_card = cards[(raw_spec["domain"], raw_spec["family_slug"])]
            card = {field: raw_card[field] for field in FAMILY_FIELDS}
            spec = {field: raw_spec[field] for field in SPEC_FIELDS}
            spec["outputs"] = [
                {field: output[field] for field in OUTPUT_FIELDS} for output in raw_spec["outputs"]
            ]
            compiled = compiler.compile(card, spec, source_role_id=raw_spec["source_role_id"])
            for column, output in zip(compiled.columns, raw_spec["outputs"], strict=True):
                column["feature_id"] = output["feature_id"]
            train = compiler.compute_matrix(compiled, context["train_structures"], context["train_ids"])
            test = compiler.compute_matrix(compiled, context["test_structures"], context["test_ids"])
            rerun_train = compiler.compute_matrix(
                compiled, context["train_structures"], context["train_ids"]
            )
            rerun_test = compiler.compute_matrix(compiled, context["test_structures"], context["test_ids"])
            invariance = run_invariance_tests(
                context["sample_structures"],
                lambda transformed, item=compiled: compiler.compute_family(item, transformed),
            )
            quarantined = quarantine_columns(
                train,
                test,
                expected_train_ids=context["train_ids"],
                expected_test_ids=context["test_ids"],
                rerun_train=rerun_train,
                rerun_test=rerun_test,
                invariance_report=invariance,
                atlas_numeric_signatures=context["atlas"],
                earlier_v2_signatures=local_seen,
            )
            local_seen.update({signature: feature for feature, signature in quarantined.signatures.items()})
            output = root / f"matrices/validated/epoch-{context['epoch']:02d}/{raw_spec['spec_id']}"
            output.mkdir(parents=True, exist_ok=True)
            train_path = output / "train.parquet"
            test_path = output / "test.parquet"
            quarantined.train.to_parquet(train_path, index=False)
            quarantined.test.to_parquet(test_path, index=False)
            receipt = {
                "epoch": context["epoch"],
                "spec_id": raw_spec["spec_id"],
                "family_id": raw_card["family_id"],
                "domain": raw_spec["domain"],
                "train_rows": 2_400,
                "test_rows": 600,
                "invariance_structures": 64,
                "all_five_invariances": True,
                "deterministic": True,
                "attempted_columns": len(compiled.columns),
                "accepted_columns": list(quarantined.accepted),
                "rejections": [rejection.__dict__ for rejection in quarantined.rejected],
                "numeric_signatures": quarantined.signatures,
                "train_sha256": sha256_file(train_path),
                "test_sha256": sha256_file(test_path),
                "compute_seconds": time.perf_counter() - started,
                "test_labels_used": False,
            }
            atomic_json(output / "receipt.json", receipt)
            completed.append(raw_spec["spec_id"])
        except Exception as error:  # Per-spec quarantine must preserve valid siblings.
            failures.append({"spec": path.name, "error": f"{type(error).__name__}: {error}"})
    return {"completed": completed, "failures": failures}


def _reconcile_epoch_duplicates(settings: Settings, epoch: int) -> None:
    atlas, seen = _signature_lookups(settings, epoch)
    seen = {**atlas, **seen}
    for receipt_path in sorted(
        (settings.run_root / f"matrices/validated/epoch-{epoch:02d}").glob("*/receipt.json")
    ):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        train_path = receipt_path.parent / "train.parquet"
        test_path = receipt_path.parent / "test.parquet"
        train = pd.read_parquet(train_path)
        test = pd.read_parquet(test_path)
        accepted = []
        signatures = {}
        rejections = list(receipt.get("rejections", []))
        for feature_id in receipt.get("accepted_columns", []):
            signature = numeric_signature(
                pd.concat([train[feature_id], test[feature_id]], ignore_index=True).to_numpy(float)
            )
            if signature in seen:
                rejections.append(
                    {
                        "column": feature_id,
                        "reason": "exact_numeric_duplicate",
                        "duplicate_of": seen[signature],
                    }
                )
                continue
            seen[signature] = feature_id
            accepted.append(feature_id)
            signatures[feature_id] = signature
        if accepted != receipt.get("accepted_columns", []):
            train = train[["id", *accepted]]
            test = test[["id", *accepted]]
            train.to_parquet(train_path, index=False)
            test.to_parquet(test_path, index=False)
        receipt["accepted_columns"] = accepted
        receipt["numeric_signatures"] = signatures
        receipt["rejections"] = rejections
        receipt["train_sha256"] = sha256_file(train_path)
        receipt["test_sha256"] = sha256_file(test_path)
        atomic_json(receipt_path, receipt)


def _execute(settings: Settings, store: CampaignStore, epoch: int, groups: Mapping[str, Sequence[Path]]) -> dict[str, Any]:
    root = settings.run_root
    train_frame = pd.read_csv(root / "inputs/public/train.csv")
    test_frame = pd.read_csv(root / "inputs/public/test.csv")
    _emit("structure_load_started", epoch=epoch)
    train_structures = load_structures(train_frame, root / "inputs/public/train_geometry")
    test_structures = load_structures(test_frame, root / "inputs/public/test_geometry")
    sample_ids = deterministic_real_sample(train_frame["id"].tolist(), 64, seed=4319 + epoch)
    by_id = dict(zip(train_frame["id"].tolist(), train_structures, strict=True))
    atlas, earlier = _signature_lookups(settings, epoch)
    global _EXECUTION_CONTEXT
    _EXECUTION_CONTEXT = {
        "root": str(root),
        "epoch": epoch,
        "cards": _cards(settings, epoch),
        "train_structures": train_structures,
        "test_structures": test_structures,
        "sample_structures": [by_id[identifier] for identifier in sample_ids],
        "train_ids": train_frame["id"].tolist(),
        "test_ids": test_frame["id"].tolist(),
        "atlas": atlas,
        "earlier": earlier,
    }
    done = {
        path.parent.name
        for path in (root / f"matrices/validated/epoch-{epoch:02d}").glob("*/receipt.json")
    }
    todo = [
        [str(path) for path in paths if json.loads(path.read_text(encoding="utf-8"))["spec_id"] not in done]
        for paths in groups.values()
    ]
    todo = [paths for paths in todo if paths]
    failures = []
    if todo:
        workers = min(8, len(todo), max(os.cpu_count() or 1, 1))
        with ProcessPoolExecutor(max_workers=workers, mp_context=get_context("fork")) as pool:
            futures = [pool.submit(_execute_spec_group, paths) for paths in todo]
            for future in as_completed(futures):
                result = future.result()
                failures.extend(result["failures"])
                _emit(
                    "execution_group_complete",
                    epoch=epoch,
                    completed=len(result["completed"]),
                    failures=len(result["failures"]),
                )
    _reconcile_epoch_duplicates(settings, epoch)
    receipts = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((root / f"matrices/validated/epoch-{epoch:02d}").glob("*/receipt.json"))
    ]
    with store.connect() as connection:
        for receipt in receipts:
            accepted = set(receipt["accepted_columns"])
            rejected = {row["column"]: row["reason"] for row in receipt["rejections"]}
            for feature_id in [*accepted, *rejected]:
                connection.execute(
                    "UPDATE columns SET executed=1,novel=?,valid=?,rejection_reason=? WHERE feature_id=?",
                    (
                        int(feature_id in accepted),
                        int(feature_id in accepted),
                        rejected.get(feature_id),
                        feature_id,
                    ),
                )
    phase = {
        "epoch": epoch,
        "smoke_structures": 16,
        "invariance_structures": 64,
        "train_rows": 2_400,
        "test_rows": 600,
        "all_five_invariances": True,
        "deterministic": True,
        "individual_column_quarantine": True,
        "test_labels_used": False,
        "executed_columns": sum(int(receipt["attempted_columns"]) for receipt in receipts),
        "novel_valid_columns": sum(len(receipt["accepted_columns"]) for receipt in receipts),
        "matrices": len(receipts),
        "execution_failures": failures,
        "matrix_receipts": {
            receipt["spec_id"]: sha256_file(
                root / f"matrices/validated/epoch-{epoch:02d}/{receipt['spec_id']}/receipt.json"
            )
            for receipt in receipts
        },
    }
    _seal_phase(settings, store, f"epoch-{epoch:02d}-execution", phase)
    _emit(
        "execution_complete",
        epoch=epoch,
        executed=phase["executed_columns"],
        novel_valid=phase["novel_valid_columns"],
        matrices=phase["matrices"],
        failures=len(failures),
    )
    return phase


def _family_candidates(settings: Settings, epoch: int) -> dict[str, FamilyCandidate]:
    cards_by_id = {
        card["family_id"]: card for card in _cards(settings, epoch).values()
    }
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"frames": [], "seconds": 0.0})
    for receipt_path in sorted(
        (settings.run_root / f"matrices/validated/epoch-{epoch:02d}").glob("*/receipt.json")
    ):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        if not receipt["accepted_columns"]:
            continue
        grouped[str(receipt["family_id"])]["frames"].append(
            pd.read_parquet(receipt_path.parent / "train.parquet")
        )
        grouped[str(receipt["family_id"])]["seconds"] += float(receipt["compute_seconds"])
    candidates = {}
    for family_id, value in grouped.items():
        matrix = value["frames"][0]
        for frame in value["frames"][1:]:
            matrix = matrix.merge(frame, on="id", validate="one_to_one")
        card = cards_by_id[family_id]
        key = f"{card['domain']}:{card['family_slug']}"
        candidates[key] = FamilyCandidate(
            str(card["family_slug"]),
            str(card["domain"]),
            matrix,
            float(value["seconds"]),
            card["target_affinity"],
        )
    return candidates


def _screen(
    settings: Settings, store: CampaignStore, epoch: int, *, final: bool
) -> tuple[dict[str, Any], dict[str, FamilyCandidate]]:
    candidates = _family_candidates(settings, epoch)
    if not candidates:
        raise CampaignError(f"epoch {epoch} has no valid family matrices to screen")
    suffix = "final" if final else "initial"
    output_dir = settings.run_root / f"score_curves/epoch-{epoch:02d}-{suffix}"
    result_path = output_dir / "controller_results.json"
    payload = (
        json.loads(result_path.read_text(encoding="utf-8"))
        if result_path.exists()
        else score_discovery(
            atlas_bundle=settings.run_root / "inputs/atlas",
            families=candidates,
            output_dir=output_dir,
        )
    )
    if final:
        phase = {
            "epoch": epoch,
            "protocol": {**payload["protocol"], "task_type": "GPU"},
            "ranking_metrics": [
                "compute_cost",
                "redundancy",
                "oof_residual_correlation",
                "spearman_correlation",
                "mutual_information",
                "catboost_importance",
            ],
            "adaptive_feedback": "categorical_only",
            "families_scored": len(payload["families"]),
            "ranking_records": len(payload["ranking"]),
            "results_sha256": sha256_file(result_path),
        }
        _seal_phase(settings, store, f"epoch-{epoch:02d}-screening", phase)
    _emit(
        "screening_complete",
        epoch=epoch,
        stage=suffix,
        families=len(payload["families"]),
        best_lift=max((float(row["lift"]) for row in payload["families"]), default=None),
    )
    return payload, candidates


def _dispatch_adaptive(
    settings: Settings,
    store: CampaignStore,
    epoch: int,
    score: Mapping[str, Any],
) -> None:
    roles = _pending_roles(
        store, epoch, {"target_exploiter", "cross_family_synthesizer"}
    )
    if not roles:
        return
    cards = {
        f"{card['domain']}:{card['family_slug']}": card
        for card in _cards(settings, epoch).values()
    }
    rows = list(score["families"])
    feedback = {
        (str(row["target"]), str(row["family_key"])): categorical_discovery_feedback(
            lift=float(row["lift"]),
            redundancy=float(row["redundancy"]),
            compute_seconds=float(row["compute_seconds"]),
            residual_correlation=float(row["residual_correlation"]),
        )
        for row in rows
    }
    by_target = {
        target: [
            str(row["family_key"])
            for row in sorted(rows, key=lambda item: -float(item["lift"]))
            if row["target"] == target and str(row["family_key"]) in cards
        ]
        for target in TARGETS
    }
    all_keys = list(dict.fromkeys(key for values in by_target.values() for key in values))
    if not all_keys:
        all_keys = sorted(cards)
    prompts = {}
    for role_index, role in enumerate(roles):
        choices = by_target.get(str(role.get("target")), []) or all_keys
        selected = (
            [choices[role_index % len(choices)], choices[(role_index + 1) % len(choices)]]
            if role["class"] == "target_exploiter"
            else [all_keys[role_index % len(all_keys)], all_keys[(role_index + 1) % len(all_keys)]]
        )
        assignments = []
        packet: dict[str, Any] = {}
        for side, key in enumerate(selected):
            card = cards[key]
            kernel = str(card["kernel"])
            assignments.append(
                {
                    "spec_index": side + 1,
                    "domain": card["domain"],
                    "family_slug": card["family_slug"],
                    "kernel": kernel,
                    "spec_slug": f"e{epoch:02d}-adaptive-{role_index + 1:02d}-{'ab'[side]}",
                    "name_prefix": "ab"[side],
                    "parameter_sets": [
                        {
                            "id": f"p{index + 1}",
                            "values": _kernel_config(
                                kernel, epoch, 20 + role_index * 2 + side, index
                            ),
                            "physical_justification": "Controller-preregistered adaptive physical resolution.",
                        }
                        for index in range(3)
                    ],
                }
            )
            packet[key] = {
                "card": card,
                "categorical_feedback": feedback.get(
                    (str(role.get("target")), key),
                    next(
                        (value for (target, family), value in feedback.items() if family == key),
                        {
                            "discovery_lift": "neutral",
                            "redundancy": "medium",
                            "compute_cost": "medium",
                            "residual_alignment": "medium",
                        },
                    ),
                ),
                "operation_registry": list(KERNEL_OPERATIONS[kernel])[:8],
            }
        packet["controller_spec_contract"] = {
            "assignments": assignments,
            "outputs_per_spec": 8,
            "aggregation": "raw",
            "instructions": (
                "Return exactly two specs with exactly 8 outputs each. Use assignment values "
                "exactly. For each family use all 8 operation_registry entries once, p1/p2/p3 "
                "cyclically, equation <=40 chars, unit <=12 chars, interpretation <=12 words. "
                "Emit minified strict JSON only."
            ),
        }
        family_feedback = {key: packet[key]["categorical_feedback"] for key in selected}
        prompts[str(role["id"])] = build_epoch_prompt(
            role, {"family_feedback": family_feedback, "family_cards": packet}
        )
    result = dispatch_role_wave(
        settings, store, roles, prompts, epoch=epoch, wave_id="adaptive-10"
    )
    _emit("adaptive_wave_complete", epoch=epoch, result=result)


def _reduce(
    settings: Settings,
    store: CampaignStore,
    epoch: int,
    discovery: Mapping[str, Any],
) -> dict[str, Any]:
    cards = {card["family_id"]: card for card in _cards(settings, epoch).values()}
    features: dict[str, list[str]] = defaultdict(list)
    for receipt_path in sorted(
        (settings.run_root / f"matrices/validated/epoch-{epoch:02d}").glob("*/receipt.json")
    ):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        card = cards[str(receipt["family_id"])]
        features[f"{card['domain']}:{card['family_slug']}"].extend(receipt["accepted_columns"])
    counts = {}
    for target_index, target in enumerate(TARGETS):
        rows = [row for row in discovery["families"] if row["target"] == target]
        weights = {
            str(row["family_key"]): max(float(row["normalized_importance"]), 1e-6)
            + max(float(row["lift"]), -0.001)
            for row in rows
        }
        universe = [feature for family in weights for feature in features.get(family, [])]
        family_of = {
            feature: family for family in weights for feature in features.get(family, [])
        }
        if len(universe) < 4:
            raise CampaignError(f"epoch {epoch} has too few valid features for {target} reduction")
        rng = np.random.default_rng(7919 + epoch * 10 + target_index)
        population = []
        while len(population) < GENETIC_POPULATION:
            size = int(rng.integers(4, min(30, len(universe)) + 1))
            candidate = tuple(sorted(rng.choice(universe, size, replace=False).tolist()))
            if candidate not in population:
                population.append(candidate)
        history = []
        all_ranked = []
        for generation in range(GENETIC_GENERATIONS):
            def fitness(candidate: Sequence[str]) -> float:
                return sum(weights[family_of[feature]] for feature in candidate) / len(candidate) ** 0.5 + 0.01 * len(
                    {family_of[feature] for feature in candidate}
                )

            ranked = sorted(
                ((fitness(candidate), candidate) for candidate in population),
                key=lambda item: (-item[0], len(item[1]), item[1]),
            )
            all_ranked.extend(ranked)
            population_dir = settings.run_root / f"genetic/populations/epoch-{epoch:02d}/{target}"
            population_dir.mkdir(parents=True, exist_ok=True)
            population_path = population_dir / f"generation-{generation + 1:02d}.json"
            atomic_json(
                population_path,
                {
                    "generation": generation + 1,
                    "population_size": GENETIC_POPULATION,
                    "members": [
                        {
                            "feature_ids": list(candidate),
                            "fitness": score,
                            "families": sorted({family_of[feature] for feature in candidate}),
                        }
                        for score, candidate in ranked
                    ],
                },
            )
            history.append(
                {
                    "generation": generation + 1,
                    "best_fitness": ranked[0][0],
                    "best_feature_count": len(ranked[0][1]),
                    "best_family_count": len({family_of[feature] for feature in ranked[0][1]}),
                    "population_sha256": sha256_file(population_path),
                }
            )
            elite = [candidate for _score, candidate in ranked[:8]]
            next_population = list(elite)
            seen = set(elite)
            while len(next_population) < GENETIC_POPULATION:
                child = set(elite[int(rng.integers(len(elite)))])
                feature = universe[int(rng.integers(len(universe)))]
                if feature in child and len(child) > 4:
                    child.remove(feature)
                else:
                    child.add(feature)
                candidate = tuple(sorted(child))
                if candidate not in seen:
                    seen.add(candidate)
                    next_population.append(candidate)
            population = next_population
        unique = []
        seen_candidates = set()
        for score, candidate in sorted(
            all_ranked, key=lambda item: (-item[0], len(item[1]), item[1])
        ):
            if candidate in seen_candidates:
                continue
            seen_candidates.add(candidate)
            unique.append((score, candidate))
            if len(unique) == 8:
                break
        views = [
            {
                "view_id": f"e{epoch:02d}-{target_index + 1}-ga-{index + 1:02d}",
                "feature_ids": list(candidate),
                "feature_count": len(candidate),
                "families": sorted({family_of[feature] for feature in candidate}),
                "diversity_aware": index > 0,
                "proxy_fitness": score,
            }
            for index, (score, candidate) in enumerate(unique)
        ]
        receipt = {
            "target": target,
            "population_size": GENETIC_POPULATION,
            "generations": GENETIC_GENERATIONS,
            "seed": 7919 + epoch * 10 + target_index,
            "history": history,
            "preregistered_views": views,
        }
        receipt_path = settings.run_root / f"receipts/genetic/epoch-{epoch:02d}-{target}.json"
        write_receipt(receipt_path, "genetic_reduction_history", receipt)
        validate_genetic_history(json.loads(receipt_path.read_text(encoding="utf-8")))
        counts[target] = len(views)
    phase = {
        "epoch": epoch,
        "population_size": GENETIC_POPULATION,
        "generations": GENETIC_GENERATIONS,
        "preregistered_views_per_target": counts,
        "confirmation_still_sealed": True,
        "receipts": {
            target: sha256_file(
                settings.run_root / f"receipts/genetic/epoch-{epoch:02d}-{target}.json"
            )
            for target in TARGETS
        },
    }
    _seal_phase(settings, store, f"epoch-{epoch:02d}-reduction", phase)
    _emit("reduction_complete", epoch=epoch, views=counts)
    return phase


def _dispatch_plugins(settings: Settings, store: CampaignStore, epoch: int) -> list[dict[str, Any]]:
    roles = _pending_roles(store, epoch, {"bounded_plugin_writer"})
    if roles:
        tasks = [
            {
                "family_slug": f"epoch-{epoch:02d}-composition-quantiles",
                "task": "compute_family returns eight finite composition distribution scalars invariant to replication and site order",
            },
            {
                "family_slug": f"epoch-{epoch:02d}-lattice-density-couplings",
                "task": "compute_family returns eight finite lattice-density couplings invariant to all five declared transforms",
            },
        ]
        prompts = {
            str(role["id"]): build_epoch_prompt(
                role,
                {
                    **task,
                    "source_contract": [
                        "imports only numpy/math/statistics",
                        "exact compute_family(structure, config) signature",
                        "eight scalar dict outputs",
                        "no labels/network/files/dynamic execution",
                    ],
                    "adversarial_tests_required": [
                        "translation",
                        "rotation",
                        "permutation",
                        "wrapping",
                        "equivalent cell",
                        "determinism",
                    ],
                },
            )
            for role, task in zip(roles, tasks, strict=False)
        }
        result = dispatch_role_wave(
            settings, store, roles, prompts, epoch=epoch, wave_id="plugin-writers-2"
        )
        _emit("plugin_wave_complete", epoch=epoch, result=result)
    sandbox_results = []
    for plugin in sorted((settings.run_root / f"plugins/epoch-{epoch:02d}").glob("*.py")):
        output = settings.run_root / f"receipts/sandbox/epoch-{epoch:02d}-{plugin.stem}"
        output.mkdir(parents=True, exist_ok=True)
        output.chmod(0o777)
        try:
            process = subprocess.run(
                plugin_sandbox_command(
                    image=settings.image,
                    plugin=plugin,
                    harness=settings.run_root / "inputs/controller/plugin_runner.py",
                    structures=settings.run_root / "inputs/public/train_geometry",
                    output=output,
                ),
                text=True,
                capture_output=True,
                timeout=1_800,
                check=False,
            )
            receipt = (
                json.loads((output / "receipt.json").read_text(encoding="utf-8"))
                if (output / "receipt.json").exists()
                else None
            )
            sandbox_results.append(
                {
                    "plugin": plugin.name,
                    "returncode": process.returncode,
                    "receipt": receipt,
                    "quarantined": process.returncode != 0,
                }
            )
        finally:
            output.chmod(0o750)
    atomic_json(
        settings.run_root / f"receipts/sandbox/epoch-{epoch:02d}-summary.json",
        {"epoch": epoch, "plugins": sandbox_results},
    )
    return sandbox_results


def _dispatch_testers_and_judges(
    settings: Settings,
    store: CampaignStore,
    epoch: int,
    sandbox_results: Sequence[Mapping[str, Any]],
) -> None:
    testers = _pending_roles(store, epoch, {"adversarial_tester"})
    if testers:
        execution_path = settings.run_root / f"receipts/phases/epoch-{epoch:02d}-execution.json"
        contexts = [
            {
                "tested_artifacts": sandbox_results or [{"artifact_id": "no-valid-plugin"}],
                "required_attacks": [
                    "API misuse",
                    "network",
                    "labels",
                    "five invariances",
                    "determinism",
                ],
                "instruction": "Return only tested_artifact_ids, attacks, findings arrays; quarantine failures.",
            },
            {
                "tested_artifacts": [
                    {
                        "artifact_id": f"epoch-{epoch:02d}-execution",
                        "sha256": sha256_file(execution_path),
                    }
                ],
                "required_attacks": [
                    "2400/600 alignment",
                    "numeric duplicates",
                    "nonfinite",
                    "five invariances",
                    "rerun determinism",
                    "test labels",
                ],
                "instruction": "Return only tested_artifact_ids, attacks, findings arrays.",
            },
        ]
        prompts = {
            str(role["id"]): build_epoch_prompt(role, context)
            for role, context in zip(testers, contexts, strict=False)
        }
        result = dispatch_role_wave(
            settings, store, testers, prompts, epoch=epoch, wave_id="adversarial-testers-2"
        )
        _emit("tester_wave_complete", epoch=epoch, result=result)
    judges = _pending_roles(store, epoch, {"blind_judge"})
    if judges:
        receipts = [
            {
                "receipt_id": f"epoch-{epoch:02d}-{name}",
                "sha256": sha256_file(
                    settings.run_root / f"receipts/phases/epoch-{epoch:02d}-{name}.json"
                ),
            }
            for name in ("execution", "screening", "reduction")
        ]
        contexts = [
            {
                "available_receipts": receipts,
                "specialty": "physics and novelty",
                "instruction": "Return only receipt_ids and judgments nonempty arrays; infer no exact scores.",
            },
            {
                "available_receipts": receipts,
                "specialty": "leakage and reproducibility",
                "instruction": "Return only receipt_ids and judgments nonempty arrays; infer no exact scores.",
            },
        ]
        prompts = {
            str(role["id"]): build_epoch_prompt(role, context)
            for role, context in zip(judges, contexts, strict=False)
        }
        result = dispatch_role_wave(
            settings, store, judges, prompts, epoch=epoch, wave_id="blind-judges-2"
        )
        _emit("judge_wave_complete", epoch=epoch, result=result)


def _finalize_epoch(settings: Settings, store: CampaignStore, epoch: int) -> dict[str, Any]:
    with store.connect() as connection:
        attempts = int(
            connection.execute(
                "SELECT COUNT(*) FROM attempts WHERE role_id LIKE ?", (f"zyal10.e{epoch:02d}.%",)
            ).fetchone()[0]
        )
        states = {
            str(row[0]): int(row[1])
            for row in connection.execute(
                "SELECT status,COUNT(*) FROM roles WHERE epoch=? GROUP BY status", (epoch,)
            )
        }
        rows = list(
            connection.execute(
                "SELECT domain,SUM(executed),SUM(novel AND valid) FROM columns WHERE epoch=? GROUP BY domain",
                (epoch,),
            )
        )
        families = int(
            connection.execute(
                "SELECT COUNT(*) FROM families WHERE epoch=? AND valid=1", (epoch,)
            ).fetchone()[0]
        )
        reported_cost = float(
            connection.execute(
                "SELECT COALESCE(SUM(reported_cost_usd),0) FROM attempts WHERE role_id LIKE ?",
                (f"zyal10.e{epoch:02d}.%",),
            ).fetchone()[0]
        )
    generation = {
        "epoch": epoch,
        "roles": 36,
        "attempts": attempts,
        "valid_roles": states.get("complete", 0),
        "exhausted_roles": states.get("exhausted", 0),
        "max_retries_per_role": 1,
        "strict_json": True,
        "controller_generated_ids": True,
        "prompt_limit_bytes": 12_288,
        "output_limit_bytes": 20_480,
        "actual_reported_cost_usd": reported_cost,
    }
    generation_path = _seal_phase(
        settings, store, f"epoch-{epoch:02d}-generation", generation
    )
    phases = {
        name: sha256_file(
            settings.run_root / f"receipts/phases/epoch-{epoch:02d}-{name}.json"
        )
        for name in ("generation", "compilation", "execution", "screening", "reduction")
    }
    result = {
        "epoch": epoch,
        "roles": 36,
        "attempts": attempts,
        "new_executed_columns": sum(int(row[1] or 0) for row in rows),
        "novel_valid_columns": sum(int(row[2] or 0) for row in rows),
        "valid_by_domain": {str(row[0]): int(row[2] or 0) for row in rows},
        "base_families": families,
        "phase_receipts": phases,
    }
    epoch_path = settings.run_root / f"receipts/epochs/epoch-{epoch:02d}.json"
    write_receipt(epoch_path, "epoch_result", result)
    _emit(
        "epoch_complete",
        epoch=epoch,
        result=result,
        generation_receipt_sha256=sha256_file(generation_path),
    )
    return result


def run_epoch(settings: Settings, epoch: int) -> dict[str, Any]:
    store = CampaignStore(settings)
    epoch_receipt = settings.run_root / f"receipts/epochs/epoch-{epoch:02d}.json"
    if epoch_receipt.exists():
        return json.loads(epoch_receipt.read_text(encoding="utf-8"))
    store.recover_interrupted_leases()
    _emit("epoch_started", epoch=epoch)
    _dispatch_architects(settings, store, epoch)
    _dispatch_builders(settings, store, epoch)
    groups = _expand_specs(settings, epoch)
    _compile(settings, store, epoch)
    _execute(settings, store, epoch, groups)
    initial, _candidates = _screen(settings, store, epoch, final=False)
    _dispatch_adaptive(settings, store, epoch, initial)
    groups = _expand_specs(settings, epoch)
    _compile(settings, store, epoch)
    _execute(settings, store, epoch, groups)
    final, _candidates = _screen(settings, store, epoch, final=True)
    _reduce(settings, store, epoch, final)
    sandbox = _dispatch_plugins(settings, store, epoch)
    _dispatch_testers_and_judges(settings, store, epoch, sandbox)
    return _finalize_epoch(settings, store, epoch)


def run_remaining_epochs(
    settings: Settings, *, start_epoch: int = 1, end_epoch: int = 10
) -> list[dict[str, Any]]:
    if not 1 <= start_epoch <= end_epoch <= 10:
        raise ValueError("epoch range must be within 1..10")
    return [run_epoch(settings, epoch) for epoch in range(start_epoch, end_epoch + 1)]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Live NOMAD ZYAL v2.1 epoch materializer")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--start-epoch", type=int, default=1)
    parser.add_argument("--end-epoch", type=int, default=10)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    settings = Settings(args.repo_root.resolve(), args.run_id)
    try:
        results = run_remaining_epochs(
            settings, start_epoch=args.start_epoch, end_epoch=args.end_epoch
        )
    except Exception as error:
        traceback.print_exc()
        _emit("campaign_error", error=f"{type(error).__name__}: {error}")
        return 2
    _emit("requested_epochs_complete", epochs=[result["epoch"] for result in results])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
