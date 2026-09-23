#!/usr/bin/env python3
"""DSSE-Ed25519-sign the V-A05 independent verify receipt (AUDIT_ONLY).
Verify-only: writes no supersession, edits no existing signed artifact, mission
front-matter, or the master manifest. Signs with the pinned Phase-0 evaluator
seed only; self-verifies the envelope before writing."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"
VDIR = MOD / "evidence/phase0/repairs/V-A05"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

VERIFIER_SCRIPT = VDIR / "work/v_a05_verify.py"
REPORT_RUN1 = Path("/tmp/v_a05_run1.json")
REPORT_RUN2 = VDIR / "work/V-A05-verify-report.v1.json"
R_A05_DONE = MOD / "evidence/phase0/repairs/R-A05/done/R-A05.done-receipt.v1.dsse.json"


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


report = json.loads(REPORT_RUN2.read_bytes())
checks = report["checks"]
assert checks["all_checks_pass"] is True

report_run1_sha = sha(REPORT_RUN1.read_bytes())
report_run2_sha = sha(REPORT_RUN2.read_bytes())
assert report_run1_sha == report_run2_sha, "two-replay byte-stability gate FAILED"

verifier_sha = sha(VERIFIER_SCRIPT.read_bytes())
r_a05_done_sha = sha(R_A05_DONE.read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

eval_pin = False
if TRUST.exists():
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust.get("keys", [])}
    eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key does not match pinned Phase-0 trust store"

body_obj = {
    "schema": "amphora.known-answer-benchmarks.repair-verify.v1",
    "verify_item": "V-A05",
    "target_repair_item": "R-A05",
    "module_id": "amphora-known-answer-benchmarks",
    "authority": "AUDIT_ONLY",
    "claim_under_verify": (
        "amphora-known-answer-benchmarks/evidence/phase0/repairs/R-A05/done/ :: "
        "the interactive repair R-A05 (superseding correction of "
        "ARITH-A221-X70P1-VOLUME-SOLIDS 'actual' 43.7 -> 42.4165, plus a full "
        "2/2 volume-solids-control sweep including ARITH-A702B75P1-VOLUME-SOLIDS) "
        "withstands independent adversarial verification."
    ),
    "refutation_would_have_shown": [
        "an independently-written, from-scratch exact-rational (Fraction) re-derivation "
        "of the A221 or A702B75P1 volume-solids values disagreeing with R-A05's corrected "
        "values to 4dp",
        "the correct volume-weighted recompute failing to reproduce the TDS's own published "
        "expected value (42.5 / 62.0) within normal source rounding",
        "a fresh, independent live re-fetch of the A221 TDS PDF failing to contain the exact "
        "masses/densities/solid-content numbers R-A05 (via the original refuting receipt) "
        "transcribed, or the cached A702B75P1 TDS PDF's sha256 not matching what R-A05 "
        "recorded",
        "an independent enumeration of all 14 raw controls in control_by_control_receipt.v1.json "
        "finding a volume-solids-semantic control R-A05's sweep missed (checked directly: field "
        "names, tolerance units, not R-A05's own classification)",
        "R-A05's DSSE envelope failing real Ed25519 verification, or its evaluator key not "
        "matching the pinned Phase-0 trust store",
        "any of the three files R-A05 claims it left byte-intact (control_by_control_receipt.v1.json, "
        "arithmetic_audit.json, result.v1.json) having drifted from the sha256 R-A05 recorded",
        "the module's RETRACTION-INDEX.md missing the R-A05 entry, or mission.md still carrying "
        "the superseded 43.7 number without R-A05 having updated it",
    ],
    "checks": checks,
    "headline": (
        "V-A05 independent verify of repair R-A05: re-derived both volume-solids controls "
        "(ARITH-A221-X70P1-VOLUME-SOLIDS, ARITH-A702B75P1-VOLUME-SOLIDS) from raw masses/densities "
        "with a freshly-written exact-rational (fractions.Fraction) implementation, not R-A05's own "
        "script -- got 42.4165 and 61.748 (642797/10410) respectively, matching R-A05's corrected "
        "values to 4dp exactly. Cross-checked the A221 TDS transcription against a FRESH live "
        "re-fetch (sha256 fa2e8ff6...dc6f, distinct bytes from R-A05's cached copy since the vendor "
        "PDF isn't byte-stable across fetches, but every printed masses/densities/solid-content "
        "number matches verbatim, including the prose 'low volume solids (43%)' rounding note) and "
        "confirmed the cached A702B75P1 TDS PDF's sha256 matches what R-A05 recorded exactly. "
        "Independently enumerated all 14 raw controls in control_by_control_receipt.v1.json (not "
        "R-A05's own classification): exactly 2 carry a VOLUME-SOLIDS semantic and both were swept; "
        "0 of the other 12 controls carry a percentage_point tolerance that could hide a mislabeled "
        "volume-solids control. Ed25519-verified R-A05's DSSE envelope against the pinned Phase-0 "
        "evaluator key: valid. Confirmed byte-intactness of all 3 files R-A05 claims it left "
        "untouched (control_by_control_receipt.v1.json, arithmetic_audit.json, result.v1.json): all "
        "3 sha256-identical to what R-A05 recorded. Confirmed RETRACTION-INDEX.md carries the R-A05 "
        "entry with the corrected value; confirmed mission.md never referenced the superseded number "
        "so no prose update was owed. Re-ran R-A05's own falsification criterion (from the receipt it "
        "supersedes) against the corrected value: the corrected 42.4165 is NOT reproducible from the "
        "superseded 43.7 (gap 1.28pp) and DOES reproduce the TDS-published 42.5 within 0.0835pp. "
        "Two-replay byte-stability gate on this verify script: PASS. Verdict: CLAIM_SURVIVED."
    ),
    "verdict": "CLAIM_SURVIVED",
    "repair_status": "confirmed_holds",
    "scientific_success_asserted": False,
    "promotes_authority": False,
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "human_review_performed": False,
    "supersedes": None,
    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, qualification, regulatory, or FTO "
        "authority.",
        "Verify-only: writes no new supersession, edits no existing signed artifact, mission "
        "front-matter, or the master manifest. Confined to evidence/phase0/repairs/V-A05/.",
        "Does not re-audit whether the +/-2.0pp tolerance band itself is justified (out of scope, "
        "already noted as an open gap by the original refuting receipt).",
        "Does not re-derive the 10 EXACT_STATUS or 4 DENSITY controls' underlying source numbers; "
        "confirmed only that none of them carries a volume-solids semantic R-A05's sweep could have "
        "missed.",
    ],
    "artifacts": {
        "verifier_script": {"path": str(VERIFIER_SCRIPT.relative_to(ROOT)), "sha256": verifier_sha},
        "verify_report_run1_sha256": report_run1_sha,
        "verify_report_run2_sha256": report_run2_sha,
        "target_r_a05_done_receipt": {"path": str(R_A05_DONE.relative_to(ROOT)), "sha256": r_a05_done_sha},
    },
    "two_replay_sha256_gate": {
        "replays": 2, "byte_stable": report_run1_sha == report_run2_sha,
        "replay_a_report_sha256": report_run1_sha, "replay_b_report_sha256": report_run2_sha,
    },
    "provenance": {"module_manifest_sha256": manifest_sha},
    "signing_key": {
        "authority": "AUDIT_ONLY", "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing only; no dual-identity ceremony",
        "used_for": "AUDIT_ONLY repair-verify receipt under evidence/phase0/repairs/V-A05/done/",
        "trust_anchored_in_phase0_promotion_store": bool(eval_pin),
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.known-answer-benchmarks.repair-verify.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}
for k in ("schema", "verify_item", "target_repair_item", "module_id", "authority"):
    receipt[k] = body_obj[k]

VDIR.mkdir(parents=True, exist_ok=True)
(VDIR / "done").mkdir(parents=True, exist_ok=True)
out = VDIR / "done/V-A05-verify-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_byte_stable", report_run1_sha == report_run2_sha)
print("self_verify_signature", True)
