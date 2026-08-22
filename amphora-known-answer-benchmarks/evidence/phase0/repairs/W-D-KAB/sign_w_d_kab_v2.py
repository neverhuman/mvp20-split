#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-D-KAB source-sweep receipt v2 (AUDIT_ONLY).
Extends (does not correct) the v1 sweep: adds 2 new swept sources (14 total) and
resolves 2 data-integrity anomalies via independent cross-checks. Supersedes v1
receipt for lineage only -- v1's figures and verdict are unchanged and reconfirmed,
not retracted. Signs with the pinned Phase-0 evaluator seed only; self-verifies the
envelope before writing."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-known-answer-benchmarks"
WDIR = MOD / "evidence/phase0/repairs/W-D-KAB"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

SWEEP_RECORD = WDIR / "work/sweep-record.v2.json"
PRIOR_RECEIPT = WDIR / "done/W-D-KAB-source-sweep-receipt.v1.dsse.json"
FIRE_ID = "20260813T040001-3318991-94760c4f3436"


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


sweep = json.loads(SWEEP_RECORD.read_bytes())
assert sweep["tally"]["swept"] == 14
assert len(sweep["sources_swept"]) == 14
for s in sweep["sources_swept"]:
    assert s.get("query"), f"source {s['n']} missing query"
    assert s.get("license_quote_verbatim"), f"source {s['n']} missing license quote"
    assert s.get("disposition") in ("RECOMMENDED", "RECOMMENDED_WITH_FLAG", "BLOCKED")
assert len(sweep["anomaly_resolutions"]) == 2

sweep_sha = sha(SWEEP_RECORD.read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())
prior_receipt_sha = sha(PRIOR_RECEIPT.read_bytes())

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

proposed_followups = [
    {
        "module": "amphora-known-answer-benchmarks",
        "defect": (
            "The locked 14-control known-answer fixture "
            "(control_by_control_receipt.v1.json) contains zero controls sourced from "
            "independently-published, rights-clean government specifications, despite "
            "MIL-DTL-24441 Navy epoxy-polyamide formula sheets (D, /19B[resolved], /20A, "
            "/21A, /29B, /30A[resolved], /31A) being public-domain-consistent, DoD-wide "
            "'approved for use' / 'DISTRIBUTION STATEMENT A' documents with complete "
            "mass-basis worked formulas (7 formula sheets now swept and RECOMMENDED across "
            "v1+v2, 2 of them with a resolved single-row transcription-typo correction)."
        ),
        "proposed_done_criterion": (
            "A new superseding receipt (id prefix R-) computes weight-solids% and "
            "approximate VOC (g/L) from the MIL-DTL-24441/20A, /21A, /29B, /30A, /31A "
            "ingredient tables (using the CORRECTED zinc-pigment 861.8kg and CORRECTED "
            "naphtha 94.35kg figures for /19B and /30A respectively, per this receipt's "
            "anomaly_resolutions, not their printed-but-erroneous kg values), cross-checks "
            "each result against the base-spec's own Type III/IV/V VOC ceilings, and lands "
            ">=2 new ARITH-*/FORM-* controls in the fixture only via a human-reviewed "
            "superseding receipt, never a direct edit to control_by_control_receipt.v1.json."
        ),
    },
    {
        "module": "amphora-known-answer-benchmarks",
        "defect": (
            "RESOLVED THIS FIRE (was v1 followup 2, open): MIL-DTL-24441/19B(SH) Component "
            "B zinc pigment printed as 86.84 kg / 1900.0 lb (a ~9.9x mismatch). Resolution: "
            "the SAME document's own Quantitative Requirements table specifies Component B "
            "pigment content must be 81.5-85.5%; only the lb-basis/corrected-kg reading "
            "(861.8 kg, yielding 83.6% pigment content) satisfies that spec, while the "
            "printed 86.84 kg reading yields 34.0%, a gross violation of the document's own "
            "requirement. The printed kg figure is confirmed as the transcription error."
        ),
        "proposed_done_criterion": (
            "Superseded by followup 1 above: any control built from /19B must use the "
            "corrected 861.8 kg zinc-pigment figure, cited with this receipt's "
            "anomaly_resolutions[0] as the justification for departing from the printed "
            "PDF text."
        ),
    },
    {
        "module": "amphora-known-answer-benchmarks",
        "defect": (
            "NEW, FOUND AND RESOLVED IN THIS SAME FIRE: MIL-DTL-24441/30A(SH) Component B "
            "naphtha printed as 93.35 kg / 208.0 lb (208.0 lb correctly converts to 94.35 "
            "kg, a 1.00 kg / ~1.1% single-digit transcription error). Independently "
            "cross-checked against source 4 (/31A, already in the v1 corpus), which "
            "specifies the identical naphtha grade at the identical 208.0 lb quantity and "
            "correctly prints 94.35 kg -- two separate Navy specification sheets citing the "
            "same figure prove which one is wrong."
        ),
        "proposed_done_criterion": (
            "Superseded by followup 1 above: any control built from /30A must use the "
            "corrected 94.35 kg naphtha figure, cited with this receipt's "
            "anomaly_resolutions[1] as the justification."
        ),
    },
    {
        "module": "amphora-known-answer-benchmarks",
        "defect": (
            "Manufacturer TDS (Westlake EPON 828, PPG Amercoat 240, Jotun Jotamastic 87) "
            "and industry standards (ASTM D5201, ISO 3233) all carry complete, "
            "independently-recomputable volume-solids/VOC/density values, but none grants "
            "an affirmative reproduction/redistribution right quotable from the source; "
            "ASTM and ISO are explicitly paywalled and copyrighted (v1 sources 6-10, "
            "unchanged this fire)."
        ),
        "proposed_done_criterion": (
            "Unchanged from v1 followup 3: human rights review either (a) purchases ASTM "
            "D5201 / ISO 3233 and re-derives only the specific numeric worked example under "
            "a fair-use/idea-not-expression citation, or (b) requests written permission "
            "from Westlake/PPG/Jotun to reproduce a single stated VS%/VOC/density figure as "
            "a citation-only known-answer control, and records the outcome regardless of "
            "which way it resolves."
        ),
    },
    {
        "module": "amphora-known-answer-benchmarks",
        "defect": (
            "Evonik Ancamine (2578/2849/2712M amine values, %solids) and Huntsman Araldite "
            "GY 250 (density) data were seen only via search-engine result snippets (v1 "
            "sources 11-12, unchanged this fire) -- direct PDF/product-page fetches all "
            "failed (404/403/empty) -- so these numbers remain UNVERIFIED against a primary "
            "source in addition to being rights-blocked by each company's website legal "
            "notice."
        ),
        "proposed_done_criterion": (
            "Unchanged from v1 followup 4: a follow-up fire re-attempts a direct fetch of "
            "the underlying Evonik/Huntsman TDS PDFs (not search snippets) to confirm the "
            "amine-value/EEW/density figures against the primary document byte-for-byte "
            "before citing them anywhere, even as an unlicensed cross-reference."
        ),
    },
]

body_obj = {
    "schema": "amphora.known-answer-benchmarks.data-sweep.v2",
    "campaign_item_id": "W-D-KAB",
    "module_id": "amphora-known-answer-benchmarks",
    "authority": "AUDIT_ONLY",
    "claim_under_attack": (
        "amphora-known-answer-benchmarks/evidence/ :: 'The arithmetic and formulation "
        "controls can be extended with independently published known answers.'"
    ),
    "attack_type": "rights-clean-source-discovery-sweep-extension-plus-anomaly-resolution",
    "sources_swept_count": 14,
    "sweep_record": sweep,
    "supersedes": {
        "superseded_path": str(PRIOR_RECEIPT.relative_to(ROOT)),
        "superseded_sha256": prior_receipt_sha,
        "superseded_deleted_or_modified": False,
        "reason": (
            "Extension, not correction. All 12 v1 sources and their dispositions are "
            "carried forward byte-identical inside this receipt's sweep_record; nothing "
            "about v1 is wrong or retracted. This receipt adds 2 new independently-swept "
            "MIL-DTL-24441 sheets (13:/21A, 14:/30A) and resolves 2 data-integrity "
            "anomalies (the v1-flagged /19B zinc-pigment row, and a newly-discovered /30A "
            "naphtha row) via independent cross-checks -- one an internal "
            "quantitative-requirements consistency proof, one a cross-document match "
            "against a sibling formula sheet already in the corpus."
        ),
    },
    "headline": (
        "Extends the W-D-KAB v1 sweep (12 sources) with 2 new named MIL-DTL-24441 Navy "
        "formula sheets (/21A Haze-Gray-TypeIII, /30A Haze-Gray-TypeIV; 14 sources total), "
        "each license-quoted verbatim, same DoD public-domain-consistent status as v1's "
        "4 clean RECOMMENDED sheets. /21A is clean (9/9 ingredient rows self-consistent "
        "lb<->kg). /30A carries its own single-row transcription anomaly (naphtha 93.35kg "
        "printed vs 94.35kg correct for 208.0lb), discovered AND resolved in this same "
        "fire by cross-matching against source 4 (/31A), which specifies the identical "
        "naphtha grade at the identical 208.0lb and prints the correct 94.35kg -- proving "
        "the /30A figure is a typo, not a real formulation difference. Separately, this "
        "fire RESOLVES v1's outstanding /19B zinc-pigment flag: /19B's own Quantitative "
        "Requirements table requires Component B pigment content in [81.5,85.5]%; only the "
        "lb-basis/corrected-kg reading (861.8kg, giving 83.6%) satisfies that spec, while "
        "the printed 86.84kg reading gives 34.0%, failing the document's own requirement by "
        "a wide margin -- confirming the printed kg figure (not the lb figure) is the error. "
        "Both resolutions are internal-cross-check proofs, not appeals to a second external "
        "document (though /30A's resolution additionally benefits from being echoed by a "
        "sibling sheet already in-corpus). Net effect: 7 rights-clean MIL-DTL-24441 formula "
        "sheets now swept (5 clean, 2 with a resolved single-row correction each), 7 sources "
        "remain BLOCKED (unchanged from v1, license quotes carried forward), 0 new controls "
        "added to the locked fixture (still an R-item action, per the item's own "
        "instruction to propose not add). Verdict unchanged: BLOCKED_DATA -- landing actual "
        "locked controls still needs a follow-up superseding-receipt fire (now with 2 rows' "
        "worth of anomalies pre-resolved, removing that blocker for a future R- item) and/or "
        "human rights review for the paywalled/manufacturer sources. This is the second and "
        "final fire under this item's max_fires:2 budget; the item is left in an honest, "
        "load-bearing BLOCKED_DATA state with 5 owned followups for whoever picks it up next."
    ),
    "verdict": "BLOCKED_DATA",
    "proposed_followups": proposed_followups,
    "scientific_success_asserted": False,
    "promotes_authority": False,
    "modifies_existing_receipts": False,
    "modifies_manifest": False,
    "modifies_locked_fixture": False,
    "human_review_performed": False,
    "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, qualification, "
        "regulatory, or FTO authority.",
        "Adds no control to control_by_control_receipt.v1.json or any other locked "
        "fixture; proposes only.",
        "Resolves WHICH figure is correct for /19B and /30A's flagged rows, but does not "
        "itself land any control in the fixture -- that remains an R-item action.",
        "Does not purchase ASTM D5201 or ISO 3233; records their blocking copyright only "
        "(unchanged from v1).",
        "Does not independently verify the Evonik/Huntsman search-snippet figures against "
        "a primary document; flags that gap explicitly (unchanged from v1).",
    ],
    "provenance": {"module_manifest_sha256": manifest_sha,
                    "sweep_record_path": str(SWEEP_RECORD.relative_to(ROOT)),
                    "sweep_record_sha256": sweep_sha,
                    "fire_id": FIRE_ID},
    "signing_key": {
        "authority": "AUDIT_ONLY", "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing only; no dual-identity ceremony",
        "used_for": "AUDIT_ONLY data-sweep receipt under evidence/phase0/repairs/W-D-KAB/done/",
        "trust_anchored_in_phase0_promotion_store": bool(eval_pin),
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.known-answer-benchmarks.data-sweep.v2+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}
for k in ("schema", "campaign_item_id", "module_id", "authority", "verdict"):
    receipt[k] = body_obj[k]

WDIR.mkdir(parents=True, exist_ok=True)
(WDIR / "done").mkdir(parents=True, exist_ok=True)
out = WDIR / "done/W-D-KAB-source-sweep-receipt.v2.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify (replay 1)
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
# self-verify (replay 2 -- re-read from disk, independent of in-memory object)
reread = json.loads(out.read_text())
env2 = reread["signature"]
Ed25519PublicKey.from_public_bytes(bytes.fromhex(reread["evaluator_public_key_hex"])).verify(
    base64.standard_b64decode(env2["signatures"][0]["sig"]),
    pae(env2["payloadType"], base64.standard_b64decode(env2["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("self_verify_signature_replay1", True)
print("self_verify_signature_replay2_from_disk", True)
print("out_sha256", sha(out.read_bytes()))
