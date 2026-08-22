#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-A06v2 superseding repair receipt (amphora-molecule-generator).

AUDIT_ONLY. Supersedes R-A06's "difunctional" LABEL by path+sha; leaves R-A06,
V-A06 and every artifact they reference byte-intact. Does not promote authority,
flip scientific_readiness, or touch the manifest, ledger, mission front-matter,
locked datasets or any signed Phase-0 KPI.

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
MOD = ROOT / "amphora-molecule-generator"
REP = MOD / "evidence/phase0/repairs/R-A06v2"
WORK = REP / "work"
DONE = REP / "done"
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

REL = "amphora-molecule-generator"
R_A06_DONE = MOD / "evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json"
V_A06_DONE = MOD / "evidence/phase0/repairs/V-A06/done/v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json"
SRC_DIAG = MOD / "evidence/audit/molgen-deterministic-grammar-yield-v1/diagnostic.canonical.json"
ENVELOPE_REF = MOD / "reference/mvp20/data/hardener_stoichiometric_envelope.v1.json"
HARNESS = WORK / "run_ra06v2.py"


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

cnt = diag["counts_under_each_convention"]
n_total = cnt["n_accepted_proposals"]
n_A2 = cnt["conventionA_n_with_exactly_2_amine_centres"]
n_B2 = cnt["conventionB_n_with_active_nh_eq_2_true_difunctional"]
n_B4 = cnt["conventionB_n_with_active_nh_eq_4_tetrafunctional"]

r_a06_sha = sha(R_A06_DONE.read_bytes())
v_a06_sha = sha(V_A06_DONE.read_bytes())
src_diag_sha = sha(SRC_DIAG.read_bytes())
env_ref_sha = sha(ENVELOPE_REF.read_bytes())
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

body_obj = {
    "schema": "amphora.molecule-generator.r-a06v2-superseding-repair-receipt.v1",
    "receipt_id": "molgen-r-a06v2-functionality-convention-repair-v1",
    "module_id": REL,
    "module": REL,
    "repair_item": "R-A06v2",
    "repair_mode": "interactive-2026-08-04",
    "run_type": "SUPERSEDING_REPAIR_FUNCTIONALITY_CONVENTION_CORRECTION",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": diag["date"],
    "generated_on_host": "xbabe2",
    "rdkit_version": diag["rdkit_version"],

    "headline": diag["headline"],

    "corrected_claim": (
        "CORRECTED restatement of the FUNCTIONALITY LABEL that repair R-A06 attached to the "
        "amphora-molecule-generator deterministic-grammar hardener universe. The 38 accepted "
        "structures are unchanged, and R-A06's two OTHER corrections (the exact Clopper-Pearson "
        "feasible-fraction interval and the family-resolved IntDiv_1 diversity table) stand -- the "
        "independent verify V-A06 reproduced both exactly and this receipt re-derives both again. "
        "What is corrected is the word 'difunctional'. R-A06 published '29/38 valid-unique-"
        "DIFUNCTIONAL-feasible' using the gate amine_sites == 2, i.e. a count of nitrogen ATOMS. "
        "Under the active-hydrogen functionality convention -- the convention that actually governs "
        "epoxy-amine stoichiometry (AHEW = M / n_activeH, Lee & Neville 1967), mix ratio "
        "(phr = 100 * AHEW / EEW) and Flory-Stockmayer network functionality f, and the convention "
        f"this module's own in-tree reference file already encodes as ground truth -- {n_B2} of "
        f"{n_total} accepted proposals are difunctional (active_NH == 2). The {n_A2} proposals R-A06 "
        f"called 'difunctional' are primary,primary DIAMINES: they have exactly 2 amine CENTRES and "
        f"active_NH == 4, i.e. they are TETRAfunctional. Both numbers are published here side by "
        "side under explicit, unambiguous definitions, together with the per-proposal table, so the "
        "label cannot be misread again. The generator is NOT thereby shown to be deficient: every "
        "one of the 38 accepted proposals has active_NH >= 3 and is therefore network-forming "
        "against difunctional DGEBA; under the active-hydrogen convention an f = 2 hardener would "
        "be a non-crosslinking chain extender, so '0/38 difunctional' is a correct and "
        "product-appropriate description of this hardener set, not a failure of it."),

    "convention_definitions": diag["convention_definitions"],

    "corrected_values": {
        "n_accepted_proposals": n_total,
        "convention_used_for_the_word_difunctional": "active_hydrogen_functionality (active_NH == 2)",
        "difunctional_yield_active_hydrogen_convention": n_B2,
        "two_amine_centre_diamine_count_amine_centre_convention": n_A2,
        "tetrafunctional_count_active_nh_eq_4": n_B4,
        "two_amine_centre_set_is_identical_to_tetrafunctional_set": cnt[
            "two_centre_set_is_identical_to_tetrafunctional_set"],
        "n_network_forming_active_nh_ge_3": cnt["n_network_forming_active_nh_ge_3"],
        "histogram_amine_centres_conventionA": cnt["conventionA_histogram_amine_centres"],
        "histogram_active_nh_conventionB": cnt["conventionB_histogram_active_nh"],
        "superseded_r_a06_difunctional_yield": 29,
        "superseded_r_a06_difunctional_yield_definition_used": "amine_sites == 2 (nitrogen-ATOM count)",
        "structures_changed": False,
    },

    "per_proposal_table": diag["per_proposal_table"],

    "instrument_validation": diag["instrument_validation"],

    "mda_ddm_external_anchor": diag["mda_ddm_external_anchor"],

    "product_relevance_of_the_convention_choice": {
        "statement": (
            "The choice is not cosmetic. For every one of the 29 two-centre proposals the "
            "active-hydrogen count is exactly twice the amine-centre count (all are "
            "primary,primary diamines), so using amine centres as functionality doubles AHEW and "
            "therefore doubles the computed hardener mix ratio phr at 1:1 epoxide:amine-hydrogen "
            "stoichiometry -- a 2x hardener overdose."),
        "measured_phr_overdose_ratio_for_all_29": 2.0,
        "worked_example_mda_ddm_vs_dgeba_eew_190": {
            "ahew_correct_active_hydrogen": diag["mda_ddm_external_anchor"]["ahew_correct_conventionB_g_per_eq"],
            "ahew_wrong_amine_centre": diag["mda_ddm_external_anchor"]["ahew_if_wrongly_using_conventionA_g_per_eq"],
            "phr_correct": next(r["phr_correct_conventionB_vs_dgeba_eew190"]
                                for r in diag["per_proposal_table"] if r["name"] == "MDA/DDM(methylene)"),
            "phr_wrong": next(r["phr_if_wrongly_using_conventionA_vs_dgeba_eew190"]
                              for r in diag["per_proposal_table"] if r["name"] == "MDA/DDM(methylene)"),
        },
        "flory_stockmayer_note": (
            "Under the active-hydrogen convention f = 2 denotes a chain extender that cannot gel "
            "with difunctional DGEBA. All 38 accepted proposals have f >= 3, so the corrected "
            "count of 0 difunctional hardeners is the desirable outcome for a thermoset marine "
            "coating, not a defect."),
    },

    "carried_forward_corrections_confirmed_by_v_a06": diag["carried_forward_corrections_confirmed_by_v_a06"],

    "values_read_from_v_a06_verify_receipt_bytes": diag["values_read_from_v_a06_verify_receipt_bytes"],

    "supersedes": [{
        "superseded_path": f"{REL}/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json",
        "superseded_sha256": r_a06_sha,
        "superseded_deleted_or_modified": False,
        "scope_of_supersession": (
            "The FUNCTIONALITY LABEL only: R-A06's corrected_values."
            "valid_unique_difunctional_feasible_yield = 29 and every use of the word "
            "'difunctional' in its corrected_claim, closes[] and headline. R-A06's other two "
            "corrections (exact Clopper-Pearson feasible-fraction interval; family-resolved "
            "IntDiv_1 diversity table) are NOT superseded -- they are re-derived here and carried "
            "forward unchanged."),
        "reason": (
            "The independent verify V-A06 (verdict CLAIM_REFUTED) reproduced R-A06's arithmetic "
            "exactly and then refuted its label: R-A06 republished 29/38 as 'difunctional' under "
            "the gate amine_sites == 2 (a nitrogen-ATOM count), but under the standard "
            "active-hydrogen functionality convention all 29 measure active_NH == 4 "
            "(tetrafunctional) and 0 of the 38 measure active_NH == 2. V-A06 declined to assert a "
            "new headline, leaving it to this v2. This receipt re-derives both conventions "
            "independently from the raw canonical SMILES with two mutually-independent RDKit "
            "implementations, validates the instrument against this module's own in-tree "
            "known_answer_amines ground truth (Lee & Neville 1967), and publishes both counts "
            "explicitly."),
    }],

    "refuted_by": [{
        "path": f"{REL}/evidence/phase0/repairs/V-A06/done/v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json",
        "sha256": v_a06_sha,
        "verify_item": "V-A06",
        "verdict": "CLAIM_REFUTED",
        "targets": "R-A06 corrected_values.valid_unique_difunctional_feasible_yield label ('difunctional')",
        "arithmetic_disputed": False,
        "note": (
            "V-A06 CONFIRMED R-A06's arithmetic reproduces exactly (Clopper-Pearson to 4dp, yield "
            "29 under its own stated gate, family IntDiv_1 to 4dp, 0 mismatches on a fresh RDKit "
            "re-derivation). This v2 does not re-litigate any of that; it fixes the residual "
            "labelling defect V-A06 named."),
    }],

    "closes": [
        "Replaces the word 'difunctional' as applied to the 29 two-amine-centre proposals: they "
        "are diamines and, under the active-hydrogen convention, TETRAfunctional (active_NH = 4).",
        f"Publishes the difunctional yield under the product-relevant active-hydrogen convention: "
        f"{n_B2} of {n_total}.",
        f"Publishes, side by side and separately named, the amine-centre count that R-A06 actually "
        f"measured: {n_A2} of {n_total} proposals have exactly 2 amine centres.",
        "Fixes the portfolio convention for the word 'difunctional' to the active-hydrogen count "
        "and records why (AHEW / mix-ratio / Flory-Stockmayer f all key off active hydrogens).",
        "Validates the functionality instrument against the module's own in-tree "
        "known_answer_amines ground truth (8/8 on both conventions) and fail_closed_decoys (6/6) "
        "before any count is asserted.",
    ],

    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, qualification, regulatory or FTO "
        "authority. AUDIT_ONLY, ceiling EVIDENCE_ONLY.",
        "Does not claim the generator is deficient: it re-labels, it does not re-score. The 38 "
        "accepted structures are byte-for-byte unchanged and all 38 remain valid, unique, "
        "SA-feasible and network-forming (active_NH >= 3).",
        "Does not re-derive or dispute R-A06's Clopper-Pearson interval or family-resolved IntDiv_1 "
        "table as findings -- both are re-computed here and reproduce exactly, and are carried "
        "forward, not superseded.",
        "Does not assert any measured cure kinetics, gel time, Tg or crosslink density; AHEW and "
        "phr values here are definitional quotients (M / n_activeH; 100 * AHEW / EEW), not "
        "measurements.",
        "Does not modify, delete or re-sign R-A06, V-A06, or any receipt they reference; all are "
        "left byte-intact on disk and their sha256 values are recorded in provenance.",
        "The radius-3 fingerprint stress caveat V-A06 raised against the F1 near-degeneracy finding "
        "is out of scope here and is neither resolved nor contradicted by this receipt.",
    ],

    "provenance": {
        "harness_sha256": {"run_ra06v2.py": harness_sha, "sign_ra06v2.py": signer_sha},
        "inputs_are_read_only": True,
        "input_artifacts_sha256": {
            f"{REL}/evidence/phase0/repairs/R-A06/done/molgen-r-a06-superseding-repair-receipt.v1.dsse.json": r_a06_sha,
            f"{REL}/evidence/phase0/repairs/V-A06/done/v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json": v_a06_sha,
            f"{REL}/evidence/audit/molgen-deterministic-grammar-yield-v1/diagnostic.canonical.json": src_diag_sha,
            f"{REL}/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json": env_ref_sha,
        },
        "originals_byte_intact_after_this_repair": True,
    },

    "checks": diag["checks"],
    "checks_all_pass": diag["checks_all_pass"],

    "acceptance": {
        "known_answer_active_nh_8_of_8": diag["checks"]["1a_known_answer_active_nh_all_match"],
        "known_answer_amine_centres_8_of_8": diag["checks"]["1b_known_answer_amine_centres_all_match"],
        "fail_closed_decoys_6_of_6": diag["checks"]["1c_decoys_active_nh_all_match"],
        "two_independent_implementations_agree": (
            diag["checks"]["1d_two_implementations_agree_on_ground_truth_set"]
            and diag["checks"]["2a_two_implementations_agree_on_all_38"]),
        "reproduces_every_value_measured_by_v_a06": all(
            diag["checks"][k] for k in diag["checks"] if k.startswith("3")
            and isinstance(diag["checks"][k], bool)),
        "carried_forward_corrections_reproduce": (
            diag["checks"]["4a_clopper_pearson_reproduces_r_a06_and_va06_4dp"]
            and diag["checks"]["4b_family_intdiv1_F1_reproduces_va06_1e-9"]
            and diag["checks"]["4c_family_intdiv1_F2_reproduces_va06_1e-9"]),
        "structures_unchanged": True,
        "all_pass": diag["checks_all_pass"],
    },

    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": (
            "run_ra06v2.py executed twice with distinct output filenames on xbabe2; the "
            "diagnostic is serialized with json.dumps(indent=2, sort_keys=True) each run and "
            "asserted byte-equal before signing. Deterministic: no RNG, no wall-clock, no "
            "network. Functionality is re-derived from the raw canonical SMILES by two "
            "mutually-independent RDKit implementations (explicit per-atom rule loop; SMARTS "
            "query) which are required to agree atom-index-for-atom-index."),
    },

    "attestation": {
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "modifies_existing_receipts": False,
        "modifies_manifest": False,
        "modifies_ledger": False,
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
    "modifies_ledger": False,
    "modifies_mission_front_matter": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_benchmark_lock": False,
    "trust_anchored_in_phase0_store": bool(eval_pin),

    "rights_posture": {
        "external_dataset_used": False,
        "new_external_data_acquired": False,
        "quarantined_data_touched": False,
        "redistributes_third_party_dataset": False,
        "input_smiles": (
            "read verbatim from the hash-locked molgen-deterministic-grammar-yield-v1 diagnostic "
            "(published epoxy-amine scaffold families) and from this module's own in-tree "
            "hardener_stoichiometric_envelope.v1.json known-answer block"),
        "methods": (
            "RDKit (BSD-licensed) SMARTS / Morgan-ECFP / Tanimoto; scipy exact binomial; all "
            "published open methods"),
        "in_scope": "marine anti-corrosion two-part epoxy-amine coatings (coating chemistry only)",
    },

    "theory_reference": diag["theory_reference"],

    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "authority": "AUDIT_ONLY",
        "used_for": "AUDIT_ONLY superseding repair receipt under evidence/phase0/repairs/R-A06v2/done/",
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

ptype = "application/vnd.amphora.molecule-generator-r-a06v2-superseding-repair+json"
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
out = DONE / "molgen-r-a06v2-functionality-convention-repair-receipt.v1.dsse.json"
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
print("WROTE", out)
print("receipt_sha256", sha(out.read_bytes()))
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("payload_sha256", sha(body))
print("two_replay_diagnostic_sha256", diag_sha)
print("SELF_VERIFY_OK", True)
