#!/usr/bin/env python3
"""DSSE-Ed25519-sign the W-D-DESIGN campaign-item done receipt for
amphora-design-rule-score. AUDIT_ONLY: this is a data-rights sweep finding,
not a model, not a KPI, not a Phase-0 evaluation. It does not promote
authority, does not flip scientific_readiness, does not modify the
portfolio manifest, module-manifest.json, any locked dataset, or any
existing signed receipt. Two-replay byte gate enforced by construction
(canonical json.dumps with sort_keys, no time-of-day fields in the body).
"""
import base64, hashlib, json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-design-rule-score"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"
OUTDIR = MOD / "evidence/phase0/repairs/W-D-DESIGN/done"
WORKDIR = MOD / "evidence/phase0/repairs/W-D-DESIGN/work"

FIRE_ID = "20260813T010001-1531359-466e20213039"


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


eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = (eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id"))
assert eval_pin, "evaluator key_id does not derive pinned trust store entry"

SOURCES = [
  {
    "n": 1,
    "query": "epoxy coating pencil hardness dataset CC-BY Zenodo formulation",
    "source": "MDPI Coatings -- \"Tailoring Mechanical and Surface Properties of Epoxy Coatings with Synthesized Pigment Particles: Microhardness, Adhesion, and Wettability Studies\"",
    "doi": "10.3390/coatings16050584",
    "license_quote": "Crossref publisher-registered license record: {\"URL\": \"https://creativecommons.org/licenses/by/4.0/\"} (page itself returned HTTP 403 to automated fetch; license taken from the publisher's own DOI-registration metadata, not a third party).",
    "license_verdict": "CC_BY_4.0",
    "coverage": "Epoxy coatings with two synthesized pigments (cobalt blue, chrome orange) on Al/phosphor-bronze/brass; composite+intrinsic microhardness (MPa), adhesion, wettability per pigment/substrate combo.",
    "overlap_verdict": "RIGHTS_CLEAR_LOW_OVERLAP -- hardness property class matches; factor axis is pigment identity, not amine-hardener class/stoichiometry; DGEBA basis not confirmed this fire.",
  },
  {
    "n": 2,
    "query": "\"pencil hardness\" epoxy coating supplementary data MDPI open access",
    "source": "MDPI Applied Sciences -- \"Ultra-Scratch-Resistant, Hydrophobic and Transparent Organosilicon-Epoxy-Resin Coating with a Double Cross-Link Structure\"",
    "doi": "10.3390/app12104854",
    "license_quote": "Crossref publisher-registered license record: {\"URL\": \"https://creativecommons.org/licenses/by/4.0/\"} (page returned HTTP 403 to automated fetch; license taken from publisher DOI-registration metadata).",
    "license_verdict": "CC_BY_4.0",
    "coverage": "Sol-gel organosilicon-epoxy (GPTES) double-crosslink coating; pencil hardness up to 8H (ASTM), water contact angle, transmittance.",
    "overlap_verdict": "RIGHTS_CLEAR_PARTIAL_OVERLAP -- pencil-hardness property matches; resin chemistry is organosilicon, not DGEBA/amine-hardener class -- moderate structural mismatch.",
  },
  {
    "n": 3,
    "query": "\"scratch resistance\" epoxy coating open data repository DGEBA amine formulation table",
    "source": "MDPI Polymers (PMC10780492) -- \"Surface Degradation of DGEBA Epoxy Resins Cured with Structurally Different Amine Hardeners: Effects of UV Radiation\"",
    "doi": "10.3390/polym16010067",
    "license_quote": "\"© 2023 by the authors. Licensee MDPI, Basel, Switzerland. This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license (https://creativecommons.org/licenses/by/4.0/).\" -- quoted verbatim from the live PMC page, fetched this fire.",
    "license_verdict": "CC_BY_4.0",
    "coverage": "DGEBA epoxy cured with 3 amine hardeners (DDS, CYDM, 8CH2DA); reports water absorption, Tg, mass loss, color change, contact angle.",
    "overlap_verdict": "RIGHTS_CLEAR_NO_MATCH -- no hardness or scratch-resistance data of any kind; does not qualify despite clean rights and DGEBA/amine-class topical match.",
  },
  {
    "n": 4,
    "query": "marine anti-corrosion epoxy coating dataset open access DOE report hardness",
    "source": "MDPI Materials (PMC8999854) -- \"Development and Characterization of PA 450 and PA 3282 Epoxy Coatings as Anti-Corrosion Materials for Offshore Applications\"",
    "doi": "10.3390/ma15072562",
    "license_quote": "\"© 2022 by the authors. Licensee MDPI, Basel, Switzerland. This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license (https://creativecommons.org/licenses/by/4.0/).\" -- quoted verbatim from the live PMC page, fetched this fire.",
    "license_verdict": "CC_BY_4.0",
    "coverage": "DGEBA + PA-450/PA-3282 amine hardeners, 6 stoichiometric variants (E-0/E-1/E-2, F-0/F-1/F-2 at -15%..+15% hardener); pendulum hardness (ASTM D-4366), impact resistance (ASTM D-2794), scratch testing (ASTM D-7027), nanoindentation hardness (>=5 indents/sample); all values in main-text Tables 3-6, no supplementary download needed.",
    "overlap_verdict": "QUALIFYING -- STRONGEST MATCH: direct scratch-hardness + amine-hardener-stoichiometry overlap with the Purformance factor space, marine/offshore anti-corrosion domain match, n=6 formulations, clean main-text tables. Appended to acquisition queue.",
  },
  {
    "n": 5,
    "query": "\"scratch resistance\" epoxy coating open data repository DGEBA amine formulation table",
    "source": "MDPI Molecules (PMC10254157) -- \"Benchmark Study of Epoxy Coatings with Selection of Bio-Based Phenalkamine versus Fossil-Based Amine Crosslinkers\"",
    "doi": "10.3390/molecules28114259",
    "license_quote": "\"© 2023 by the authors. Licensee MDPI, Basel, Switzerland. This article is an open access article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license\" -- quoted verbatim from the live PMC page, fetched this fire; the article states this CC BY 4.0 license also covers the downloadable supplementary zip at https://www.mdpi.com/article/10.3390/molecules28114259/s1.",
    "license_verdict": "CC_BY_4.0",
    "coverage": "DGEBA + FA1-FA4 fossil amines / PK1-PK4 phenalkamines; 80+ formulation matrix (5 resin:hardener ratio points per crosslinker, 7 FA1:PK1 blend ratios, 4 thermal precure durations 0/1/6/12h at 60C); Shore D hardness + scratch resistance reported, but numeric values are embedded in Figures 5a/7a/9 rather than a plain-text table.",
    "overlap_verdict": "QUALIFYING -- LARGEST n, same amine-class/DGEBA overlap as source 4, but requires figure-digitization before use (not a clean table). Appended to acquisition queue.",
  },
  {
    "n": 6,
    "query": "epoxy amine curing agent stoichiometry pencil hardness supplementary table CC BY",
    "source": "ACS Applied Polymer Materials -- \"Dual-Curable Epoxy-Amine Thermosets: Influence of Stoichiometry and Ratio between Hardeners on Thermal and Thermomechanical Properties\"",
    "doi": "10.1021/acsapm.3c03132",
    "license_quote": "Crossref publisher-registered license record lists three STM-signatory manuscript-sharing policy URLs (https://doi.org/10.15223/policy-029, -037, -045) -- the standard ACS subscription/TDM-sharing terms, not a Creative Commons open license. Page itself returned HTTP 403 to automated fetch.",
    "license_verdict": "BLOCKED_PROPRIETARY",
    "coverage": "Not extracted (paywalled).",
    "overlap_verdict": "BLOCKED_RIGHTS -- topically strong (epoxy-amine stoichiometry/hardener-ratio study) but no open license; not usable without a paid license or author permission.",
  },
  {
    "n": 7,
    "query": "\"pencil hardness\" epoxy coating supplementary data MDPI open access",
    "source": "ACS Omega -- \"Characteristics of Mechanical Properties and Thermal Behavior of Epoxy Nanocomposites and Coatings by Zinc Borate, Nano Silica, and Hardener\"",
    "doi": "10.1021/acsomega.2c02462",
    "license_quote": "Crossref publisher-registered license record: {\"URL\": \"https://creativecommons.org/licenses/by-nc-nd/4.0/\"} -- CC BY-NC-ND 4.0. Page itself returned HTTP 403 to automated fetch; license taken from publisher DOI-registration metadata.",
    "license_verdict": "BLOCKED_NC_ND",
    "coverage": "Not extracted (blocked on license before content review).",
    "overlap_verdict": "BLOCKED_RIGHTS -- nominally \"open access\" but NC-ND forbids derivative works and redistribution of a retrained/repackaged training corpus; not rights-clean for this module's use even though the article is freely readable.",
  },
  {
    "n": 8,
    "query": "marine anti-corrosion epoxy coating dataset open access DOE report hardness",
    "source": "Elsevier Progress in Organic Coatings -- \"High performance polyaniline containing coating system for wet surfaces\"",
    "doi": "10.1016/j.porgcoat.2009.06.008",
    "license_quote": "Crossref publisher-registered license record: {\"URL\": \"https://www.elsevier.com/tdm/userlicense/1.0/\"} -- Elsevier's standard subscriber/text-and-data-mining user license, not an open redistribution license.",
    "license_verdict": "BLOCKED_PROPRIETARY",
    "coverage": "Not extracted (paywalled).",
    "overlap_verdict": "BLOCKED_RIGHTS.",
  },
  {
    "n": 9,
    "query": "\"scratch resistance\" epoxy coating open data repository DGEBA amine formulation table",
    "source": "Elsevier Progress in Organic Coatings -- \"Linseed amide diol/DGEBA epoxy blends for coating applications: Preparation, characterization, ageing studies and coating properties\"",
    "doi": "10.1016/j.porgcoat.2009.09.012",
    "license_quote": "Crossref publisher-registered license record: {\"URL\": \"https://www.elsevier.com/tdm/userlicense/1.0/\"} -- Elsevier's standard subscriber/TDM user license, not open.",
    "license_verdict": "BLOCKED_PROPRIETARY",
    "coverage": "Not extracted (paywalled).",
    "overlap_verdict": "BLOCKED_RIGHTS -- despite the strongest topical DGEBA-blend title match of the whole sweep, no open license is available.",
  },
  {
    "n": 10,
    "query": "\"scratch resistance\" epoxy coating open data repository DGEBA amine formulation table",
    "source": "ACS Sustainable Chemistry & Engineering (PMC8938888) -- \"Novel Biobased Epoxy Thermosets and Coatings from Poly(limonene carbonate) Oxide and Synthetic Hardeners\"",
    "doi": "10.1021/acssuschemeng.1c07665",
    "license_quote": "Crossref publisher-registered license record: {\"URL\": \"https://creativecommons.org/licenses/by/4.0/\"} -- CC BY 4.0.",
    "license_verdict": "CC_BY_4.0",
    "coverage": "Poly(limonene carbonate) oxide (PLCO) biobased epoxy + polyetheramine/polyamideamine hardeners; thermal/mechanical property spectrum reported; hardness/scratch content not confirmed this fire.",
    "overlap_verdict": "RIGHTS_CLEAR_LOW_OVERLAP -- rights-clean but non-DGEBA resin backbone (bio-based), structural mismatch to the Purformance target space.",
  },
  {
    "n": 11,
    "query": "marine anti-corrosion epoxy coating dataset open access DOE report hardness",
    "source": "Elsevier Tribology International -- \"Research progress of marine anti-corrosion and wear-resistant coating\"",
    "doi": "10.1016/j.triboint.2024.109864",
    "license_quote": "Crossref publisher-registered license record: {\"URL\": \"https://www.elsevier.com/tdm/userlicense/1.0/\"} plus STM-signatory sharing-policy URLs (10.15223/policy-017/-037/-012/-029/-004) -- proprietary subscription terms.",
    "license_verdict": "BLOCKED_PROPRIETARY",
    "coverage": "Review article; no per-formulation raw data even if rights allowed access.",
    "overlap_verdict": "BLOCKED_RIGHTS, and would not have qualified on content (review, not primary data) even if open.",
  },
  {
    "n": 12,
    "query": "Zhoushan seawater station coating corrosion dataset China National Materials Corrosion Protection Data Center license access",
    "source": "National Materials Corrosion and Protection Data Center (corrdata.org.cn; re3data.org r3d100013752) -- Zhoushan seawater-station exposure/corrosion data referenced by marine-coating detection studies",
    "doi": "n/a -- national data center, no single DOI; re3data record r3d100013752",
    "license_quote": "Quoted verbatim from the re3data.org repository record: \"Type of access to data: open\" and \"Type of access to data: restricted\" with registration required for restricted content; the record also states \"Copyrights\" apply to the data.",
    "license_verdict": "BLOCKED_MIXED_RESTRICTED",
    "coverage": "Atmospheric/immersion corrosion-rate exposure data at national test stations (incl. Zhoushan); not per-formulation scratch-hardness with composition even where access is open.",
    "overlap_verdict": "BLOCKED_RIGHTS_AND_WRONG_PROPERTY_CLASS -- registration-gated for restricted content, and covers corrosion-rate exposure data rather than the scratch-hardness + composition property class this item targets.",
  },
]

REPOSITORY_SWEEPS = [
  {"repository_class": "Zenodo (site:zenodo.org and zenodo.org record search)",
   "queries": ["site:zenodo.org epoxy amine coating hardness formulation data"],
   "result": "No qualifying epoxy-coating hardness+composition record surfaced; top hits were unrelated (electrical-conductivity conference PDF)."},
  {"repository_class": "Figshare (site:figshare.com and figshare.com search)",
   "queries": ["site:figshare.com epoxy coating scratch hardness dataset"],
   "result": "One candidate found (Scielo/Polimeros RT-cure epoxy post-cure dataset, scielo.figshare.com/articles/dataset/9870671); WebFetch and targeted Crossref bibliographic search both failed to resolve a verifiable license this fire (403 on fetch, no exact Crossref record match) -- recorded as UNVERIFIED, not counted toward the 12 named sources, and not queued without a verbatim license."},
  {"repository_class": "Mendeley Data (data.mendeley.com)",
   "queries": ["Mendeley Data epoxy coating pencil hardness formulation composition"],
   "result": "No qualifying Mendeley Data record surfaced in top results."},
  {"repository_class": "NIST / data.gov",
   "queries": ["NIST data.gov coating hardness dataset epoxy"],
   "result": "NIST's Hardness and Coating Thickness Standardization program covers metrology traceability (Rockwell/Vickers/Knoop scales, magnetic coating-thickness methods), not epoxy-amine formulation/hardness data; no qualifying dataset found."},
]

body_obj = {
    "schema": "amphora.design-rule-score.repair-done.w-d-design.v1",
    "campaign_item_id": "W-D-DESIGN",
    "module": "amphora-design-rule-score",
    "fire_id": FIRE_ID,
    "authority": "AUDIT_ONLY",
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_existing_receipts": False,
    "claim_under_attack": {
        "receipt_path": "amphora-design-rule-score/evidence/",
        "claim_text": "The n=58 single-formulator binding constraint can be relaxed with a rights-clean second corpus.",
    },
    "objective": "DATA-DIMENSION ITEM: search for rights-clean (CC-BY/CC0/public-domain) coating hardness or scratch-resistance datasets with per-formulation composition; verdict is a rights-clean evidence position, not a new model.",
    "done_criterion": ">=12 named sources swept, each recorded with the exact query string used and EITHER its licence quoted verbatim from the source OR the blocking licence quoted verbatim. Every qualifying find appended to the acquisition queue with n, property/feature coverage, structural/factor overlap, and concrete next action.",
    "done_criterion_met": True,
    "outcome": "BLOCKED_DATA",
    "outcome_rationale": (
        "The sweep surfaced two rights-clean (CC BY 4.0) sources with genuine per-formulation "
        "DGEBA/amine-hardener composition alongside scratch/pendulum/pencil hardness data "
        "(sources #4 and #5 below) -- proving the claim is not categorically false: a rights-clean "
        "second corpus DOES exist in the literature. But neither is a downloadable structured "
        "dataset: #4 is n=6 formulations sitting in main-text tables requiring hand transcription; "
        "#5 is a larger (80+) formulation matrix with hardness/scratch values embedded in figures "
        "requiring digitization. Forward motion (actually relaxing the n=58 constraint) needs a "
        "human to transcribe/digitize and a follow-up fire to integrate and re-run the leak-free "
        "split-integrity benchmark -- hence BLOCKED_DATA rather than a completed corpus-merge."
    ),
    "n_named_sources_swept": len(SOURCES),
    "sources_swept": SOURCES,
    "repository_class_sweeps": REPOSITORY_SWEEPS,
    "qualifying_finds_appended_to_acquisition_queue": [
        {
            "candidate_source": "MDPI Materials 10.3390/ma15072562",
            "queue_path": "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl (xbabe1)",
            "fire_id": FIRE_ID,
        },
        {
            "candidate_source": "MDPI Molecules 10.3390/molecules28114259",
            "queue_path": "/home/ubuntu/amphora-cron/data-acquisition-queue.jsonl (xbabe1)",
            "fire_id": FIRE_ID,
        },
    ],
    "proposed_followups": [
        {
            "module": "amphora-design-rule-score",
            "defect": "Purformance scratch-hardness KPI corpus (n=58, single formulator/instrument) has an identified but unintegrated second-formulator candidate: MDPI Materials 10.3390/ma15072562, 6 DGEBA/PA-450/PA-3282 formulations with pendulum/impact/scratch/nanoindentation hardness in main-text Tables 3-6, CC BY 4.0.",
            "proposed_done_criterion": "A human or follow-up fire hand-transcribes Tables 3-6 into the Purformance factor schema, stages it as a second-source addition, and a signed receipt shows split-integrity-dedup-v1 and the Guth-Gold concordance benchmark re-run on the combined (n=58 + n<=6) corpus, reporting whether the concordance CI narrows or the physics-vs-chance margin changes.",
        },
        {
            "module": "amphora-design-rule-score",
            "defect": "A second, larger (80+ formulation) rights-clean candidate exists (MDPI Molecules 10.3390/molecules28114259, CC BY 4.0) but its hardness/scratch values are embedded in figures (5a/7a/9), not a plain-text table -- unusable without digitization.",
            "proposed_done_criterion": "A human or follow-up fire digitizes Figures 5a/7a/9 (or obtains the underlying spreadsheet from the authors), maps the FA/PK ratio + precure-time factors onto the Purformance schema, and a signed receipt records the resulting n and whether it changes the binding-constraint analysis.",
        },
        {
            "module": "amphora-design-rule-score",
            "defect": "Two topically strong DGEBA/epoxy-amine hardness sources are rights-blocked: ACS Applied Polymer Materials 10.1021/acsapm.3c03132 (proprietary STM-signatory sharing policy) and Elsevier Progress in Organic Coatings 10.1016/j.porgcoat.2009.09.012 (Elsevier TDM userlicense 1.0, linseed-amide/DGEBA blend).",
            "proposed_done_criterion": "A human contacts the corresponding authors of both papers directly (as R-D05 already recommends for the Purformance authors) to ask for a CC-licensed data release or explicit permission to use the raw tables for non-commercial AUDIT_ONLY research; record any reply as a new BLOCKED_RIGHTS or rights-cleared receipt.",
        },
    ],
    "confidentiality": "No masked customer, CTO, or internal identity named in this receipt. No LOCKED-INTERNAL formulation content disclosed -- all cited chemistry is from public literature.",
    "does_not_close": [
        "No product-performance, batch-release, procurement, safety, or freedom-to-operate authority.",
        "Does not itself relax the n=58 constraint -- that requires human transcription/digitization and a follow-up benchmark re-run (see proposed_followups).",
        "Does not modify any existing signed receipt, the module manifest, or any locked dataset.",
        "BLOCKED_PROPRIETARY / BLOCKED_NC_ND / BLOCKED_MIXED_RESTRICTED verdicts above are this fire's read of publicly stated licensing terms, not a legal opinion.",
    ],
    "signing_key": {
        "role": "PHASE0_EVALUATOR", "key_id": eval_key_id, "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY repair-done receipt under evidence/phase0/repairs/W-D-DESIGN/done/",
        "derives_pinned_trust_store_key_id": bool(eval_pin)},
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.design-rule-score-repair-done-w-d-design+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {"payload": base64.standard_b64encode(body).decode(), "payloadType": ptype,
            "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}]}
receipt = {"evaluator_key_id": eval_key_id, "evaluator_public_key_hex": eval_pub_hex,
           "signature": envelope}

OUTDIR.mkdir(parents=True, exist_ok=True)
out = OUTDIR / "w-d-design-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

# self-verify
Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])))

WORKDIR.mkdir(parents=True, exist_ok=True)
state = {
    "campaign_item_id": "W-D-DESIGN",
    "fire_id": FIRE_ID,
    "status": "done",
    "n_sources_swept": len(SOURCES),
    "n_qualifying_finds": 2,
    "done_receipt": "evidence/phase0/repairs/W-D-DESIGN/done/w-d-design-done-receipt.v1.dsse.json",
    "next_action": "None required for this item's done_criterion. Follow-up transcription/digitization work is filed in proposed_followups[] of the done receipt, not owed by this item.",
}
(WORKDIR / "STATE.json").write_text(json.dumps(state, indent=2, sort_keys=True))

print("WROTE", out)
print("self_verify_signature", True)
print("envelope_sha256", sha(out.read_bytes()))
print("body_sha256", sha(body))
