#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-D-KAB source-sweep receipt (AUDIT_ONLY).
Data-dimension campaign item: sweeps published sources for rights-clean known-answer
controls; proposes new controls without touching the locked fixture; signs with the
pinned Phase-0 evaluator seed only; self-verifies the envelope before writing."""
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

SWEEP_RECORD = WDIR / "work/sweep-record.v1.json"
FIRE_ID = "20260813T030002-2723015-0125b9e50f8a"


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
assert sweep["tally"]["swept"] == 12
assert len(sweep["sources_swept"]) == 12
for s in sweep["sources_swept"]:
    assert s.get("query"), f"source {s['n']} missing query"
    assert s.get("license_quote_verbatim"), f"source {s['n']} missing license quote"
    assert s.get("disposition") in ("RECOMMENDED", "RECOMMENDED_WITH_FLAG", "BLOCKED")

sweep_sha = sha(SWEEP_RECORD.read_bytes())
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

proposed_followups = [
    {
        "module": "amphora-known-answer-benchmarks",
        "defect": (
            "The locked 14-control known-answer fixture "
            "(control_by_control_receipt.v1.json) contains zero controls sourced from "
            "independently-published, rights-clean government specifications, despite "
            "MIL-DTL-24441 Navy epoxy-polyamide formula sheets (D, /19B, /20A, /29B, /31A) "
            "being public-domain-consistent, DoD-wide 'approved for use' / "
            "'DISTRIBUTION STATEMENT A' documents with complete mass-basis worked formulas "
            "(sources 1-5 of this sweep)."
        ),
        "proposed_done_criterion": (
            "A new superseding receipt (id prefix R-) computes weight-solids% and "
            "approximate VOC (g/L) from the MIL-DTL-24441/29B, /20A, /31A ingredient "
            "tables using each named ingredient's density/volatile fraction, cross-checks "
            "the result against the base-spec's own Type III/IV/V VOC ceilings "
            "(<340, <340, <250 g/L respectively), resolves the /19B zinc-pigment kg/lb "
            "inconsistency (see followup 2) against a second independent copy of the "
            "document first, and lands >=2 new ARITH-*/FORM-* controls in the fixture "
            "only via a human-reviewed superseding receipt, never a direct edit to "
            "control_by_control_receipt.v1.json."
        ),
    },
    {
        "module": "amphora-known-answer-benchmarks",
        "defect": (
            "MIL-DTL-24441/19B(SH) Component B lists zinc pigment as 86.84 kg / 1900.0 lb "
            "-- 1900 lb converts to 861.8 kg, a ~9.9x mismatch against the printed kg "
            "figure, while every other row in the same table (epoxy resin, naphtha, paint "
            "thinner) converts consistently to within normal rounding. Found in the "
            "primary everyspec.com-mirrored PDF text extraction this fire, not introduced "
            "by us."
        ),
        "proposed_done_criterion": (
            "A human or follow-up fire cross-references a second independent copy of "
            "MIL-DTL-24441/19B(SH) (e.g. the DLA ASSIST-hosted original at "
            "assist.dla.mil / quicksearch.dla.mil) to determine which figure (86.84 kg or "
            "~861.8 kg) is the transcription error, and records the resolution before any "
            "control derived from this formula sheet is locked."
        ),
    },
    {
        "module": "amphora-known-answer-benchmarks",
        "defect": (
            "Manufacturer TDS (Westlake EPON 828, PPG Amercoat 240, Jotun Jotamastic 87) "
            "and industry standards (ASTM D5201, ISO 3233) all carry complete, "
            "independently-recomputable volume-solids/VOC/density values, but none grants "
            "an affirmative reproduction/redistribution right quotable from the source; "
            "ASTM and ISO are explicitly paywalled and copyrighted (sources 6-10)."
        ),
        "proposed_done_criterion": (
            "Human rights review either (a) purchases ASTM D5201 / ISO 3233 and re-derives "
            "only the specific numeric worked example under a fair-use/idea-not-expression "
            "citation (title+date+section, not verbatim standard text) as a new control, or "
            "(b) requests written permission from Westlake/PPG/Jotun to reproduce a single "
            "stated VS%/VOC/density figure as a citation-only known-answer control, and "
            "records the outcome (grant or refusal) as a new disposition regardless of "
            "which way it resolves."
        ),
    },
    {
        "module": "amphora-known-answer-benchmarks",
        "defect": (
            "Evonik Ancamine (2578/2849/2712M amine values, %solids) and Huntsman Araldite "
            "GY 250 (density) data were seen only via search-engine result snippets this "
            "fire -- direct PDF/product-page fetches all failed (404/403/empty) -- so "
            "these numbers are UNVERIFIED against a primary source in addition to being "
            "rights-blocked by each company's website legal notice (sources 11-12)."
        ),
        "proposed_done_criterion": (
            "A follow-up fire re-attempts a direct fetch of the underlying Evonik/Huntsman "
            "TDS PDFs (not search snippets) to confirm the amine-value/EEW/density figures "
            "against the primary document byte-for-byte before citing them anywhere, even "
            "as an unlicensed cross-reference."
        ),
    },
]

body_obj = {
    "schema": "amphora.known-answer-benchmarks.data-sweep.v1",
    "campaign_item_id": "W-D-KAB",
    "module_id": "amphora-known-answer-benchmarks",
    "authority": "AUDIT_ONLY",
    "claim_under_attack": (
        "amphora-known-answer-benchmarks/evidence/ :: 'The arithmetic and formulation "
        "controls can be extended with independently published known answers.'"
    ),
    "attack_type": "rights-clean-source-discovery-sweep",
    "sources_swept_count": 12,
    "sweep_record": sweep,
    "headline": (
        "Swept 12 named published sources for candidate known-answer controls covering "
        "two-component epoxy-polyamide marine coatings. RECOMMENDED (rights-clean, "
        "public-domain-consistent): 4 US DoD/NAVSEA MIL-DTL-24441 formula sheets "
        "(D, /20A Formula150-TypeIII, /29B Formula150-TypeIV, /31A Formula152-TypeIV) "
        "carrying zero copyright notices and explicit 'approved for use by all "
        "Departments and Agencies of the Department of Defense' / 'DISTRIBUTION "
        "STATEMENT A: Approved for public release; distribution is unlimited' language, "
        "each with a complete mass-basis worked formula (component-by-component ingredient "
        "masses in kg and lb) independently recomputable into weight-solids% and "
        "approximate VOC (g/L), cross-checkable against the base spec's own VOC ceilings. "
        "RECOMMENDED_WITH_FLAG: a 5th sheet (/19B, zinc primer Formula 159) has the same "
        "rights-clean status but a printed zinc-pigment kg/lb figure fails self-consistency "
        "by ~9.9x against every other row in its own table -- filed as a data-integrity "
        "followup, not adopted. BLOCKED: the remaining 7 sources (Westlake EPON 828, PPG "
        "Amercoat 240, Jotun Jotamastic 87 manufacturer TDS; ASTM D5201 and ISO 3233 "
        "paywalled standards; Evonik Ancamine and Huntsman Araldite corporate sites) each "
        "carry either an explicit copyright/no-redistribution clause or no affirmative "
        "reproduction grant at all -- quoted verbatim in every case; none is adopted. "
        "This fire lands NO new control into the locked fixture (per the item's own "
        "instruction: propose, don't add without a superseding receipt) -- it proposes 4 "
        "concrete, owned followups (filed below) so a future R- item can convert the "
        "MIL-DTL-24441 finds into locked controls. Verdict: BLOCKED_DATA -- forward motion "
        "on actually landing new locked controls needs a follow-up superseding-receipt "
        "fire (for the RECOMMENDED sources) and/or human rights review (for the paywalled "
        "and manufacturer sources); this receipt is the honest, complete, itemized "
        "evidence position the item asks for."
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
        "Does not resolve the /19B zinc-pigment inconsistency; flags it for a human or "
        "follow-up fire.",
        "Does not purchase ASTM D5201 or ISO 3233; records their blocking copyright only.",
        "Does not independently verify the Evonik/Huntsman search-snippet figures against "
        "a primary document; flags that gap explicitly.",
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
ptype = "application/vnd.amphora.known-answer-benchmarks.data-sweep.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}
for k in ("schema", "campaign_item_id", "module_id", "authority", "verdict"):
    receipt[k] = body_obj[k]

WDIR.mkdir(parents=True, exist_ok=True)
(WDIR / "done").mkdir(parents=True, exist_ok=True)
out = WDIR / "done/W-D-KAB-source-sweep-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("self_verify_signature", True)
