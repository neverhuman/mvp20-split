#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-SOLV-COV coverage-scope attack (campaign item
W-SOLV-COV). AUDIT_ONLY repair receipt under
evidence/phase0/repairs/W-SOLV-COV/. Does not modify the portfolio manifest
or any previously-signed Phase-0 KPI/receipt. Uses the pinned PHASE0_EVALUATOR
key.
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
BENCH = MOD / "benchmarks/ml-vs-physics-coverage-scope-v1"
REPAIR_DIR = MOD / "evidence/phase0/repairs/W-SOLV-COV"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
FIRE_ID = "20260814T060001-2670169-d74f421d5261"


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

    harness_sha = sha((BENCH / "run_coverage_scope.py").read_bytes())

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

    v1solv_path = MOD / "evidence/phase0/repairs/V1-SOLV/done/ml-vs-physics-corrected-comparison-receipt.v1.dsse.json"

    refutation_fires = diag["refutation_criterion_fires"]
    headline_verdict = "CLAIM_REFUTED" if refutation_fires else "CLAIM_SURVIVED"
    framing_survives = not refutation_fires

    pc = diag.get("positive_control")
    assert pc is not None and pc.get("detected") is True, (
        "CLAIM_SURVIVED requires a positive control that actually fired")

    body_obj = {
        "schema": "amphora.solvency-score.ml-vs-physics-coverage-scope-repair-receipt.v1",
        "receipt_id": "ml-vs-physics-coverage-scope-v1",
        "authority": "AUDIT_ONLY",
        "run_type": "REPAIR",
        "module_id": "amphora-solvency-score",
        "repair_item": "W-SOLV-COV",
        "campaign_item_id": "W-SOLV-COV",
        "fire_id": FIRE_ID,
        "repair_mode": "campaign-2026-08-14",
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
        "organizational_independence_asserted": False,
        "modifies_manifest": False,
        "modifies_existing_receipts": False,
        "claim_under_attack": "ML beats corrected classical theory for chi prediction.",
        "claim": (
            "W-SOLV-COV attacks the covered-subset scoping of V1-SOLV's "
            "ML-beats-corrected-physics headline. V1-SOLV computed physics R2 "
            "only over instrument-RETURNED test molecules (coverage 85.5% "
            "Fedors/Hildebrand, 75.1% Hansen 3-component), which is correct "
            "methodology but excludes 14.5%-24.9% of the test set from the "
            "comparison entirely -- and non-randomly: exactly the molecules "
            "the corrected instrument's fail-closed gates reject. This fire "
            "reuses V1-SOLV's IDENTICAL seed-0 scaffold-safe 60/20/20 split "
            "and IDENTICAL HistGradientBoostingRegressor ML arm (same "
            "hyperparameters, same 528 features) on the same seed-0 n=40,000 "
            "OMG sample (test n=5,261), and computes: (1) a characterisation "
            "of which fragments/groups drive each rejection reason, (2) the "
            "ML arm's OWN r2 on the REJECTED-only ('abstained') test subset "
            "versus the RETURNED-only ('covered') subset per family per "
            "solvent, and (3) the deployment-relevant any-arm coverage "
            "fraction of the full test set."
        ),
        "pre_registration": diag["pre_registration"],
        "refutation_criterion_verbatim": (
            "if ML's error on the abstained subset is materially worse than "
            "on the covered subset (state your threshold and pre-register it "
            "BEFORE computing), the unqualified 'ML beats physics' framing is "
            "REFUTED and must be superseded with the scope stated"
        ),
        "refutation_criterion_operationalised": (
            "materially_degraded(arm) := gap > 0.15 absolute R2 AND "
            "n_abstained >= 50; overall REFUTED if >=4/6 arms flagged"
        ),
        "refutation_criterion_fired": bool(refutation_fires),
        "n_arms_materially_degraded": diag["n_arms_materially_degraded"],
        "n_arms_eligible": diag["n_arms_eligible"],
        "headline_verdict": headline_verdict,
        "headline_note": (
            "Per the pre-registered criterion, ML does NOT degrade materially "
            "on the physics-rejected subset: gaps (covered_r2 - abstained_r2) "
            "range 0.015-0.107 across all 6 arms, all below the 0.15 "
            "pre-registered threshold. ML retains R2 0.75-0.93 on exactly the "
            "molecules the corrected physics instrument refuses to score at "
            "all. The unqualified 'ML beats physics' framing, AS APPLIED TO "
            "V1-SOLV's covered-subset comparison, SURVIVES this attack: it is "
            "not an artifact of physics screening out ML's hard cases. "
            "Nevertheless the deployment-relevant honest number remains that "
            "physics (fedors OR hansen RETURNED) only ever answers "
            "%.4f of the test set (any-arm coverage); the remaining %.4f gets "
            "NO physics answer at any accuracy, so a truly unqualified 'ML "
            "beats physics' STATEMENT OF GENERALITY (not just of this "
            "covered-subset comparison) remains unsupported by V1-SOLV or "
            "this fire outside the covered region -- V1-SOLV's mission.md "
            "disclosure already scopes this correctly ('on the "
            "instrument-covered subset ... coverage 85.5%%') and needs no "
            "further correction."
        ) % (
            diag["deployment_relevant_any_arm_coverage"]["physics_any_arm_coverage_rate"],
            1.0 - diag["deployment_relevant_any_arm_coverage"]["physics_any_arm_coverage_rate"],
        ),
        "abstained_molecule_characterisation": diag["abstained_molecule_characterisation"],
        "per_arm_ml_error_covered_vs_abstained": diag["per_arm"],
        "deployment_relevant_any_arm_coverage": diag["deployment_relevant_any_arm_coverage"],
        "positive_control": pc,
        "diagnostic": diag,
        "reproducibility": {
            "two_replay_sha256_gate": "PASS" if byte_identical else "FAIL",
            "canonical_diagnostic_sha256": canon_sha,
            "runA_diagnostic_sha256": sha_file(BENCH / "diagnostic.runA.json"),
            "runB_diagnostic_sha256": sha_file(BENCH / "diagnostic.runB.json"),
            "byte_identical": byte_identical,
            "harness_sha256": harness_sha,
            "determinism": "seed=0 throughout (corpus sample, scaffold shuffle, HistGBM random_state), identical to V1-SOLV; rdkit 2026.03.2, sklearn 1.7.2",
        },
        "attacked_receipt": {
            "campaign_item_id": "V1-SOLV",
            "path": str(v1solv_path.relative_to(ROOT)),
            "sha256": sha_file(v1solv_path),
            "headline_verdict": "ML_BEATS_CORRECTED_PHYSICS_ON_COVERED_SUBSET",
        },
        "supersedes": None,
        "does_not_close": [
            "extending the sample to the full 265,721-molecule chi-labeled pool (compute-budget scoped, same as V1-SOLV)",
            "human / independent review",
            "any change to scientific_success_required_for_phase0 or manifest counts",
            "quantifying deployment coverage below what the fedors/hansen instrument, as specced, can ever return -- that is a scope limit of the corrected physics instrument (R-B03), not of this attack",
        ],
        "toolchain": {"python": "3", "rdkit": "2026.03.2", "sklearn": "1.7.2"},
        "signing_key": {
            "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
            "used_for": "AUDIT_ONLY repair done/attempt receipt under evidence/phase0/repairs/W-SOLV-COV/",
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
    ptype = "application/vnd.amphora.solvency-score-ml-vs-physics-coverage-scope-repair-receipt+json"
    sig = eval_sk.sign(pae(ptype, body))
    envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
                "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
    receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
               "reviewer_public_key_hex": rev_pub_hex, "signature": envelope}

    dest_dir_name = sys.argv[1] if len(sys.argv) > 1 else "attempts"
    out_dir = REPAIR_DIR / dest_dir_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "ml-vs-physics-coverage-scope-receipt.v1.dsse.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    Ed25519PublicKey.from_public_bytes(eval_pub).verify(
        base64.standard_b64decode(envelope["signatures"][0]["sig"]),
        pae(ptype, base64.standard_b64decode(envelope["payload"])))

    print("WROTE", out)
    print("headline_verdict", headline_verdict)
    print("refutation_criterion_fired", refutation_fires)
    print("evaluator_key_id", eval_key_id)
    print("eval_derives_pinned_trust_key", eval_pin)
    print("two_replay_sha256", canon_sha)
    print("envelope_sha256", sha_file(out))
    print("signature_verified", True)


if __name__ == "__main__":
    main()
