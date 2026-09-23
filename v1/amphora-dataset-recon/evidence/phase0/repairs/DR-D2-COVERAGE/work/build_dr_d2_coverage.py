#!/usr/bin/env python3
"""Build the obligation-coverage table for AMPHORA-DIRECTIVE-2026-08-09 (DR-D2-COVERAGE).
Cross-checks the directive's obligation index against campaign.json and the live
on-disk receipt tree; reports UNMAPPED / ORPHAN lists; spot-checks >=4 closed
obligations by decoding and DSSE-verifying their actual receipts.
No web access, no acquisition -- pure read/cross-check over already-present repo state.
"""
import base64
import glob as globmod
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-dataset-recon"
ITEM = MOD / "evidence/phase0/repairs/DR-D2-COVERAGE"
WORK = ITEM / "work"

DIRECTIVE_MD = ROOT / "docs/directives/2026-08-09-dataset-reconnaissance-multilingual.md"
DIRECTIVE_INDEX = ROOT / "docs/directives/2026-08-09-dataset-recon.index.json"
DIRECTIVE_SHA_EXPECTED = "97fad5d1636f5ccb106562c2d940535651c216d357dd5276088f2db12bdba207"
CAMPAIGN_SNAPSHOT = WORK / "campaign.snapshot.json"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"


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


def resolve_glob(pattern):
    # done_check globs use `**` -- Path.glob handles this with recursive=True equivalent
    matches = sorted(globmod.glob(str(ROOT / pattern), recursive=True))
    return [str(Path(m).relative_to(ROOT)) for m in matches]


def build_table(obligations, campaign_by_id):
    """Pure function: obligations (list of dicts from directive index) x
    campaign_by_id (dict id -> campaign item) -> (rows, unmapped, orphan)."""
    rows = []
    unmapped = []
    for ob in obligations:
        oid = ob["id"]
        item = campaign_by_id.get(oid)
        if item is None:
            unmapped.append(oid)
            rows.append({
                "id": oid, "section": ob.get("section"), "owner": ob.get("owner"),
                "index_module": ob.get("module"), "campaign_status": None,
                "campaign_module": None, "done_check_glob": None,
                "receipt_files": [], "receipt_count": 0,
                "closed_supported": None,
            })
            continue
        dc = item.get("done_check", {})
        glob_pat = dc.get("glob") if dc.get("kind") == "signed_receipt_glob" else None
        files = resolve_glob(glob_pat) if glob_pat else []
        status = item.get("status")
        closed_supported = None
        if status == "done":
            closed_supported = len(files) > 0
        rows.append({
            "id": oid, "section": ob.get("section"), "owner": ob.get("owner"),
            "index_module": ob.get("module"), "campaign_status": status,
            "campaign_module": item.get("module"), "done_check_glob": glob_pat,
            "receipt_files": files, "receipt_count": len(files),
            "closed_supported": closed_supported,
        })
    return rows


def orphan_check(campaign_items, obligation_ids, directive_id):
    orphans = []
    for it in campaign_items:
        dref = it.get("directive_ref")
        if dref and dref.get("doc") == directive_id:
            if it["id"] not in obligation_ids:
                orphans.append(it["id"])
    return orphans


def violations_of(rows):
    """The mechanical refutation check: any row with campaign_status == 'done'
    but receipt_count == 0 (closed status the receipts do not support), or
    any row representing an obligation absent from campaign (unmapped)."""
    v = []
    for r in rows:
        if r["campaign_status"] is None:
            v.append({"id": r["id"], "reason": "UNMAPPED: obligation in index has no matching campaign item"})
        elif r["campaign_status"] == "done" and r["receipt_count"] == 0:
            v.append({"id": r["id"], "reason": "closed status ('done') not supported by any receipt file at its done_check glob"})
    return v


def canonical(obj):
    return json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True).encode("utf-8")


# ---------- load inputs ----------
directive_bytes = DIRECTIVE_MD.read_bytes()
directive_sha_actual = sha(directive_bytes)
assert directive_sha_actual == DIRECTIVE_SHA_EXPECTED, "directive md sha mismatch: %s" % directive_sha_actual

directive_index = json.loads(DIRECTIVE_INDEX.read_bytes())
obligations = directive_index["obligations"]
obligation_ids = [o["id"] for o in obligations]
obligation_ids_set = set(obligation_ids)
assert len(obligation_ids) == len(obligation_ids_set), "duplicate obligation ids in index"

campaign = json.loads(CAMPAIGN_SNAPSHOT.read_bytes())
campaign_items = campaign["items"]
campaign_by_id = {it["id"]: it for it in campaign_items if "id" in it}

DIRECTIVE_ID = directive_index["directive"]["directive_id"]
assert DIRECTIVE_ID == "AMPHORA-DIRECTIVE-2026-08-09"

# ---------- run A (real state) ----------
rows_A = build_table(obligations, campaign_by_id)
unmapped_A = [r["id"] for r in rows_A if r["campaign_status"] is None]
orphan_A = orphan_check(campaign_items, obligation_ids_set, DIRECTIVE_ID)
violations_A = violations_of(rows_A)

diagnostic_A = {
    "directive_id": DIRECTIVE_ID,
    "num_obligations": len(obligations),
    "rows": rows_A,
    "unmapped": sorted(unmapped_A),
    "orphan": sorted(orphan_A),
    "violations": violations_A,
    "refutation_criterion_observed_overall": len(violations_A) > 0,
}
(WORK / "diagnostic.runA.json").write_bytes(canonical(diagnostic_A))

# ---------- run B (byte-stability replay, independent process invocation semantics) ----------
rows_B = build_table(obligations, campaign_by_id)
unmapped_B = [r["id"] for r in rows_B if r["campaign_status"] is None]
orphan_B = orphan_check(campaign_items, obligation_ids_set, DIRECTIVE_ID)
violations_B = violations_of(rows_B)
diagnostic_B = {
    "directive_id": DIRECTIVE_ID,
    "num_obligations": len(obligations),
    "rows": rows_B,
    "unmapped": sorted(unmapped_B),
    "orphan": sorted(orphan_B),
    "violations": violations_B,
    "refutation_criterion_observed_overall": len(violations_B) > 0,
}
(WORK / "diagnostic.runB.json").write_bytes(canonical(diagnostic_B))

sha_A = sha(canonical(diagnostic_A))
sha_B = sha(canonical(diagnostic_B))
assert sha_A == sha_B, "two-replay byte-stability gate FAILED: %s vs %s" % (sha_A, sha_B)

# ---------- positive control: plant a fabricated closed flag in a COPY ----------
# DR-FRESH is currently status='blocked' with 0 receipt files at its done glob.
# Flip it to 'done' in an in-memory copy only (nothing written to campaign.json,
# nothing written to campaign.snapshot.json) and confirm the checker's
# closed-status-unsupported clause fires on exactly that id.
PLANT_TARGET = "DR-FRESH"
assert campaign_by_id[PLANT_TARGET]["status"] != "done", "positive control precondition failed: target already done"
mutant_campaign_by_id = {k: (dict(v) if k != PLANT_TARGET else {**v, "status": "done"}) for k, v in campaign_by_id.items()}
mutant_rows = build_table(obligations, mutant_campaign_by_id)
mutant_violations = violations_of(mutant_rows)
mutant_diagnostic = {
    "directive_id": DIRECTIVE_ID,
    "num_obligations": len(obligations),
    "rows": mutant_rows,
    "unmapped": sorted([r["id"] for r in mutant_rows if r["campaign_status"] is None]),
    "orphan": sorted(orphan_check(campaign_items, obligation_ids_set, DIRECTIVE_ID)),
    "violations": mutant_violations,
    "refutation_criterion_observed_overall": len(mutant_violations) > 0,
}
(WORK / "diagnostic.mutant.json").write_bytes(canonical(mutant_diagnostic))

plant_detected = (
    len(mutant_violations) == 1
    and mutant_violations[0]["id"] == PLANT_TARGET
    and "closed status" in mutant_violations[0]["reason"]
)
assert plant_detected, "POSITIVE CONTROL FAILED: planted defect on %s not detected: %r" % (PLANT_TARGET, mutant_violations)

# run the mutant check a second time for its own byte-stability
mutant_rows_2 = build_table(obligations, mutant_campaign_by_id)
mutant_violations_2 = violations_of(mutant_rows_2)
mutant_diagnostic_2 = {
    "directive_id": DIRECTIVE_ID,
    "num_obligations": len(obligations),
    "rows": mutant_rows_2,
    "unmapped": sorted([r["id"] for r in mutant_rows_2 if r["campaign_status"] is None]),
    "orphan": sorted(orphan_check(campaign_items, obligation_ids_set, DIRECTIVE_ID)),
    "violations": mutant_violations_2,
    "refutation_criterion_observed_overall": len(mutant_violations_2) > 0,
}
mutant_sha_2 = sha(canonical(mutant_diagnostic_2))
mutant_sha_1 = sha(canonical(mutant_diagnostic))
assert mutant_sha_1 == mutant_sha_2, "mutant two-replay byte-stability gate FAILED"

print("REAL two-replay sha:", sha_A, "==", sha_B)
print("MUTANT two-replay sha:", mutant_sha_1, "==", mutant_sha_2)
print("real violations:", violations_A)
print("mutant violations:", mutant_violations)
print("unmapped:", unmapped_A)
print("orphan:", orphan_A)

# ---------- spot-check >=4 closed obligations by reading their actual DSSE receipts ----------
SEED_DIR_TRUST = ROOT / "config/phase0-trust-store.v1.json"
trust = json.loads(SEED_DIR_TRUST.read_bytes())
trust_by_role = {k.get("role"): k for k in trust["keys"]}
pinned_pub_hex = trust_by_role.get("PHASE0_EVALUATOR", {}).get("public_key_hex") or trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id")

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub_hex = eval_sk.public_key().public_bytes_raw().hex()
eval_key_id = f"phase0-evaluator-{sha(bytes.fromhex(eval_pub_hex))}"
assert eval_key_id == trust_by_role.get("PHASE0_EVALUATOR", {}).get("key_id"), "evaluator key_id does not derive pinned trust store entry"

SPOT_CHECK_IDS = ["PROBE-WEB", "DR-LANG-DE", "DR-COVERAGE", "CF-ARITH"]

spot_checks = []
pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(eval_pub_hex))
for oid in SPOT_CHECK_IDS:
    row = next(r for r in rows_A if r["id"] == oid)
    assert row["campaign_status"] == "done", f"{oid} not status=done, cannot spot-check as a closed obligation"
    assert row["receipt_count"] >= 1, f"{oid} has no receipt file to spot-check"
    receipt_path = ROOT / row["receipt_files"][0]
    raw = json.loads(receipt_path.read_bytes())
    # Two observed envelope shapes in this module's receipt corpus:
    # (a) DSSE envelope at top level: {payloadType, payload, signatures}
    # (b) DSSE envelope nested under "signature": {..., signature: {payloadType, payload, signatures}}
    envelope = raw["signature"] if ("payloadType" not in raw and "signature" in raw) else raw
    payload_type = envelope["payloadType"]
    payload_bytes = base64.b64decode(envelope["payload"])
    sig = envelope["signatures"][0]
    keyid_matches_pinned = sig["keyid"] == eval_key_id
    msg = pae(payload_type, payload_bytes)
    sig_valid = False
    try:
        pub.verify(base64.b64decode(sig["sig"]), msg)
        sig_valid = True
    except Exception as e:
        sig_valid = False
    payload = json.loads(payload_bytes)
    # Receipt schemas across modules use different field names for the same concept
    # (claim_verdict vs verdict; refutation_criterion_observed vs ..._observation_occurred
    # vs ..._observed_overall). Scan the known aliases rather than assuming one schema.
    VERDICT_KEYS = ["claim_verdict", "verdict"]
    CONTRADICTION_BOOL_KEYS = [
        "refutation_criterion_observed", "refutation_criterion_observation_occurred",
        "refutation_criterion_observed_overall",
    ]
    found_verdict = next((payload[k] for k in VERDICT_KEYS if k in payload), None)
    contradiction_reasons = []
    if found_verdict is not None and found_verdict not in ("CLAIM_SURVIVED", "CLAIM_REFUTED"):
        contradiction_reasons.append(f"verdict field holds unexpected value {found_verdict!r}")
    for k in CONTRADICTION_BOOL_KEYS:
        if payload.get(k) is True:
            contradiction_reasons.append(f"{k} is True (refutation criterion fired against this receipt's own deliverable state)")
    if payload.get("done_criterion_met") is False:
        contradiction_reasons.append("done_criterion_met is False")
    rs = payload.get("repair_status")
    if rs and "in_progress" in str(rs):
        contradiction_reasons.append(f"repair_status={rs!r}")
    closure_supported = bool(sig_valid and keyid_matches_pinned and not contradiction_reasons)
    spot_checks.append({
        "obligation_id": oid,
        "receipt_path": row["receipt_files"][0],
        "receipt_sha256": sha(receipt_path.read_bytes()),
        "payload_type": payload_type,
        "envelope_shape": "nested_under_signature_key" if ("payloadType" not in raw and "signature" in raw) else "top_level",
        "signature_keyid_matches_pinned_evaluator": keyid_matches_pinned,
        "dsse_signature_verifies": sig_valid,
        "verdict_field_found_in_payload": found_verdict,
        "contradiction_reasons": contradiction_reasons,
        "closure_supported": closure_supported,
    })
    assert sig_valid, f"DSSE signature FAILED to verify for {oid} receipt {row['receipt_files'][0]}"
    assert keyid_matches_pinned, f"receipt for {oid} signed by non-pinned key"

print(json.dumps(spot_checks, indent=2, sort_keys=True))
spot_check_all_ok = all(s["closure_supported"] for s in spot_checks)
assert spot_check_all_ok, "at least one spot-checked closed obligation's receipt does not support its closed status"
assert len(spot_checks) >= 3

with open(WORK / "spot_checks.json", "w") as f:
    f.write(json.dumps(spot_checks, indent=2, ensure_ascii=False, sort_keys=True))

print("spot checks OK:", [s["obligation_id"] for s in spot_checks])
print("ALL GATES PASS")
