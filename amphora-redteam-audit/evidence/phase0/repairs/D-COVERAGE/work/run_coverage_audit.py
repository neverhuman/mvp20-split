#!/usr/bin/env python3
"""D-COVERAGE self-attack: for every obligation the raw directive_coverage.py
output marks 'closed', check whether the underlying campaign item's actual
recorded fire outcome (and, for a spot-checked subset, the actual signed DSSE
receipt payload read from disk) shows the founder's own done_criteria were
met -- or whether 'closed' means only 'a campaign item investigated this and
banked a verdict', which for a CLAIM_REFUTED verdict means the opposite: a
confirmed, currently-unremediated defect.

Deterministic: pure filesystem read of already-signed receipts + the pinned
campaign.json/coverage snapshots. No RNG, no wall-clock in the output body.
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
WORK = ROOT / "amphora-redteam-audit/evidence/phase0/repairs/D-COVERAGE/work"

SPOT_CHECK_IDS = ["T2-01", "T2-04", "T2-05", "T2-13"]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_dsse_body(path):
    d = json.loads(path.read_bytes())
    env = d.get("signature", d)
    body = json.loads(base64.b64decode(env["payload"]))
    return body, env


def main():
    cov = json.loads((WORK / "diagnostic.runA.json").read_bytes())
    campaign = json.loads((WORK / "campaign.snapshot.json").read_bytes())
    items = campaign["items"] if isinstance(campaign, dict) else campaign
    by_id = {i["id"]: i for i in items}

    rows = cov["rows"]
    closed_rows = [r for r in rows
                   if r["closed"] or r["index_status"] in ("already-delivered", "already-satisfied")]

    audit = []
    for r in closed_rows:
        cids = r["campaign_items"]
        if not cids:
            # implementation obligation, not an attack -- delivered by construction
            audit.append({
                "id": r["id"], "basis": "already-delivered (non-attack implementation obligation)",
                "campaign_items": [], "per_item": [], "verdict": "delivered",
            })
            continue
        per_item = []
        for cid in cids:
            it = by_id.get(cid)
            fires = (it or {}).get("fires", [])
            last = fires[-1] if fires else None
            outcome = last["outcome"] if last else None
            per_item.append({
                "campaign_item": cid,
                "item_status": (it or {}).get("status"),
                "n_fires": len(fires),
                "last_fire_outcome": outcome,
                # CLAIM_REFUTED on a Wave-T2/V2 "does the defense hold" attack means the
                # founder's stated done_criteria (defense holds) was NOT met -- the attack
                # found the very defect the obligation asks to be absent.
                "founder_done_criteria_met_inferred": (outcome == "CLAIM_SURVIVED"),
            })
        all_delivered = all(p["founder_done_criteria_met_inferred"] for p in per_item)
        any_delivered = any(p["founder_done_criteria_met_inferred"] for p in per_item)
        verdict = "delivered" if all_delivered else ("mixed" if any_delivered else "not_delivered")
        audit.append({
            "id": r["id"], "basis": "campaign-item last-fire-outcome (ledger/campaign.json)",
            "campaign_items": cids, "per_item": per_item, "verdict": verdict,
        })

    # ---- spot check: read the ACTUAL signed receipt bytes for a subset, don't trust fire-summary text ----
    spot_checks = []
    for oid in SPOT_CHECK_IDS:
        row = next(r for r in rows if r["id"] == oid)
        receipt_paths = [p for p in row["receipts"] if p.endswith(".json")]
        # prefer the repairs/<item>/done/ receipt path if present
        done_paths = [p for p in receipt_paths if "/repairs/" in p and "/done/" in p]
        target = done_paths[0] if done_paths else (receipt_paths[0] if receipt_paths else None)
        if target is None:
            spot_checks.append({"obligation_id": oid, "error": "no .json receipt path recorded"})
            continue
        full = ROOT / target
        if not full.exists():
            spot_checks.append({"obligation_id": oid, "receipt_path": target,
                                 "error": "receipt path does not resolve on disk"})
            continue
        body, env = load_dsse_body(full)
        directive_obl = body.get("directive_obligation")
        if directive_obl is None and isinstance(body.get("directive_ref"), dict):
            directive_obl = body["directive_ref"].get("directive_obligation") or body["directive_ref"].get("item_id")
        verdict_field = body.get("verdict")
        done_met = body.get("founder_directive_done_criteria_met")
        refuted_obs = body.get("refutation_criterion_observed")
        if refuted_obs is None:
            refuted_obs = body.get("refutation_criterion_observation_occurred")
        if done_met is None:
            # infer from verdict + refutation-observed fields when the receipt predates
            # the founder_directive_done_criteria_met field
            if verdict_field == "SURVIVED" and refuted_obs is False:
                done_met = True
            elif verdict_field == "CLAIM_REFUTED" and refuted_obs is True:
                done_met = False
            elif verdict_field == "CLAIM_REFUTED":
                done_met = False
        spot_checks.append({
            "obligation_id": oid,
            "receipt_path": target,
            "receipt_sha256": sha(full),
            "receipt_directive_obligation_field": directive_obl,
            "receipt_verdict_field": verdict_field,
            "receipt_refutation_criterion_observed": refuted_obs,
            "receipt_founder_done_criteria_met": done_met,
            "delivered_verdict": "DELIVERED" if done_met is True else (
                "NOT_DELIVERED" if done_met is False else "INDETERMINATE"),
        })

    n_closed = len(closed_rows)
    n_delivered = sum(1 for a in audit if a["verdict"] == "delivered")
    n_mixed = sum(1 for a in audit if a["verdict"] == "mixed")
    n_not_delivered = sum(1 for a in audit if a["verdict"] == "not_delivered")

    out = {
        "schema": "amphora.redteam-audit.d-coverage-closed-obligation-audit.v1",
        "n_obligations_total": len(rows),
        "n_closed_by_naive_flag": n_closed,
        "closed_obligation_audit": audit,
        "closed_delivered_count": n_delivered,
        "closed_mixed_count": n_mixed,
        "closed_not_delivered_count": n_not_delivered,
        "spot_checks": spot_checks,
        "unmapped": cov["unmapped"],
        "unmapped_count": len(cov["unmapped"]),
        "orphans": cov["orphans"],
        "orphans_count": len(cov["orphans"]),
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
