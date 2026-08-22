#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V-A06v2 independent verify receipt (amphora-molecule-generator).

AUDIT_ONLY. Independently verifies R-A06v2 by re-deriving both functionality
conventions from the raw 38 canonical SMILES using an implementation
structurally distinct from BOTH of R-A06v2's own implementations (bond-type
enumeration, no SMARTS string at all), validating the instrument against the
in-tree known_answer_amines ground truth first, running a positive control
(planted defect on a mutated MDA/DDM SMILES) before asserting survival, and
then attacking the convention-choice conclusion against four independent
published/standards sources. Signing pattern replicated from
amphora-molecule-generator/evidence/phase0/repairs/R-A06v2/work/sign_ra06v2.py
(PAE construction, load_seed, payloadType, two-replay gate, self-verify).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-generator"
ITEM = MOD / "evidence/phase0/repairs/V-A06v2"
WORK = ITEM / "work"
DONE = ITEM / "done"
DONE.mkdir(parents=True, exist_ok=True)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

REL = "amphora-molecule-generator"
R_A06V2_DONE = MOD / "evidence/phase0/repairs/R-A06v2/done/molgen-r-a06v2-functionality-convention-repair-receipt.v1.dsse.json"
V_A06_DONE = MOD / "evidence/phase0/repairs/V-A06/done/v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json"
SRC_DIAG = MOD / "evidence/audit/molgen-deterministic-grammar-yield-v1/diagnostic.canonical.json"
ENVELOPE_REF = MOD / "reference/mvp20/data/hardener_stoichiometric_envelope.v1.json"
HARNESS = WORK / "run_va06v2.py"


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
assert diag["verdict"] == "CLAIM_SURVIVED"
assert diag["step1_instrument_validation"]["instrument_validated_before_any_count_asserted"] is True
assert diag["step2_positive_control"]["detected"] is True
assert diag["step2_positive_control"]["control_real_input_does_not_false_fire"] is True
assert diag["step3_rederivation_vs_r_a06v2"]["n_mismatches"] == 0
assert diag["step3_rederivation_vs_r_a06v2"]["headline_reproduced"] is True

r_a06v2_sha = sha(R_A06V2_DONE.read_bytes())
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
    "schema": "amphora.molecule-generator.v-a06v2-independent-verify-receipt.v1",
    "receipt_id": "molgen-v-a06v2-functionality-convention-verify-v1",
    "module_id": REL,
    "module": REL,
    "campaign_item_id": "V-A06v2",
    "verifies": "R-A06v2",
    "run_type": "INDEPENDENT_VERIFY_FUNCTIONALITY_CONVENTION",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "date": "2026-08-05",
    "generated_on_host": "xbabe2",
    "rdkit_version": diag["rdkit_version"],

    "verdict": "CLAIM_SURVIVED",

    "headline": (
        "Independent re-derivation of both functionality conventions from the raw 38 canonical "
        "SMILES, using an RDKit implementation structurally distinct from both implementations "
        "R-A06v2 itself used (bond-type enumeration, no SMARTS pattern at all), reproduces "
        "R-A06v2's published numbers with ZERO mismatches: 0/38 difunctional under active-hydrogen "
        "(active_NH==2), 29/38 with exactly 2 amine centres, all 29 of those active_NH==4 "
        "(tetrafunctional), the two-centre set identical to the tetrafunctional set. The instrument "
        "was validated against the module's own known_answer_amines ground truth (8/8 both "
        "conventions) and fail_closed_decoys (6/6) BEFORE any count was asserted, exactly as "
        "R-A06v2 claims to have done. A positive control -- deliberately demethylating one -NH2 of "
        "MDA/DDM to -CH3 -- was correctly flagged by the instrument (active_nh 4->3, mismatch vs "
        "ground truth), while the unmutated structure did not false-fire. The refutation criterion "
        "for the convention-choice attack (a citable, epoxy-authoritative source defining AHEW / "
        "mix ratio / Flory-Stockmayer functionality on a nitrogen-atom-count basis) was checked "
        "against four independent sources and did not occur: Lee & Neville 1967, Ellis 1993, Flory "
        "1953 and ASTM D2074 are unanimous that reaction stoichiometry and network functionality "
        "for epoxy-amine systems are active-hydrogen-based, and that the nitrogen-atom (amine "
        "value / basicity) count is a recognized, separately-named, non-interchangeable "
        "measurement (ASTM D2074 amine value) that does not set stoichiometry. R-A06v2 SURVIVES "
        "this independent verify on both the arithmetic and the convention-choice conclusion."
    ),

    "refutation_criteria_checked": {
        "criterion_1_rederivation": (
            "WOULD REFUTE if an independent RDKit implementation, built without reference to "
            "R-A06v2's SMARTS string or per-atom loop, disagreed with R-A06v2's published "
            "amine_centres or active_nh value for ANY of the 38 accepted proposals, or with the "
            "aggregate counts (29 two-centre / 0 true-difunctional / 29 tetrafunctional)."),
        "criterion_1_observed": "0/38 mismatches; all four aggregate counts reproduced exactly.",
        "criterion_2_instrument_validity": (
            "WOULD REFUTE (as UNKNOWN/inadmissible) if the independent instrument failed to "
            "reproduce the 8/8 known_answer_amines or 6/6 fail_closed_decoys BEFORE any count on "
            "the 38 was asserted."),
        "criterion_2_observed": "8/8 known_answer_amines matched (both amine_centres and active_nh); 6/6 decoys matched.",
        "criterion_3_positive_control": (
            "WOULD REFUTE the survival (downgrade to UNKNOWN) if the independent instrument failed "
            "to detect a deliberately planted structural defect (demethylated MDA/DDM) in its own "
            "known-answer input, or if it false-fired on the unmutated structure."),
        "criterion_3_observed": "Planted defect detected (active_nh 4->3 vs ground truth); unmutated control did not false-fire.",
        "criterion_4_convention_choice": (
            "WOULD REFUTE the convention-choice conclusion if any published, epoxy-formulation-"
            "authoritative source (handbook, textbook, or ASTM standard) defined AHEW, mix ratio, "
            "or Flory-Stockmayer network functionality f on a nitrogen-atom-count basis rather than "
            "an active-hydrogen (N-H) basis for primary/secondary amine hardeners."),
        "criterion_4_observed": (
            "Checked Lee & Neville 1967 (Handbook of Epoxy Resins), Ellis 1993 (Chemistry and "
            "Technology of Epoxy Resins), Flory 1953 (Principles of Polymer Chemistry) and ASTM "
            "D2074-07(2019); all four define stoichiometry/functionality on the active-hydrogen "
            "basis and treat nitrogen-atom count (amine value) as a distinct, non-interchangeable "
            "titration quantity. No refuting source found."),
    },

    "positive_control": {
        "planted_defect": diag["step2_positive_control"]["planted_defect"],
        "how_planted": diag["step2_positive_control"]["how_planted"],
        "detected": diag["step2_positive_control"]["detected"],
        "evidence": diag["step2_positive_control"]["evidence"],
    },
    "step1_instrument_validation": diag["step1_instrument_validation"],
    "step2_positive_control": diag["step2_positive_control"],
    "step3_rederivation_vs_r_a06v2": {
        k: v for k, v in diag["step3_rederivation_vs_r_a06v2"].items() if k != "per_proposal"
    },
    "step3_per_proposal_table_note": (
        "Full 38-row per-proposal independent re-derivation table is in the two-replay-hashed "
        "diagnostic.canonical.json referenced in provenance; omitted from the signed body only to "
        "keep this receipt to a manageable size -- every aggregate and mismatch count above is "
        "computed over the full table and n_mismatches==0 covers all 38 rows."),
    "attack_on_convention_choice": diag["attack_on_convention_choice"],

    "independent_implementation_note": diag["independent_implementation_note"],

    "carried_forward_r_a06v2_claim": {
        "difunctional_yield_active_hydrogen_convention": 0,
        "two_amine_centre_diamine_count_amine_centre_convention": 29,
        "tetrafunctional_count_active_nh_eq_4": 29,
        "two_amine_centre_set_is_identical_to_tetrafunctional_set": True,
        "n_accepted_proposals": 38,
    },

    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, qualification, regulatory or FTO "
        "authority. AUDIT_ONLY, ceiling EVIDENCE_ONLY.",
        "Does not modify, delete or re-sign R-A06, R-A06v2, V-A06 or any receipt they reference; "
        "all are left byte-intact on disk and their sha256 values are recorded in provenance.",
        "Does not re-derive or dispute the carried-forward Clopper-Pearson interval or "
        "family-resolved IntDiv_1 table; those were checked by V-A06 and R-A06v2 and are out of "
        "scope for this item (V-A06v2 targets the functionality convention only).",
        "The convention-choice literature check is a targeted, four-source check of the specific "
        "refutation criterion (nitrogen-atom-basis stoichiometry definition), not an exhaustive "
        "literature review.",
    ],

    "provenance": {
        "harness_sha256": {"run_va06v2.py": harness_sha, "sign_va06v2.py": signer_sha},
        "inputs_are_read_only": True,
        "input_artifacts_sha256": {
            f"{REL}/evidence/phase0/repairs/R-A06v2/done/molgen-r-a06v2-functionality-convention-repair-receipt.v1.dsse.json": r_a06v2_sha,
            f"{REL}/evidence/phase0/repairs/V-A06/done/v-a06-molecule-generator-repair-verify-receipt.v1.dsse.json": v_a06_sha,
            f"{REL}/evidence/audit/molgen-deterministic-grammar-yield-v1/diagnostic.canonical.json": src_diag_sha,
            f"{REL}/reference/mvp20/data/hardener_stoichiometric_envelope.v1.json": env_ref_sha,
        },
        "originals_byte_intact_after_this_repair": True,
    },

    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "replay_method": (
            "run_va06v2.py executed twice on xbabe2, output serialized with "
            "json.dumps(indent=2, sort_keys=True) each run and asserted byte-equal before signing. "
            "Deterministic: no RNG, no wall-clock, no network. Functionality is re-derived from raw "
            "canonical SMILES by a single independent RDKit implementation (bond-type enumeration) "
            "that is itself structurally distinct from BOTH of R-A06v2's two mutually-independent "
            "implementations (explicit per-atom rule loop; SMARTS query)."),
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
        "methods": "RDKit (BSD-licensed) bond-type enumeration; all published open methods",
        "in_scope": "marine anti-corrosion two-part epoxy-amine coatings (coating chemistry only)",
    },

    "theory_reference": {
        "ahew_and_functionality": "Lee, H. & Neville, K. 1967, Handbook of Epoxy Resins, McGraw-Hill (LCCN 66-23992)",
        "epoxy_formulation_stoichiometry": "Ellis, B. (ed.) 1993, Chemistry and Technology of Epoxy Resins, Blackie/Chapman & Hall, ISBN 978-0-7514-0095-4",
        "gelation_functionality": "Flory, P.J. 1953, Principles of Polymer Chemistry, Cornell Univ. Press, ch. IX (Flory-Stockmayer)",
        "amine_value_standard": "ASTM D2074-07(2019) Standard Test Methods for Total, Primary, Secondary, and Tertiary Amine Values",
        "toolkit": f"RDKit {diag['rdkit_version']}",
    },

    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "authority": "AUDIT_ONLY",
        "used_for": "AUDIT_ONLY independent verify receipt under evidence/phase0/repairs/V-A06v2/done/",
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

ptype = "application/vnd.amphora.molecule-generator-v-a06v2-independent-verify+json"
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
out = DONE / "v-a06v2-molecule-generator-independent-verify-receipt.v1.dsse.json"
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
assert json.loads(body_back)["verdict"] == "CLAIM_SURVIVED"
print("WROTE", out)
print("receipt_sha256", sha(out.read_bytes()))
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("payload_sha256", sha(body))
print("two_replay_diagnostic_sha256", diag_sha)
print("SELF_VERIFY_OK", True)
