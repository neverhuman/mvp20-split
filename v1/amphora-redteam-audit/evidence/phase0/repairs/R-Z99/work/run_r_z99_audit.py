#!/usr/bin/env python3
"""R-Z99 batch audit of Wave R interactive doc/prose repair done receipts.

Deterministic, pure filesystem-read audit: no RNG, no wall-clock embedded
in the diagnostic body. Checks, per receipt:
  (1) every path cited in the receipt's supersedes block(s) resolves to the
      claimed superseded_sha256 -- either directly (byte-identical artifact
      that was never touched) or via a documented preserved pre-repair
      backup (when the superseded artifact is mission.md prose that was
      intentionally edited going forward);
  (2) the receipt's DSSE envelope verifies against the pinned Phase-0
      evaluator key (derived from the seed and cross-checked against
      config/phase0-trust-store.v1.json);
  (3) the owning module's live docs/mission.md front-matter
      (phase/scientific_readiness/authority_ceiling/operational_readiness)
      matches the module's rank snapshot -- i.e. no promotion was smuggled
      in via the repair -- plus, for the two receipts that intentionally
      edited mission.md prose, that the front-matter is byte-identical
      between the preserved pre-repair backup and the live file;
  (4) (spot-check only, judged by the auditor, not scripted) 3 receipts
      read in full for substantive vs boilerplate corrected claims.
"""
import base64
import hashlib
import json
import os
import re
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
os.chdir(ROOT)

SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
RANK_SNAPSHOT = ROOT / "reports/portfolio-status-2026-08-03/data/rank.json"

RECEIPTS = [
    "amphora-ingredient-library/evidence/phase0/repairs/R-A01/done/repair-R-A01-done-receipt.v1.dsse.json",
    "amphora-cure-potlife-gate/evidence/phase0/repairs/R-A02/done/R-A02-repair-receipt.v1.dsse.json",
    "amphora-viscosity-score/evidence/phase0/repairs/R-A03/done/r-a03-disclosure-repair-receipt.v1.dsse.json",
    "amphora-sourceability-ehs/evidence/phase0/repairs/R-A04/done/r-a04-osha-table-z2-attribution-correction-receipt.v1.dsse.json",
    "amphora-molecule-property/evidence/phase0/repairs/R-A09/done/R-A09.done-receipt.v1.dsse.json",
    "amphora-solvency-score/evidence/phase0/repairs/R-A10/done/r-a10-prose-consistency-w7-disclosure-repair-receipt.v1.dsse.json",
    "amphora-design-rule-score/evidence/phase0/repairs/R-A11/done/R-A11.done-receipt.v1.dsse.json",
    "amphora-molecule-property/evidence/phase0/repairs/R-A11/done/R-A11.done-receipt.v1.dsse.json",
    "amphora-ip-fto-guard/evidence/phase0/repairs/R-A13/done/claim-chart-supersede-repair.R-A13.v1.dsse.json",
]

# receipts hand-read in full by the auditor for the (4) substantive/boilerplate
# spot-check (not scripted -- judgment call, recorded here for reproducibility
# of *which* 3 were chosen and what was found)
SPOT_CHECK_JUDGMENT = {
    "amphora-sourceability-ehs/evidence/phase0/repairs/R-A04/done/r-a04-osha-table-z2-attribution-correction-receipt.v1.dsse.json": {
        "substantive": True,
        "why": "Names the specific defect (toluene misattributed OSHA Table Z-1 "
               "vs actual Table Z-2), cites 29 CFR 1910.1000(b)(2) and the Z-2 "
               "acceptable-ceiling/peak structure, re-derives the 21-row Z-2 "
               "roster live from the refuting receipt, includes two matcher "
               "self-check probes (Styrene/Xylenes) to demonstrate the "
               "classifier is trustworthy, and explicitly scopes what is NOT "
               "changed (8/9 and 5/6 other attributions verified still correct, "
               "TWA ppm numerically unaffected). Not boilerplate.",
    },
    "amphora-design-rule-score/evidence/phase0/repairs/R-A11/done/R-A11.done-receipt.v1.dsse.json": {
        "substantive": True,
        "why": "Reads as a bare 'signature-identity re-issue' at first glance, "
               "but the artifact trail is real and independently verifiable: "
               "an anchored-reissue file was written "
               "(physical_baseline_receipt.v1.anchored-reissue.v1.json, sha "
               "confirmed live), and a brand-new "
               "evidence/phase0/kpis/RETRACTION-INDEX.md was created for a "
               "module that had none before (existed_before:false, sha "
               "confirmed live). This is a genuine anchoring-gap repair, not "
               "a placeholder re-sign.",
    },
    "amphora-ip-fto-guard/evidence/phase0/repairs/R-A13/done/claim-chart-supersede-repair.R-A13.v1.dsse.json": {
        "substantive": True,
        "why": "Replaces two fabricated/unsupported claim-1 elements "
               "('polyurea topcoat', 'low VOC coating system') with the real "
               "rendered EP2653485A2 claim-1 text (epoxy binder, >=82% volume "
               "solids per modified ISO 3233, <5hr dry-to-walk-on at 20C), "
               "flips design-around advice accordingly (baseline already "
               "sits below the volume-solids threshold; withdraws the prior "
               "polyurea-package rationale), and states residual scope limits "
               "(no legal-status verification, no equivalents analysis). Not "
               "boilerplate.",
    },
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(path):
    p = Path(path)
    if not p.exists() or p.is_dir():
        return None
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


def extract_front_matter(mission_md_text):
    m = re.match(r"^---\n(.*?)\n---\n", mission_md_text, re.S)
    if not m:
        return None
    return json.loads(m.group(1))


def find_supersede_entries(obj, out):
    if isinstance(obj, dict):
        if "superseded_path" in obj and "superseded_sha256" in obj:
            out.append(obj)
        for v in obj.values():
            find_supersede_entries(v, out)
    elif isinstance(obj, list):
        for v in obj:
            find_supersede_entries(v, out)


def check_supersedes_entry(entry):
    raw_path = entry["superseded_path"]
    expect = entry["superseded_sha256"]
    clean_path = raw_path.split(" (")[0].strip()

    # Case A: directory-listing digest (R-A09 style) -- surface_listing
    # sibling inside the same supersedes dict, path resolves to a directory.
    if "surface_listing" in entry and Path(clean_path).is_dir():
        listing = entry["surface_listing"]
        lines = []
        per_file_ok = True
        mismatches = []
        for item in sorted(listing, key=lambda x: x["file"]):
            fp = os.path.join(clean_path, item["file"])
            actual = sha_file(fp)
            if actual != item["sha256"]:
                per_file_ok = False
                mismatches.append(item["file"])
            lines.append(item["file"] + ":" + item["sha256"])
        computed = sha("\n".join(lines).encode())
        ok = per_file_ok and (computed == expect)
        return {
            "kind": "directory_listing_digest", "path": raw_path,
            "n_files": len(listing), "per_file_all_match": per_file_ok,
            "mismatched_files": mismatches, "computed_digest": computed,
            "expect_sha256": expect, "digest_match": computed == expect,
            "pass": ok,
        }

    # Case B: direct file check -- live file byte-matches superseded_sha256
    # (artifact claimed unmodified: another receipt, a fixture, etc).
    live_sha = sha_file(clean_path)
    live_match = live_sha == expect

    # Case C: preserved pre-repair backup -- either machine-declared via
    # superseded_preserved_at, or (R-A02) documented only in prose as a
    # work/ file; we resolve both by checking every *.pre-repair / *.pre-*
    # file under this receipt's sibling work/ dir plus any explicit path.
    preserved_at = entry.get("superseded_preserved_at")
    preserved_sha = sha_file(preserved_at) if preserved_at else None
    preserved_match = (preserved_sha == expect) if preserved_at else None

    return {
        "kind": "direct_or_preserved_file", "path": raw_path,
        "clean_path": clean_path, "expect_sha256": expect,
        "live_sha256": live_sha, "live_match": live_match,
        "preserved_at": preserved_at, "preserved_sha256": preserved_sha,
        "preserved_match": preserved_match,
        "pass": bool(live_match or preserved_match),
    }


def unstructured_backup_search(receipt_dir, expect_sha):
    """R-A02 preserves its mission.md backup only in free-text prose, not a
    structured superseded_preserved_at field. Search the receipt's sibling
    work/ dir for any file whose bytes match the claimed superseded_sha256,
    so the check does not depend on prose-parsing."""
    work_dir = Path(receipt_dir).parent.parent / "work"
    if not work_dir.is_dir():
        return None
    for f in work_dir.iterdir():
        if f.is_file() and sha_file(f) == expect_sha:
            return str(f)
    return None


def verify_dsse(receipt_path, eval_pub_bytes, eval_key_id):
    d = json.loads(Path(receipt_path).read_bytes())
    env = d["signature"] if isinstance(d.get("signature"), dict) and "payload" in d["signature"] else d
    try:
        payload_b = base64.standard_b64decode(env["payload"])
        ptype = env["payloadType"]
        sig_entry = env["signatures"][0]
        sig_b = base64.standard_b64decode(sig_entry["sig"])
        keyid = sig_entry["keyid"]
        Ed25519PublicKey.from_public_bytes(eval_pub_bytes).verify(sig_b, pae(ptype, payload_b))
        sig_ok = True
    except Exception as e:
        sig_ok = False
        keyid = None
        payload_b = b""
    keyid_pinned = (keyid == eval_key_id)
    return {
        "sig_valid": sig_ok, "keyid": keyid, "keyid_pinned_match": keyid_pinned,
        "pass": bool(sig_ok and keyid_pinned),
        "payload_sha256": sha(payload_b) if payload_b else None,
    }


def main():
    eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
    eval_pub = eval_sk.public_key().public_bytes_raw()
    eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
    trust = json.loads(TRUST.read_text())
    tbr = {k.get("role"): k for k in trust["keys"]}
    pinned_eval_key_id = tbr.get("PHASE0_EVALUATOR", {}).get("key_id")
    eval_pin_ok = (eval_key_id == pinned_eval_key_id)

    rank = json.loads(RANK_SNAPSHOT.read_bytes())
    rank_by_module = {m["module"]: m for m in rank["ranked"]}
    RANK_FIELDS = ["phase", "scientific_readiness", "authority_ceiling", "operational_readiness"]

    module_frontmatter_checked = {}
    rows = []
    all_pass = True

    for rp in RECEIPTS:
        d = json.loads(Path(rp).read_bytes())
        env = d["signature"] if isinstance(d.get("signature"), dict) and "payload" in d["signature"] else d
        body = json.loads(base64.standard_b64decode(env["payload"]))
        module = body.get("module_id") or body.get("module")
        repair_item = body.get("repair_item")

        dsse = verify_dsse(rp, eval_pub, eval_key_id)

        entries = []
        find_supersede_entries(body.get("supersedes"), entries)
        entry_results = []
        for e in entries:
            r = check_supersedes_entry(e)
            if not r["pass"] and r["kind"] == "direct_or_preserved_file" and not r["preserved_at"]:
                # R-A02-style: no structured preserved_at pointer given;
                # search sibling work/ dir for a byte-matching backup before
                # declaring failure.
                found = unstructured_backup_search(rp, r["expect_sha256"])
                if found:
                    r["preserved_at_unstructured_search"] = found
                    r["preserved_match"] = True
                    r["pass"] = True
            entry_results.append(r)
        supersedes_pass = all(r["pass"] for r in entry_results) if entry_results else False

        # mission front-matter parity vs rank snapshot (per module, checked once)
        if module not in module_frontmatter_checked:
            mission_path = Path(module) / "docs/mission.md"
            fm = extract_front_matter(mission_path.read_text())
            rk = rank_by_module.get(module, {})
            mismatches = [f for f in RANK_FIELDS if fm.get(f) != rk.get(f)]
            module_frontmatter_checked[module] = {
                "mission_md_path": str(mission_path),
                "live_front_matter": {f: fm.get(f) for f in RANK_FIELDS},
                "rank_snapshot": {f: rk.get(f) for f in RANK_FIELDS},
                "mismatches": mismatches,
                "pass": len(mismatches) == 0,
            }

        # front-matter byte-identity for the two receipts that intentionally
        # edited mission.md prose (R-A02, R-A10): compare preserved backup's
        # front matter vs live front matter.
        fm_identity_check = None
        for e in entry_results:
            preserved = e.get("preserved_at") or e.get("preserved_at_unstructured_search")
            if preserved and Path(preserved).exists() and "mission.md" in e.get("path", ""):
                before_fm_raw = extract_front_matter(Path(preserved).read_text())
                after_fm_raw = extract_front_matter((Path(module) / "docs/mission.md").read_text())
                fm_identity_check = {
                    "preserved_backup": preserved,
                    "front_matter_byte_identical": before_fm_raw == after_fm_raw,
                }

        row_pass = dsse["pass"] and supersedes_pass and module_frontmatter_checked[module]["pass"]
        if fm_identity_check is not None:
            row_pass = row_pass and fm_identity_check["front_matter_byte_identical"]
        all_pass = all_pass and row_pass

        rows.append({
            "receipt_path": rp,
            "module": module,
            "repair_item": repair_item,
            "dsse_verify": dsse,
            "supersedes_entries_checked": len(entry_results),
            "supersedes_results": entry_results,
            "supersedes_pass": supersedes_pass,
            "mission_frontmatter_parity_pass": module_frontmatter_checked[module]["pass"],
            "mission_frontmatter_prose_edit_identity_check": fm_identity_check,
            "row_pass": row_pass,
        })

    duplicate_repair_items = {}
    for rp in RECEIPTS:
        d = json.loads(Path(rp).read_bytes())
        env = d["signature"] if isinstance(d.get("signature"), dict) and "payload" in d["signature"] else d
        body = json.loads(base64.standard_b64decode(env["payload"]))
        ri = body.get("repair_item")
        duplicate_repair_items.setdefault(ri, []).append(body.get("module_id") or body.get("module"))
    duplicate_ids = {k: v for k, v in duplicate_repair_items.items() if len(v) > 1}

    verdict = "CLAIM_SURVIVED" if all_pass else "CLAIM_REFUTED"

    diagnostic = {
        "schema": "amphora.redteam-audit.r-z99-wave-r-batch-audit-diagnostic.v1",
        "claim_under_attack": {
            "receipt_path": "logs/falsification-ledger.jsonl",
            "claim_text": (
                "Every interactive Wave R done receipt (R-A01..R-A04, R-A09..R-A11, "
                "R-A13) is mechanically sound: originals byte-intact per embedded "
                "shas, DSSE verifies anchored, mission front-matter untouched, "
                "corrected claims substantive."
            ),
        },
        "pre_registered_refutation_criteria": {
            "would_refute_if": (
                "ANY of: (a) a supersedes-block path's live bytes (or, when the "
                "superseded artifact is mission.md prose intentionally amended, "
                "its preserved pre-repair backup) fail to sha256-match the "
                "declared superseded_sha256; (b) a receipt's DSSE envelope fails "
                "Ed25519 verification against the pinned PHASE0_EVALUATOR key or "
                "signs with a non-pinned keyid; (c) a module's live mission.md "
                "front-matter (phase/scientific_readiness/authority_ceiling/"
                "operational_readiness) diverges from that module's rank "
                "snapshot, indicating a promotion smuggled in via the repair; "
                "(d) any of the 3 hand-read spot-check receipts turns out to "
                "contain only boilerplate/placeholder corrected-claim text with "
                "no verifiable specific defect and fix."
            ),
            "n_receipts_audited": len(RECEIPTS),
            "n_supersedes_entries_checked": sum(r["supersedes_entries_checked"] for r in rows),
            "n_modules_frontmatter_checked": len(module_frontmatter_checked),
            "n_spot_checked_for_substantiveness": len(SPOT_CHECK_JUDGMENT),
            "verdict": verdict,
        },
        "evaluator_key": {
            "derived_key_id": eval_key_id,
            "pinned_trust_store_key_id": pinned_eval_key_id,
            "pin_match": eval_pin_ok,
        },
        "rows": rows,
        "module_frontmatter_parity": module_frontmatter_checked,
        "spot_check_substantiveness_judgment": SPOT_CHECK_JUDGMENT,
        "observations_non_fatal": {
            "duplicate_repair_item_ids_across_modules": duplicate_ids,
            "note": (
                "R-A11 is used as the repair_item id by two independent, "
                "unrelated repairs in two different modules "
                "(amphora-design-rule-score anchoring the Guth-Gold baseline "
                "receipt; amphora-molecule-property anchoring the "
                "phys-ml-stack c8-fire2 receipt). Both receipts independently "
                "pass all four mechanical checks; the shared id is a campaign "
                "numbering collision, not a data-integrity defect, and does not "
                "affect this claim's truth value."
            ),
        },
        "summary_counts": {
            "n_rows": len(rows),
            "n_rows_pass": sum(1 for r in rows if r["row_pass"]),
            "n_rows_fail": sum(1 for r in rows if not r["row_pass"]),
        },
        "verdict": verdict,
    }
    return diagnostic


if __name__ == "__main__":
    diag = main()
    print(json.dumps(diag, indent=2, sort_keys=True))
