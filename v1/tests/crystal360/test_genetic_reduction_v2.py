from __future__ import annotations

import json
import numpy as np
import pandas as pd

from nomad_feature_hunt.v2.genetic_reduction import (
    Genome,
    analyze_feature_bundle,
    breed_population,
    choose_confirmation_genomes,
    initial_population,
    summarize_jobs,
)
from nomad_feature_hunt.v2.zyal_graduation import (
    _feature_signature,
    _unique_addition_names,
)


TARGET = "formation_energy_ev_natom"


def _ranking(width: int, shift: int = 0) -> pd.DataFrame:
    indices = np.roll(np.arange(width), shift)
    return pd.DataFrame({"feature_index": indices, "rank": np.arange(1, width + 1)})


def test_initial_population_is_deterministic_and_covers_all_features() -> None:
    aggregate = _ranking(900)
    first = initial_population(
        target=TARGET,
        aggregate_ranking=aggregate,
        fold_rankings=[_ranking(900, 3), _ranking(900, -5)],
        selected_columns=list(range(120)),
        population_size=10,
        seed=17,
    )
    second = initial_population(
        target=TARGET,
        aggregate_ranking=aggregate,
        fold_rankings=[_ranking(900, 3), _ranking(900, -5)],
        selected_columns=list(range(120)),
        population_size=10,
        seed=17,
    )

    assert [item.genome_id for item in first] == [item.genome_id for item in second]
    assert len({item.genome_id for item in first}) == 10
    assert any(item.origin == "all-features" and len(item.columns) == 900 for item in first)
    assert any(item.origin == "existing-809-control" for item in first)

    allowed = [index for index in range(900) if index != 850]
    quarantined = initial_population(
        target=TARGET,
        aggregate_ranking=aggregate,
        fold_rankings=[_ranking(900, 3), _ranking(900, -5)],
        selected_columns=list(range(120)),
        allowed_columns=allowed,
        population_size=10,
        seed=17,
    )
    validated = next(
        item for item in quarantined if item.origin == "all-validated-features"
    )
    assert validated.columns == tuple(allowed)


def test_breeding_produces_bounded_unique_unseen_genomes() -> None:
    aggregate = _ranking(900)
    population = initial_population(
        target=TARGET,
        aggregate_ranking=aggregate,
        fold_rankings=[_ranking(900, 2), _ranking(900, -2)],
        selected_columns=list(range(160)),
        population_size=10,
        seed=23,
    )
    scored = [(genome, 0.02 + index / 10_000) for index, genome in enumerate(population)]
    children = breed_population(
        target=TARGET,
        ranked_results=scored,
        aggregate_ranking=aggregate,
        population_size=10,
        generation=1,
        seed=23,
        seen_ids={item.genome_id for item in population},
    )

    assert len(children) == len({item.genome_id for item in children}) == 10
    assert not {item.genome_id for item in children} & {item.genome_id for item in population}
    assert all(64 <= len(item.columns) <= 900 for item in children)
    assert all(item.generation == 1 and item.parents for item in children)


def test_job_summary_aggregates_seed_fold_scores() -> None:
    genome = Genome(TARGET, (0, 1, 2), 0, "fixture")
    pairs = []
    for seed in (1, 2, 3):
        for fold in (0, 1):
            job = {
                "genome_id": genome.genome_id,
                "seed": seed,
                "fold": fold,
                "job_id": f"{seed}-{fold}",
            }
            pairs.append((job, {"score": 0.01 * seed + 0.001 * fold}))
    rows = summarize_jobs(pairs, {genome.genome_id: genome})

    assert len(rows) == 1
    assert rows[0]["model_jobs"] == 6
    assert rows[0]["mean_rmsle"] == np.mean([0.01, 0.011, 0.02, 0.021, 0.03, 0.031])


def test_confirmation_selection_is_frozen_to_eight_and_includes_atlas() -> None:
    targets = ("formation_energy_ev_natom", "bandgap_energy_ev")
    genomes: dict[str, Genome] = {}
    rows = []
    atlas = {}
    for target_index, target in enumerate(targets):
        atlas[target] = Genome(target, tuple(range(100 + target_index)), 0, "atlas-winner")
        for index in range(12):
            genome = Genome(
                target,
                tuple(range(20 + index * 7, 84 + index * 7)),
                1,
                "fixture",
            )
            genomes[genome.genome_id] = genome
            rows.append(
                {
                    "target": target,
                    "genome_id": genome.genome_id,
                    "feature_count": len(genome.columns),
                    "mean_rmsle": 0.02 + target_index * 0.05 + index / 10_000,
                }
            )

    selected = choose_confirmation_genomes(rows, genomes, atlas)

    assert set(selected) == set(targets)
    assert all(len(items) == 8 for items in selected.values())
    assert all(items[0].origin == "atlas-winner" for items in selected.values())


def test_feature_analysis_quarantines_constants_duplicates_and_infinity(
    tmp_path, monkeypatch
) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    train = np.asarray(
        [[1.0, 7.0, 1.0, np.nan], [2.0, 7.0, 2.0, 3.0], [3.0, 7.0, 3.0, 4.0]],
        dtype=np.float32,
    )
    test = np.asarray([[4.0, 7.0, 4.0, 5.0]], dtype=np.float32)
    np.save(bundle / "train.npy", train, allow_pickle=False)
    np.save(bundle / "test.npy", test, allow_pickle=False)
    (bundle / "columns.json").write_text(json.dumps(["good", "constant", "dupe", "missing"]))
    monkeypatch.setattr(
        "nomad_feature_hunt.v2.genetic_reduction.verify_public_bundle",
        lambda _path: {"train_rows": 3, "test_rows": 1, "predictors": 4},
    )

    accepted, report = analyze_feature_bundle(bundle)

    assert accepted == [0, 3]
    assert report["validated_columns"] == 2
    assert report["columns_with_declared_missingness"] == 1
    assert {item["reason"] for item in report["rejections"]} == {
        "constant",
        "exact_numeric_duplicate",
    }


def test_augmented_bundle_rechecks_atlas_and_cross_domain_duplicates() -> None:
    train = pd.DataFrame(
        {
            "atlas_copy": [1.0, 2.0],
            "fresh": [10.0, 11.0],
            "fresh_copy": [10.0, 11.0],
        }
    )
    test = pd.DataFrame(
        {"atlas_copy": [3.0], "fresh": [12.0], "fresh_copy": [12.0]}
    )
    atlas_signature = _feature_signature(np.asarray([1.0, 2.0, 3.0]))

    accepted, rejected = _unique_addition_names(
        train,
        test,
        ["atlas_copy", "fresh", "fresh_copy"],
        {atlas_signature: "atlas.original"},
    )

    assert accepted == ["fresh"]
    assert rejected == [
        {
            "feature_id": "atlas_copy",
            "reason": "exact_numeric_duplicate",
            "duplicate_of": "atlas.original",
        },
        {
            "feature_id": "fresh_copy",
            "reason": "exact_numeric_duplicate",
            "duplicate_of": "fresh",
        },
    ]
