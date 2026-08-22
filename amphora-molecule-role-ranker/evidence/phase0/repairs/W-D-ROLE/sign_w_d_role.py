#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-D-ROLE source-sweep receipt (AUDIT_ONLY).
Data-dimension campaign item: sweeps published sources for a rights-clean external
set of coating-relevant amines/accelerators/resins with independently attested roles,
to attack the claim that the role-classification rule can be tested against molecules
from outside its own 39-record self-authored fixture. Signs with the pinned Phase-0
evaluator seed only; self-verifies the envelope before writing."""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-role-ranker"
WDIR = MOD / "evidence/phase0/repairs/W-D-ROLE"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"

SWEEP_RECORD = WDIR / "work/sweep-record.v1.json"
FIRE_ID = "20260813T070001-495707-020cba43b3e2"


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
        "module": "amphora-molecule-role-ranker",
        "defect": (
            "Two chemotype families with zero representation in the flagship 39-record "
            "self-authored fixture (role_fit_benchmark.v1.json) were identified this sweep: "
            "(a) phenalkamine curing agents (cashew-nutshell-liquid-derived Mannich-base "
            "analogs, e.g. Cardolite NX-series) and (b) polyetheramine hardeners (e.g. BASF "
            "Baxxodur EC 302 / Jeffamine-D400-class). Both are commercially significant "
            "coating-relevant chemotypes never probed by any prior fire against this rule, "
            "unlike the guanidine gap (already found and repaired via R-N02/V-N02b)."
        ),
        "proposed_done_criterion": (
            "A follow-up fire builds RDKit-verified structures for >=3 phenalkamine and "
            ">=3 polyetheramine named compounds (citing CASRNs from source 4 and source 5 "
            "of this sweep's sources_swept[], with role independently cross-checked against "
            "PubChem source 6 or the CC BY Wiegand & Osburg 2023 paper's methodology for "
            "novel-compound curing verification, source 9), runs them through the live "
            "RDKit FFI the way role-live-runtime-domain-probe-v1 and "
            "role-guanidine-accelerator-domain-probe-v1 did, and reports whether the rule's "
            "structural inference still agrees with the independently-attested role -- "
            "landing either a CLAIM_SURVIVED with these 6+ external molecules as a genuine "
            "held-out set, or a fresh CLAIM_REFUTED chemotype gap."
        ),
    },
    {
        "module": "amphora-molecule-role-ranker",
        "defect": (
            "The single CC BY 4.0-licensed source found this sweep (Wiegand & Osburg 2023, "
            "Polymers 15(4):990, source 9) independently synthesizes and DSC/TGA-confirms "
            "two novel bio-based amine hardeners from lignin-derived vanillin and "
            "syringaldehyde -- a renewable-chemotype family with zero fixture coverage -- "
            "but this fire only read the license and abstract-level chemotype description, "
            "not the full structures (SMILES/CAS) needed to build test molecules."
        ),
        "proposed_done_criterion": (
            "A follow-up fire reads the full text/SI of Wiegand & Osburg 2023 (CC BY 4.0, "
            "doi.org/10.3390/polym15040990), extracts the reported structures for compounds "
            "5 and 6 (the vanillin/syringaldehyde-derived hardeners) plus IPDA and DDS as "
            "reference points, builds RDKit MoleculeFactsV1 records citing the paper as the "
            "independent role attestation, and runs the same live-FFI role probe against "
            "them."
        ),
    },
    {
        "module": "amphora-molecule-role-ranker",
        "defect": (
            "USPTO granted-patent specifications (source 12) are public domain as US "
            "government works per 17 U.S.C. 105 and directly target the heterocyclic/"
            "guanidine-adjacent accelerator chemotype family that already broke this rule "
            "once, but no specific patent has been read past its title/abstract this fire "
            "-- the worked examples that would supply concrete named-compound role "
            "attestations (e.g. US 10,556,985's nitrogen-heterocyclic curing agents) remain "
            "unextracted."
        ),
        "proposed_done_criterion": (
            "A follow-up fire reads the worked examples/claims of US 10,556,985 and "
            "US 7,008,555 (both cited in this sweep's source 12), extracts >=3 named "
            "heterocyclic or Mannich-base curing-agent structures with their stated role "
            "from the patent text (screening each for the narrow 37 CFR 1.71(d)/(e) "
            "copyrighted-excerpt exception first), and adds them to a probe set alongside "
            "the phenalkamine/polyetheramine set from the first followup above."
        ),
    },
]

body_obj = {
    "schema": "amphora.molecule-role-ranker.data-sweep.v1",
    "campaign_item_id": "W-D-ROLE",
    "module_id": "amphora-molecule-role-ranker",
    "authority": "AUDIT_ONLY",
    "claim_under_attack": (
        "amphora-molecule-role-ranker/evidence/phase0/kpis/role-classification-kpi.v1.json "
        "#structural_inference_agreement_rate=1.0 -- claim_text: 'The role-classification "
        "rule can be tested against molecules from outside its own fixture.' Currently the "
        "rule has only ever been tested against the 39-record self-authored fixture plus "
        "ad-hoc probe molecules chosen by this cron itself (never an independently-curated "
        "external corpus swept for that purpose)."
    ),
    "attack_type": "rights-clean-external-role-attestation-source-discovery-sweep",
    "sources_swept_count": 13,
    "sweep_record": sweep,
    "headline": (
        "Swept 13 named published/public sources for a rights-clean external set of "
        "coating-relevant amines/accelerators/resins with independently attested roles, as "
        "the campaign item instructs, in place of directly falsifying a model claim (this "
        "is a DATA-DIMENSION item). RECOMMENDED (clean CC BY 4.0 license, quoted verbatim, "
        "immediately actionable): Wiegand & Osburg 2023 Polymers 15(4):990, a peer-reviewed "
        "paper independently synthesizing and DSC/TGA-confirming amine hardeners spanning "
        "aliphatic (IPDA), aromatic (DDS), and two genuinely novel bio-based/renewable "
        "chemotypes absent from our fixture. RECOMMENDED_WITH_FLAG (citable per-record with "
        "attribution, no explicit bulk-reuse grant): five specialty-coatings supplier TDS "
        "lines (Huntsman Araldite/Aradur, Evonik Ancamine, Olin/Westlake Epikote/Epicure, "
        "BASF Baxxodur, Cardolite NX phenalkamines) plus PubChem/NCBI (public domain "
        "aggregation, per-record submitter-rights caveat) and USPTO granted-patent "
        "specifications (public domain US government work per 17 U.S.C. 105, per-patent "
        "37 CFR 1.71(d)/(e) screening caveat). Two of these -- Cardolite phenalkamine and "
        "BASF Baxxodur polyetheramine -- name chemotype families with ZERO representation "
        "in the flagship 39-record fixture, directly answering the campaign item's 'chemotypes "
        "nobody thought to include' framing. BLOCKED (explicit no-redistribution or bulk-"
        "collection prohibition, quoted verbatim in every case): ECHA REACH dissemination "
        "portal (systematic collection generally prohibited), NOAA CAMEO Chemicals "
        "(third-party-contributed fields require permission to duplicate), Sigma-Aldrich/"
        "MilliporeSigma (blanket IP-rights assertion incl. database rights), TCI Chemicals "
        "(explicit no-copy/no-distribute clause), and PCI Magazine/BNP Media (all-rights-"
        "reserved trade-press article that happens to contain the single broadest "
        "role-by-chemotype table found in this entire sweep -- six named hardener classes "
        "in one table -- but cannot be reproduced without a licensing request). This fire "
        "lands NO new structures into the fixture and asserts NO change to the KPI's "
        "verdict -- it proposes 3 concrete, owned followups (filed below) so a future fire "
        "can convert the CC BY paper plus the two flagged supplier chemotype gaps into an "
        "actual external held-out probe set the way role-guanidine-accelerator-domain-"
        "probe-v1 did for guanidines. Verdict: BLOCKED_DATA -- the honest current state is "
        "that no single source in this sweep is a ready-made, independently-labeled, "
        "multi-record EXTERNAL role-classification dataset; forward motion needs a "
        "follow-up fire to extract and structure-verify named compounds from the sources "
        "flagged RECOMMENDED / RECOMMENDED_WITH_FLAG, which this receipt is the itemized "
        "evidence position for."
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
        "Adds no structure to the fixture and changes no existing role-classification KPI "
        "verdict; proposes only.",
        "Does not resolve the Sigma-Aldrich Site Use Terms fetch that timed out this fire.",
        "Does not extract structures/SMILES from the CC BY paper, the two flagged "
        "supplier chemotype lines, or the USPTO patents; flags that as the concrete next "
        "step for a follow-up fire.",
        "Does not open, parse, or bulk-acquire from any BLOCKED source (ECHA, CAMEO, "
        "Sigma-Aldrich, TCI, PCI Magazine).",
    ],
    "provenance": {"module_manifest_sha256": manifest_sha,
                    "sweep_record_path": str(SWEEP_RECORD.relative_to(ROOT)),
                    "sweep_record_sha256": sweep_sha,
                    "fire_id": FIRE_ID},
    "signing_key": {
        "authority": "AUDIT_ONLY", "role": "PHASE0_EVALUATOR", "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "note": "phase0-evaluator seed used for AUDIT_ONLY signing only; no dual-identity ceremony",
        "used_for": "AUDIT_ONLY data-sweep receipt under evidence/phase0/repairs/W-D-ROLE/done/",
        "trust_anchored_in_phase0_promotion_store": bool(eval_pin),
    },
}
body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.molecule-role-ranker.data-sweep.v1+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}
for k in ("schema", "campaign_item_id", "module_id", "authority", "verdict"):
    receipt[k] = body_obj[k]

WDIR.mkdir(parents=True, exist_ok=True)
(WDIR / "done").mkdir(parents=True, exist_ok=True)
out = WDIR / "done/W-D-ROLE-source-sweep-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("self_verify_signature", True)
