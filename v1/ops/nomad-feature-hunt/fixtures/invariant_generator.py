from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def featurize_structure(structure):
    counts: dict[str, int] = {}
    for site in structure:
        symbol = str(site.specie)
        counts[symbol] = counts.get(symbol, 0) + 1
    fractions = np.asarray(list(counts.values()), dtype=float) / len(structure)
    entropy = float(-np.sum(fractions * np.log(np.clip(fractions, 1e-15, None))))
    return {
        "fixture_composition_entropy": entropy,
        "fixture_volume_per_atom": float(structure.volume / len(structure)),
    }


def public_features(frame: pd.DataFrame) -> pd.DataFrame:
    fractions = frame[["percent_atom_al", "percent_atom_ga", "percent_atom_in"]].to_numpy(float)
    oxygen = np.full((len(frame), 1), 0.6)
    cations = 0.4 * fractions / np.clip(fractions.sum(axis=1, keepdims=True), 1e-15, None)
    composition = np.column_stack([cations, oxygen])
    entropy = -np.sum(composition * np.log(np.clip(composition, 1e-15, None)), axis=1)
    a = frame["lattice_vector_1_ang"].to_numpy(float)
    b = frame["lattice_vector_2_ang"].to_numpy(float)
    c = frame["lattice_vector_3_ang"].to_numpy(float)
    alpha = np.radians(frame["lattice_angle_alpha_degree"].to_numpy(float))
    beta = np.radians(frame["lattice_angle_beta_degree"].to_numpy(float))
    gamma = np.radians(frame["lattice_angle_gamma_degree"].to_numpy(float))
    radicand = 1 + 2 * np.cos(alpha) * np.cos(beta) * np.cos(gamma)
    radicand -= np.cos(alpha) ** 2 + np.cos(beta) ** 2 + np.cos(gamma) ** 2
    volume = a * b * c * np.sqrt(np.clip(radicand, 0, None))
    return pd.DataFrame(
        {
            "id": frame["id"].astype(int),
            "fixture_composition_entropy": entropy,
            "fixture_volume_per_atom": volume / frame["number_of_total_atoms"].to_numpy(float),
        }
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-csv", type=Path, required=True)
    parser.add_argument("--test-csv", type=Path, required=True)
    parser.add_argument("--train-geometry", type=Path, required=True)
    parser.add_argument("--test-geometry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    public_features(pd.read_csv(args.train_csv)).to_parquet(args.output / "train.parquet", index=False)
    public_features(pd.read_csv(args.test_csv)).to_parquet(args.output / "test.parquet", index=False)


if __name__ == "__main__":
    main()
