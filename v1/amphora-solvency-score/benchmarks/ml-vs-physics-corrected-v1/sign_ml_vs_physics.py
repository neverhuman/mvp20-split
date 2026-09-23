#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V1-SOLV fair ML-vs-corrected-physics comparison
(campaign item V1-SOLV, fire 20260804T120002-908503-d3abb9d9d83c). AUDIT_ONLY
repair receipt under evidence/phase0/repairs/V1-SOLV/. Does not modify the
portfolio manifest or any previously-signed Phase-0 KPI (supersede, never
rewrite). Uses the pinned PHASE0_EVALUATOR key.
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-solvency-score"
BENCH = MOD / "benchmarks/ml-vs-physics-corrected-v1"
REPAIR_DIR = MOD / "evidence/phase0/repairs/V1-SOLV"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260804T120002-908503-d3abb9d9d83c"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha(p.read_bytes())


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def main():
    runA = json.loads((BENCH / "diagnostic.runA.json").read_bytes())
    runB = json.loads((BENCH / "diagnostic.runB.json").read_bytes())
    canon_bytes = json.dumps(runA, indent=2, sort_keys=True).encode()
    runB_canon_bytes = json.dumps(runB, indent=2, sort_keys=True).encode()
    byte_identical = canon_bytes == runB_canon_bytes
    canon_sha = sha(canon_bytes)
    diag = runA

    harness_sha = sha((BENCH / "run_ml_vs_physics.py").read_bytes())

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
    assert eval_pin, "evaluator key_id does not match pinned trust store"
    assert byte_identical, "two-replay bytes differ -- NOT stable, do not sign"

    fh_kpi_path = MOD / "evidence/phase0/kpis/omg-chi-flory-huggins-physical-baseline-vs-ml-kpi.v1.json"
    hn_kpi_path = MOD / "evidence/phase0/kpis/omg-chi-hansen-3component-physical-baseline-vs-ml-kpi.v1.json"
    rb03_path = MOD / "evidence/phase0/repairs/R-B03/done/flory-hansen-corrected-instrument-repair-receipt.v1.dsse.json"
    w7_path = MOD / "evidence/audit/flory-hansen-physical-admissibility-v1/flory-hansen-physical-admissibility-audit-receipt.v1.dsse.json"

    # decide verdict from the honest numbers: does ML beat BOTH physics arms
    # (pure and rescaled) on the covered subset, for every solvent, for both
    # physics families, at reasonable coverage? Report truthfully either way.
    results = diag["results"]
    per_arm_verdicts = []
    for family, per_solvent in results.items():
        for solvent, r in per_solvent.items():
            ml = r.get("b3_ml_r2_on_covered_subset")
            b1 = r.get("b1_pure_r2")
            b2 = r.get("b2_rescaled_r2")
            cov = r.get("coverage_rate_test")
            per_arm_verdicts.append({
                "family": family, "solvent": solvent,
                "coverage_rate_test": cov,
                "ml_beats_pure": (ml is not None and b1 is not None and ml > b1),
                "ml_beats_rescaled": (ml is not None and b2 is not None and ml > b2),
                "n_test_covered": r.get("n_test_covered"),
            })
    all_ml_beats_pure = all(v["ml_beats_pure"] for v in per_arm_verdicts if v["n_test_covered"])
    all_ml_beats_rescaled = all(v["ml_beats_rescaled"] for v in per_arm_verdicts if v["n_test_covered"])
    min_coverage = min((v["coverage_rate_test"] for v in per_arm_verdicts if v["coverage_rate_test"] is not None), default=None)

    if all_ml_beats_pure and all_ml_beats_rescaled:
        headline = "ML_BEATS_CORRECTED_PHYSICS_ON_COVERED_SUBSET"
    elif not all_ml_beats_pure or not all_ml_beats_rescaled:
        headline = "MIXED_OR_PHYSICS_COMPETITIVE_ON_COVERED_SUBSET"
    else:
        headline = "INCONCLUSIVE"

    body_obj = {
        "schema": "amphora.solvency-score.ml-vs-physics-corrected-comparison-repair-receipt.v1",
        "receipt_id": "ml-vs-physics-corrected-comparison-v1",
        "authority": "AUDIT_ONLY",
        "run_type": "REPAIR",
        "module_id": "amphora-solvency-score",
        "repair_item": "V1-SOLV",
        "campaign_item_id": "V1-SOLV",
        "fire_id": FIRE_ID,
        "repair_mode": "campaign-2026-08-04",
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "modifies_manifest": False,
        "modifies_existing_receipts": False,
        "claim": (
            "W7b CLOSED. Fair re-run of the ML-vs-classical-theory chi comparison "
            "(3 canonical solvents x 2 physics families = 6 arms) using the R-B03 "
            "corrected, coverage-gated Fedors/Van-Krevelen instrument in place of "
            "the W7-refuted generator. Deterministic seed-0 sample of "
            f"{diag['provenance']['n_sample']} unique chi-labeled OMG SMILES "
            "(scope-reduced from the original's full pool for single-hour "
            "synchronous compute; documented, not hidden). Identical scaffold-safe "
            "60/20/20 split (seed 0) and identical ML arm "
            "(HistGradientBoostingRegressor max_iter=500/lr=0.05/depth=8/"
            "min_leaf=25/l2=0.1, 528 features = 16 RDKit descriptors + 512-bit "
            "Morgan fp radius 2) as the two W7-refuted KPIs. Physics R2 computed "
            "ONLY over instrument-RETURNED test molecules; abstentions/rejections "
            "excluded and counted, never zero-filled -- coverage reported per arm."
        ),
        "headline_verdict": headline,
        "headline_note": (
            "ml_beats_pure and ml_beats_rescaled evaluated on the SAME covered "
            "test molecules as each physics arm (like-for-like), per solvent per "
            "family. min_coverage_rate_test across all 6 arms = %r." % min_coverage
        ),
        "per_arm_verdicts": per_arm_verdicts,
        "diagnostic": diag,
        "reproducibility": {
            "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
            "canonical_diagnostic_sha256": canon_sha,
            "runA_diagnostic_sha256": sha_file(BENCH / "diagnostic.runA.json"),
            "runB_diagnostic_sha256": sha_file(BENCH / "diagnostic.runB.json"),
            "byte_identical": byte_identical,
            "harness_sha256": harness_sha,
            "determinism": "seed=0 throughout (corpus sample, scaffold shuffle, HistGBM random_state); rdkit 2026.03.2, sklearn 1.7.2",
        },
        "supersedes": {
            "reason": (
                "R-B03 rebuilt the physics instrument but deliberately deferred the "
                "ML-vs-theory re-run (queued as W7b). This receipt closes W7b: it "
                "supersedes the instrument-validity-scope of the two W7-refuted KPIs "
                "with the actual fair comparison, computed honestly at whatever the "
                "result turns out to be."
            ),
            "refuted_by": {
                "campaign_item_id": "W7", "path": str(w7_path.relative_to(ROOT)),
                "sha256": sha_file(w7_path), "verdict": "CLAIM_REFUTED",
            },
            "repair_instrument": {
                "campaign_item_id": "R-B03", "path": str(rb03_path.relative_to(ROOT)),
                "sha256": sha_file(rb03_path),
            },
            "also_superseded": [
                {"superseded_path": str(fh_kpi_path.relative_to(ROOT)),
                 "superseded_sha256": sha_file(fh_kpi_path),
                 "superseded_deleted_or_modified": False},
                {"superseded_path": str(hn_kpi_path.relative_to(ROOT)),
                 "superseded_sha256": sha_file(hn_kpi_path),
                 "superseded_deleted_or_modified": False},
            ],
        },
        "does_not_close": [
            "extending the sample to the full 265,721-molecule chi-labeled pool "
            "(this fire's compute budget only)",
            "human / independent review",
            "any change to scientific_success_required_for_phase0 or manifest counts",
        ],
        "toolchain": {"python": "3", "rdkit": "2026.03.2", "sklearn": "1.7.2"},
        "signing_key": {
            "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
            "used_for": "AUDIT_ONLY repair done/attempt receipt under evidence/phase0/repairs/V1-SOLV/",
            "signs_phase0_evaluation_or_review": False,
            "derives_pinned_trust_store_key_id": bool(eval_pin),
        },
        "reviewer_reference": {
            "role": "PHASE0_INTERNAL_REVIEWER", "key_id": rev_key_id, "public_key_hex": rev_pub_hex,
            "derives_pinned_trust_store_key_id": bool(rev_pin), "reviewer_signature_present": False,
            "note": "Reviewer key referenced for provenance only; no independent human review performed.",
        },
    }

    body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
    ptype = "application/vnd.amphora.solvency-score-ml-vs-physics-corrected-comparison-repair-receipt+json"
    sig = eval_sk.sign(pae(ptype, body))
    envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
                "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
    receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
               "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

    dest_dir_name = sys.argv[1] if len(sys.argv) > 1 else "attempts"
    out_dir = REPAIR_DIR / dest_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "ml-vs-physics-corrected-comparison-receipt.v1.dsse.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    Ed25519PublicKey.from_public_bytes(eval_pub).verify(
        base64.standard_b64decode(envelope["signatures"][0]["sig"]),
        pae(ptype, base64.standard_b64decode(envelope["payload"])))

    print("WROTE", out)
    print("headline_verdict", headline)
    print("min_coverage_rate_test", min_coverage)
    print("evaluator_key_id", eval_key_id)
    print("eval_derives_pinned_trust_key", eval_pin)
    print("two_replay_sha256", canon_sha)
    print("envelope_sha256", sha_file(out))
    print("signature_verified", True)


if __name__ == "__main__":
    main()
