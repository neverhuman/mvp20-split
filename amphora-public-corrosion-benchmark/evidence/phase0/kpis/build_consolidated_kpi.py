#!/usr/bin/env python3
"""
Consolidates the four audit verdicts produced against USBR-21019 (this module's
coating-side EIS/rustcreep/adhesion data) into a signed KPI-surface receipt.

Objective (campaign item C10): the KPI surface at
evidence/phase0/kpis/nist-corr-data-marine-steel-corrosion-baseline-kpi.v1.json
only reflects the NIST CORR-DATA bare-substrate baseline. It does NOT index the
module's four coating-side audit verdicts (three negative/underpowered, one a
hard H0_REFUTED plus a newly discovered data-integrity defect). Per the claim
under test -- "the module's KPI surface reflects its strongest current evidence"
-- that claim is FALSE as the surface currently stands: the strongest, hardest-won
evidence in this module (the falsifications) is invisible to the KPI surface.
This receipt repairs that by publishing a second, indexing KPI artifact.
"""
import csv, glob, os, json, hashlib, base64, sys

MODULE_ROOT = "/home/ubuntu/amphora/build/mvp20-split/amphora-public-corrosion-benchmark"
SEED_PATH = "/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed"

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_dsse_payload(path):
    d = json.load(open(path))
    payload = json.loads(base64.b64decode(d["signature"]["payload"]))
    return d, payload


def build():
    os.chdir(MODULE_ROOT)

    audits = [
        ("evidence/audit/eis-brasher-kingsbury-water-uptake-admissibility-v1/"
         "eis-brasher-kingsbury-water-uptake-admissibility-receipt.v1.dsse.json"),
        ("evidence/audit/eis-reproducibility-discrimination-power-v1/"
         "eis-reproducibility-discrimination-power-receipt.v1.dsse.json"),
        ("evidence/audit/eis-rustcreep-crossmodality-v1/"
         "eis-rustcreep-crossmodality-receipt.v1.dsse.json"),
        ("evidence/audit/multi-instrument-concordance-v1/"
         "multi-instrument-concordance-receipt.v1.dsse.json"),
    ]

    audit_index = []
    for rel in audits:
        raw, payload = load_dsse_payload(rel)
        audit_index.append({
            "audit_id": payload.get("audit_id") or os.path.basename(os.path.dirname(rel)),
            "receipt_path": rel,
            "receipt_sha256": sha256_file(rel),
            "evaluator_key_id": raw["evaluator_key_id"],
            "verdict": payload.get("verdict"),
            "headline": payload.get("headline"),
            "n_records": payload.get("n_records_parsed") or payload.get("n_records_total"),
            "does_not_close": payload.get("does_not_close", []),
        })

    nist_kpi_path = "evidence/phase0/kpis/nist-corr-data-marine-steel-corrosion-baseline-kpi.v1.json"
    nist_kpi_sha256 = sha256_file(nist_kpi_path)

    erratum_source_path = ("reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw/"
                            "128772_2-z-p-2k-2-s_eis.csv")
    erratum_sha256 = sha256_file(erratum_source_path)

    payload = {
        "$schema": "amphora.module-phase0-kpi.v1",
        "schema": "amphora.public-corrosion-benchmark.audit-verdicts-consolidated-kpi.v1",
        "kpi_id": "amphora-public-corrosion-benchmark-phase0-audit-verdicts-consolidated-v1",
        "module_id": "amphora-public-corrosion-benchmark",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "REAL_ARITHMETIC",
        "phase": "PRE_PHASE_0",
        "promotes_authority": False,
        "modifies_manifest": False,
        "modifies_signed_phase0_kpi": False,
        "scientific_success_asserted": False,
        "campaign_item_id": "C10",
        "capability": (
            "Consolidated index of this module's four coating-side audit verdicts against "
            "USBR-21019 (rights-clean, US Federal Government work, public domain 17 U.S.C. 105), "
            "published as a second KPI-surface artifact alongside the bare-substrate NIST CORR-DATA "
            "baseline KPI. This receipt does not fit new data or claim new capability: it indexes "
            "four already-signed AUDIT_ONLY receipts so the module's strongest evidence -- three "
            "underpowered-or-null cross-instrument results and one hard H0_REFUTED physical-law "
            "falsification plus a newly discovered upstream data-integrity defect -- is discoverable "
            "from evidence/phase0/kpis/ instead of being buried in evidence/audit/."
        ),
        "honest_headline": (
            "Two independent evidence lines exist in this module. (1) BARE-SUBSTRATE, uncoated-metal "
            "seawater corrosion: NIST CORR-DATA LOSD-CV ridge MAE(log10 mm/yr)=0.6331 vs per-material-"
            "group-median NULL MAE=0.6806, a +0.0475 log10-unit (7.0%) reduction on n=588 records / 30 "
            "source documents -- modest but real, and the module's only externally-validated positive "
            "result (see evidence/phase0/kpis/nist-corr-data-marine-steel-corrosion-baseline-kpi.v1.json). "
            "(2) COATING-SIDE, USBR-21019 (6 coating systems x 4 baths, single-frequency 0.01 Hz EIS + "
            "rust-creep + wet pull-off adhesion): every audit attempted against this data has produced a "
            "negative, underpowered, or refuted result. Brasher-Kingsbury (1954) water-uptake reduction is "
            "H0_REFUTED on 6 of 6 independent physical screens (rank-redundant with |Z|, precondition-"
            "violating, range-inadmissible, no Fickian time signature, noise floor 2.2x the physical signal "
            "range). Within-instrument EIS discrimination among the 6 systems is NOT established at the "
            "observed effect size (p=0.2554; n~90 systems required at r~0.30, vs n~11 if the optimistic "
            "r~0.77 aggregate held). Cross-modality |Z|-vs-rustcreep concordance is sign-confounded when "
            "pooled and only recovers the physically-expected negative sign after bath-stratification, "
            "still underpowered at n=6 (CI crosses zero). Three-instrument concordance is WEAK_OR_NULL "
            "(Kendall's W=0.492, p=0.194-0.202). The module's correct, evidenced posture on coating-side "
            "claims is abstention, not because no test was tried, but because every test that was tried "
            "failed to clear its own pre-registered bar."
        ),
        "data_quality_flags": [
            {
                "flag_id": "usbr-21019-item-128772-impossible-phase-erratum",
                "status": "STANDING_OPEN",
                "severity": "DATA_INTEGRITY",
                "source_path": erratum_source_path,
                "source_sha256": erratum_sha256,
                "catalog_item": "https://data.usbr.gov/catalog/8048/item/128772",
                "finding": (
                    "6 of 306 USBR-21019 EIS records (1.96%) carry |phase| > 90 deg "
                    "(observed: +167.26, +134.70, +117.45, +105.45, -142.80, -116.72 deg), which is "
                    "impossible for any passive LTI two-terminal cell (Re{Z}>=0 <=> phase in [-90,+90] deg; "
                    "Kramers-Kronig prerequisite). All 6 are localized to source file "
                    "128772_2-z-p-2k-2-s_eis.csv (5 of 6 in replicate 2 / HAR bath), indicating a cell-level "
                    "acquisition fault rather than a global sign-convention error."
                ),
                "discovered_by_receipt": (
                    "evidence/audit/eis-brasher-kingsbury-water-uptake-admissibility-v1/"
                    "eis-brasher-kingsbury-water-uptake-admissibility-receipt.v1.dsse.json"
                ),
                "discovered_by_receipt_sha256": [a for a in audit_index
                                                  if a["audit_id"] == "eis-brasher-kingsbury-water-uptake-admissibility-v1"][0]["receipt_sha256"],
                "remediation": (
                    "This cron holds no authority to edit or re-issue upstream USBR public bytes. The 6 "
                    "rows are excluded from all impedance-derived quantities in existing signed receipts. "
                    "Resolution requires USBR to confirm the phase-sign/wrap convention or re-issue a "
                    "corrected item 128772. Tracked in data-acquisition-queue.jsonl (this fire adds the "
                    "escalation entry; original erratum ask filed in a prior fire, sha256 "
                    "92b10b4a5c0f4d6669ac5cd7bef976374d7cc848ba49be0d753d665542c10cbc)."
                ),
            }
        ],
        "referenced_bare_substrate_kpi": {
            "path": nist_kpi_path,
            "sha256": nist_kpi_sha256,
        },
        "audit_verdicts_index": audit_index,
        "n_audits_indexed": len(audit_index),
        "n_audits_refuted": sum(1 for a in audit_index if a["verdict"] == "H0_REFUTED"),
        "claim_locks": {
            "no_coating_efficacy_claim_grantable": True,
            "no_product_performance_authority": True,
            "no_batch_release_authority": True,
            "no_manufacturing_qualification_authority": True,
            "no_regulatory_authority": True,
            "no_optimizer_authority": True,
            "no_solver_authority": True,
            "no_patentability_authority": True,
            "no_safety_authority": True,
            "no_release_authority": True,
            "no_phase_1_or_phase_2_claim": True,
            "fto_not_performed": True,
            "pre_phase_0_research_only": True,
            "declarative_public_baseline_only": True,
            "unresolved_rights_quarantined": False,
            "consolidation_only_no_new_data_fit": True,
        },
        "awaiting": [
            "PHASE0_EVALUATOR signed evaluation.v1.dsse.json",
            "PHASE0_INTERNAL_REVIEWER signed phase0-review-receipt.v1.json",
            "Phase-1: frequency-resolved EIS Bode/Nyquist spectra Z'(f), Z''(f) with a high-frequency "
            "(>=1 kHz) coating-capacitance plateau, Kramers-Kronig / linear-KK residual validation, a "
            "pre-immersion dry C_0, and specimen area + dry-film thickness (unlocks Brasher-Kingsbury-"
            "admissible water-uptake work; escalated data ask filed this fire).",
            "Phase-1: >= ~90 independent coating systems at the observed within-bath EIS effect size "
            "(r~0.30), or a corroborating higher-effect-size instrument, to power within-instrument "
            "discrimination.",
            "Phase-1: >= ~12-20 independent coating systems to power a p<0.05 multi-instrument "
            "concordance and cross-modality rank.",
            "USBR resolution of the item 128772 impossible-phase erratum (see data_quality_flags).",
        ],
        "does_not_close": [
            "No coating-efficacy, product-performance, batch-release, or corrosion-rank authority.",
            "This receipt indexes and cross-references existing signed audit verdicts; it performs no "
            "new statistical test and fits no new model.",
            "Does not modify, supersede, or re-sign the four indexed audit receipts or the NIST "
            "bare-substrate KPI; all remain independently valid and are referenced by path + sha256.",
        ],
    }
    return payload


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
    print("n_audits_indexed:", d1["n_audits_indexed"], "| n_refuted:", d1["n_audits_refuted"])

    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        outdir = os.path.join(MODULE_ROOT, "evidence/phase0/kpis")
        with open(os.path.join(outdir, "audit-verdicts-consolidated-kpi.diagnostic.canonical.json"), "wb") as f:
            f.write(b1)
        seed = open(SEED_PATH, "rb").read()
        pt = "application/vnd.amphora.public-corrosion-benchmark-audit-verdicts-consolidated-kpi.v1+json"
        env, keyid, pubhex = dsse_sign(b1, pt, seed)
        receipt = {"signature": env, "evaluator_key_id": keyid, "reviewer_public_key_hex": pubhex}
        outpath = os.path.join(outdir, "audit-verdicts-consolidated-kpi.v1.json")
        with open(outpath, "w") as f:
            f.write(json.dumps(receipt, indent=2, sort_keys=True))
        print("emitted diagnostic + signed receipt:", outpath)
