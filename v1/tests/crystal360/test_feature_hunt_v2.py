from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from nomad_feature_hunt.v2.budget import BudgetAccount, BudgetError
from nomad_feature_hunt.v2.constants import (
    EXPECTED_JNOCCIO_ROLES,
    OUTPUT_LIMIT_BYTES,
    role_specs,
)
from nomad_feature_hunt.v2.evidence import (
    build_claim_pack,
    deduplicate_sources,
    source_identity,
    validate_evidence_coverage,
)
from nomad_feature_hunt.v2.execution import quarantine_columns
from nomad_feature_hunt.v2.fake_campaign import run_fake_180_campaign
from nomad_feature_hunt.v2.novelty import seed_atlas_registry
from nomad_feature_hunt.v2.prompts import build_retry_prompt, build_role_prompt
from nomad_feature_hunt.v2.schemas import (
    SchemaError,
    controller_feature_id,
    expand_feature_spec,
    parse_strict_json,
    validate_family_card,
    validate_feature_spec,
    validate_role_payload,
)
from nomad_feature_hunt.v2.scoring import (
    ConfirmationGate,
    FamilyCandidate,
    build_confirmation_preregistration,
    validate_confirmation_views,
)
from nomad_feature_hunt.v2.runbooks import dry_run_runbooks
from nomad_feature_hunt.v2.security import plugin_full_execution_command, static_check_plugin
from nomad_feature_hunt.v2.state import (
    CampaignDB,
    mark_batch_submitted,
    prepare_job_batch,
    record_attempt_result,
)
from nomad_feature_hunt.v2.verification import verify_hash_manifest


def family_card(domain: str = "D01", slug: str = "orbit-entropy") -> dict[str, object]:
    return {
        "family_slug": slug,
        "domain": domain,
        "physical_hypothesis": "Orbit population entropy resolves local symmetry breaking.",
        "target_affinity": "both",
        "kernel": "symmetry",
        "custom_plugin_required": False,
        "inputs": ["periodic_structure"],
        "citation_ids": ["source-0001.claim-01"],
        "atlas_novelty_argument": "Uses joint orbit populations absent from Atlas.",
        "invariances": [
            "translation",
            "rotation",
            "atom_permutation",
            "periodic_wrapping",
            "equivalent_cell",
        ],
        "falsifier": "Destroy orbit membership while holding composition fixed.",
        "complexity": "O(N log N)",
    }


def feature_spec(domain: str = "D01", family: str = "orbit-entropy") -> dict[str, object]:
    operations = (
        "spacegroup-number",
        "orbit-fraction",
        "orbit-entropy",
        "largest-orbit-fraction",
        "wyckoff-fraction",
        "site-symmetry-fraction",
        "symmetry-operations-per-site",
        "centrosymmetric",
    )
    return {
        "spec_slug": "symmetry-summary",
        "family_slug": family,
        "domain": domain,
        "kernel": "symmetry",
        "parameter_sets": [
            {
                "id": "strict-symmetry",
                "values": {"symprec": 0.001},
                "physical_justification": "Sub-picometre rounding is below geometry precision.",
            }
        ],
        "aggregations": ["per-primitive-site"],
        "outputs": [
            {
                "name": operation,
                "operation": operation,
                "parameter_set": "strict-symmetry",
                "aggregation": "per-primitive-site",
                "equation": f"trusted symmetry operator {operation}",
                "unit": "dimensionless",
                "physical_interpretation": f"Physical summary of {operation}.",
            }
            for operation in operations
        ],
        "missingness_policy": "Return zero only when spglib has no symmetry dataset.",
    }


def test_v2_roster_is_exact_and_stable() -> None:
    roles = role_specs()
    assert len(roles) == EXPECTED_JNOCCIO_ROLES == 180
    assert len({role["id"] for role in roles}) == 180
    assert Counter(role["class"] for role in roles) == {
        "evidence_curator": 10,
        "family_architect": 40,
        "spec_builder": 80,
        "plugin_writer": 20,
        "target_exploiter": 10,
        "cross_family_synthesizer": 10,
        "experimental_analyst": 4,
        "blind_judge": 4,
        "memory_curator": 2,
    }
    assert sum(role.get("canary") is True for role in roles) == 10


def test_strict_json_never_salvages_or_accepts_markdown() -> None:
    assert parse_strict_json("\n{\"ok\":true}\n") == {"ok": True}
    for invalid in (
        "prefix {\"ok\":true}",
        "{\"ok\":true} suffix",
        "```json\n{\"ok\":true}\n```",
        "{\"truncated\":",
    ):
        with pytest.raises(SchemaError):
            parse_strict_json(invalid)
    with pytest.raises(SchemaError, match="limit"):
        parse_strict_json('"' + "x" * OUTPUT_LIMIT_BYTES + '"')


def test_compact_schemas_and_controller_ids() -> None:
    card = family_card()
    spec = feature_spec()
    assert validate_family_card(card, citation_ids={"source-0001.claim-01"}) == []
    assert validate_feature_spec(spec, families={"orbit-entropy": card}) == []
    rows = expand_feature_spec(card, spec, source_role_id="spec-builder-d01-01")
    assert len(rows) == 8
    assert rows[0]["feature_id"].startswith("v2.d01.orbit-entropy.symmetry-summary.")
    assert len({row["feature_id"] for row in rows}) == 8
    assert (
        controller_feature_id("D10", "transport", "coupling", "entropy")
        == "v2.d10.transport.coupling.entropy"
    )
    hostile = {**card, "inputs": ["bandgap_energy_ev"]}
    assert any("forbidden" in error for error in validate_family_card(hostile))
    wrong_domain_kernel = {**card, "kernel": "periodic_graph"}
    assert any("physical domain" in error for error in validate_family_card(wrong_domain_kernel))
    unsupported_setting = feature_spec()
    unsupported_setting["parameter_sets"][0]["values"] = {"invented_bin": 99}
    assert any(
        "unsupported symmetry setting" in error
        for error in validate_feature_spec(unsupported_setting, families={"orbit-entropy": card})
    )
    nested_reference = feature_spec()
    nested_reference["outputs"][0]["parameter_set"] = {"id": "p1"}
    nested_reference["outputs"][0]["aggregation"] = {"id": "raw"}
    nested_errors = validate_feature_spec(nested_reference, families={"orbit-entropy": card})
    assert any("unknown parameter set" in error for error in nested_errors)
    assert any("unknown aggregation" in error for error in nested_errors)
    pytest.importorskip("pymatgen.core")
    from nomad_feature_hunt.v2.compiler import TrustedCompiler

    compiler = TrustedCompiler()
    compiler.compile(card, spec)
    with pytest.raises(SchemaError, match="already compiled"):
        compiler.compile(card, spec)


def test_trusted_compiler_applies_declared_aggregations() -> None:
    pytest.importorskip("pymatgen.core")
    from pymatgen.core import Lattice, Structure

    from nomad_feature_hunt.v2.compiler import CompiledFamily, TrustedCompiler
    from nomad_feature_hunt.v2.kernels import canonical_structure

    class _Cache:
        def compute(self, kernel, structure, config):
            return {"orbit-entropy": 12.0}

    structure = Structure(
        Lattice.cubic(4.0),
        ["Na", "Cl"],
        [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]],
    )
    columns = tuple(
        {
            "feature_id": f"v2.d01.test.aggregate.{aggregation}",
            "kernel": "symmetry",
            "configuration": {"symprec": 0.001},
            "operation": "orbit-entropy",
            "aggregation": aggregation,
        }
        for aggregation in ("raw", "per-atom", "volume-normalized")
    )
    values = TrustedCompiler(_Cache()).compute_family(
        CompiledFamily(card={}, spec={}, columns=columns), structure
    )
    canonical = canonical_structure(structure)
    assert values["v2.d01.test.aggregate.raw"] == 12.0
    assert values["v2.d01.test.aggregate.per-atom"] == 12.0 / len(canonical)
    assert values["v2.d01.test.aggregate.volume-normalized"] == pytest.approx(
        12.0 / canonical.volume
    )


def test_campaign_role_schemas_make_the_4000_column_goal_reachable() -> None:
    builder = next(role for role in role_specs() if role["class"] == "spec_builder")
    card = family_card(domain=builder["domain"])
    undersized = feature_spec(domain=builder["domain"])
    errors = validate_role_payload(
        builder,
        {"feature_specs": [undersized, {**undersized, "spec_slug": "second"}]},
        families={str(card["family_slug"]): card},
    )
    assert any("exactly 19" in error for error in errors)
    assert any("role-prefixed" in error for error in errors)
    adaptive = next(
        role for role in role_specs() if role["class"] == "target_exploiter"
    )
    adaptive_errors = validate_role_payload(
        adaptive,
        {"feature_specs": [undersized]},
        families={f"{card['domain']}:{card['family_slug']}": card},
    )
    assert adaptive_errors == ["adaptive role must return exactly two feature_specs"]


def test_canonical_research_dedup_and_coverage() -> None:
    records = [
        {"title": "One", "doi": "https://doi.org/10.1/ABC", "domains": ["D01"]},
        {"title": "Renamed", "DOI": "doi:10.1/abc", "domains": ["D02"]},
        {"title": "A  Crystal—Graph!", "domains": ["D03"]},
        {"title": "a crystal graph", "domains": ["D04"]},
        {"title": "Preprint", "arxiv": "arXiv:2401.00001v3", "domains": ["D05"]},
        {"title": "Preprint changed", "arxiv_id": "2401.00001", "domains": ["D06"]},
    ]
    assert source_identity(records[0]) == ("doi", "10.1/abc")
    deduplicated = deduplicate_sources(records)
    assert len(deduplicated) == 3
    assert set(deduplicated[0]["domains"]) == {"D01", "D02"}

    covered = []
    for domain_index in range(1, 11):
        domain = f"D{domain_index:02d}"
        for index in range(25):
            covered.append(
                {
                    "source_id": f"{domain}-{index}",
                    "title": f"Unique {domain} source {index}",
                    "domains": [domain],
                    "claims": ["A claim"],
                    "relevant": True,
                }
            )
    assert validate_evidence_coverage(covered) == []
    assert len(build_claim_pack(covered, "D01")) == 10


def test_prompt_and_retry_contracts_are_bounded() -> None:
    role = next(role for role in role_specs() if role["class"] == "family_architect")
    evidence = [
        {"source_id": f"s-{index}", "title": "short", "claims": ["claim"]}
        for index in range(10)
    ]
    prompt = build_role_prompt(role, evidence=evidence, novelty_summary={"columns": 9969})
    assert len(prompt.encode()) <= 12 * 1024
    retry = build_retry_prompt(role, "x" * 10_000, ["family_cards[0] invalid"])
    assert len(retry.encode()) <= 12 * 1024
    assert "evidence" not in json.loads(retry)


def test_plugin_policy_rejects_network_secrets_labels_and_hostile_calls() -> None:
    safe = "def compute_family(structure, config):\n    return {str(i): float(i) for i in range(8)}\n"
    assert static_check_plugin(safe) == []
    assert any("socket" in error for error in static_check_plugin("import socket\n" + safe))
    assert any("target or label" in error for error in static_check_plugin(safe + "# test_labels"))
    assert any("open" in error for error in static_check_plugin(safe.replace("return", "open('x')\n    return")))
    assert any("signature" in error for error in static_check_plugin("def compute_family(x):\n return {}"))


def test_budget_is_conservative_and_preserves_reported_null(tmp_path: Path) -> None:
    account = BudgetAccount(tmp_path / "budget.sqlite3", ceiling_usd=55.0)
    account.reserve("ops", "research")
    assert account.settle("ops", None) == 50.0
    account.reserve("j-1", "jnoccio")
    assert account.settle("j-1", None) == 2.5
    account.reserve("j-2", "jnoccio")
    assert account.settle("j-2", 1.0) == 2.5
    with sqlite3.connect(account.path) as connection:
        assert connection.execute(
            "SELECT reported_cost_json FROM budget_entries WHERE entry_id='j-1'"
        ).fetchone()[0] == "null"
    with pytest.raises(BudgetError, match="exceed"):
        account.reserve("j-3", "jnoccio")


def test_prepared_lease_does_not_consume_an_attempt(tmp_path: Path) -> None:
    db = CampaignDB(tmp_path / "campaign.sqlite3")
    role = role_specs()[0]
    db.execute(
        "INSERT INTO roles(role_id,role_class,domain,wave,spec_json) VALUES(?,?,?,?,?)",
        (role["id"], role["class"], role["domain"], role["wave"], json.dumps(role)),
    )
    jobs_path = tmp_path / "jobs.json"
    prepare_job_batch(
        db,
        batch_id="canary-0",
        jobs_path=jobs_path,
        prompt_dir=tmp_path / "prompts",
        roles_and_prompts=[(role, '{"prompt":"stable"}')],
        attempt=0,
    )
    assert jobs_path.exists()
    assert db.one("SELECT status FROM leases")["status"] == "prepared"
    assert db.one("SELECT COUNT(*) n FROM attempts")["n"] == 0


def test_missing_router_metadata_is_preserved_as_missing(tmp_path: Path) -> None:
    db = CampaignDB(tmp_path / "campaign.sqlite3")
    budget = BudgetAccount(tmp_path / "budget.sqlite3")
    role = role_specs()[0]
    db.execute(
        "INSERT INTO roles(role_id,role_class,domain,wave,spec_json) VALUES(?,?,?,?,?)",
        (role["id"], role["class"], role["domain"], role["wave"], json.dumps(role)),
    )
    prepare_job_batch(
        db,
        batch_id="missing-metadata",
        jobs_path=tmp_path / "jobs.json",
        prompt_dir=tmp_path / "prompts",
        roles_and_prompts=[(role, "{}")],
        attempt=0,
    )
    mark_batch_submitted(db, budget, "missing-metadata")
    result = {
        "success": True,
        "assistant_text": "{}",
        "provider_id": "fake",
        "model_id": "router",
        "credential_user_id": None,
    }
    record_attempt_result(
        db,
        budget,
        role_id=role["id"],
        attempt=0,
        result=result,
        raw_result_path=tmp_path / "raw/result.json",
        valid=True,
        errors=[],
    )
    attempt = db.one("SELECT * FROM attempts")
    assert attempt["router_metadata_present"] == 0
    assert attempt["router_metadata_json"] == "null"
    assert attempt["credential_user"] is None


def test_optional_jailgun_absence_writes_skip_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from nomad_feature_hunt.v2 import controller

    settings = controller.Settings(
        repo_root=tmp_path,
        inbox_root=tmp_path / "nomad/artifacts/v2/inbox",
        nomad_root=tmp_path / "nomad",
        run_id="optional-jailgun",
    )
    monkeypatch.setattr(controller.shutil, "which", lambda _name: None)
    receipt = controller.run_optional_jailgun(settings)
    assert receipt["status"] == "skipped"
    assert receipt["optional"] is True
    assert (settings.run_root / "receipts/jailgun/optional.json").exists()


def test_atlas_registry_seeds_every_novelty_fingerprint(tmp_path: Path) -> None:
    atlas = tmp_path / "atlas"
    atlas.mkdir()
    (atlas / "columns.json").write_text(json.dumps(["old", "atlas-a", "atlas-b"]))
    (atlas / "atlas_definitions.json").write_text(
        json.dumps(
            [
                {
                    "name": "atlas-a",
                    "formula": "sum x_i",
                    "interpretation": "composition sum",
                },
                {
                    "name": "atlas-b",
                    "formula": "mean r_ij",
                    "interpretation": "pair scale",
                },
            ]
        )
    )
    np.save(atlas / "train.npy", np.asarray([[0.0, 1.0, 2.0], [1.0, 2.0, 3.0]]))
    np.save(atlas / "test.npy", np.asarray([[2.0, 3.0, 4.0]]))
    output = tmp_path / "registry.jsonl"
    receipt = seed_atlas_registry(
        atlas,
        output,
        expected_width=3,
        expected_train_rows=2,
        expected_test_rows=1,
    )
    assert receipt["columns"] == receipt["numeric_signatures"] == 3
    assert receipt["definitions"] == 2
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert all(row["formula_fingerprint"] and row["semantic_fingerprint"] for row in rows)


def test_per_column_quarantine_keeps_valid_siblings() -> None:
    train_ids = [1, 2, 3, 4]
    test_ids = [5, 6]
    train = pd.DataFrame(
        {"id": train_ids, "good": [0.0, 1.0, 2.0, 3.0], "constant": [1.0] * 4, "bad": [1.0, 2.0, np.nan, 4.0]}
    )
    test = pd.DataFrame(
        {"id": test_ids, "good": [4.0, 5.0], "constant": [1.0] * 2, "bad": [5.0, 6.0]}
    )
    invariance = {
        name: {column: True for column in ("good", "constant", "bad")}
        for name in (
            "translation", "rotation", "atom_permutation", "periodic_wrapping", "equivalent_cell"
        )
    }
    result = quarantine_columns(
        train,
        test,
        expected_train_ids=train_ids,
        expected_test_ids=test_ids,
        rerun_train=train.copy(),
        rerun_test=test.copy(),
        invariance_report=invariance,
    )
    assert result.accepted == ("good",)
    assert {item.column for item in result.rejected} == {"constant", "bad"}
    assert list(result.train) == ["id", "good"]


def test_confirmation_is_sealed_and_views_are_nonoverlapping() -> None:
    gate = ConfirmationGate()
    with pytest.raises(RuntimeError, match="sealed"):
        gate.unseal()
    gate.freeze_adaptive_generation()
    gate.unseal()
    with pytest.raises(RuntimeError, match="only once"):
        gate.unseal()
    with pytest.raises(ValueError, match="overlap"):
        validate_confirmation_views(
            "bandgap_energy_ev",
            [
                {"view_id": "a", "kind": "family", "families": ["f1"]},
                {"view_id": "b", "kind": "family", "families": ["f1"]},
            ],
        )


def test_confirmation_preregistration_is_bounded_and_domain_diverse() -> None:
    candidates: dict[str, FamilyCandidate] = {}
    rows = []
    for index in range(12):
        family = f"family-{index:02d}"
        domain = f"D{index % 4 + 1:02d}"
        candidates[family] = FamilyCandidate(
            family,
            domain,
            pd.DataFrame({"id": [1, 2], f"v2.{index}": [0.0, 1.0]}),
            1.0,
        )
        for target in ("formation_energy_ev_natom", "bandgap_energy_ev"):
            rows.append(
                {
                    "target": target,
                    "family_slug": family,
                    "domain": domain,
                    "lift": 0.001 - index * 0.00001,
                    "feature_count": index + 8,
                }
            )
    preregistration = build_confirmation_preregistration(rows, candidates)
    for target, views in preregistration.items():
        assert len(views) == 8
        validate_confirmation_views(target, views)
        family_views = [view for view in views if view["kind"] == "family"]
        assert len(family_views) == 5
        assert len(
            {candidates[view["families"][0]].domain for view in family_views}
        ) >= 3


def test_custom_full_harness_executes_and_reruns_controller_rows(tmp_path: Path) -> None:
    train = tmp_path / "train"
    test = tmp_path / "test"
    geometry = """lattice_vector 4 0 0
lattice_vector 0 4 0
lattice_vector 0 0 4
atom 0 0 0 Al
atom 2 2 2 O
"""
    for directory, identifiers in ((train, (1, 2)), (test, (3,))):
        for identifier in identifiers:
            path = directory / str(identifier)
            path.mkdir(parents=True)
            (path / "geometry.xyz").write_text(geometry, encoding="utf-8")
    plugin = tmp_path / "plugin.py"
    plugin.write_text(
        "def compute_family(structure, config):\n"
        "    base = float(structure.density)\n"
        "    return {f'out{i}': base + i for i in range(8)}\n",
        encoding="utf-8",
    )
    specification = tmp_path / "specification.json"
    specification.write_text(
        json.dumps(
            {
                "train_ids": [1, 2],
                "test_ids": [3],
                "invariance_ids": [1],
                "columns": [
                    {
                        "feature_id": f"v2.d01.custom.spec.out-{index}",
                        "operation": f"out{index}",
                        "plugin_key": f"out{index}",
                        "configuration": {},
                    }
                    for index in range(8)
                ],
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "output"
    harness = Path(__file__).resolve().parents[2] / "ops/nomad-feature-hunt-v2/plugin_runner.py"
    result = subprocess.run(
        [
            sys.executable,
            str(harness),
            "--plugin",
            str(plugin),
            "--output",
            str(output),
            "--mode",
            "full",
            "--train-structures",
            str(train),
            "--test-structures",
            str(test),
            "--specification",
            str(specification),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads((output / "receipt.json").read_text(encoding="utf-8"))
    assert receipt["deterministic"] is True
    assert receipt["train_rows"] == 2 and receipt["test_rows"] == 1
    assert all(receipt["invariances"].values())
    command = plugin_full_execution_command(
        image="sandbox:test",
        plugin=plugin,
        harness=harness,
        train_structures=train,
        test_structures=test,
        specification=specification,
        output=output,
    )
    assert command[command.index("--network") + 1] == "none"
    assert "--read-only" in command and "no-new-privileges" in command


def test_all_trusted_kernels_are_finite_and_invariant() -> None:
    pymatgen = pytest.importorskip("pymatgen.core")
    from nomad_feature_hunt.v2.constants import TRUSTED_KERNELS
    from nomad_feature_hunt.v2.execution import run_invariance_tests
    from nomad_feature_hunt.v2.kernels import compute_kernel

    structure = pymatgen.Structure(
        pymatgen.Lattice.cubic(4.2),
        ["Al", "O", "O"],
        [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25]],
    )
    for kernel in TRUSTED_KERNELS:
        values = compute_kernel(kernel, structure, {})
        assert len(values) >= 8
        assert np.isfinite(list(values.values())).all()
        report = run_invariance_tests([structure], lambda item: compute_kernel(kernel, item, {}))
        assert all(all(columns.values()) for columns in report.values()), kernel


def test_canonical_topology_batched_grid_matches_anchor_reference() -> None:
    pymatgen = pytest.importorskip("pymatgen.core")
    from nomad_feature_hunt.v2.kernels import canonical_structure, canonical_topology_kernel

    structure = pymatgen.Structure(
        pymatgen.Lattice.hexagonal(3.1, 5.2),
        ["Al", "O", "O"],
        [[0.0, 0.0, 0.0], [1 / 3, 2 / 3, 0.25], [2 / 3, 1 / 3, 0.75]],
    )
    crystal = canonical_structure(structure)
    grid_n = 4
    threshold = 1.2
    axis = (np.arange(grid_n, dtype=float) + 0.5) / grid_n
    base_grid = np.asarray(np.meshgrid(axis, axis, axis, indexing="ij")).reshape(3, -1).T
    fractional = np.asarray(crystal.frac_coords)
    reference = np.concatenate(
        [
            np.min(
                crystal.lattice.get_all_distances((base_grid + anchor) % 1.0, fractional),
                axis=1,
            )
            for anchor in fractional
        ]
    )
    result = canonical_topology_kernel(crystal, {"grid": grid_n, "void_threshold": threshold})
    assert result["void-radius-mean"] == pytest.approx(reference.mean())
    assert result["void-radius-max"] == pytest.approx(reference.max())
    assert result["minkowski-volume-fraction"] == pytest.approx(np.mean(reference <= threshold))


def test_symmetry_species_batching_matches_site_reference() -> None:
    pymatgen = pytest.importorskip("pymatgen.core")
    import spglib

    from nomad_feature_hunt.v2.kernels import canonical_structure, symmetry_kernel

    structure = pymatgen.Structure(
        pymatgen.Lattice.cubic(4.2),
        ["Al", "O", "O"],
        [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25]],
    )
    crystal = canonical_structure(structure)
    symprec = 1e-3
    fractional = np.asarray(crystal.frac_coords)
    atomic_numbers = np.asarray([site.specie.Z for site in crystal], dtype=int)
    dataset = spglib.get_symmetry_dataset(
        (np.asarray(crystal.lattice.matrix), fractional, atomic_numbers),
        symprec=symprec,
    )
    assert dataset is not None
    reference = []
    for rotation, translation in list(
        zip(dataset.rotations, dataset.translations, strict=True)
    )[:32]:
        transformed = (fractional @ rotation.T + translation) % 1.0
        for index, coordinate in enumerate(transformed):
            same_species = fractional[atomic_numbers == atomic_numbers[index]]
            distances = crystal.lattice.get_all_distances(coordinate[None, :], same_species)
            reference.append(float(np.min(distances)))
    reference_array = np.asarray(reference)
    result = symmetry_kernel(crystal, {"symprec": symprec})
    assert result["symmetry-residual-mean"] == pytest.approx(reference_array.mean())
    assert result["symmetry-residual-std"] == pytest.approx(reference_array.std())
    assert result["symmetry-residual-max"] == pytest.approx(reference_array.max())
    assert result["symmetry-residual-q90"] == pytest.approx(np.quantile(reference_array, 0.9))


def test_orbital_neighbor_batching_matches_site_reference() -> None:
    import math

    pymatgen = pytest.importorskip("pymatgen.core")
    from nomad_feature_hunt.v2.kernels import canonical_structure, orbital_local_kernel

    structure = pymatgen.Structure(
        pymatgen.Lattice.cubic(4.2),
        ["Al", "O", "O"],
        [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5], [0.25, 0.25, 0.25]],
    )
    crystal = canonical_structure(structure)
    cutoff = 4.1
    z = np.asarray([float(site.specie.Z) for site in crystal])
    group = np.asarray([float(site.specie.group) for site in crystal])
    electronegativity = np.asarray([float(site.specie.X) for site in crystal])
    coordinations = []
    z_mismatch = []
    group_mismatch = []
    x_mismatch = []
    orbital_field = []
    for index, site in enumerate(crystal):
        neighbors = [
            neighbor
            for neighbor in crystal.get_neighbors(site, cutoff)
            if neighbor.nn_distance > 1e-8
        ]
        coordinations.append(float(len(neighbors)))
        for neighbor in neighbors:
            other = int(neighbor.index)
            weight = math.exp(-float(neighbor.nn_distance) / cutoff)
            z_mismatch.append(abs(z[index] - z[other]) * weight)
            group_mismatch.append(abs(group[index] - group[other]) * weight)
            x_mismatch.append(abs(electronegativity[index] - electronegativity[other]) * weight)
            orbital_field.append(group[index] * group[other] * weight)
    result = orbital_local_kernel(crystal, {"cutoff": cutoff})
    coordination_array = np.asarray(coordinations)
    assert result["coordination-mean"] == pytest.approx(coordination_array.mean())
    assert result["coordination-std"] == pytest.approx(coordination_array.std())
    assert result["atomic-number-mismatch"] == pytest.approx(np.mean(z_mismatch))
    assert result["group-mismatch"] == pytest.approx(np.mean(group_mismatch))
    assert result["electronegativity-mismatch"] == pytest.approx(np.mean(x_mismatch))
    assert result["orbital-field-mean"] == pytest.approx(np.mean(orbital_field))
    assert result["orbital-field-std"] == pytest.approx(np.std(orbital_field))


def test_all_trusted_kernels_on_a_real_nomad_structure() -> None:
    geometry = Path("/home/ubuntu/nomad/train/1/geometry.xyz")
    if not geometry.exists():
        pytest.skip("real NOMAD geometry is not staged in this test environment")
    from nomad_crystal360.io import read_geometry
    from nomad_feature_hunt.v2.constants import TRUSTED_KERNELS
    from nomad_feature_hunt.v2.execution import run_invariance_tests
    from nomad_feature_hunt.v2.kernels import compute_kernel

    structure = read_geometry(geometry)
    for kernel in TRUSTED_KERNELS:
        values = compute_kernel(kernel, structure, {})
        assert np.isfinite(list(values.values())).all()
        report = run_invariance_tests([structure], lambda item: compute_kernel(kernel, item, {}))
        assert all(all(columns.values()) for columns in report.values()), kernel


def test_all_five_runbooks_dry_run() -> None:
    root = Path(__file__).resolve().parents[2]
    report = dry_run_runbooks(root / "ops/nomad-feature-hunt-v2")
    assert report["valid"], report["errors"]
    assert report["runbooks"] == 5


def test_fake_180_role_campaign_passes_fail_closed_verifier(tmp_path: Path) -> None:
    report = run_fake_180_campaign(tmp_path / "fake-inbox")
    assert report["complete"], report["missing"]
    assert report["counts"]["roles"] == 180
    assert report["counts"]["attempted_columns"] == 4000
    assert report["counts"]["validated_columns"] == 2500
    assert (tmp_path / "fake-inbox/promotion/integration_manifest.json").exists()
    assert (tmp_path / "fake-inbox/final_hashes/manifest.json").exists()
    assert verify_hash_manifest(tmp_path / "fake-inbox") == (True, [])
