#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import socket
import subprocess
import sys

import numpy as np
import pandas as pd
from pymatgen.core import Lattice, Structure


TARGETS = {"formation_energy_ev_natom", "bandgap_energy_ev"}


def read_geometry(path: Path) -> Structure:
    lattice: list[list[float]] = []
    species: list[str] = []
    cartesian: list[list[float]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        parts = raw.split()
        if not parts or parts[0].startswith("#"):
            continue
        if parts[0] == "lattice_vector":
            lattice.append([float(value) for value in parts[1:4]])
        elif parts[0] == "atom":
            cartesian.append([float(value) for value in parts[1:4]])
            species.append(parts[4])
    if len(lattice) != 3 or not species:
        raise ValueError(f"invalid NOMAD geometry: {path}")
    return Structure(Lattice(lattice), species, cartesian, coords_are_cartesian=True, to_unit_cell=True)


def load_generator(path: Path):
    spec = importlib.util.spec_from_file_location("untrusted_generator", path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not callable(getattr(module, "featurize_structure", None)):
        raise ValueError("generator does not define featurize_structure")
    return module


def vector(module, structure: Structure) -> tuple[list[str], np.ndarray]:
    result = module.featurize_structure(structure)
    if not isinstance(result, dict) or not result:
        raise ValueError("featurize_structure must return a nonempty dict")
    keys = sorted(result)
    values = np.asarray([result[key] for key in keys], dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("featurize_structure returned nonfinite values")
    return keys, values


def same(module, reference: Structure, transformed: Structure) -> bool:
    left_keys, left = vector(module, reference)
    right_keys, right = vector(module, transformed)
    return left_keys == right_keys and bool(np.allclose(left, right, rtol=1e-8, atol=1e-10))


def transformations(structure: Structure) -> dict[str, Structure]:
    frac = np.asarray(structure.frac_coords)
    species = list(structure.species)
    translation = Structure(structure.lattice, species, frac + [0.137, -0.211, 0.083], to_unit_cell=True)
    permutation = Structure(structure.lattice, species[::-1], frac[::-1], to_unit_cell=True)
    wrapping_offsets = np.arange(len(structure))[:, None] * np.array([[1, -1, 2]])
    wrapping = Structure(structure.lattice, species, frac + wrapping_offsets, to_unit_cell=False)
    angle = 0.731
    rotation_matrix = np.array(
        [[math.cos(angle), -math.sin(angle), 0.0], [math.sin(angle), math.cos(angle), 0.0], [0.0, 0.0, 1.0]]
    )
    rotation = Structure(
        Lattice(np.asarray(structure.lattice.matrix) @ rotation_matrix.T),
        species,
        np.asarray(structure.cart_coords) @ rotation_matrix.T,
        coords_are_cartesian=True,
        to_unit_cell=True,
    )
    order = [1, 2, 0]
    equivalent = Structure(
        Lattice(np.asarray(structure.lattice.matrix)[order]),
        species,
        frac[:, order],
        to_unit_cell=True,
    )
    return {
        "translation": translation,
        "rotation": rotation,
        "atom_permutation": permutation,
        "periodic_wrapping": wrapping,
        "equivalent_cell": equivalent,
    }


def run_generator(generator: Path, inputs: Path, output: Path) -> None:
    command = [
        sys.executable,
        str(generator),
        "--train-csv",
        str(inputs / "train_public.csv"),
        "--test-csv",
        str(inputs / "test_public.csv"),
        "--train-geometry",
        str(inputs / "train_geometry"),
        "--test-geometry",
        str(inputs / "test_geometry"),
        "--output",
        str(output),
    ]
    subprocess.run(command, check=True, timeout=6_800)


def security_checks(inputs: Path) -> dict[str, bool]:
    network_blocked = False
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=1):
            pass
    except OSError:
        network_blocked = True
    columns = set(pd.read_csv(inputs / "train_public.csv", nrows=1).columns)
    labels_absent = not bool(columns & TARGETS)
    forbidden_host_file_absent = not Path("/home/ubuntu/nomad/labeled_test.csv").exists()
    secret_names = {name for name in os.environ if any(token in name.upper() for token in ("TOKEN", "SECRET", "PASSWORD", "API_KEY"))}
    return {
        "network_blocked": network_blocked,
        "public_labels_absent": labels_absent,
        "forbidden_host_file_absent": forbidden_host_file_absent,
        "host_secrets_absent": not secret_names,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--real-sample-id", type=int, required=True)
    args = parser.parse_args()
    checks = security_checks(args.inputs)
    if not all(checks.values()):
        raise RuntimeError(f"sandbox security checks failed: {checks}")
    run_generator(args.generator, args.inputs, args.output)
    rerun = args.output / "rerun"
    rerun.mkdir(parents=True, exist_ok=True)
    run_generator(args.generator, args.inputs, rerun)
    module = load_generator(args.generator)
    toy = Structure(
        Lattice.cubic(4.3),
        ["Al", "Ga", "In", "O", "O", "O"],
        [[0, 0, 0], [0.5, 0.5, 0], [0.5, 0, 0.5], [0.25, 0.25, 0.25], [0.75, 0.75, 0.25], [0.25, 0.75, 0.75]],
    )
    real = read_geometry(args.inputs / "train_geometry" / str(args.real_sample_id) / "geometry.xyz")
    results: dict[str, bool] = {}
    for name in transformations(toy):
        results[name] = same(module, toy, transformations(toy)[name]) and same(module, real, transformations(real)[name])
    (args.output / "invariance.json").write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
    (args.output / "sandbox_security.json").write_text(json.dumps(checks, indent=2, sort_keys=True) + "\n")
    if not all(results.values()):
        raise RuntimeError(f"invariance tests failed: {results}")


if __name__ == "__main__":
    main()
