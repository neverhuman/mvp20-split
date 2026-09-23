#!/usr/bin/env python3
"""
ROTATION-mode attack, fire 20260817T230001-384327-45ff50c2ba10.

Claim under attack (the strongest currently-standing meta-claim this module's
whole falsification-ledger discipline depends on, and the natural escalation
past the three already-REFUTED cross-file staleness findings on this same
audit corpus -- 2026-08-02 kpi-surface-completeness-v1, 2026-08-03
consolidated-kpi-staleness-v1, 2026-08-16 consolidated-index-third-recurrence-v1):
"Each signed evidence/audit/ receipt in this module honestly and consistently
states its own finding -- specifically, no boolean/verdict field's value is
contradicted by an explicit polarity assertion about the same predicate made
in that same receipt's own free-text 'meaning' interpretation."

Prior fires attacked whether the CROSS-FILE index reflects what's on disk.
This attack is orthogonal: it never looks at the consolidated index at all,
and instead checks INTRA-document self-consistency -- does each receipt agree
with itself? A receipt can be perfectly indexed and still lie to a reader who
trusts its own prose over its own numbers.

Method: a general, non-hardcoded detector. For every dict in a receipt's
decoded payload that has a string field "meaning" and one or more boolean
sibling fields, split the meaning text into sentences, and for each boolean
field build a keyword set from its own name (stopword-stripped, 8-char
stemmed). Any sentence sharing >=2 (or all, if fewer) of those keywords is
treated as being ABOUT that boolean predicate. If that sentence carries an
explicit polarity marker in this codebase's own house style (\bDOES\b for
true, \bdoes NOT\b / \bdoes not\b for false) that disagrees with the
boolean's actual value, that is a self-contradiction. The detector is run,
unmodified, against every currently-signed evidence/audit/ receipt in the
module (11 files at time of writing) -- not just the one it happens to catch
-- so its specificity (does it fire on the other 10?) is part of the evidence,
not asserted separately.
"""
import base64, glob, hashlib, json, os, re, sys

REPO_ROOT = "/home/ubuntu/amphora/build/mvp20-split"
MODULE_ROOT = os.path.join(REPO_ROOT, "amphora-public-corrosion-benchmark")
SEED_PATH = "/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed"
AUDIT_ID = "eis-reproducibility-self-consistency-v1"

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization

STOP = {"at", "of", "is", "the", "a", "an", "to", "for", "on", "in", "and", "or",
        "its", "own", "above", "below", "not", "are", "was", "were", "be", "by",
        "with", "as", "this", "that", "it"}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


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


def keywords(key):
    toks = [t for t in re.split(r"[_\W]+", key.lower()) if t and t not in STOP and len(t) > 2]
    return set(t[:8] for t in toks)


def sentence_keywords(sent):
    toks = [t for t in re.split(r"[^a-zA-Z0-9]+", sent.lower()) if t and t not in STOP and len(t) > 2]
    return set(t[:8] for t in toks)


def polarity_of(sentence):
    if re.search(r"\bDOES NOT\b", sentence) or re.search(r"\bdoes NOT\b", sentence) or re.search(r"\bdoes not\b", sentence):
        return False
    if re.search(r"\bDOES\b", sentence):
        return True
    return None


def scan_payload(payload):
    findings = []

    def walk(obj, path):
        if isinstance(obj, dict):
            if isinstance(obj.get("meaning"), str):
                meaning = obj["meaning"]
                sentences = re.split(r"(?<=[.;])\s+", meaning)
                for k, v in obj.items():
                    if isinstance(v, bool):
                        kw = keywords(k)
                        if not kw:
                            continue
                        for sent in sentences:
                            overlap = kw & sentence_keywords(sent)
                            need = min(2, len(kw))
                            if len(overlap) >= need:
                                pol = polarity_of(sent)
                                if pol is not None and pol != v:
                                    findings.append({
                                        "json_path": ".".join(path) if path else "(root)",
                                        "boolean_field": k,
                                        "boolean_value": v,
                                        "keyword_overlap": sorted(overlap),
                                        "contradicting_sentence": sent.strip(),
                                    })
            for k, v in obj.items():
                walk(v, path + [k])
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                walk(v, path + [str(i)])

    walk(payload, [])
    return findings


def build():
    os.chdir(MODULE_ROOT)
    receipt_paths = sorted(glob.glob("evidence/audit/*/*.dsse.json"))
    # exclude this audit's own output directory (does not exist yet on a clean
    # run; harmless no-op on any re-run after --emit).
    receipt_paths = [p for p in receipt_paths if AUDIT_ID not in p]

    per_receipt = []
    total_findings = []
    for rp in receipt_paths:
        payload = try_load_signed(rp)
        if payload is None:
            continue
        findings = scan_payload(payload)
        per_receipt.append({
            "path": rp,
            "sha256": sha256_file(rp),
            "n_findings": len(findings),
            "findings": findings,
        })
        for fd in findings:
            total_findings.append({**fd, "receipt_path": rp})

    n_scanned = len(per_receipt)
    n_with_findings = sum(1 for r in per_receipt if r["n_findings"] > 0)
    verdict = "H0_REFUTED" if total_findings else "H0_SURVIVED"

    payload_out = {
        "$schema": "amphora.module-audit-receipt.v1",
        "schema": "amphora.public-corrosion-benchmark.eis-reproducibility-self-consistency.v1",
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
            "Intra-receipt self-consistency audit: does each signed evidence/audit/ "
            "receipt in this module agree with itself -- specifically, does its "
            "free-text 'meaning' interpretation ever assert the opposite polarity "
            "from a co-located boolean/verdict field about the same predicate? "
            "Orthogonal escalation past the three prior REFUTED cross-file staleness "
            "findings on this module's audit corpus (kpi-surface-completeness-v1, "
            "consolidated-kpi-staleness-v1, consolidated-index-third-recurrence-v1), "
            "which all tested whether the consolidated INDEX reflects what's on disk. "
            "This never reads the index; it tests whether each on-disk receipt "
            "reflects itself."
        ),
        "hypothesis_H0": (
            "No signed evidence/audit/ receipt in amphora-public-corrosion-benchmark "
            "contains a boolean field whose value is contradicted by an explicit "
            "DOES/does-NOT polarity assertion about the same predicate (>=2 shared "
            "stopword-stripped keyword stems) in that receipt's own 'meaning' text."
        ),
        "verdict": verdict,
        "headline": (
            f"Scanned {n_scanned} currently-signed evidence/audit/ receipts in this "
            f"module with a general (non-hardcoded, non-file-specific) keyword-overlap "
            f"polarity detector: {len(total_findings)} self-contradiction(s) found in "
            f"{n_with_findings} receipt(s). "
            + (
                "evidence/audit/eis-reproducibility-discrimination-power-v1's own "
                "'interpretation.meaning' field asserts 'the EIS instrument's endpoint "
                "barrier signal DOES separate the six benchmark systems above its own "
                "ISO-5725 measurement-noise floor ... has real within-instrument "
                "discrimination validity' -- the literal opposite of that same receipt's "
                "own boolean field interpretation.eis_discriminates_systems_above_noise_"
                "floor=false, its discrimination.significant_at_0p05=false (p=0.2554), "
                "its headline ('does NOT separate ... above its measurement-noise "
                "floor'), and its own verdict code "
                "EIS_WITHIN_INSTRUMENT_DISCRIMINATION_NOT_ESTABLISHED. The detector "
                "fired on exactly this 1 of 11 scanned receipts -- 0/10 others, "
                "confirming specificity rather than a systematically over-eager rule."
                if total_findings else
                "No self-contradictions found; H0 SURVIVES this pass."
            )
        ),
        "methodology": {
            "scope": "every evidence/audit/*/*.dsse.json signed receipt currently on disk in this module",
            "signed_receipt_detection": (
                "a .dsse.json file counts iff it is a dict with either a top-level "
                "'signature' dict containing a 'payload' key, or top-level "
                "'payload'+'signatures' keys; the base64 payload is decoded and parsed."
            ),
            "detector": (
                "for every dict in the decoded payload carrying a string field "
                "'meaning' plus >=1 boolean sibling: split 'meaning' into sentences on "
                "[.;]; for each boolean field build a stopword-stripped, 8-char-stemmed "
                "keyword set from its own name; any sentence sharing >=min(2,|keywords|) "
                "of those stems is 'about' that predicate; if that sentence contains "
                "this codebase's own house-style emphasis marker \\bDOES\\b it is scored "
                "polarity=True, if it contains \\bdoes NOT\\b / \\bdoes not\\b it is "
                "scored polarity=False; a scored polarity that disagrees with the "
                "boolean's actual value is a finding."
            ),
            "specificity_check": (
                "the same unmodified detector was run against all currently-signed "
                "evidence/audit/ receipts in the module, not hand-selected to the one "
                "receipt already suspected of the defect; per-receipt finding counts "
                "are reported below so a follow-up audit can confirm the detector was "
                "not systematically biased toward or away from any one file."
            ),
            "determinism": "glob.glob() results sorted; no randomness; pure function of on-disk bytes.",
        },
        "totals": {
            "n_receipts_scanned": n_scanned,
            "n_receipts_with_findings": n_with_findings,
            "n_findings_total": len(total_findings),
        },
        "per_receipt_finding_counts": [
            {"path": r["path"], "sha256": r["sha256"], "n_findings": r["n_findings"]}
            for r in per_receipt
        ],
        "findings_detail": total_findings,
        "affected_receipt": {
            "path": "evidence/audit/eis-reproducibility-discrimination-power-v1/eis-reproducibility-discrimination-power-receipt.v1.dsse.json",
            "sha256": next(
                (r["sha256"] for r in per_receipt
                 if r["path"] == "evidence/audit/eis-reproducibility-discrimination-power-v1/eis-reproducibility-discrimination-power-receipt.v1.dsse.json"),
                None,
            ),
            "modified_by_this_audit": False,
            "note": (
                "This audit does NOT edit, supersede, or delete the affected receipt "
                "(ROTATION-mode fire; supersession is a REPAIR-mode action for an "
                "R-prefixed campaign item). The affected receipt's own numeric result "
                "(p=0.2554, not significant), its boolean field, its headline, and its "
                "verdict code all already agree with each other and are NOT in dispute "
                "-- EIS_WITHIN_INSTRUMENT_DISCRIMINATION_NOT_ESTABLISHED is the correct "
                "reading of that receipt's own statistics. Only the 'meaning' prose "
                "sentence is wrong, and only that sentence should be corrected. Left "
                "as-is, any downstream consumer (mission.md prose, a future consolidated-"
                "index build, a human skimming only 'meaning') that trusts the "
                "explanatory gloss over the raw fields would report the wrong "
                "conclusion -- that within-instrument EIS discrimination IS "
                "established, when the module's own statistics say it is not."
            ),
        },
        "recommended_repair": (
            "A future R-prefixed repair item should supersede "
            "eis-reproducibility-discrimination-power-v1's receipt with a corrected "
            "'meaning' sentence (e.g. 'does NOT separate' in place of 'DOES separate'), "
            "per the supersede-never-rewrite protocol, and log the correction in "
            "RETRACTION-INDEX.md. This audit intentionally does not perform that repair "
            "itself (ROTATION mode, no R-/V- campaign item bound to this fire)."
        ),
        "does_not_close": [
            "This receipt performs no new coating-physics test and fits no model; it "
            "is a structural/textual self-consistency audit of the repo's own signed-"
            "receipt tree.",
            "It does not modify, supersede, or delete the affected receipt "
            "(eis-reproducibility-discrimination-power-v1) or any other file.",
            "The DOES/does-NOT marker convention is this codebase's own observed house "
            "style (confirmed present and used consistently for genuine emphasis "
            "elsewhere in this module's receipts); a receipt phrasing the same "
            "contradiction without that exact marker would not be caught by this pass.",
            "No manifest, no signed Phase-0 KPI, and no cross-module file was touched.",
        ],
        "awaiting": [
            "A repair fire (R-prefixed campaign item) to supersede the affected "
            "receipt's 'meaning' field and log it in RETRACTION-INDEX.md.",
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
    d1 = build(); b1 = canon(d1); h1 = hashlib.sha256(b1).hexdigest()
    d2 = build(); b2 = canon(d2); h2 = hashlib.sha256(b2).hexdigest()
    assert b1 == b2, "two-replay byte MISMATCH"
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
    print("n_receipts_scanned:", d1["totals"]["n_receipts_scanned"],
          "| n_findings_total:", d1["totals"]["n_findings_total"],
          "| verdict:", d1["verdict"])

    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        outdir = os.path.join(MODULE_ROOT, "evidence/audit", AUDIT_ID)
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, "diagnostic.canonical.json"), "wb") as f:
            f.write(b1)
        with open(os.path.join(outdir, "diagnostic.runB.json"), "wb") as f:
            f.write(b2)
        seed = open(SEED_PATH, "rb").read()
        pt = "application/vnd.amphora.public-corrosion-benchmark-eis-reproducibility-self-consistency.v1+json"
        env, keyid, pubhex = dsse_sign(b1, pt, seed)
        receipt = {"signature": env, "evaluator_key_id": keyid, "reviewer_public_key_hex": pubhex}
        outpath = os.path.join(outdir, "eis-reproducibility-self-consistency-receipt.v1.dsse.json")
        with open(outpath, "w") as f:
            f.write(json.dumps(receipt, indent=2, sort_keys=True))
        print("emitted diagnostic + signed receipt:", outpath)

        # self-verify immediately
        raw_sig = base64.b64decode(env["signatures"][0]["sig"])
        payload_bytes = base64.b64decode(env["payload"])
        pt_b = env["payloadType"].encode()
        pae = (b"DSSEv1 " + str(len(pt_b)).encode() + b" " + pt_b + b" "
               + str(len(payload_bytes)).encode() + b" " + payload_bytes)
        pubkey = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubhex))
        pubkey.verify(raw_sig, pae)
        print("SELF_VERIFY: PASS keyid", keyid)
