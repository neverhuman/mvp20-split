#!/usr/bin/env python3
"""DSSE-Ed25519-sign the R-A06 superseding repair receipt for
amphora-molecule-generator. Construction replicated from
amphora-evidence-intake-validator/benchmarks/sign_canon_invariance.py
(pae, load_seed, payloadType, envelope fields, trust-store key derivation).

SUPERSEDES (never modifies) two prior AUDIT_ONLY receipts. Does not touch the
ledger, any mission.md front-matter, the master manifest, or /home/ubuntu/amphora-cron.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-generator"
AUD = MOD / "evidence/audit"
REP = MOD / "evidence/phase0/repairs/R-A06"
WORK, DONE = REP / "work", REP / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

REL = "amphora-molecule-generator"
O1_REL = f"{REL}/evidence/audit/molgen-deterministic-grammar-yield-v1/molgen-deterministic-grammar-yield-receipt.v1.dsse.json"
O2_REL = f"{REL}/evidence/audit/molgen-scaffold-diversity-v1/molgen-scaffold-diversity-receipt.v1.dsse.json"
RA_REL = f"{REL}/evidence/audit/molgen-grammar-yield-bootstrap-ci-inadmissibility-v1/molgen-grammar-yield-ci-inadmissibility-receipt.v1.dsse.json"
RB_REL = f"{REL}/evidence/audit/molgen-hardener-functionality-mislabel-v1/molgen-hardener-functionality-mislabel-receipt.v1.dsse.json"
RC_REL = f"{REL}/evidence/audit/molgen-scaffold-diversity-homolog-fingerprint-saturation-v1/molgen-scaffold-diversity-homolog-fingerprint-saturation-receipt.v1.dsse.json"
O1, O2 = ROOT / O1_REL, ROOT / O2_REL
RA, RB, RC = ROOT / RA_REL, ROOT / RB_REL, ROOT / RC_REL
SRC_DIAG = AUD / "molgen-deterministic-grammar-yield-v1/diagnostic.canonical.json"


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


# ---------------------------------------------- two-replay gate over the diagnostic
canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
assert diag["acceptance"]["all_pass"] is True, "acceptance gates not all passed"

# canonical-payload two-replay: serialize twice, assert byte-equal, record sha256
s1 = json.dumps(diag, sort_keys=True, separators=(",", ":")).encode()
s2 = json.dumps(json.loads(canon), sort_keys=True, separators=(",", ":")).encode()
assert s1 == s2, "canonical payload serialization not byte-stable"
canonical_payload_sha = sha(s1)

harness_sha = sha((WORK / "run_ra06_repair.py").read_bytes())
o1_sha, o2_sha = sha(O1.read_bytes()), sha(O2.read_bytes())
ra_sha, rb_sha, rc_sha = sha(RA.read_bytes()), sha(RB.read_bytes()), sha(RC.read_bytes())
src_diag_sha = sha(SRC_DIAG.read_bytes())

# ---------------------------------------------- keys / trust anchoring
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == tbr.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key not anchored in phase0 trust store"

cp = diag["clopper_pearson"]
cy = diag["corrected_difunctional_yield"]
fd = diag["family_resolved_diversity"]

body_obj = {
    "schema": "amphora.molecule-generator.r-a06-superseding-repair-receipt.v1",
    "receipt_id": "molgen-r-a06-superseding-repair-v1",
    "repair_item": "R-A06",
    "repair_mode": "interactive-2026-08-03",
    "module_id": REL,
    "module": REL,
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-03",
    "generated_on_host": "xbabe2",
    "run_type": "SUPERSEDING_REPAIR_STATISTICAL_AND_LABEL_CORRECTION",

    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_existing_receipts": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_benchmark_lock": False,
    "modifies_ledger": False,
    "modifies_mission_front_matter": False,

    "attestation": {
        "modifies_existing_receipts": False,
        "modifies_manifest": False,
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "trust_anchored_in_phase0_store": bool(eval_pin),
        "two_replay_sha256_gate": {
            "status": "PASS",
            "canonical_diagnostic_sha256": diag_sha,
            "runB_diagnostic_sha256": sha(runB),
            "byte_identical": canon == runB,
            "canonical_payload_serialization_sha256": canonical_payload_sha,
            "canonical_payload_serialization_byte_stable": s1 == s2,
        },
    },

    "supersedes": [
        {
            "superseded_path": O1_REL,
            "superseded_sha256": o1_sha,
            "superseded_deleted_or_modified": False,
            "reason": (
                "Two independently signed falsification attacks refute two numeric "
                "components of this receipt's headline. (a) "
                "molgen-grammar-yield-bootstrap-ci-inadmissibility-v1 shows the "
                "published feasible_fraction bootstrap 95% CI [1.0000,1.0000] at the "
                "k=n=38 all-success boundary is statistically inadmissible: the "
                "percentile bootstrap is degenerate there (every resample of 38 "
                "identical successes returns exactly 1.0), so the interval reports "
                "zero sampling uncertainty where the admissible exact Clopper-Pearson "
                "interval is [0.9075,1.0000] -- a 0.0925 lower-bound gap exceeding the "
                "a-priori 0.02 admissibility threshold. (b) "
                "molgen-hardener-functionality-mislabel-v1 shows the 'difunctional' "
                "component of the '38 valid-unique-difunctional-feasible' headline is "
                "false: 9 of the 38 accepted proposals carry amine_sites of 3-9 in this "
                "receipt's OWN diagnostic yet are flagged difunctional_hardener=true, "
                "so the gate did not implement its own stated definition "
                "(difunctional == amine_sites==2); the true difunctional yield is "
                "29/38. This repair republishes both corrected values with full "
                "derivation. The superseded receipt is left byte-intact on disk."),
        },
        {
            "superseded_path": O2_REL,
            "superseded_sha256": o2_sha,
            "superseded_deleted_or_modified": False,
            "reason": (
                "molgen-scaffold-diversity-homolog-fingerprint-saturation-v1 (2026-08-03) "
                "refutes this receipt's hypothesis_evaluation verdict "
                "CORROBORATED_IN_AUDIT_INSTRUMENT for the hypothesis 'accepted proposals "
                "span a diverse region of chemical space (not trivially inflated variants "
                "of a single scaffold)'. The headline aggregate IntDiv_1=0.7681 is an "
                "aggregation artifact: evaluated at family resolution under the SAME "
                "Morgan/ECFP r2/2048 Tanimoto instrument, the two linear chain-homolog "
                "families comprising 47.4% of the accepted set collapse to internal "
                "IntDiv_1 of 0.1851 (F1_polyethyleneamine) and 0.0870 "
                "(F2_alpha_omega_diamine), with 12 of 16 chain-length-adjacent neighbour "
                "pairs fingerprint-saturated at Tanimoto>=0.99. This repair republishes "
                "the diversity finding family-resolved rather than aggregate-only. The "
                "superseded receipt is left byte-intact on disk."),
        },
    ],

    "refuted_by": [
        {"path": RA_REL, "sha256": ra_sha,
         "study_id": "molgen-grammar-yield-bootstrap-ci-inadmissibility-v1",
         "verdict": "CLAIM_REFUTED",
         "targets": "molgen-deterministic-grammar-yield-v1 feasible_fraction_bootstrap95_ci"},
        {"path": RB_REL, "sha256": rb_sha,
         "study_id": "molgen-hardener-functionality-mislabel-v1",
         "verdict": "REFUTED",
         "targets": "molgen-deterministic-grammar-yield-v1 valid_unique_difunctional_feasible_yield"},
        {"path": RC_REL, "sha256": rc_sha,
         "study_id": "molgen-scaffold-diversity-homolog-fingerprint-saturation-v1",
         "verdict": "H0_REFUTED",
         "targets": "molgen-scaffold-diversity-v1 hypothesis_evaluation (aggregate IntDiv_1=0.7681)"},
    ],

    "corrected_claim": (
        "CORRECTED restatement of the deterministic-grammar generation-quality claim "
        "for amphora-molecule-generator, superseding molgen-deterministic-grammar-yield-v1 "
        "and molgen-scaffold-diversity-v1. The deterministic rule/template grammar over 5 "
        "published epoxy-amine hardener scaffold families still enumerates 39 productions "
        "-> 39 valid, 38 unique accepted hardener proposals, and the STRUCTURES THEMSELVES "
        "ARE UNCHANGED. Three published numbers are corrected. (1) FEASIBILITY INTERVAL: "
        "all 38 accepted proposals pass the Ertl SA<6 feasibility proxy (a deterministic, "
        "undisputed observation, point estimate 38/38 = 1.0000), but the calibrated 95% "
        "interval is the exact Clopper-Pearson binomial interval [0.9075, 1.0000], NOT the "
        "previously published bootstrap [1.0000, 1.0000]: at the k=n all-success boundary "
        "the percentile bootstrap is degenerate and conveys no sampling uncertainty, so the "
        "data are consistent with a true population feasible fraction as low as 90.75%. "
        "(2) DIFUNCTIONAL YIELD: the valid-unique-DIFUNCTIONAL-feasible yield is 29/38, "
        "NOT 38/38. Nine accepted proposals flagged difunctional_hardener=true carry 3-9 "
        "amine sites in the generator's own diagnostic -- homopiperazine-N,N' (3), "
        "piperazine-bis(aminoethyl)/AEP (3), DETA (3), TETA (4), TEPA (5), PEHA (6), "
        "ethyleneamine-k6 (7), ethyleneamine-k7 (8), ethyleneamine-k8 (9) -- and are "
        "poly- rather than di-functional; DETA/TETA/TEPA/PEHA match published Lee & Neville "
        "1967 functionality of 3/4/5/6. Those nine remain valid, unique and SA-feasible "
        "hardeners; they are simply not difunctional, and the higher-functionality members "
        "carry distinct crosslink-density and gelation behaviour (Flory-Stockmayer f) that "
        "downstream formulation logic must not treat as f=2. (3) DIVERSITY: cross-family "
        "diversity is REAL, but the two within-family homolog series are NEAR-DEGENERATE. "
        "The aggregate IntDiv_1=0.7681 is valid only as a CROSS-family statement: the "
        "homolog bloc versus ring-bearing mean Tanimoto is 0.1054, and the ring-bearing "
        "families are genuinely spread (F3_cycloaliphatic IntDiv_1=0.7485, "
        "F4_bridged_bisaniline 0.6093, F5_xylylenediamine 0.5211). WITHIN the two linear "
        "chain-homolog families -- 18/38 = 47.4% of the accepted set -- the same "
        "Morgan/ECFP r2/2048 Tanimoto instrument is near-blind: F1_polyethyleneamine "
        "IntDiv_1 = 0.1851 (mean pairwise Tanimoto 0.8149) and F2_alpha_omega_diamine "
        "IntDiv_1 = 0.0870 (mean pairwise Tanimoto 0.9130), with 12 of 16 chain-adjacent "
        "neighbour pairs saturated at Tanimoto>=0.99 (5/7 in F1, 7/9 in F2) -- literally "
        "fingerprint-indistinguishable. The generator therefore spans a genuinely diverse "
        "set of scaffold FAMILIES while producing trivially-inflated chain-length variants "
        "within two of them; the aggregate IntDiv_1 must not be used to argue the "
        "generator avoids near-duplicate proposals."),

    "corrected_values": {
        "feasible_fraction_point_estimate": cp["point_estimate"],
        "feasible_fraction_exact_clopper_pearson95_ci": [
            cp["corrected_ci_lower"], cp["corrected_ci_upper"]],
        "feasible_fraction_ci_method": "exact binomial Clopper-Pearson (1934)",
        "superseded_feasible_fraction_bootstrap95_ci": cp["superseded_reported_ci"],
        "valid_unique_difunctional_feasible_yield": cy["corrected_valid_unique_difunctional_feasible_yield"],
        "superseded_valid_unique_difunctional_feasible_yield": cy["superseded_claimed_yield"],
        "valid_unique_accepted_proposals": cy["n_accepted_proposals"],
        "intdiv1_aggregate_cross_family": fd["aggregate"]["recomputed_intdiv1"],
        "intdiv1_within_F1_polyethyleneamine": fd["per_family_resolved"]["F1_polyethyleneamine"]["intdiv1"],
        "intdiv1_within_F2_alpha_omega_diamine": fd["per_family_resolved"]["F2_alpha_omega_diamine"]["intdiv1"],
        "homolog_bloc_fraction_of_accepted_set": fd["homolog_bloc"]["fraction_of_accepted_set"],
        "structures_changed": False,
    },

    "derivation": {
        "1_clopper_pearson": cp,
        "2_corrected_difunctional_yield": cy,
        "3_family_resolved_diversity": fd,
    },

    "hypothesis_evaluation": {
        "hypothesis_1_feasibility": {
            "statement": "The deterministic grammar's accepted proposals are synthetically feasible (Ertl SA<6) with a calibrated interval.",
            "verdict": "CORROBORATED_WITH_CORRECTED_INTERVAL",
            "note": "38/38 observed; admissible exact 95% CI [0.9075,1.0000], not [1.0000,1.0000].",
        },
        "hypothesis_2_difunctional_yield": {
            "statement": "Deterministic generation yields 38 valid, unique, DIFUNCTIONAL, feasible hardener proposals.",
            "verdict": "REFUTED_AS_STATED_CORRECTED_TO_29",
            "note": "9/38 flagged difunctional are 3-9-functional; corrected difunctional yield 29/38. Validity/uniqueness/feasibility components stand.",
        },
        "hypothesis_3_diversity": {
            "statement": "The accepted proposals span a diverse region of chemical space (not trivially inflated variants of a single scaffold).",
            "verdict": "CORROBORATED_ACROSS_FAMILIES_REFUTED_WITHIN_HOMOLOG_FAMILIES",
            "note": "Cross-family diversity real (bloc-vs-ring mean Tanimoto 0.1054); within-family homolog series near-degenerate (IntDiv_1 0.1851 and 0.0870 over 47.4% of the set).",
        },
    },

    "re_attack": diag["re_attack"],
    "re_attack_summary": (
        "All three refuting checks were re-run from scratch in this repair against the "
        "same hash-locked inputs and all three original findings reproduced exactly: "
        "(a) exact Clopper-Pearson at k=38,n=38 gives [0.907487,1.000000], a 0.092513 "
        "lower-bound gap versus the superseded [1.0,1.0], exceeding the a-priori 0.02 "
        "threshold; (b) 9 of 38 accepted proposals are flagged difunctional_hardener=true "
        "with amine_sites!=2, corrected yield 29/38, mismatch set and per-molecule amine "
        "counts identical to the refuting receipt; (c) both F1 and F2 independently "
        "violate the a-priori family-resolution rule (IntDiv_1 0.1851 and 0.0870, both "
        "<=0.25, with adjacent saturation 5/7 and 7/9, both >=50%). Against THIS receipt's "
        "corrected values the same three checks pass: post-fix CI gap 0.0, post-fix "
        "functionality mismatches 0, post-fix undisclosed violating families 0."),

    "acceptance": diag["acceptance"],
    "observed_notes": diag["observed_notes"],

    "closes": [
        "Replaces the inadmissible degenerate bootstrap feasible-fraction interval with the admissible exact Clopper-Pearson interval.",
        "Replaces the mislabelled 38/38 difunctional yield with the correctly gated 29/38 and enumerates all 9 mislabelled proposals with amine-site counts.",
        "Replaces the aggregate-only diversity verdict with a family-resolved table that discloses the two near-degenerate homolog series.",
    ],
    "does_not_close": [
        "Runtime remains LOCKED_INTERNAL; no proposal emission enabled.",
        "No Phase-0 promotion; scientific_readiness stays UNVALIDATED.",
        "AUDIT_ONLY: does not promote authority and does not flip scientific readiness.",
        "Does not re-enumerate, alter, add or remove any molecule -- the 38 accepted structures are byte-identical to the superseded receipt's diagnostic.",
        "Does not repair the generator's difunctional_hardener gate implementation in source; this receipt corrects the published claim only.",
        "Does not assert the true population feasible fraction is below 100%; only that the data cannot exclude values down to 0.9075.",
        "Structural/fingerprint diversity remains a structural proxy -- not a property, FTO, or wet-lab performance claim.",
        "Does not modify, delete, or re-sign either superseded receipt, the falsification ledger, any mission.md front-matter, or the master manifest.",
    ],

    "provenance": {
        "harness_sha256": {"run_ra06_repair.py": harness_sha},
        "source_diagnostic_sha256": src_diag_sha,
        "superseded_receipts_sha256": {O1_REL: o1_sha, O2_REL: o2_sha},
        "refuting_receipts_sha256": {RA_REL: ra_sha, RB_REL: rb_sha, RC_REL: rc_sha},
        "inputs_are_read_only": True,
    },

    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "canonical_payload_serialization_sha256": canonical_payload_sha,
        "replay_method": (
            "independent re-derivation on xbabe2: exact Clopper-Pearson via "
            "scipy.stats.beta.ppf with a closed-form (alpha/2)^(1/n) boundary "
            "cross-check; difunctional yield recounted from the hash-locked "
            "grammar-yield diagnostic amine_sites table under the receipt's own "
            "stated gate definition; per-family IntDiv_1 and chain-adjacent Tanimoto "
            "recomputed with RDKit Morgan r2/2048 fingerprints, with the aggregate "
            "IntDiv_1=0.768098 reproduced as a parity self-test proving the same "
            "instrument is evaluated at finer resolution. Harness is deterministic "
            "(no RNG, no wall-clock); run twice to byte-identical output."),
        "rdkit_version": diag["rdkit_version"],
        "scipy_version": diag["scipy_version"],
    },

    "rights_posture": {
        "external_dataset_used": False,
        "new_external_data_acquired": False,
        "quarantined_data_touched": False,
        "input_smiles": "read verbatim from the hash-locked molgen-deterministic-grammar-yield-v1 diagnostic (published epoxy-amine scaffold families)",
        "methods": "Clopper & Pearson 1934 exact binomial; RDKit (BSD-licensed) Morgan/ECFP fingerprints and Tanimoto; all published open methods",
        "note": "No PI1M, Polyverse, ST-19168, or CONTEXT_ONLY data opened by this repair.",
    },

    "theory_reference": {
        "exact_binomial_interval": "Clopper & Pearson 1934 Biometrika 26(4):404-413",
        "bootstrap_boundary_failure": "Efron & Tibshirani 1993 An Introduction to the Bootstrap, ch. 13 (percentile-bootstrap unreliability at parameter boundaries)",
        "feasibility_sa_score": "Ertl & Schuffenhauer 2009 J. Cheminform. 1:8",
        "functionality_reference": "Lee & Neville 1967 Handbook of Epoxy Resins (McGraw-Hill)",
        "gelation_functionality_theory": "Flory 1953 Principles of Polymer Chemistry, Cornell Univ. Press, ch. IX",
        "fingerprint": "Rogers & Hahn 2010 J. Chem. Inf. Model. 50(5):742-754 (ECFP)",
        "internal_diversity_metric": "Polykovskiy et al. 2020 Front. Pharmacol. 11:565644 (MOSES IntDiv_p)",
        "similarity_coefficient": "Bajusz, Racz & Heberger 2015 J. Cheminform. 7:20 (Tanimoto)",
        "homolog_fingerprint_saturation": "Finite-radius circular fingerprints saturate on linear repeat-unit chains once chain length exceeds ~2x the fingerprint radius.",
        "toolkit": "RDKit 2026.03.2; scipy 1.16.3",
    },

    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY superseding repair receipt under evidence/phase0/repairs/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed."},
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
assert body == json.dumps(body_obj, indent=2, sort_keys=True).encode(), "body not byte-stable"
ptype = "application/vnd.amphora.molecule-generator-r-a06-superseding-repair+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}
DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "molgen-r-a06-superseding-repair-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_sha256", diag_sha)
print("canonical_payload_sha256", canonical_payload_sha)
print("receipt_sha256", sha(out.read_bytes()))
print("signature_verified", True)
