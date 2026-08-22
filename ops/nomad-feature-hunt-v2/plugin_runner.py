from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
from pymatgen.core import Lattice, Structure


def read_geometry(path: Path) -> Structure:
    lattice: list[list[float]] = []
    species: list[str] = []
    coordinates: list[list[float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "lattice_vector":
            lattice.append([float(value) for value in parts[1:4]])
        elif parts[0] == "atom":
            coordinates.append([float(value) for value in parts[1:4]])
            species.append(parts[4])
    if len(lattice) != 3 or not species:
        raise ValueError(f"invalid geometry: {path}")
    return Structure(
        Lattice(lattice), species, coordinates, coords_are_cartesian=True, to_unit_cell=True
    )


def variants(structure: Structure) -> dict[str, Structure]:
    frac = np.asarray(structure.frac_coords, dtype=float)
    rotation = np.asarray([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    translated = Structure(
        structure.lattice,
        structure.species,
        np.asarray(structure.cart_coords) + [1.234, -0.456, 2.345],
        coords_are_cartesian=True,
    )
    rotated = Structure(np.asarray(structure.lattice.matrix) @ rotation.T, structure.species, frac)
    order = list(range(len(structure) - 1, -1, -1))
    permuted = Structure(
        structure.lattice, [structure.species[index] for index in order], frac[order]
    )
    offsets = np.arange(len(structure))[:, None] * np.asarray([[1.0, -1.0, 2.0]])
    wrapped = Structure(structure.lattice, structure.species, frac + offsets)
    equivalent = structure.copy()
    equivalent.make_supercell([2, 1, 1])
    return {
        "translation": translated,
        "rotation": rotated,
        "atom_permutation": permuted,
        "periodic_wrapping": wrapped,
        "equivalent_cell": equivalent,
    }


def normalized(result: Any) -> dict[str, float]:
    if not isinstance(result, dict) or not 8 <= len(result) <= 25:
        raise ValueError("compute_family must return 8..25 scalar outputs")
    output: dict[str, float] = {}
    for key, value in result.items():
        numeric = float(value)
        if not isinstance(key, str) or not key or not math.isfinite(numeric):
            raise ValueError("compute_family returned an invalid key or nonfinite scalar")
        output[key] = numeric
    return output


def geometry_map(directory: Path) -> dict[str, Path]:
    return {path.parent.name: path for path in directory.glob("*/geometry.xyz")}


def compute_columns(
    compute_family: Any, structure: Structure, columns: list[dict[str, Any]]
) -> dict[str, float]:
    cached: dict[str, dict[str, float]] = {}
    row: dict[str, float] = {}
    for column in columns:
        config = column["configuration"]
        key = json.dumps(config, sort_keys=True, separators=(",", ":"))
        if key not in cached:
            cached[key] = normalized(compute_family(structure, config))
        values = cached[key]
        plugin_key = str(column.get("plugin_key") or column["operation"])
        if plugin_key not in values:
            raise ValueError(f"custom plugin omitted declared output: {plugin_key}")
        row[str(column["feature_id"])] = values[plugin_key]
    return row


def write_rows(path: Path, rows: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            line = json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            handle.write(line)
            digest.update(line.encode())
    return digest.hexdigest()


def run_full(module: Any, args: argparse.Namespace) -> int:
    specification = json.loads(args.specification.read_text(encoding="utf-8"))
    if set(specification) != {"train_ids", "test_ids", "invariance_ids", "columns"}:
        raise ValueError("invalid controller specification fields")
    columns = specification["columns"]
    if not isinstance(columns, list) or not 8 <= len(columns) <= 25:
        raise ValueError("full custom execution requires 8..25 declared columns")
    train_paths = geometry_map(args.train_structures)
    test_paths = geometry_map(args.test_structures)

    def split_rows(ids: list[Any], paths: dict[str, Path]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for identifier in ids:
            path = paths.get(str(identifier))
            if path is None:
                raise ValueError(f"geometry is missing for controller row ID {identifier}")
            values = compute_columns(module.compute_family, read_geometry(path), columns)
            rows.append({"id": identifier, **values})
        return rows

    first_train = split_rows(specification["train_ids"], train_paths)
    first_test = split_rows(specification["test_ids"], test_paths)
    rerun_train = split_rows(specification["train_ids"], train_paths)
    rerun_test = split_rows(specification["test_ids"], test_paths)
    deterministic = first_train == rerun_train and first_test == rerun_test
    invariances = {
        name: {str(column["feature_id"]): True for column in columns}
        for name in (
            "translation",
            "rotation",
            "atom_permutation",
            "periodic_wrapping",
            "equivalent_cell",
        )
    }
    for identifier in specification["invariance_ids"]:
        structure = read_geometry(train_paths[str(identifier)])
        baseline = compute_columns(module.compute_family, structure, columns)
        for invariant, transformed in variants(structure).items():
            candidate = compute_columns(module.compute_family, transformed, columns)
            for feature_id, value in baseline.items():
                invariances[invariant][feature_id] = invariances[invariant][
                    feature_id
                ] and bool(
                    feature_id in candidate
                    and np.isclose(value, candidate[feature_id], rtol=1e-7, atol=1e-9)
                )
    args.output.mkdir(parents=True, exist_ok=True)
    hashes = {
        "train.jsonl": write_rows(args.output / "train.jsonl", first_train),
        "test.jsonl": write_rows(args.output / "test.jsonl", first_test),
        "rerun_train.jsonl": write_rows(
            args.output / "rerun_train.jsonl", rerun_train
        ),
        "rerun_test.jsonl": write_rows(args.output / "rerun_test.jsonl", rerun_test),
    }
    (args.output / "invariance.json").write_text(
        json.dumps(invariances, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    receipt = {
        "mode": "full",
        "train_rows": len(first_train),
        "test_rows": len(first_test),
        "invariance_structures": len(specification["invariance_ids"]),
        "network": "none",
        "deterministic": deterministic,
        "invariances": {
            name: all(results.values()) for name, results in invariances.items()
        },
        "outputs": [str(column["feature_id"]) for column in columns],
        "files": hashes,
        "test_labels_used": False,
    }
    (args.output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0 if deterministic else 2


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin", type=Path, required=True)
    parser.add_argument("--mode", choices=("smoke", "full"), default="smoke")
    parser.add_argument("--structures", type=Path)
    parser.add_argument("--train-structures", type=Path)
    parser.add_argument("--test-structures", type=Path)
    parser.add_argument("--specification", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("foundry_plugin", args.plugin)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load plugin")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if args.mode == "full":
        if not args.train_structures or not args.test_structures or not args.specification:
            raise ValueError("full mode requires train/test structures and specification")
        return run_full(module, args)
    if not args.structures:
        raise ValueError("smoke mode requires structures")
    geometry_paths = sorted(
        args.structures.glob("*/geometry.xyz"),
        key=lambda path: int(path.parent.name),
    )[:16]
    if len(geometry_paths) != 16:
        raise ValueError("custom smoke requires exactly 16 selected real structures")
    invariances = {
        name: True
        for name in (
            "translation",
            "rotation",
            "atom_permutation",
            "periodic_wrapping",
            "equivalent_cell",
        )
    }
    deterministic = True
    output_names: set[str] | None = None
    toy = Structure(
        Lattice.cubic(4.2),
        ["Al", "O", "O"],
        [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25]],
    )
    toy_baseline = normalized(module.compute_family(toy, {}))
    toy_rerun = normalized(module.compute_family(toy, {}))
    deterministic = toy_baseline.keys() == toy_rerun.keys() and all(
        np.isclose(toy_baseline[key], toy_rerun[key], rtol=1e-7, atol=1e-9)
        for key in toy_baseline
    )
    for invariant, transformed in variants(toy).items():
        candidate = normalized(module.compute_family(transformed, {}))
        invariances[invariant] = toy_baseline.keys() == candidate.keys() and all(
            np.isclose(toy_baseline[key], candidate[key], rtol=1e-7, atol=1e-9)
            for key in toy_baseline
        )
    for path in geometry_paths:
        structure = read_geometry(path)
        baseline = normalized(module.compute_family(structure, {}))
        rerun = normalized(module.compute_family(structure, {}))
        deterministic = deterministic and baseline.keys() == rerun.keys() and all(
            np.isclose(baseline[key], rerun[key], rtol=1e-7, atol=1e-9) for key in baseline
        )
        output_names = set(baseline) if output_names is None else output_names & set(baseline)
        for invariant, transformed in variants(structure).items():
            candidate = normalized(module.compute_family(transformed, {}))
            invariances[invariant] = invariances[invariant] and baseline.keys() == candidate.keys()
            invariances[invariant] = invariances[invariant] and all(
                np.isclose(baseline[key], candidate[key], rtol=1e-7, atol=1e-9)
                for key in baseline
            )
    receipt = {
        "structures": 16,
        "network": "none",
        "toy": True,
        "deterministic": deterministic,
        "invariances": invariances,
        "outputs": sorted(output_names or []),
        "test_labels_used": False,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0 if deterministic and all(invariances.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
