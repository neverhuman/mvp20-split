#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-D-NOV source-sweep receipt (AUDIT_ONLY).
Data-dimension campaign item: sweeps published sources for a second rights-clean
polymer/monomer structure corpus to attack the single-OpenPoly-corpus novelty claim;
signs with the pinned Phase-0 evaluator seed only; self-verifies the envelope before
writing."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-novelty"
WDIR = MOD / "evidence/phase0/repairs/W-D-NOV"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

SWEEP_RECORD = WDIR / "work/sweep-record.v1.json"
FIRE_ID = "20260813T050002-3861856-74742f3ffe2c"


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
assert sweep["tally"]["swept"] == 13
assert len(sweep["sources_swept"]) == 13
for s in sweep["sources_swept"]:
    assert s.get("query"), f"source {s['n']} missing query"
    assert s.get("license_quote_verbatim"), f"source {s['n']} missing license quote"
    assert s.get("disposition") in ("RECOMMENDED", "RECOMMENDED_WITH_FLAG", "BLOCKED", "BLOCKED_WITH_FLAG")

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
        "module": "amphora-molecule-novelty",
        "defect": (
            "Every novelty verdict this module has ever issued (see "
            "tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json, whose own "
            "awaiting[] already names this gap) is measured against the single 442-row "
            "OpenPoly corpus, previously proved to hold only 350 distinct structures after "
            "dedup. This sweep found two genuinely CC BY 4.0-licensed candidate second "
            "corpora: the Khazana/Polymer Genome data descriptor (Huan et al. 2016, "
            "Scientific Data 3:160012, 1,073 polymers, structures on Dryad DOI "
            "10.5061/dryad.5ht3n) and Google Patents Public Data (IFI CLAIMS + Google, "
            "CC BY 4.0, via BigQuery) -- neither has been downloaded, canonicalized, "
            "deduped, or Tanimoto-compared against OpenPoly."
        ),
        "proposed_done_criterion": (
            "A follow-up fire downloads the Khazana/Polymer Genome structure files from "
            "Dryad, canonicalizes SMILES with RDKit, dedups against OpenPoly's 350 distinct "
            "structures, and computes an ECFP4/Tanimoto nearest-neighbor overlap "
            "distribution the same way the existing OpenPoly KPI did (Rogers-Hahn 2010, "
            "radius=2, 2048 bits), landing a new signed KPI that reports n after dedup and "
            "the overlap statistic -- BLOCKED_DATA is not an acceptable outcome for this "
            "specific follow-up since the licence is already confirmed clean."
        ),
    },
    {
        "module": "amphora-molecule-novelty",
        "defect": (
            "SureChEMBL (source 8) is the single best-fit candidate for the campaign item's "
            "explicit ask for a 'public patent-derived structure set' -- ~30M structures "
            "mined from 14M+ patent documents, directly covering coatings/epoxy-resin patent "
            "literature -- but this fire could not find a SureChEMBL-specific license clause "
            "on either its gitbook or github.io pages; only EMBL-EBI's general terms ('no "
            "additional restriction ... than those provided by the data owner') apply, and "
            "the 'data owner' for patent-mined structures is ambiguous."
        ),
        "proposed_done_criterion": (
            "A human or follow-up fire emails surechembl-help@ebi.ac.uk (address published "
            "on SureChEMBL's own documentation) or locates a SureChEMBL-specific data-use "
            "policy page, quotes it verbatim, and records whether patent-mined structures "
            "from the epoxy/amine coatings space may be redistributed as part of a novelty "
            "reference corpus before any SureChEMBL data is used."
        ),
    },
    {
        "module": "amphora-molecule-novelty",
        "defect": (
            "PolyUniverse (source 11, github.com/ytl0410/PolyUniverse) is the single best "
            "topical chemistry match found in this entire sweep -- it explicitly generates "
            "epoxy and vitrimer polymer-class structures via rule-based polymerization "
            "reactions, directly adjacent to our DGEBA/amine target space -- but the GitHub "
            "repository carries no LICENSE file (API-reported license: null) and the "
            "companion Zenodo deposit (record 12585902), which might carry an independent "
            "CC license badge, returned HTTP 403 (anti-bot block) to this fire's fetch."
        ),
        "proposed_done_criterion": (
            "A follow-up fire re-attempts the Zenodo record 12585902 fetch (possibly via a "
            "different route/timing to avoid the rate-limit block) to check for an "
            "independent CC-license badge on the deposited dataset; if still blocked or "
            "still unlicensed, a human rights review contacts the repository author to ask "
            "for an explicit reuse grant before any PolyUniverse-derived structure is "
            "compared against OpenPoly."
        ),
    },
    {
        "module": "amphora-molecule-novelty",
        "defect": (
            "Four sources (PubChem, EPA CompTox, CAS Common Chemistry, ChEMBL) are each "
            "individually rights-flagged in a way that blocks blanket bulk use (submitter "
            "IP claims possible, non-commercial-only, or share-alike) but are each "
            "individually low-risk for the small, named set of commodity epoxy-resin and "
            "amine-hardener monomers this portfolio's ingredient library already references "
            "by name/CASRN -- the systematic-bulk-download restriction that blocks sources "
            "1, 3, 9, 12 targets a different (larger, unreviewed) use case than a per-CASRN "
            "lookup of ~20-30 already-named commodity chemicals."
        ),
        "proposed_done_criterion": (
            "A follow-up fire builds a small, explicitly per-CASRN-diligenced 'commodity "
            "monomer cross-check' corpus by looking up the specific DGEBA analogs and amine "
            "hardeners already named in amphora-ingredient-library, one CASRN at a time, "
            "against PubChem and EPA CompTox (the two sources with the least-restrictive "
            "per-record terms), records that diligence per compound, and computes a partial "
            "Tanimoto overlap signal against OpenPoly as a second, narrower reference set -- "
            "explicitly not a bulk-scrape of any of the four sources."
        ),
    },
]

body_obj = {
    "schema": "amphora.molecule-novelty.data-sweep.v1",
    "campaign_item_id": "W-D-NOV",
    "module_id": "amphora-molecule-novelty",
    "authority": "AUDIT_ONLY",
    "claim_under_attack": (
        "amphora-molecule-novelty/evidence/ :: 'Novelty claims rest on more than one "
        "reference corpus.' -- currently FALSE: every issued novelty verdict "
        "(tanimoto-nn-novelty-canonical-epoxy-amines-vs-openpoly-kpi.v1.json) is measured "
        "against the single 442-row / 350-distinct-structure OpenPoly corpus alone."
    ),
    "attack_type": "rights-clean-second-reference-corpus-discovery-sweep",
    "sources_swept_count": 13,
    "sweep_record": sweep,
    "headline": (
        "Swept 13 named published/public sources for a second rights-clean polymer/monomer "
        "structure corpus with chemistry overlapping our epoxy-amine coating target space, "
        "as the campaign item instructs, in place of directly falsifying a model claim "
        "(this is a DATA-DIMENSION item). RECOMMENDED (rights-clean, licence quoted "
        "verbatim, immediately actionable): (a) the Khazana/Polymer Genome data descriptor "
        "(Huan et al. 2016, Scientific Data, CC BY 4.0, 1,073 polymers, Dryad-hosted "
        "structures) and (b) Google Patents Public Data (IFI CLAIMS + Google, CC BY 4.0 via "
        "BigQuery, patent text/metadata requiring a downstream structure-extraction step). "
        "RECOMMENDED_WITH_FLAG (clean but conditioned -- non-commercial, share-alike, or "
        "per-record submitter-IP-risk): PubChem, EPA CompTox Dashboard (1,376,722 chemicals "
        "per its own live count), Open Reaction Database (CC BY-SA 4.0), CAS Common "
        "Chemistry (CC BY-NC 4.0), SureChEMBL (ambiguous data-owner terms), ChEMBL "
        "(CC BY-SA 3.0, weak chemistry overlap). BLOCKED (explicit no-redistribution or "
        "hard access wall, quoted verbatim in every case): PoLyInfo/NIMS MatNavi "
        "(login-gated, scraping/bulk-acquisition explicitly prohibited by its own Terms of "
        "Use -- ironically the single best 'PoLyInfo-adjacent' name-match the campaign item "
        "asks for), NIST Chemistry WebBook (SRD-69 copyright-secured, 'All rights reserved', "
        "not ordinary US-government public domain), Reaxys/Elsevier (explicit "
        "no-derivative-works clause, paywalled), CCDC/Cambridge Structural Database "
        "('must not be used to systematically download or redistribute'). BLOCKED_WITH_FLAG: "
        "PolyUniverse (github.com/ytl0410/PolyUniverse) is the single best topical chemistry "
        "match found in this sweep -- an explicitly rule-based-generated epoxy/vitrimer "
        "polymer library -- but its GitHub repo carries no LICENSE file and its companion "
        "Zenodo deposit could not be checked this fire (HTTP 403). This fire lands NO new "
        "structures into any corpus and asserts NO change to the KPI's novelty verdicts -- "
        "it proposes 4 concrete, owned followups (filed below) so a future fire can convert "
        "the two RECOMMENDED clean sources into an actual second Tanimoto-comparison corpus. "
        "Verdict: BLOCKED_DATA -- the honest current state is that the single-corpus problem "
        "named by this campaign item is real, documented, and not yet resolved; forward "
        "motion needs a follow-up fire to acquire/canonicalize/dedup/compare the two clean "
        "CC BY 4.0 sources, which this receipt is the itemized evidence position for."
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
        "Adds no structure to any corpus and changes no existing novelty KPI verdict; "
        "proposes only.",
        "Does not confirm SureChEMBL's data-owner terms; flags that ambiguity explicitly.",
        "Does not resolve the PolyUniverse/Zenodo license-badge check blocked by HTTP 403 "
        "this fire.",
        "Does not download, canonicalize, or compare any candidate corpus against OpenPoly; "
        "flags that as the concrete next step for a follow-up fire.",
    ],
    "provenance": {"module_manifest_sha256": manifest_sha,
                    "sweep_record_path": str(SWEEP_RECORD.relative_to(ROOT)),
                    "sweep_record_sha256": sweep_sha,
                    "fire_id": FIRE_ID},
    "signing_key": {
        "authority": "AUDIT_ONLY", "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing only; no dual-identity ceremony",
        "used_for": "AUDIT_ONLY data-sweep receipt under evidence/phase0/repairs/W-D-NOV/done/",
        "trust_anchored_in_phase0_promotion_store": bool(eval_pin),
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-novelty.data-sweep.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}
for k in ("schema", "campaign_item_id", "module_id", "authority", "verdict"):
    receipt[k] = body_obj[k]

WDIR.mkdir(parents=True, exist_ok=True)
(WDIR / "done").mkdir(parents=True, exist_ok=True)
out = WDIR / "done/W-D-NOV-source-sweep-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("self_verify_signature", True)
