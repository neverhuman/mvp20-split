#!/usr/bin/env python3
"""DSSE-Ed25519-sign the U-GHS campaign-item done receipt: certifies that the
SMARTS-based structural-alert hazard prescreen prototype for NOVEL structures
(no CAS/CID regulatory record) is committed, runnable, cites a published
source for every alert, demonstrates the three-valued fail-closed contract
(never emits "safe"), reports honest recall on the 5 canonical amines with
the explicit n=5-cannot-support-general-accuracy caveat, tabulates the
grammar-38 alert distribution, and carries a positive control showing the
validation harness detects a defect planted in its own alert catalogue.
AUDIT_ONLY: does not promote authority, does not flip scientific_readiness,
does not modify the portfolio manifest or any locked dataset, and does not
touch the existing 5-CAS hardcoded GHS/CLP oracle (which remains authoritative
for those 5 substances).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

WORKDIR = MOD / "evidence/phase0/repairs/U-GHS/work"
SCRIPT = WORKDIR / "run_ghs_structural_alert_prescreen.py"
DIAG_A = WORKDIR / "diagnostic.canonical.json"
DIAG_B = WORKDIR / "diagnostic.runB.json"
OUTDIR = MOD / "evidence/phase0/repairs/U-GHS/done"


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


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

diag_a_bytes = DIAG_A.read_bytes()
diag_b_bytes = DIAG_B.read_bytes()
diag_a = json.loads(diag_a_bytes)
two_replay_byte_identical = sha(diag_a_bytes) == sha(diag_b_bytes)
assert two_replay_byte_identical, "two-replay byte-stability gate FAILED"

val = diag_a["validation_5_canonical_amines"]
grammar = diag_a["grammar_38_alert_distribution"]
decoy = diag_a["fail_closed_decoy_demo"]
pc = diag_a["positive_control"]

assert val["n"] == 5
assert val["specificity_computable"] is False
assert grammar["n"] == 38
assert decoy["never_emitted_safe_or_unrecognised_verdict"] is True
assert pc["detected"] is True
assert pc["sabotaged_any_alert_recall_for_H317"] < pc["baseline_any_alert_recall_for_H317"]
for alert in diag_a["alert_catalogue"]:
    assert alert["source"], f"alert {alert['alert_id']} missing source citation"

body_obj = {
    "schema": "amphora.sourceability-ehs.repair-done.u-ghs.v1",
    "campaign_item_id": "U-GHS",
    "module": "amphora-sourceability-ehs",
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "claim_under_attack": {
        "receipt_path": "amphora-sourceability-ehs/evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json",
        "claim_text": "For a novel structure with no regulatory record, a defensible hazard prescreen can assert structural alerts with explicit UNKNOWN outcomes rather than silently having no opinion.",
        "gap_being_closed": "The existing GHS/CLP oracle at this receipt path is a hardcoded 5-CAS-keyed lookup table. It is structurally empty for any novel structure with no CAS/CID -- exactly the molecules this product exists to propose.",
    },
    "refutation_criterion": (
        "The prescreen contract is refuted if, over the 5 canonical amines, the 6 fail-closed "
        "decoys, and the 38 grammar candidates (49 total structures), it EVER emits an "
        "unqualified 'safe' verdict, OR if it fails to flag a majority of the H317-positive "
        "canonical amines via at least one cited structural alert."
    ),
    "refutation_observed": (
        "Not observed. Across all 49 test structures the verdict space was restricted to "
        "{HAZARD_FLAGGED, NO_ALERT_MATCHED, UNKNOWN_NO_REGULATORY_RECORD} by construction "
        "(the enum contains no 'safe' value) and empirically confirmed by direct inspection "
        "of every returned verdict. 5/5 H317-positive canonical amines were HAZARD_FLAGGED "
        "via >=1 alert (recall 1.0). Verdict: CLAIM_SURVIVED."
    ),
    "claim_verdict": "CLAIM_SURVIVED",
    "done_criterion": (
        "SMARTS prescreen committed and runnable, every alert citing a published source with "
        "year+DOI/ISBN, the three-valued fail-closed contract demonstrated (never emits "
        "'safe'), sensitivity/specificity reported on the 5 canonical amines WITH the explicit "
        "statement that n=5 cannot support a general accuracy claim, and the alert distribution "
        "over all 38 grammar proposals tabulated. On CLAIM_SURVIVED, positive_control required."
    ),
    "done_criterion_met": True,
    "deliverable_prototype": {
        "path": "evidence/phase0/repairs/U-GHS/work/run_ghs_structural_alert_prescreen.py",
        "sha256": sha(SCRIPT.read_bytes()),
        "diagnostic_canonical_path": "evidence/phase0/repairs/U-GHS/work/diagnostic.canonical.json",
        "diagnostic_canonical_sha256": sha(diag_a_bytes),
        "diagnostic_runB_sha256": sha(diag_b_bytes),
        "two_replay_byte_identical": two_replay_byte_identical,
        "rdkit_version_used": "2026.03.2",
    },
    "alert_catalogue": [
        {
            "alert_id": a["alert_id"],
            "smarts": a["smarts"],
            "hazard_class": a["hazard_class"],
            "source": a["source"],
        }
        for a in diag_a["alert_catalogue"]
    ],
    "three_valued_contract": diag_a["contract"],
    "fail_closed_decoy_demo": {
        "n_decoys": len(decoy["decoys"]),
        "never_emitted_safe_or_unrecognised_verdict": decoy["never_emitted_safe_or_unrecognised_verdict"],
        "decoys": decoy["decoys"],
    },
    "validation_5_canonical_amines": val,
    "grammar_38_alert_distribution": {
        "n": grammar["n"],
        "verdict_distribution": grammar["verdict_distribution"],
        "alert_hit_counts": grammar["alert_hit_counts"],
        "honest_caveat": (
            "38/38 grammar candidates were HAZARD_FLAGGED because this grammar universe is by "
            "construction restricted to difunctional amine hardeners, so the amine-class alerts "
            "are near-tautological for this specific population -- 0/38 landed in "
            "UNKNOWN_NO_REGULATORY_RECORD or NO_ALERT_MATCHED. That branch is real and reachable "
            "(see fail_closed_decoy_demo: 'unregistered_alkane_novel' -> "
            "UNKNOWN_NO_REGULATORY_RECORD, five inert decoys -> NO_ALERT_MATCHED), but this "
            "specific grammar population does not exercise it. Per-compound table is in "
            "diagnostic.canonical.json:grammar_38_alert_distribution.per_compound."
        ),
        "per_compound_path": "evidence/phase0/repairs/U-GHS/work/diagnostic.canonical.json#/grammar_38_alert_distribution/per_compound",
    },
    "positive_control": {
        "planted_defect": pc["planted_defect"],
        "how_planted": pc["how_planted"],
        "detected": pc["detected"],
        "evidence": pc["evidence"],
        "baseline_any_alert_recall_for_H317": pc["baseline_any_alert_recall_for_H317"],
        "sabotaged_any_alert_recall_for_H317": pc["sabotaged_any_alert_recall_for_H317"],
    },
    "scope_can_assert": diag_a["scope_can_assert"],
    "scope_cannot_assert": diag_a["scope_cannot_assert"],
    "does_not_close": [
        "Does not modify, supersede, or re-derive the existing 5-CAS hardcoded GHS/CLP oracle "
        "(evidence/phase0/kpis/ghs-clp-public-hazard-prescreen-5-canonical-epoxy-amines-kpi.v1.json), "
        "which remains the authoritative regulatory record for those 5 substances.",
        "No GHS H-code, CLP category, batch-release, procurement, product-performance, or "
        "freedom-to-operate authority. AUDIT_ONLY triage prefilter.",
        "No Phase-0 promotion: PHASE0_EVALUATOR evaluation.v1.dsse.json and "
        "PHASE0_INTERNAL_REVIEWER review remain human dual-identity steps outside this cron's "
        "authority.",
        "No specificity / general accuracy claim of any kind (n=5, zero true negatives in the "
        "canonical validation population).",
        "Alert catalogue coverage is finite by construction -- e.g. bare (non-amine-bearing) "
        "aromatic rings are out of scope, so benzene (a real H350 carcinogen) returns "
        "NO_ALERT_MATCHED against this catalogue. NO_ALERT_MATCHED is not a hazard-absence claim.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/U-GHS/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.sourceability-ehs-repair-done-u-ghs+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}

OUTDIR.mkdir(parents=True, exist_ok=True)
out = OUTDIR / "u-ghs-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", out)
print("self_verify_signature", True)
print("envelope_sha256", sha(out.read_bytes()))
