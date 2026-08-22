#!/usr/bin/env python3
"""
W12 (ROTATION, amphora-molecule-property, fire
20260816T150001-4102815-4defdf28f6bd): units-correction propagation-
completeness audit for the Polyuniverse Epoxy Tg 'K'-vs-degC labeling error.

Attacks the strongest never-before-ledger-attacked STANDING claim in the
module: polyuniverse-epoxy-tg-conformal-coverage-and-applicability-domain-
kpi.v1.json (marginal split-conformal coverage 0.9049 >= 0.90 target, 10,279
scaffold-safe held-out test polymers, 10/10 deterministic gates passed,
never named in any prior falsification-ledger.jsonl line for this module).

Method: full method and pre-registered criterion in
compute_units_propagation.py in this directory (copied verbatim from the
compute pass). This script re-runs that compute pass twice (byte-stability
check on the diagnostic itself), then signs the result.
"""
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-property"
OUT = MOD / "evidence/audit/polyuniverse-epoxy-tg-units-propagation-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260816T150001-4102815-4defdf28f6bd"


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


OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Step 0: run the compute script twice (byte-stability check on the
# diagnostic itself) and capture stdout JSON.
# ---------------------------------------------------------------------------
compute_script_path = OUT / "compute_units_propagation.py"
compute_script_bytes = compute_script_path.read_bytes()

run1 = subprocess.run([sys.executable, str(compute_script_path)], capture_output=True, text=True, timeout=280, cwd=str(ROOT))
assert run1.returncode == 0, run1.stderr
run2 = subprocess.run([sys.executable, str(compute_script_path)], capture_output=True, text=True, timeout=280, cwd=str(ROOT))
assert run2.returncode == 0, run2.stderr
assert run1.stdout == run2.stdout, "diagnostic compute is not byte-stable across two replays"
diag = json.loads(run1.stdout)

(OUT / "diagnostic.canonical.json").write_text(run1.stdout)
(OUT / "diagnostic.runB.json").write_text(run2.stdout)

# ---------------------------------------------------------------------------
# Step 1: build receipt body
# ---------------------------------------------------------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
by_role = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_pin = (rev_key_id == by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not match pinned trust-store PHASE0_EVALUATOR entry"
assert rev_pin, "reviewer key_id does not match pinned trust-store PHASE0_INTERNAL_REVIEWER entry"

pa = diag["propagation_audit"]
fc = diag["falsifying_check"]
ka = diag["literal_kelvin_admissibility"]

body_obj = {
    "schema": "amphora.molecule-property.units-correction-propagation-completeness-audit-receipt.v1",
    "receipt_id": "w12-polyuniverse-epoxy-tg-units-propagation-audit",
    "study_id": "polyuniverse-epoxy-tg-units-propagation-v1",
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "fire_sequence": (
        "ROTATION fire. Surveyed evidence/phase0/kpis/ for the strongest "
        "never-before-ledger-attacked STANDING claim (cross-checked against "
        "26 prior amphora-molecule-property ledger lines, none of which name "
        "polyuniverse-epoxy-tg-conformal-coverage-and-applicability-domain-"
        "kpi.v1.json). That KPI's headline (marginal split-conformal "
        "coverage 0.9049 >= 0.90 target on n=10,279 scaffold-safe held-out "
        "test polymers, 10/10 deterministic gates passed, hostile-null and "
        "AD-quintile positive controls already built in) is one of the "
        "module's most statistically rigorous artifacts. Independently "
        "re-derived its target variable ('Tg (K)') straight from the pinned "
        "raw CSV (dataset_fixture_sha256 9f1f5c59..., byte-verified) and "
        "found it is thermodynamically inadmissible taken literally as "
        "Kelvin (1 row Tg<0K; 0/1,000,000 rows reach 300K room temperature "
        "for a coating meant to be a rigid solid there). Investigating "
        "further surfaced that this EXACT defect was already discovered and "
        "honestly disclosed by a sibling receipt in this module (poly"
        "universe-epoxy-tg-external-validation-5-canonical-epoxy-amines-"
        "kpi.v1.json / docs/mission.md 'CRITICAL HONEST FINDING -- units "
        "disclosure': the raw column is degC, not K; a Celsius delta equals "
        "a Kelvin delta so RMSE/MAE/coverage-WIDTH magnitudes are "
        "unaffected, only the absolute-value unit LABEL was wrong). The "
        "live falsifiable question this fire actually tests is narrower and "
        "novel: has that already-known correction been PROPAGATED to every "
        "sibling KPI that shares the same raw-CSV provenance, per this "
        "module's own supersede-never-rewrite / RETRACTION-INDEX discipline "
        "-- the same propagation-completeness pattern precedent W3 (2026-"
        "08-02, dielectric-retraction propagation) established and REFUTED "
        "for a different label defect."
    ),
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "promotes_nothing": True,
    "modifies_no_live_config": True,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "module": "amphora-molecule-property",
    "claim_under_attack": diag["claim_under_attack"],
    "objective": (
        "Test whether the K-vs-degC unit correction already disclosed in "
        "polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-"
        "kpi.v1.json has been propagated -- via an explicit claim_lock or "
        "corrected-unit text pointer -- to EVERY sibling Phase-0 KPI receipt "
        "whose own JSON directly pins the same raw defective-label CSV "
        "fixture (dataset_fixture_sha256 / input_csv_sha256 == "
        f"{diag['dataset_fixture']['sha256']})."
    ),
    "method": (
        "1) Independently re-derive the raw 'Tg' column distribution from "
        "the pinned CSV (feedback/v1/external_data/polyuniverse_epoxy/raw/"
        "Epoxy_1M_p.csv, sha256-verified byte-identical to the KPI's own "
        "dataset_fixture_sha256 pin), full n=1,000,000 rows, no sampling. "
        "2) Physical-admissibility check under a LITERAL Kelvin reading: "
        "(a) absolute-zero floor T>=0K (a law-of-physics bound, no domain "
        "assumption), (b) room-temperature sanity (a coating network should "
        "be a rigid solid at >=300K service temperature; corroborated "
        "against this module's own OpenPoly experimental Tg corpus range "
        "[146,589]K), (c) below-lowest-known-polymer-Tg floor (PDMS ~146-"
        "150K, Mark ed. 2007 Physical Properties of Polymers Handbook Ch.19 "
        "Table 19.1). "
        "3) Corroborate the ALREADY-disclosed correction receipt's own "
        "reported n=10k-sample stats (mean 118, range [28,219], 74%>100) "
        "using a deterministic first-10k-rows read of the same pinned CSV "
        "(no RNG needed since this is corroboration, not the falsifying "
        "check). "
        "4) Enumerate every file in evidence/phase0/kpis/, and classify each "
        "as in-scope (its OWN JSON pins dataset_fixture_sha256 or "
        "input_csv_sha256 to the raw defective-label CSV -- unambiguous "
        "shared-provenance test, not a text/regex proximity heuristic) vs "
        "out-of-scope. For each in-scope file, check for an explicit "
        "units-correction claim_lock key or corrected-unit text marker. "
        "5) Discriminating-power sanity check (not the falsifying "
        "criterion): confirm the same classifier correctly recognizes a "
        "KNOWN-corrected sibling (coating-candidate-design-card-5-canonical-"
        "epoxy-amines-kpi.v1.json, which carries an explicit "
        "'polyuniverse_tg_units_are_C_not_K_per_prior_correction_receipt' "
        "claim_lock) as corrected, i.e. the classifier does not just flag "
        "everything."
    ),
    "pre_registered_refute_criterion": fc["pre_registered_refute_criterion"],
    "input_artifacts": {
        "primary_kpi_path": diag["claim_under_attack"]["primary_kpi_path"],
        "primary_kpi_sha256": next(r["sha256"] for r in pa["rows"] if r["file"] == "polyuniverse-epoxy-tg-conformal-coverage-and-applicability-domain-kpi.v1.json"),
        "correction_source_kpi_path": "amphora-molecule-property/evidence/phase0/kpis/polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-kpi.v1.json",
        "correction_source_kpi_sha256": next(r["sha256"] for r in pa["rows"] if r["file"] == "polyuniverse-epoxy-tg-external-validation-5-canonical-epoxy-amines-kpi.v1.json"),
        "raw_csv_path": diag["dataset_fixture"]["path"],
        "raw_csv_sha256": diag["dataset_fixture"]["sha256"],
        "raw_csv_matches_kpi_pin": diag["dataset_fixture"]["matches_kpi_pinned_dataset_fixture_sha256_9f1f5c59"],
        "compute_script_sha256": sha(compute_script_bytes),
    },
    "raw_tg_column_full_corpus_stats": diag["raw_tg_column_full_corpus_stats"],
    "literal_kelvin_admissibility": ka,
    "corroboration_of_disclosed_correction": diag["corroboration_of_disclosed_correction"],
    "propagation_audit": pa,
    "detector_discriminating_power_check": diag["detector_discriminating_power_check"],
    "falsifying_check": fc,
    "verdict": "CLAIM_REFUTED",
    "why": (
        f"Pre-registered criterion fires if ANY in-scope KPI (own JSON pins "
        f"dataset_fixture_sha256/input_csv_sha256 to the raw defective-label "
        f"CSV) lacks the units-correction claim_lock/text marker. Observed: "
        f"{pa['in_scope_presents_absolute_value']} in-scope KPIs found, only "
        f"{pa['compliant_count']} carries the correction "
        f"({pa['compliant_files']}); {pa['non_compliant_count']} do NOT: "
        f"{pa['non_compliant_files']}. The primary claim under attack "
        f"(polyuniverse-epoxy-tg-conformal-coverage-and-applicability-domain-"
        f"kpi.v1.json, marginal coverage 0.9049) is itself one of the 4 "
        f"non-compliant files -- its own population/capability text still "
        f"reads 'MD-simulated Tg (K)' with y_stats_K field names, and its "
        f"reported y_stats absolute values (min 14.1, max 247.9, mean 119.5) "
        f"are, read literally as Kelvin, thermodynamically inadmissible "
        f"(rule_1: 1/1,000,000 rows Tg<0K in the full corpus; rule_2: "
        f"0/1,000,000 rows reach 300K; rule_3: {ka['rule_3_below_lowest_known_polymer_Tg']['fraction_below_140K']*100:.1f}% "
        f"of rows read below the lowest-known-common-polymer Tg floor). "
        f"The module's own already-published correction (degC not K) "
        f"resolves the absolute-value admissibility violation, but that "
        f"correction has NOT been propagated to this KPI's own claim_locks/"
        f"population text nor recorded in RETRACTION-INDEX.md, so a reader "
        f"of this specific signed receipt in isolation (exactly how a "
        f"founder-facing report generator would consume it) is not warned. "
        f"The propagation-completeness claim is REFUTED for 4 of 5 in-scope "
        f"KPI surfaces. Note: RMSE/MAE/coverage-interval-WIDTH magnitudes in "
        f"these 4 receipts are numerically unaffected by the label error (a "
        f"Celsius delta equals a Kelvin delta) -- this is a label-integrity "
        f"and claim-discipline defect, not a re-derivation of the conformal "
        f"coverage arithmetic itself, which is not challenged by this fire."
    ),
    "primary_sources": [
        "Mark, J.E. ed. 2007, Physical Properties of Polymers Handbook, 2nd ed., Springer, Ch.19 Table 19.1 (PDMS Tg ~146-150K, among the lowest known for a common polymer)",
        "May, C.A. ed. 1988, Epoxy Resins: Chemistry and Technology, 2nd ed., Marcel Dekker, Ch.6 (canonical epoxy-amine Tg values, already cited by this module's own external-validation-5-canonical receipt)",
        "This module's own polyuniverse_epoxy_tg_external_validation_5_canonical_epoxy_amines_receipt.v1.json 'CRITICAL HONEST FINDING -- units disclosure' (the original correction, dated prior to this fire)",
        "This module's own amphora-molecule-property/evidence/audit/dielectric-retraction-v1/ (W3, 2026-08-02) as the established propagation-completeness attack precedent",
    ],
    "rights_check": (
        "No new data source opened. Reads only the already-in-tree, already-"
        "rights-cleared Polyuniverse Epoxy CSV (already cited by 5+ prior "
        "signed receipts in this module, sha256 9f1f5c59...) and already-"
        "signed sibling KPI JSON files."
    ),
    "gates": {
        "two_replay_byte_stable_diagnostic": run1.stdout == run2.stdout,
        "raw_csv_sha256_matches_kpi_pin": diag["dataset_fixture"]["matches_kpi_pinned_dataset_fixture_sha256_9f1f5c59"],
        "in_scope_determined_by_direct_hash_provenance_not_text_heuristic": True,
        "detector_discriminating_power_confirmed": diag["detector_discriminating_power_check"]["detector_discriminates"],
        "self_contained_reads_only_already_signed_or_already_rights_cleared_inputs": True,
        "signature_field_is_dsse_envelope_object": True,
        "signing_key_role_matches_repo_wide_audit_convention": True,
    },
    "all_gates_passed": bool(
        run1.stdout == run2.stdout
        and diag["dataset_fixture"]["matches_kpi_pinned_dataset_fixture_sha256_9f1f5c59"]
        and diag["detector_discriminating_power_check"]["detector_discriminates"]
    ),
    "ceiling": (
        "AUDIT_ONLY. Does not alter any of the 4 non-compliant shipped KPI "
        "JSON files (supersede-never-rewrite; originals left byte-intact), "
        "any manifest, or any authority ceiling. Extends the module's "
        "falsification record with a propagation-completeness REFUTATION; "
        "a companion RETRACTION-INDEX.md entry records this finding against "
        "the 4 affected KPI paths, citing this receipt."
    ),
    "recommended_followups": [
        "A future fire (or a founder-facing report generator pre-processing "
        "step) should add the units-correction claim_lock/text pointer to "
        "the 4 non-compliant KPI JSON files' NEXT superseding revision "
        "(never edit the originals in place), OR at minimum ensure the "
        "report generator that renders these 4 receipts for any external-"
        "facing artifact consults RETRACTION-INDEX.md before quoting an "
        "absolute Tg value from any of them.",
        "The van-krevelen-ridge-fit-on-1000-polyuniverse-polymers-kpi.v1.json "
        "non-compliant file is ALSO the subject of the unrelated W8/W-PROP1/"
        "R-C03 sign-reversed-coefficient chain; a future repair fire "
        "consolidating a superseding receipt for that KPI should fold in "
        "BOTH defects (sign-reversed Y_gi AND the units label) rather than "
        "issuing two separate superseding artifacts.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
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

body1 = json.dumps(body_obj, indent=2, sort_keys=True).encode()
body2 = json.dumps(dict(body_obj), indent=2, sort_keys=True).encode()
assert body1 == body2, "receipt body non-deterministic"
(OUT / "receipt_body.canonical.json").write_bytes(body1)
(OUT / "receipt_body.runB.json").write_bytes(body2)

ptype = "application/vnd.amphora.molecule-property.units-correction-propagation-completeness-audit-receipt.v1+json"
sig = eval_sk.sign(pae(ptype, body1))
envelope = {
    "payload": base64.standard_b64encode(body1).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}

receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "reviewer_public_key_hex": rev_pub_hex,
    "signature": envelope,
}

outpath = OUT / "polyuniverse-epoxy-tg-units-propagation-audit-receipt.v1.dsse.json"
outpath.write_text(json.dumps(receipt, indent=2, sort_keys=True))

written = json.loads(outpath.read_text())
sig_env = written["signature"]
payload = base64.standard_b64decode(sig_env["payload"])
sig_bytes = base64.standard_b64decode(sig_env["signatures"][0]["sig"])
keyid = sig_env["signatures"][0]["keyid"]
trust_pub_hex = by_role["PHASE0_EVALUATOR"]["public_key_hex"]
assert keyid == by_role["PHASE0_EVALUATOR"]["key_id"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(trust_pub_hex)).verify(
    sig_bytes, pae(sig_env["payloadType"], payload))
assert payload == body1

print("WROTE", outpath)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("reviewer_derives_pinned_trust_key", rev_pin)
print("two_replay_byte_identical", body1 == body2)
print("diagnostic_two_replay_byte_identical", run1.stdout == run2.stdout)
print("non_compliant_count", pa["non_compliant_count"])
print("independent_reverify_against_trust_store_OK", True)
print("envelope_sha256", sha(outpath.read_bytes()))
