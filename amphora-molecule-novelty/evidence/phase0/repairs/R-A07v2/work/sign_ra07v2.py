#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-A07v2 superseding repair receipt (amphora-molecule-novelty).

AUDIT_ONLY. Supersedes R-A07's four-family conformal table by path+sha; leaves R-A07,
V-A07 and every artifact they reference byte-intact. Does not promote authority, flip
scientific_readiness, or touch the manifest, ledger, mission front-matter, locked
datasets or any signed Phase-0 KPI.

Signing pattern replicated from
amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py
(PAE construction, load_seed, payloadType, attestation keys, two-replay gate),
followed by an in-process self-verify (rebuild PAE, Ed25519 verify, keyid prefix).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-novelty"
REP = MOD / "evidence/phase0/repairs/R-A07v2"
WORK = REP / "work"
DONE = REP / "done"
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

REL = "amphora-molecule-novelty"
R_A07_DONE = MOD / "evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json"
V_A07_DONE = MOD / "evidence/phase0/repairs/V-A07/done/v-a07-independent-verify-of-r-a07-receipt.v1.dsse.json"
DEDUP_AUDIT = MOD / "evidence/audit/corpus-duplicate-exchangeability-audit-v1/corpus-duplicate-exchangeability-receipt.v1.dsse.json"
IDENTITY_AUDIT = MOD / "evidence/audit/candidate-structure-identity-audit-v1/candidate-structure-identity-audit-receipt.v1.dsse.json"
GENMOD_REF = ROOT / "amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json"
HARNESS = WORK / "run_ra07v2.py"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


# ------------------------------------------------------------ two-replay gate
canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["checks_all_pass"] is True, "diagnostic checks did not all pass"

fd = diag["flip_disclosure"]
n_A, n_B, n_C, n_D = fd["A_dedup_effect_old_structure_ra07_disclosed_set"]["n"], \
    fd["B_structural_effect_undisclosed_by_ra07_found_by_va07"]["n"], \
    fd["C_total_originally_signed_to_fully_corrected"]["n"], \
    fd["D_dedup_effect_under_correct_structure"]["n"]

r_a07_sha = sha(R_A07_DONE.read_bytes())
v_a07_sha = sha(V_A07_DONE.read_bytes())
dedup_sha = sha(DEDUP_AUDIT.read_bytes())
ident_sha = sha(IDENTITY_AUDIT.read_bytes())
genmod_sha = sha(GENMOD_REF.read_bytes())
harness_sha = sha(HARNESS.read_bytes())
signer_sha = sha(Path(__file__).read_bytes())

# ------------------------------------------------------------------- identity
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
rev_pin = rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id")

tl = diag["top_level_five_over_five"]

body_obj = {
    "schema": "amphora.molecule-novelty.r-a07v2-superseding-repair-receipt.v1",
    "receipt_id": "r-a07v2-four-family-ipda-propagation-repair-v1",
    "module_id": REL,
    "repair_item": "R-A07v2",
    "repair_mode": "interactive-2026-08-04",
    "run_type": "SUPERSEDING_REPAIR_STRUCTURAL_CORRECTION_PROPAGATION",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": diag["date"],
    "generated_on_host": "xbabe2",
    "rdkit_version": diag["rdkit_version"],

    "headline": diag["headline"],

    "claim": (
        "The conformal family/alpha novelty table for the 5 canonical epoxy-amine hardener "
        "candidates is republished on the canonically-deduplicated 350-distinct OpenPoly "
        "calibration corpus with the corrected isophorone diamine structure (CAS 2855-13-2, "
        "C10H22N2) applied in ALL FOUR fingerprint families -- morgan_r2_2048, maccs_166, "
        "atompair_2048, toptorsion_2048. R-A07 applied that structural correction only inside a "
        "separate morgan_r2_2048-only side table, leaving the maccs_166 / atompair_2048 / "
        "toptorsion_2048 IPDA cells of its SHIPPED table computed on the refuted C9H20N2 string; "
        "the independent verify V-A07 established this (verdict CLAIM_REFUTED) and this receipt "
        f"reproduces it constructively -- all {diag['ra07_shipped_table_parity_under_old_ipda']['n_cells_compared']} "
        "cells of R-A07's shipped table reproduce exactly when the OLD string is used in every "
        f"family. Every flip is disclosed: {n_A} cells flip under the deduplication correction "
        f"alone (R-A07's declared set, reproduced exactly), {n_B} further cell flips when the "
        "structural correction is actually applied in atompair_2048 (the undisclosed flip V-A07 "
        f"surfaced: atompair_2048 / IPDA / alpha=0.01, conformal p 0.011396 -> 0.008547, NOVEL "
        f"false -> true), and {n_C} cells differ net between what was ORIGINALLY signed and this "
        "fully-corrected table. THE TOP-LEVEL 5/5-NOVEL HEADLINE STANDS: all 5 candidates have "
        "Morgan(r2,2048) nearest-neighbour Tanimoto below the 0.40 Bajusz-Racz-Heberger cutoff on "
        "the deduplicated corpus with the corrected structure, and the IPDA structural fix leaves "
        "the Morgan nearest-neighbour similarity numerically unchanged, so the headline never "
        "depended on any defective cell."),

    "top_level_headline_status": {
        "headline": "5/5 NOVEL",
        "stands": True,
        "n_candidates": tl["n_candidates"],
        "n_novel": tl["n_novel"],
        "lane": tl["lane"],
        "per_candidate": tl["per_candidate"],
        "nn_range_vs_deduped_350": diag["checks"]["5c_nn_range"],
        "fixed_cutoff": 0.40,
        "why_unaffected_by_the_defect": tl["why_unaffected"],
        "matches_ra07_published_per_candidate_to_1e-12": diag["checks"][
            "5b_top_level_matches_ra07_published_per_candidate_1e-12"],
        "explicit_statement": (
            "The 5/5-NOVEL headline is UNAFFECTED by the defect this repair fixes and STANDS."),
    },

    "method": diag["method"],
    "corpus": diag["corpus"],
    "corrected_ipda": diag["corrected_ipda"],

    "corrected_family_alpha_table_deduped_350_all_four_families": diag[
        "corrected_family_alpha_table_deduped_350_all_four_families_corrected_ipda"],
    "reference_tables_for_audit": diag["reference_tables_for_audit"],

    "flip_disclosure": diag["flip_disclosure"],
    "n_flip_cells_dedup_effect": n_A,
    "n_flip_cells_structural_effect": n_B,
    "n_flip_cells_net_originally_signed_to_fully_corrected": n_C,
    "n_flip_cells_dedup_effect_under_correct_structure": n_D,

    "ipda_nn_shift_by_family": diag["ipda_nn_shift_by_family"],
    "ra07_shipped_table_parity_under_old_ipda": diag["ra07_shipped_table_parity_under_old_ipda"],
    "cross_family_novelty_counts_alpha_0_05": diag["cross_family_novelty_counts_alpha_0_05_fully_corrected"],
    "dds_cross_family_count_a05": {
        "value": diag["cross_family_novelty_counts_alpha_0_05_fully_corrected"]["DDS"],
        "note": ("R-A07's correction of DDS's cross-family count from 1/4 to 0/4 at alpha=0.05 is "
                 "unaffected by the IPDA structural fix and is reproduced here on the "
                 "fully-corrected table."),
    },

    "values_read_from_v_a07_verify_receipt_bytes": diag["values_read_from_v_a07_verify_receipt_bytes"],

    "supersedes": [{
        "superseded_path": f"{REL}/evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json",
        "superseded_sha256": r_a07_sha,
        "superseded_deleted_or_modified": False,
        "scope_of_supersession": (
            "R-A07's corrected_family_alpha_table_deduped_350 and its claim that that table is "
            "'recomputed ... under both corrections'. R-A07's dedup correction, its 5 declared "
            "flip cells, its DDS 0/4 cross-family count and its top-level 5/5-NOVEL result are "
            "NOT superseded -- all four reproduce exactly here and are carried forward."),
        "reason": (
            "The independent verify V-A07 (verdict CLAIM_REFUTED) confirmed all 11 of its "
            "self-tests, reproduced R-A07's 5 declared flip cells and its independent IPDA "
            "re-derivation, then found that R-A07's shipped four-family table applies the "
            "IPDA structural correction (C9H20N2 -> C10H22N2) in no family at all: the fix "
            "lives only in a separate morgan_r2_2048-only side table. Propagating the corrected "
            "structure into maccs_166 / atompair_2048 / toptorsion_2048 surfaces one undisclosed "
            "verdict flip (atompair_2048 / IPDA / alpha=0.01). This receipt republishes the "
            "complete four-family table with the correction applied everywhere and discloses "
            "every flip."),
    }],

    "refuted_by": [{
        "path": f"{REL}/evidence/phase0/repairs/V-A07/done/v-a07-independent-verify-of-r-a07-receipt.v1.dsse.json",
        "sha256": v_a07_sha,
        "verify_item": "V-A07",
        "verdict": "CLAIM_REFUTED",
        "targets": "R-A07 corrected_family_alpha_table_deduped_350 (IPDA cells in maccs_166 / atompair_2048 / toptorsion_2048)",
        "arithmetic_disputed": False,
        "note": (
            "V-A07 CONFIRMED R-A07's arithmetic: 11/11 self-tests, the 5 flip cells reproduced, "
            "and an independent re-derivation of the corrected IPDA structure. This v2 does not "
            "re-litigate any of that; it fixes the specific residual defect V-A07 named."),
    }],

    "refuting_receipts_sha256": {
        f"{REL}/evidence/audit/corpus-duplicate-exchangeability-audit-v1/corpus-duplicate-exchangeability-receipt.v1.dsse.json": dedup_sha,
        f"{REL}/evidence/audit/candidate-structure-identity-audit-v1/candidate-structure-identity-audit-receipt.v1.dsse.json": ident_sha,
    },

    "closes": [
        "Propagates the corrected isophorone diamine structure (CAS 2855-13-2, C10H22N2) into "
        "ALL FOUR fingerprint families of the shipped conformal table, not only morgan_r2_2048.",
        "Publishes the complete four-family / five-candidate / four-alpha table computed under "
        "both corrections simultaneously.",
        f"Discloses the {n_B} flip V-A07 surfaced (atompair_2048 / IPDA / alpha=0.01, NOVEL false "
        "-> true) alongside R-A07's 5 dedup flips, and publishes the net difference set relative "
        "to the originally-signed table so no flip can hide in a comparison that was never made.",
        "Reproduces R-A07's shipped table exactly under the OLD structure in all four families, "
        "converting V-A07's diagnosis into a positive, replayable demonstration.",
        "Re-derives isophorone diamine a third independent way and pins it to the in-tree "
        "amphora-molecule-generator known_answer_amines ground truth.",
        "Re-affirms explicitly that the top-level 5/5-NOVEL headline stands.",
    ],

    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, qualification, regulatory or FTO "
        "authority. AUDIT_ONLY, ceiling EVIDENCE_ONLY.",
        "Novelty here is structural dissimilarity against one CC-BY polymer corpus under four "
        "fingerprint families; it is not patentability, freedom-to-operate, or evidence of any "
        "coating performance advantage.",
        "Does not re-derive or dispute the deduplication correction itself; the 443 -> 350 "
        "canonical dedup, the 36 duplicate groups / 129 duplicate rows, the locked dedup-set "
        "sha256 and R-A07's 5 declared flip cells all reproduce exactly and are carried forward.",
        "Does not modify, delete or re-sign R-A07, V-A07, the two refuting audit receipts, or the "
        "superseded Phase-0 KPI; all are left byte-intact on disk with sha256 recorded in "
        "provenance.",
        "Conformal validity here is conditional on exchangeability of the deduplicated corpus; "
        "deduplication removes the specific violation the exchangeability audit found and does "
        "not certify exchangeability in general.",
    ],

    "provenance": {
        "harness_sha256": {"run_ra07v2.py": harness_sha, "sign_ra07v2.py": signer_sha},
        "inputs_are_read_only": True,
        "input_artifacts_sha256": {
            f"{REL}/evidence/phase0/repairs/R-A07/done/r-a07-novelty-dedup-and-ipda-identity-repair-receipt.v1.dsse.json": r_a07_sha,
            f"{REL}/evidence/phase0/repairs/V-A07/done/v-a07-independent-verify-of-r-a07-receipt.v1.dsse.json": v_a07_sha,
            f"{REL}/evidence/audit/corpus-duplicate-exchangeability-audit-v1/corpus-duplicate-exchangeability-receipt.v1.dsse.json": dedup_sha,
            f"{REL}/evidence/audit/candidate-structure-identity-audit-v1/candidate-structure-identity-audit-receipt.v1.dsse.json": ident_sha,
            "amphora-molecule-generator/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json": genmod_sha,
            "feedback/v1/external_data/openpoly_benchmark/raw/final_polymer_properties_fromliterature.csv": diag["corpus"]["csv_sha256"],
        },
        "originals_byte_intact_after_this_repair": True,
    },

    "checks": diag["checks"],
    "checks_all_pass": diag["checks_all_pass"],

    "self_tests": [
        {"name": "csv_sha_locked", "pass": diag["checks"]["1a_csv_sha_locked"]},
        {"name": "dedup_counts_443_350_129_36", "pass": all(
            diag["checks"][k] for k in ["1b_n_rows_with_Tg_443", "1c_n_canonically_unique_350",
                                        "1d_n_dedupe_350", "1e_n_duplicate_groups_36",
                                        "1f_n_duplicate_rows_129"])},
        {"name": "dedup_canonical_set_sha_matches_locked_value",
         "pass": diag["checks"]["1g_dedup_canonical_set_sha_matches_locked_value"]},
        {"name": "old_ipda_refutation_reproduced_C9H20N2",
         "pass": diag["checks"]["2a_old_signed_ipda_is_C9H20N2_refutation_reproduced"]},
        {"name": "v2_third_independent_ipda_rederivation_C10H22N2",
         "pass": diag["checks"]["2b_v2_rederived_ipda_is_C10H22N2"]},
        {"name": "v2_rederivation_matches_ra07_and_genmod_ground_truth", "pass": (
            diag["checks"]["2c_v2_rederivation_canonical_equals_ra07_corrected"]
            and diag["checks"]["2d_v2_rederivation_canonical_equals_genmod_ground_truth"])},
        {"name": "v2_ipda_constitution_crosschecks", "pass": all(
            diag["checks"][k] for k in ["2f_v2_ipda_one_six_membered_ring",
                                        "2g_v2_ipda_two_primary_amine_nitrogens",
                                        "2h_v2_ipda_three_methyl_carbons"])},
        {"name": "ra07_five_dedup_flip_cells_reproduced", "pass": (
            diag["checks"]["3a_dedup_only_flip_count_reproduces_ra07_disclosed_5"]
            and diag["checks"]["3b_dedup_only_flip_cells_match_ra07_declared_set"])},
        {"name": "va07_undisclosed_structural_flip_reproduced", "pass": (
            diag["checks"]["3c_structure_only_flip_count_reproduces_va07_finding"]
            and diag["checks"]["3d_structure_only_flip_cell_matches_va07"])},
        {"name": "ra07_shipped_table_reproduces_under_old_ipda_all_four_families",
         "pass": diag["checks"]["4a_ra07_shipped_table_reproduces_exactly_under_OLD_ipda_all_20_cells"]},
        {"name": "ipda_nn_shifts_reproduce_va07_measurements",
         "pass": diag["checks"]["4c_ipda_nn_shifts_reproduce_va07_measurements_1e-12"]},
        {"name": "morgan_ipda_nn_unchanged_so_headline_independent_of_defect",
         "pass": diag["checks"]["4d_morgan_family_ipda_nn_unchanged_by_structural_fix"]},
        {"name": "top_level_five_of_five_novel_stands",
         "pass": diag["checks"]["5a_top_level_five_of_five_novel"]},
        {"name": "top_level_matches_ra07_published_values",
         "pass": diag["checks"]["5b_top_level_matches_ra07_published_per_candidate_1e-12"]},
        {"name": "dds_cross_family_a05_still_0_of_4",
         "pass": diag["checks"]["6a_dds_cross_family_a05_still_0_of_4"]},
        {"name": "r_a07_and_v_a07_dsse_signatures_verify_and_key_pinned", "pass": all(
            diag["checks"][k] for k in ["7a_r_a07_dsse_signature_verifies",
                                        "7b_v_a07_dsse_signature_verifies",
                                        "7c_evaluator_key_pinned_in_phase0_trust_store"])},
    ],

    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": (
            "run_ra07v2.py executed twice with distinct output filenames on xbabe2; the "
            "diagnostic is serialized with json.dumps(indent=2, sort_keys=True) each run and "
            "asserted byte-equal before signing. Deterministic: no RNG, no wall-clock, no "
            "network. Leave-one-out calibration alphas are cached once per (family, corpus) and "
            "reused across all four candidate-set/corpus table variants, so every published "
            "table shares one calibration derivation."),
    },

    "attestation": {
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "modifies_existing_receipts": False,
        "modifies_manifest": False,
        "modifies_ledger": False,
        "appends_to_falsification_ledger": False,
        "modifies_mission_front_matter": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "modifies_benchmark_lock": False,
        "modifies_quarantined_data": False,
        "weakens_verifier_or_governance_guard": False,
        "trust_anchored_in_phase0_store": bool(eval_pin),
        "two_replay_sha256_gate": {
            "status": "PASS",
            "byte_identical": canon == runB,
            "canonical_diagnostic_sha256": diag_sha,
            "runB_diagnostic_sha256": sha(runB),
        },
    },

    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "appends_to_falsification_ledger": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "trust_anchored_in_phase0_store": bool(eval_pin),

    "rights_posture": diag["rights_posture"],
    "theory_reference": diag["theory_reference"],

    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "authority": "AUDIT_ONLY",
        "used_for": "AUDIT_ONLY superseding repair receipt under evidence/phase0/repairs/R-A07v2/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing only; no dual-identity ceremony",
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(json.loads(body), indent=2, sort_keys=True).encode()
assert body == body2, "canonical payload serialization not byte-stable"
assert all(t["pass"] for t in body_obj["self_tests"]), "a self test failed"

ptype = "application/vnd.amphora.molecule-novelty-r-a07v2-superseding-repair+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}
out = DONE / "r-a07v2-four-family-ipda-propagation-repair-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# ------------------------------------------------------------- SELF-VERIFY
back = json.loads(out.read_text())
env2 = back["signature"]
body_back = base64.standard_b64decode(env2["payload"])
pae_back = pae(env2["payloadType"], body_back)
Ed25519PublicKey.from_public_bytes(bytes.fromhex(back["evaluator_public_key_hex"])).verify(
    base64.standard_b64decode(env2["signatures"][0]["sig"]), pae_back)
assert env2["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35"), env2["signatures"][0]["keyid"]
assert back["evaluator_key_id"] == eval_key_id
assert json.loads(body_back)["attestation"]["promotes_authority"] is False
assert json.loads(body_back)["top_level_headline_status"]["stands"] is True
print("WROTE", out)
print("receipt_sha256", sha(out.read_bytes()))
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("payload_sha256", sha(body))
print("two_replay_diagnostic_sha256", diag_sha)
print("SELF_VERIFY_OK", True)
