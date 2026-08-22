#!/usr/bin/env python3
"""DSSE-Ed25519-sign the ip-fto-guard R-S02 CPC category-screen audit,
batch 3/3 FINAL. This is the campaign's done/ receipt: R-S02's
done_criterion (all 54 rows verdicted, cumulative table, fabricated/
misassigned counts stated, every finding filed with an owner in
proposed_followups) is met by this fire. The receipt lands in done/
because the AUDIT is complete -- NOT because the pinned claim survived.
The claim itself remains CLAIM_REFUTED (row n=19's misassignment, found in
batch1, is not yet repaired); 'done' and 'claim survives' are independent
per the campaign's REPAIR MODE rules.
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
ITEM = ROOT / "amphora-ip-fto-guard/evidence/phase0/repairs/R-S02"
WORK = ITEM / "work"
ATTEMPTS = ITEM / "attempts"
DONE = ITEM / "done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
REVIEWER_SEED = SEED_DIR / "internal-reviewer.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


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


def load_envelope_body(path):
    d = json.loads(path.read_text())
    return json.loads(base64.b64decode(d["signature"]["payload"]))


# --- two-replay gate (batch3) ------------------------------------------------
canon = (WORK / "diagnostic.canonical.json").read_bytes()
runB = (WORK / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag3 = json.loads(canon)
harness_sha = sha((WORK / "run_cpc_category_screen_audit_batch3.py").read_bytes())
state = json.loads((WORK / "STATE.json").read_text())

# --- pull batch1 + batch2 rows from their already-signed receipts -----------
body1 = load_envelope_body(ATTEMPTS / "cpc-category-screen-audit-batch1.R-S02.v1.dsse.json")
body2 = load_envelope_body(ATTEMPTS / "cpc-category-screen-audit-batch2.R-S02.v1.dsse.json")

all_rows = sorted(body1["rows"] + body2["rows"] + diag3["rows"], key=lambda r: r["n"])
assert len(all_rows) == 54, f"expected 54 total rows, got {len(all_rows)}"
assert [r["n"] for r in all_rows] == sorted(set(r["n"] for r in all_rows)), "duplicate row n"

cumulative_counts = {"faithful": 0, "misassigned": 0, "fabricated": 0}
misassigned_ns, fabricated_ns = [], []
for r in all_rows:
    cumulative_counts[r["verdict"]] += 1
    if r["verdict"] == "misassigned":
        misassigned_ns.append(r["n"])
    if r["verdict"] == "fabricated":
        fabricated_ns.append(r["n"])
assert cumulative_counts == diag3["cumulative_counts"], (cumulative_counts, diag3["cumulative_counts"])
assert misassigned_ns == [19]
assert fabricated_ns == []

claim_refuted = cumulative_counts["misassigned"] > 0 or cumulative_counts["fabricated"] > 0

# --- merge proposed_followups from all three batches (dedup by defect text) -
seen_defects = set()
merged_followups = []
for src in (body1.get("proposed_followups", []), body2.get("proposed_followups", []), diag3["proposed_followups"]):
    for f in src:
        key = f["defect"]
        if key not in seen_defects:
            seen_defects.add(key)
            merged_followups.append(f)

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
    "schema": "amphora.ip-fto-guard.r-s02-cpc-category-screen-audit-receipt.v1",
    "study_id": "IP_FTO_GUARD_R_S02_CPC_CATEGORY_SCREEN_AUDIT_DONE",
    "authority": "AUDIT_ONLY",
    "run_type": "CPC_CATEGORY_SCREEN_PER_ROW_ADJUDICATION_AUDIT_DONE",
    "module": "amphora-ip-fto-guard",
    "campaign_item_id": "R-S02",
    "batch": "3_of_3 (FINAL -- cumulative done receipt covering all 54/54 rows across batches 1+2+3)",
    "repair_status": "in_progress",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "modifies_manifest": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_pinned_fixture": False,
    "supersedes": None,
    "claim_under_attack": "amphora-ip-fto-guard/evidence/audit/: the 54 of 60 patent-landscape rows audited only by bare CPC/IPC screen contain no further fabricated or misassigned elements.",
    "purpose": "Campaign R-S02 DONE receipt: cumulative per-row CPC/IPC classification-faithfulness adjudication of ALL 54 bare-category-screen rows (n=6-25,27-60, excluding n=26 which is claim-charted and already audited elsewhere), assembled from batch1 (n=6-23), batch2 (n=24,25,27-42) and batch3 (n=43-60) against the OFFICIAL CPC Title List (EPO/USPTO, edition 202608).",
    "non_circularity": "Real-world published classification corpus (EPO/USPTO CPC Title List, edition 202608), hash-pinned bulk-data download, independent of the fixture under audit and independent of any prior ip-fto-guard receipt.",
    "theory_reference": "Cooperative Patent Classification (CPC), joint EPO/USPTO scheme extending IPC (Strasbourg Agreement 1971, as amended); Guide to the CPC (EPO/USPTO); CPC Title List bulk data edition 202608.",
    "source_provenance_batch1": body1.get("source_provenance"),
    "source_provenance_batch2": body2.get("source_provenance"),
    "source_provenance_batch3": diag3["source_provenance"],
    "fixture": diag3["fixture"],
    "total_rows_to_audit": 54,
    "all_54_rows_verdicted": True,
    "rows": all_rows,
    "cumulative_counts": cumulative_counts,
    "misassigned_row_ns": misassigned_ns,
    "fabricated_row_ns": fabricated_ns,
    "batch_provenance": {
        "batch1": {"rows": body1["batch_rows"], "receipt": "amphora-ip-fto-guard/evidence/phase0/repairs/R-S02/attempts/cpc-category-screen-audit-batch1.R-S02.v1.dsse.json", "fire_id": "20260812T150001-697004-87a45b133eb8"},
        "batch2": {"rows": body2["batch_rows"], "receipt": "amphora-ip-fto-guard/evidence/phase0/repairs/R-S02/attempts/cpc-category-screen-audit-batch2.R-S02.v1.dsse.json", "fire_id": "20260812T160001-1356894-a058b877d112"},
        "batch3": {"rows": diag3["batch_rows"], "receipt": "amphora-ip-fto-guard/evidence/phase0/repairs/R-S02/done/cpc-category-screen-audit-batch3-FINAL.R-S02.v1.dsse.json (this receipt)", "fire_id": "20260812T170002-1705294-e13ed5fa16dd"},
    },
    "cumulative_state": state,
    "headline": (
        f"R-S02 DONE: all 54/54 bare-CPC-screen rows verdicted across 3 batches -- "
        f"{cumulative_counts['faithful']} faithful, {cumulative_counts['misassigned']} misassigned "
        f"(row n=19), {cumulative_counts['fabricated']} fabricated. The pinned universal claim "
        "('the 54 rows contain no further fabricated or misassigned elements') is CLAIM_REFUTED "
        "by row n=19's C08G59/50 ('Amines', curing-agent branch) misassignment for an epoxide-side "
        "reactive-diluent family (correct branch: C08G59/20's epoxy-compound subgroups). This is an "
        "AUDIT-COMPLETION receipt, not a repair: 'done' means all 54 rows now carry a verdict "
        "(the R-S02 done_criterion), independent of the claim's truth value, which remains false "
        "and unrepaired. Two open follow-ups are filed (see proposed_followups) naming "
        "amphora-ip-fto-guard as owner: (1) repair row n=19's cpc_ipc_class tag via a superseding "
        "patch, and (2) resolve whether the correct replacement symbol is C08G59/36 or the more "
        "specific C08G59/223 sibling (di-epoxy branch), a refinement question surfaced while "
        "adjudicating row n=55 in batch3."
    ),
    "verdict": "CLAIM_REFUTED",
    "verdict_rationale": (
        "The pinned claim is a universal claim over all 54 rows ('contain no further fabricated or "
        "misassigned elements'). Batch1 found one genuine counter-example (row n=19) in the first "
        "18 rows; batches 2 and 3 (36 further rows, now 100% of the 54) found zero additional "
        "defects. One true counter-example is sufficient to refute a universal claim regardless of "
        "how many other rows check out -- the claim was refuted as soon as batch1 landed, and "
        "remains refuted now that the audit is complete, because row n=19 has not been repaired. "
        "This receipt satisfies R-S02's own done_criterion (all 54 rows adjudicated with quoted "
        "CPC definition text and stated fabricated/misassigned counts, every finding owned in "
        "proposed_followups) and therefore lands in done/ -- but 'audit done' and 'claim survived' "
        "are independent facts, and only the latter is false here."
    ),
    "proposed_followups": merged_followups,
    "does_not_close": [
        "Does not assert any row is FTO or legally cleared (every row already carries not_fto=true; this audit does not touch that field).",
        "Does not verify legal status, prosecution history, or claim scope of any cited patent family -- title-list classification faithfulness only.",
        "Uses the CPC Scheme Title List (symbol titles + hierarchy), not the longer prose CPC Definitions document; a title-level mismatch is sufficient to prove misassignment, but title-level agreement does not itself prove exhaustive definitional agreement.",
        "Does not repair row n=19's cpc_ipc_class tag -- that is a separate, still-open follow-up action (see proposed_followups), out of scope for R-S02's audit-only mandate and its exhausted max_fires=3 budget.",
        "Does not audit row n=26 (independent_claim_chart.charted=true) -- already covered by amphora-ip-fto-guard-claim-chart-provenance-result, per batch1's exclusion note.",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": sha(canon),
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "harness_sha256": harness_sha,
        "batch1_receipt_verified_present": True,
        "batch2_receipt_verified_present": True,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY done receipt under evidence/phase0/repairs/R-S02/done/",
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
ptype = "application/vnd.amphora.ip-fto-guard-r-s02-cpc-category-screen-audit-done+json"
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

DONE.mkdir(parents=True, exist_ok=True)
out = DONE / "cpc-category-screen-audit-batch3-FINAL.R-S02.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# --- self-verify ------------------------------------------------------------
pk = Ed25519PublicKey.from_public_bytes(eval_pub)
pk.verify(base64.standard_b64decode(envelope["signatures"][0]["sig"]),
          pae(ptype, base64.standard_b64decode(envelope["payload"])))

print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_derives_pin)
print("reviewer_derives_pinned_trust_key", rev_derives_pin)
print("cumulative_counts", cumulative_counts)
print("misassigned_row_ns", misassigned_ns)
print("receipt_body_sha256", sha(body))
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
