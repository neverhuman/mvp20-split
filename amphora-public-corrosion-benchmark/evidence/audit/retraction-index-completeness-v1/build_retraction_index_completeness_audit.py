#!/usr/bin/env python3
"""
ROTATION-mode attack, fire 20260819T170001-2124960-8d2aadf89e64.

Claim under attack (the strongest currently-standing governance claim this
module's whole falsification-ledger discipline depends on that has NOT yet
been directly, mechanically tested): "RETRACTION-INDEX.md is a complete and
current record of every claim this module's own signed evidence/audit/
receipts have found refuted." This file is the module's own stated
supersede-never-rewrite mechanism (docs/mission.md and every repair receipt
point to it as the authoritative retraction record) and it is read by
humans, not machine-checked at build time the way the consolidated-KPI
index is (R-S07's check_index_completeness.py already covers THAT surface;
this audit covers the orthogonal one R-S07 does not touch).

Prior escalations on THIS module attacked cross-file staleness of the
audit_verdicts_index blob inside the *-consolidated-kpi.json (2026-08-02
kpi-surface-completeness-v1, 2026-08-03 consolidated-kpi-staleness-v1,
2026-08-16 consolidated-index-third-recurrence-v1), and separately
intra-receipt self-consistency of each receipt's own prose
(2026-08-17 eis-reproducibility-self-consistency-v1). The most recent
(2026-08-18 nist-baseline-still-valid-claim-currency-v1) found, as a side
observation while attacking a different specific KPI field, that neither
RETRACTION-INDEX.md nor docs/mission.md mention two already-REFUTED audits
and explicitly logged `awaiting: "A repair fire ... to update
RETRACTION-INDEX.md + docs/mission.md"`. No fire has yet built a general,
reusable, non-hardcoded checker for RETRACTION-INDEX.md completeness itself
(the R-S07 precedent for the *other* index). This audit builds and runs
that checker.

Method: general, non-hardcoded. Enumerate every currently-signed
evidence/audit/*/*.dsse.json receipt. Decode its payload. Extract its
`verdict` field (any receipt lacking one is reported, not silently
skipped). Treat a verdict as a refutation iff its string value contains
"REFUT" case-insensitively (catches H0_REFUTED, REFUTED, CLAIM_REFUTED,
etc. -- not hardcoded to one exact spelling). For every refuting receipt,
check whether its own repo-relative path appears as a literal substring
anywhere in RETRACTION-INDEX.md's raw text (the same identity convention
RETRACTION-INDEX.md's own existing rows already use -- each row cites the
refuting receipt by exactly this path). A refuting receipt whose path is
absent from RETRACTION-INDEX.md is an "unindexed_refutation": a retraction
the append-only ledger never recorded.
"""
import base64, glob, hashlib, json, os, re, sys

REPO_ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MODULE_ROOT = os.path.join(REPO_ROOT, "amphora-public-corrosion-benchmark")
SEED_PATH = "/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed"
AUDIT_ID = "retraction-index-completeness-v1"
RETRACTION_INDEX_REL = "evidence/phase0/kpis/RETRACTION-INDEX.md"
MISSION_REL = "docs/mission.md"

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def try_load_signed(path):
    try:
        d = json.load(open(path))
    except Exception:
        return None
    sig = None
    if isinstance(d, dict):
        if isinstance(d.get("signature"), dict) and "payload" in d["signature"]:
            sig = d["signature"]
        elif "payload" in d and "signatures" in d:
            sig = d
    if sig is None:
        return None
    try:
        payload = json.loads(base64.b64decode(sig["payload"]))
    except Exception:
        return None
    return payload


def enumerate_audit_receipts(module_root, exclude_audit_id):
    paths = sorted(glob.glob(os.path.join(module_root, "evidence/audit/*/*.dsse.json")))
    paths = [p for p in paths if "/superseded/" not in p and exclude_audit_id not in p]
    out = []
    for p in paths:
        rel = os.path.relpath(p, module_root).replace(os.sep, "/")
        payload = try_load_signed(p)
        entry = {
            "path": rel,
            "sha256": sha256_file(p),
            "verdict": (payload or {}).get("verdict"),
            "audit_id": (payload or {}).get("audit_id") or os.path.basename(os.path.dirname(p)),
            "load_ok": payload is not None,
        }
        out.append(entry)
    return out


def is_refutation(verdict):
    return isinstance(verdict, str) and "REFUT" in verdict.upper()


def build():
    os.chdir(MODULE_ROOT)
    receipts = enumerate_audit_receipts(MODULE_ROOT, AUDIT_ID)

    retraction_index_path = os.path.join(MODULE_ROOT, RETRACTION_INDEX_REL)
    retraction_index_text = open(retraction_index_path, "r").read()
    retraction_index_sha256 = sha256_file(retraction_index_path)

    mission_path = os.path.join(MODULE_ROOT, MISSION_REL)
    mission_text = open(mission_path, "r").read()
    mission_sha256 = sha256_file(mission_path)

    refuting = [r for r in receipts if is_refutation(r["verdict"])]
    non_refuting = [r for r in receipts if not is_refutation(r["verdict"])]

    unindexed = []
    indexed = []
    for r in refuting:
        in_retraction_index = r["path"] in retraction_index_text
        in_mission = r["path"] in mission_text
        rec = {
            "path": r["path"],
            "sha256": r["sha256"],
            "audit_id": r["audit_id"],
            "verdict": r["verdict"],
            "cited_in_retraction_index_md": in_retraction_index,
            "cited_in_mission_md": in_mission,
        }
        if in_retraction_index:
            indexed.append(rec)
        else:
            unindexed.append(rec)

    verdict = "H0_REFUTED" if unindexed else "H0_SURVIVED"

    unindexed_summary = "; ".join(
        f"{u['audit_id']} ({u['path']}, verdict={u['verdict']}, "
        f"also_missing_from_mission_md={not u['cited_in_mission_md']})"
        for u in unindexed
    )

    payload_out = {
        "$schema": "amphora.module-audit-receipt.v1",
        "schema": "amphora.public-corrosion-benchmark.retraction-index-completeness.v1",
        "audit_id": AUDIT_ID,
        "module_id": "amphora-public-corrosion-benchmark",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "REAL_ARITHMETIC",
        "axis": "governance",
        "phase": "PRE_PHASE_0",
        "campaign_item_id": "",
        "promotes_authority": False,
        "modifies_manifest": False,
        "modifies_signed_phase0_kpi": False,
        "scientific_success_asserted": False,
        "human_review_performed": False,
        "purpose": (
            "Build-time-style completeness gate for RETRACTION-INDEX.md, the module's "
            "own supersede-never-rewrite retraction record, analogous to R-S07's "
            "check_index_completeness.py for the audit_verdicts_index consolidated-KPI "
            "blob -- but that checker never reads RETRACTION-INDEX.md, so this surface "
            "has never had a dedicated, reusable, mechanical completeness check. "
            "Directly answers the `awaiting` note logged by "
            "evidence/audit/nist-baseline-still-valid-claim-currency-v1 (2026-08-18), "
            "which asked for exactly this update but as a REPAIR-mode action; this "
            "ROTATION-mode fire instead builds and runs the general checker so the gap "
            "is quantified precisely and reproducibly, not just spot-observed."
        ),
        "hypothesis_H0": (
            "Every currently-signed evidence/audit/*/*.dsse.json receipt in "
            "amphora-public-corrosion-benchmark whose own `verdict` field contains "
            "REFUT (case-insensitive) is cited by repo-relative path somewhere in "
            "evidence/phase0/kpis/RETRACTION-INDEX.md."
        ),
        "verdict": verdict,
        "headline": (
            f"Scanned {len(receipts)} currently-signed evidence/audit/ receipts "
            f"({len(refuting)} carry a REFUT* verdict, {len(non_refuting)} do not). "
            + (
                f"{len(unindexed)} of {len(refuting)} refuting receipts are NOT cited "
                f"by path anywhere in RETRACTION-INDEX.md ({retraction_index_sha256[:16]}...): "
                f"{unindexed_summary}. RETRACTION-INDEX.md's own append-only retraction "
                f"record is itself stale -- a fourth instance of this module's recurring "
                f"index-staleness failure mode, now confirmed on the retraction ledger "
                f"itself rather than the consolidated-KPI audit index."
                if unindexed else
                f"All {len(refuting)} refuting receipts are cited in RETRACTION-INDEX.md; "
                f"H0 SURVIVES this pass."
            )
        ),
        "methodology": {
            "scope": "every evidence/audit/*/*.dsse.json signed receipt currently on disk (excl. this audit's own output dir and evidence/superseded/)",
            "refutation_detection": (
                "a receipt's decoded payload `verdict` field is treated as a refutation "
                "iff the substring REFUT appears in its uppercased string value -- not "
                "hardcoded to the single literal H0_REFUTED, so it would also catch a "
                "future receipt spelling it CLAIM_REFUTED or REFUTED."
            ),
            "citation_detection": (
                "a refuting receipt counts as indexed iff its own repo-relative path "
                "(e.g. evidence/audit/<dir>/<file>.dsse.json) appears as a literal "
                "substring in RETRACTION-INDEX.md's raw text -- the identity convention "
                "RETRACTION-INDEX.md's own 4 existing rows already use for their "
                "'refuted-by receipt path' column."
            ),
            "determinism": "glob.glob() results sorted; no randomness; pure function of on-disk bytes.",
        },
        "totals": {
            "n_receipts_scanned": len(receipts),
            "n_refuting_receipts": len(refuting),
            "n_indexed": len(indexed),
            "n_unindexed": len(unindexed),
        },
        "retraction_index_md": {
            "path": RETRACTION_INDEX_REL,
            "sha256": retraction_index_sha256,
        },
        "mission_md": {
            "path": MISSION_REL,
            "sha256": mission_sha256,
        },
        "per_receipt": [
            {"path": r["path"], "sha256": r["sha256"], "audit_id": r["audit_id"],
             "verdict": r["verdict"], "is_refutation": is_refutation(r["verdict"])}
            for r in receipts
        ],
        "unindexed_refutations": unindexed,
        "indexed_refutations": indexed,
        "does_not_close": [
            "This receipt performs no new coating-physics test and fits no model; it "
            "is a structural completeness audit of the repo's own governance artifacts.",
            "It does not modify, supersede, or delete RETRACTION-INDEX.md, mission.md, "
            "or any receipt (ROTATION-mode fire; supersession/repair is an R-prefixed "
            "campaign action). It only enumerates and reports.",
            "Citation detection is a literal path-substring match, matching this "
            "module's own existing RETRACTION-INDEX.md row convention; a hypothetical "
            "future row that referenced a refuting receipt by sha256 or audit_id alone "
            "instead of path would not be recognized as a citation by this pass.",
            "No manifest, no signed Phase-0 KPI, and no cross-module file was touched.",
        ],
        "awaiting": [
            "A repair fire (R-prefixed campaign item) to append the missing rows to "
            "RETRACTION-INDEX.md (one per unindexed_refutations entry) and correct the "
            "'remain valid' seawater_uncoated_substrate_baselines prose in docs/mission.md "
            "(NIST CORR-DATA marine steel baseline section) to reflect the two receipts "
            "that already found that descriptive block unit-inconsistent.",
        ],
    }
    return payload_out


def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()


def dsse_sign(payload_bytes, payload_type, seed):
    sk = Ed25519PrivateKey.from_private_bytes(seed)
    pub = sk.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    keyid = "phase0-evaluator-" + hashlib.sha256(pub).hexdigest()
    pt = payload_type.encode()
    pae = (b"DSSEv1 " + str(len(pt)).encode() + b" " + pt + b" "
           + str(len(payload_bytes)).encode() + b" " + payload_bytes)
    sig = sk.sign(pae)
    env = {"payload": base64.b64encode(payload_bytes).decode(),
           "payloadType": payload_type,
           "signatures": [{"keyid": keyid, "sig": base64.b64encode(sig).decode()}]}
    return env, keyid, pub.hex()


if __name__ == "__main__":
    d1 = build(); b1 = canon(d1); h1 = sha256_bytes(b1)
    d2 = build(); b2 = canon(d2); h2 = sha256_bytes(b2)
    assert b1 == b2, "two-replay byte MISMATCH"
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
    print("n_receipts_scanned:", d1["totals"]["n_receipts_scanned"],
          "| n_refuting:", d1["totals"]["n_refuting_receipts"],
          "| n_unindexed:", d1["totals"]["n_unindexed"],
          "| verdict:", d1["verdict"])

    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        outdir = os.path.join(MODULE_ROOT, "evidence/audit", AUDIT_ID)
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "diagnostic.canonical.json"), "wb") as f:
            f.write(b1)
        with open(os.path.join(outdir, "diagnostic.runB.json"), "wb") as f:
            f.write(b2)
        seed = open(SEED_PATH, "rb").read()
        pt = "application/vnd.amphora.public-corrosion-benchmark-retraction-index-completeness.v1+json"
        env, keyid, pubhex = dsse_sign(b1, pt, seed)
        receipt = {"signature": env, "evaluator_key_id": keyid, "reviewer_public_key_hex": pubhex}
        outpath = os.path.join(outdir, "retraction-index-completeness-receipt.v1.dsse.json")
        with open(outpath, "w") as f:
            f.write(json.dumps(receipt, indent=2, sort_keys=True))
        print("emitted diagnostic + signed receipt:", outpath)

        raw_sig = base64.b64decode(env["signatures"][0]["sig"])
        payload_bytes = base64.b64decode(env["payload"])
        pt_b = env["payloadType"].encode()
        pae = (b"DSSEv1 " + str(len(pt_b)).encode() + b" " + pt_b + b" "
               + str(len(payload_bytes)).encode() + b" " + payload_bytes)
        pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubhex))
        pubkey.verify(raw_sig, pae)
        print("SELF_VERIFY: PASS keyid", keyid)
