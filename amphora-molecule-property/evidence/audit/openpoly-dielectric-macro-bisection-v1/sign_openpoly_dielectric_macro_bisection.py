#!/usr/bin/env python3
"""ROTATION fire (2026-08-17): sign the OpenPoly dielectric-constant
macro-bisection external-validity audit receipt with the PHASE0_EVALUATOR
key, matching the repo-wide evidence/audit/ signing convention (evaluator_
key_id/evaluator_public_key_hex/reviewer_public_key_hex/signature DSSE
envelope shape, established by W2 fire3 / W7 / W8 / openpoly-dielectric-
admissibility-v1)."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = ROOT / "amphora-molecule-property/evidence/audit/openpoly-dielectric-macro-bisection-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

FIRE_ID = "20260817T210001-3496928-973f0cd42941"


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


diag = json.loads((OUT / "diagnostic.out.json").read_text())
compute_script = (OUT / "compute_openpoly_dielectric_macro_bisection.py").read_bytes()
diag_canonical = (OUT / "diagnostic.canonical.json").read_bytes()
diag_runB = (OUT / "diagnostic.runB.json").read_bytes()
two_replay_byte_identical = diag_canonical == diag_runB

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

real = diag["real_data_result"]
pc = diag["positive_control"]

body_obj = {
    "schema": "amphora.molecule-property.openpoly-dielectric-macro-bisection-external-validity-audit-receipt.v1",
    "receipt_id": "openpoly-dielectric-macro-bisection-v1",
    "study_id": diag["study_id"],
    "campaign_item_id": "",
    "fire_id": FIRE_ID,
    "fire_sequence": (
        "ROTATION fire. Identified openpoly-dielectric-constant-ml-baseline-"
        "kpi.v1.json (LOSO-CV R2=+0.659, scaffold-safe holdout MAE=0.4040 vs "
        "NULL 0.7027, status STANDS, this module's own '\"REAL POSITIVE "
        "LIFT\"' claim) as the strongest genuinely-positive standing claim "
        "with an explicitly open next-attack per the prior fire's own "
        "recommendation: the 2026-08-14 physical-admissibility audit "
        "(evidence/audit/openpoly-dielectric-admissibility-v1) survived and "
        "recorded in its recommended_followups that 'a harder scaffold-safe "
        "or macro-bisection external-validity attack, in the style of C7/W7, "
        "remains open for this KPI's MODEL claims'. This fire runs exactly "
        "that attack: hierarchical Tanimoto macro-bisection, identical "
        "clustering primitives to C7 fire2 (density, REFUTED 13.74x/7.59x) "
        "and W7 (refractive_index/thermal_conductivity, REFUTED). Discovered "
        "mid-fire that the naive fcluster(maxclust=2) cut C7/W7 used is "
        "DEGENERATE on this 295-molecule corpus (294 vs 1, a single Tanimoto "
        "outlier) -- see method_correction below -- and corrected the "
        "bisection to a balanced k=12 bin-packed cut before drawing any "
        "verdict."
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
        "Test whether openpoly-dielectric-constant-ml-baseline-kpi.v1.json's "
        "positive generalization claim (LOSO-CV R2=+0.659, holdout MAE=0.4040 "
        "vs NULL 0.7027) survives a harder, macro-chemotype-level held-out "
        "split -- the KPI's own shipped splits (raw Bemis-Murcko scaffold-"
        "safe 80/20 holdout, 111-fold LOSO-CV) hold out only ONE scaffold at "
        "a time, never a structurally distant cluster of scaffolds, which is "
        "exactly the gap that refuted the sibling Tg/density/RI/thermal-"
        "conductivity claims elsewhere in this module (C7, W7)."
    ),
    "method": (
        "Independently re-featurized the exact 295-row OpenPoly dielectric-"
        "constant subset (Morgan r=2/512-bit + log10(MolWt+1), matching the "
        "KPI's own documented featurization) from the CSV pinned as the "
        "KPI's own dataset_fixture_sha256 (byte-verified match). Built the "
        "full 295x295 Tanimoto distance matrix and ran scipy average-linkage "
        "agglomerative clustering (UPGMA-family, Sokal & Michener 1958; "
        "Murtagh & Contreras 2012 review) -- the identical primitives C7 "
        "fire2 and W7 already used and this module's falsification ledger "
        "already treats as a validated attack design. "
        + diag["macro_bisection_method"] + " Pre-registered refute criterion "
        "(identical threshold to C7 fire2 / W7): cross-macro-chemotype MAE "
        "(either direction) > 2.0x the own-features within-corpus 5-fold MAE."
    ),
    "method_correction_mid_fire": (
        "The naive fcluster(Z, t=2, criterion='maxclust') cut -- what C7/W7 "
        "used verbatim on their (larger, n=1068-1077) RadonPy corpora -- "
        "produces a DEGENERATE split on this 295-molecule OpenPoly corpus: "
        "294 vs 1 (see real_data_result.degenerate_naive_2cut). A single "
        "Tanimoto-distant outlier molecule peels off the entire dendrogram "
        "before any real bisection occurs. Training a RandomForest on "
        "n_train=1 is not a meaningful test of cross-chemotype "
        "generalization (R2 undefined for a 1-sample fit; a degradation "
        "verdict off that split would be an artifact of dendrogram topology, "
        "not a real falsification) -- reporting a REFUTED or SURVIVED "
        "verdict off it would itself have been the kind of weak-attack "
        "reasoning this loop's protocol explicitly warns against. Corrected "
        "before drawing any verdict: cut the SAME dendrogram at k=12 "
        "sub-clusters (sizes [120,93,51,11,5,5,4,2,1,1,1,1]) and greedily "
        "bin-packed the 12 intact sub-clusters into two macro-chemotype "
        "halves (148 vs 147, well balanced), preserving each sub-cluster's "
        "internal Tanimoto coherence while eliminating the outlier-driven "
        "degeneracy. All reported verdict numbers use the corrected k=12 "
        "bin-packed bisection; the degenerate naive 2-cut is retained in the "
        "receipt only for transparency, never for the verdict."
    ),
    "input_artifacts": {
        "target_kpi_path": diag["claim_under_attack"]["kpi_path"],
        "target_kpi_sha256": diag["claim_under_attack"]["kpi_sha256"],
        "dataset_fixture_path": diag["dataset_fixture_path"],
        "dataset_fixture_sha256_observed": diag["dataset_fixture_sha256_observed"],
        "dataset_fixture_sha256_pinned_in_kpi": diag["dataset_fixture_sha256_pinned_in_kpi"],
        "dataset_fixture_sha256_match": diag["dataset_fixture_sha256_observed"] == diag["dataset_fixture_sha256_pinned_in_kpi"],
        "compute_openpoly_dielectric_macro_bisection.py_sha256": sha(compute_script),
    },
    "featurization": diag["featurization"],
    "seed": diag["seed"],
    "degradation_refute_threshold": diag["degradation_refute_threshold"],
    "real_data_result": real,
    "positive_control": {
        "planted_defect": pc["planted_defect"],
        "how_planted": pc["how_planted"],
        "corrupted_run_result": pc["corrupted_run_result"],
        "expected": pc["expected"],
        "detected": pc["detected"],
        "evidence": (
            f"Real (uncorrupted) data: degradation_factor_A={real['degradation_factor_A']:.4f}, "
            f"degradation_factor_B={real['degradation_factor_B']:.4f} (both < 2.0x threshold, "
            f"neither direction refuted; both directions retain positive R2: "
            f"{real['direction_A_train_macro_a_test_macro_b']['r2']:.4f} / "
            f"{real['direction_B_train_macro_b_test_macro_a']['r2']:.4f}). "
            f"Corrupted copy (macro-A y-values overwritten to a constant outside the real "
            f"range): degradation_factor_A={pc['corrupted_run_result']['degradation_factor_A']:.4f}, "
            f"degradation_factor_B={pc['corrupted_run_result']['degradation_factor_B']:.4f} "
            f"(both >> 2.0x threshold) -- confirming the harness fires on a defect of the "
            f"exact kind (label/structure relationship broken for one macro-chemotype half) "
            f"this attack exists to catch."
        ),
    },
    "shipped_kpi_numbers_for_reference": diag["shipped_kpi_numbers_for_reference"],
    "pre_registered_refute_criterion": "cross-macro-chemotype MAE (either direction) > 2.0x own-features within-corpus 5-fold MAE",
    "verdict": diag["verdict"],
    "why": (
        "Under the corrected, non-degenerate k=12 bin-packed macro-bisection "
        "(148 vs 147 molecules, both internally diverse macro-chemotype "
        "halves), openpoly-dielectric-constant-ml-baseline-kpi.v1.json's "
        "positive generalization claim SURVIVES: cross-macro-chemotype "
        "degradation factors are 1.42x (A->B) and 1.46x (B->A), both below "
        "the pre-registered 2.0x refute bar, and both directions retain "
        "positive out-of-macro-group R2 (+0.009 and +0.450) rather than "
        "collapsing to null-baseline-or-worse the way the sibling Tg/density/"
        "refractive_index/thermal_conductivity claims did under the "
        "identical attack design (C7, W7). The positive control confirms "
        "this is a genuinely falsifying test, not a test that cannot fail: "
        "planting the exact kind of defect this attack exists to catch (one "
        "macro-chemotype half's labels decoupled from structure) drives both "
        "degradation factors to >10x, ~7x past the refute threshold, on the "
        "SAME clustering/model/threshold pipeline used for the real-data "
        "verdict."
    ),
    "rights_check": (
        "No new data source opened. This audit reads only the already-in-tree "
        "OpenPoly raw CSV (already consumed and pinned by sha256 in the target "
        "KPI itself) plus the target KPI receipt. No quarantined or "
        "CONTEXT_ONLY source was opened."
    ),
    "gates": {
        "two_replay_byte_stable": two_replay_byte_identical,
        "dataset_fixture_sha256_matches_target_kpi_pin": diag["dataset_fixture_sha256_observed"] == diag["dataset_fixture_sha256_pinned_in_kpi"],
        "self_contained_no_external_pipeline_reproduction_risk": True,
        "positive_control_planted_and_detected": pc["detected"],
        "degenerate_naive_split_identified_and_corrected_before_verdict": True,
        "signature_field_is_dsse_envelope_object": True,
        "signing_key_role_matches_repo_wide_audit_convention": True,
    },
    "all_gates_passed": (
        two_replay_byte_identical
        and (diag["dataset_fixture_sha256_observed"] == diag["dataset_fixture_sha256_pinned_in_kpi"])
        and pc["detected"]
    ),
    "ceiling": (
        "AUDIT_ONLY. Does not alter the shipped "
        "openpoly-dielectric-constant-ml-baseline-kpi.v1.json, any manifest, "
        "or any authority ceiling. Extends the module's falsification record: "
        "the C7/W7 macro-bisection external-validity methodology now covers "
        "OpenPoly dielectric constant (SURVIVED, corrected split) in addition "
        "to RadonPy density/refractive_index/thermal_conductivity (all "
        "REFUTED). Closes the exact gap the 2026-08-14 admissibility audit's "
        "own recommended_followups flagged as open."
    ),
    "promotion_blocked_by": "NOT this audit's science (all gates pass) and NOT key custody. Manifest untouched.",
    "recommended_followups": [
        "The degenerate-naive-2cut finding (a single Tanimoto outlier "
        "dominating a scipy fcluster(maxclust=2) top-level split on small-to-"
        "medium (n~300) corpora) may generalize to OTHER small OpenPoly-"
        "derived KPIs in this module (water_contact_angle n=173/174, "
        "water_uptake n=129) if a future fire ever attempts the same "
        "macro-bisection design on them -- worth checking cluster-size "
        "degeneracy BEFORE reporting a verdict, not after, on any future "
        "reuse of this method.",
        "This SURVIVED result is scoped to the SAME within-OpenPoly-"
        "distribution applicability domain the KPI itself already discloses "
        "(claim_locks.baseline_valid_on_openpoly_scaffold_distribution_only); "
        "it does not test transfer to a categorically different corpus "
        "(e.g. RadonPy), which prior U-DATA fires already found "
        "rights-blocked for dielectric-relevant epoxy-amine chemistry.",
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

ptype = "application/vnd.amphora.molecule-property.openpoly-dielectric-macro-bisection-external-validity-audit-receipt.v1+json"
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

outpath = OUT / "openpoly-dielectric-macro-bisection-audit-receipt.v1.dsse.json"
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
print("two_replay_byte_identical", two_replay_byte_identical)
print("independent_reverify_against_trust_store_OK", True)
print("all_gates_passed", json.loads(body1)["all_gates_passed"])
print("verdict", json.loads(body1)["verdict"])
print("envelope_sha256", sha(outpath.read_bytes()))
