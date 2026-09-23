#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard kpi-benchmark-pin-integrity AUDIT_ONLY receipt.

AUDIT_ONLY: produces a signed audit receipt under evidence/audit/. Does NOT
sign a phase0 evaluation/review, does NOT promote authority, does NOT modify
the manifest or the pinned patent_landscape.json fixture. Documents and (in
the same fire) corrects the module's own KPI receipt's stale
benchmark_result_sha256 pin -- the same pre-R-B01 stale value PIN-01
(2026-08-16) already fixed in docs/mission.md and docs/capability-profile.json
but never touched here.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-ip-fto-guard/evidence/audit/kpi-benchmark-pin-integrity-v1"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
KPI = ROOT / "amphora-ip-fto-guard/evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" "
            + str(len(body)).encode() + b" " + body)


def load_seed(path):
    raw = path.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


# --- two-replay gate --------------------------------------------------------
canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag = json.loads(canon)
harness_sha = sha((BENCH / "run_kpi_benchmark_pin_integrity.py").read_bytes())

assert diag["H0_verdict"] == "REFUTED"

# --- REPAIR (same fire, precedent: PIN-01): fix the stale pin in the KPI file
kpi_before_bytes = KPI.read_bytes()
kpi_before_sha256 = sha(kpi_before_bytes)
kpi_obj = json.loads(kpi_before_bytes)
STALE = "bbd8a9675d78bb65d1dfee9209b441bb5cb3ec4c28e2871cf8febf0f7168eec3"
LIVE = diag["live_hashes"]["result_v1_json_sha256"]
assert kpi_obj["benchmark_result_sha256"] == STALE
kpi_obj["benchmark_result_sha256"] = LIVE
kpi_obj["pin_integrity_correction_2026_08_17"] = (
    "benchmark_result_sha256 corrected from the stale pre-R-B01 value "
    f"({STALE}) to the live evidence/phase0/benchmark/result.v1.json hash "
    f"({LIVE}) by evidence/audit/kpi-benchmark-pin-integrity-v1/"
    "kpi-benchmark-pin-integrity-receipt.v1.dsse.json. This is the same "
    "stale value the 2026-08-16 PIN-01 audit already fixed in "
    "docs/mission.md and docs/capability-profile.json; PIN-01's own scope "
    "did not include this KPI file. Documentation-pin fix only -- no "
    "scientific readiness, phase, gate, or metric value changed; this file "
    "is still unsigned/PRE_PHASE_0 and awaiting PHASE0_EVALUATOR/"
    "PHASE0_INTERNAL_REVIEWER signature per its own 'awaiting' field."
)
KPI.write_text(json.dumps(kpi_obj, indent=2, sort_keys=False) + "\n")
kpi_after_sha256 = sha(KPI.read_bytes())

# --- RETRACTION-INDEX.md entry ----------------------------------------------
RETRACTION = ROOT / "amphora-ip-fto-guard/evidence/phase0/kpis/RETRACTION-INDEX.md"
entry = f"""
## PIN-02 - stale benchmark_result_sha256 pin inside the KPI receipt itself (2026-08-17)

| claim | refuted-by receipt | superseded-by | date |
|---|---|---|---|
| evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json's checked-in benchmark_result_sha256 pin ({STALE}) currently identifies the real live evidence/phase0/benchmark/result.v1.json file | amphora-ip-fto-guard/evidence/audit/kpi-benchmark-pin-integrity-v1/kpi-benchmark-pin-integrity-receipt.v1.dsse.json | amphora-ip-fto-guard/evidence/audit/kpi-benchmark-pin-integrity-v1/kpi-benchmark-pin-integrity-receipt.v1.dsse.json | 2026-08-17 |

Finding: the KPI receipt file that docs/mission.md names as "The Phase-0 KPI receipt" (still unsigned, awaiting PHASE0_EVALUATOR/PHASE0_INTERNAL_REVIEWER per its own `awaiting` field) carried the exact same stale pre-R-B01 benchmark_result_sha256 value that the 2026-08-16 PIN-01 audit already found and fixed in docs/mission.md and docs/capability-profile.json. PIN-01's own receipt scoped itself to those two files only and did not enumerate this KPI file, so the stale pin survived undetected for a further 24 hours. `benchmark_lock_sha256` and `dataset_fixture_sha256` inside the same KPI file were independently checked and both remain correctly pinned -- this was a single-field defect. Repair: `benchmark_result_sha256` corrected from `{STALE}` to `{LIVE}` in the same fire. KPI file sha256 before={kpi_before_sha256}, after={kpi_after_sha256}.
"""
with open(RETRACTION, "a") as f:
    f.write(entry)
retraction_after_sha256 = sha(RETRACTION.read_bytes())

# --- derive public keys / key_ids from on-host seeds ------------------------
eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"

rev_sk = Ed25519PrivateKey.from_private_bytes(load_seed(REVIEWER_SEED))
rev_pub_hex = rev_sk.public_key().public_bytes_raw().hex()
rev_key_id = f"phase0-internal-reviewer-{sha(bytes.fromhex(rev_pub_hex))}"

trust = json.loads(TRUST.read_text())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
eval_derives_pin = (eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"))
rev_derives_pin = (rev_key_id == trust_by_role.get("PHASE0_INTERNAL_REVIEWER", {}).get("key_id"))

# --- receipt body -----------------------------------------------------------
body_obj = {
    "schema": "amphora.ip-fto-guard.kpi-benchmark-pin-integrity-receipt.v1",
    "study_id": diag["study_id"],
    "authority": "AUDIT_ONLY",
    "run_type": "KPI_BENCHMARK_PIN_INTEGRITY_AUDIT",
    "module": "amphora-ip-fto-guard",
    "campaign_item_id": "",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "claim_under_attack": (
        "evidence/phase0/kpis/ip-fto-guard-technical-landscape-kpi.v1.json's "
        "checked-in SHA-256 pins (benchmark_result_sha256, "
        "benchmark_lock_sha256, dataset_fixture_sha256) -- the module's own "
        "named 'Phase-0 KPI receipt', still awaiting evaluator/reviewer "
        "signature -- currently identify the real, live files on disk."
    ),
    "claim": diag["headline"],
    "purpose": diag["purpose"],
    "inputs": diag["inputs"],
    "live_hashes": diag["live_hashes"],
    "asserted_pins": diag["asserted_pins"],
    "consistency_checks": diag["consistency_checks"],
    "prior_repair_scope_cross_check": diag["prior_repair_scope_cross_check"],
    "fail_closed_mutation_demo": diag["fail_closed_mutation_demo"],
    "results": {
        "H0": diag["H0"],
        "H0_verdict": diag["H0_verdict"],
        "kpi_result_pin_matches_live": diag["consistency_checks"]["kpi_result_pin_matches_live"],
        "kpi_lock_pin_matches_live": diag["consistency_checks"]["kpi_lock_pin_matches_live"],
        "kpi_landscape_pin_matches_live": diag["consistency_checks"]["kpi_landscape_pin_matches_live"],
    },
    "does_not_close": diag["does_not_close"],
    "repair_performed_this_fire": {
        "description": (
            "Corrects evidence/phase0/kpis/ip-fto-guard-technical-landscape-"
            "kpi.v1.json's benchmark_result_sha256 field in place to the "
            "live, mechanically-verified value, and records a new "
            "RETRACTION-INDEX.md entry (PIN-02). This file is not itself a "
            "DSSE-signed artifact (no evaluator/reviewer signature exists on "
            "it yet -- it is still PRE_PHASE_0), so this is an in-place "
            "documentation-pin correction, the same pattern PIN-01 used for "
            "docs/mission.md and docs/capability-profile.json, not a "
            "supersession of a signed receipt."
        ),
        "kpi_file_path": str(KPI.relative_to(ROOT)),
        "benchmark_result_sha256_before": STALE,
        "benchmark_result_sha256_after": LIVE,
        "kpi_file_sha256_before": kpi_before_sha256,
        "kpi_file_sha256_after": kpi_after_sha256,
        "retraction_index_path": str(RETRACTION.relative_to(ROOT)),
        "retraction_index_sha256_after": retraction_after_sha256,
        "retraction_index_entry_id": "PIN-02",
        "note": (
            "Only the pin VALUE was corrected; benchmark_lock_sha256, "
            "dataset_fixture_sha256, all metrics, floors, observed values, "
            "claim_locks, and the 'awaiting' PHASE0_EVALUATOR/"
            "PHASE0_INTERNAL_REVIEWER signature list were left untouched. No "
            "scientific readiness, phase, or gate status was changed."
        ),
    },
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY audit receipt under evidence/audit/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_derives_pin),
    },
    "reviewer_reference": {
        "role": "PHASE0_INTERNAL_REVIEWER",
        "key_id": rev_key_id,
        "public_key_hex": rev_pub_hex,
        "derives_pinned_trust_store_key_id": bool(rev_derives_pin),
        "reviewer_signature_present": False,
        "note": "Reviewer key referenced for provenance only; no independent human review performed.",
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.ip-fto-guard-kpi-benchmark-pin-integrity+json"
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

out = BENCH / "kpi-benchmark-pin-integrity-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify ------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
print("H0_verdict", body_obj["results"]["H0_verdict"])
print("kpi_file_sha256_before", kpi_before_sha256)
print("kpi_file_sha256_after", kpi_after_sha256)
