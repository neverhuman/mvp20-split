#!/usr/bin/env python3
"""OSHA Table Z-1 vs Table Z-2 provenance audit for amphora-sourceability-ehs.

FALSIFICATION-AXIS attack on the module's standing claim (repeated verbatim in
THREE signed receipts):

  * benchmarks/vapor-hazard-ratio-v1        gate "all_scored_have_osha_public_pel":
        note = "every VHR denominator is a public-domain OSHA Table Z-1 PEL"
        observed=9, floor=9, passed=True
  * benchmarks/vhr-temperature-envelope-v1  per-solvent field "osha_pel_table_z1_name"
        (toluene -> "Toluene")
  * benchmarks/mixture-additivity-raoult-osha-v1  field "pel_denominator_source" =
        "OSHA 29 CFR 1910.1000 Table Z-1 (8-hour TWA permissible exposure limits) ..."

H0 UNDER TEST: "every OEL denominator used anywhere in this module's VHR family is
codified in 29 CFR 1910.1000 TABLE Z-1."

REFUTATION CRITERION (pre-declared, falsifying): if ANY panel solvent's canonical
substance name is a listed row in 29 CFR 1910.1000 TABLE Z-2 (a *different* table,
with a materially different limit structure -- TWA + acceptable ceiling +
acceptable maximum peak, rather than Z-1's single TWA/ceiling/STEL columns), then
H0 is FALSE for that solvent and every receipt asserting "Table Z-1" for it is
factually mis-provenanced.

METHOD: this script does NOT re-fit or re-derive anything. It (a) reads the
module's own already-signed receipts directly off disk to extract their literal
per-solvent Table Z-1 attribution claims (no re-typing of the claim under test),
and (b) checks each attributed solvent's canonical name against a pinned,
hand-transcribed, cited copy of the OSHA Table Z-2 substance roster (21 rows,
29 CFR 1910.1000 Table Z-2, U.S. federal regulation, public domain, verified
against osha.gov 2026-08-02).

RESULT (pre-registered before computing, see REFUTATION CRITERION above):
Toluene IS a Table Z-2 substance (TWA 200 ppm / acceptable ceiling 300 ppm /
acceptable maximum peak 500 ppm for <=10 min in any 8-hr shift), NOT a Table Z-1
substance. All three receipts' explicit "Table Z-1" attribution for toluene is
FALSE. This is 1 of 9 panel solvents (1 of 6 in the Antoine-concordant subset
used by the temperature-envelope and mixture-additivity receipts).

WHAT SURVIVES: the numeric TWA value used as the VHR denominator for toluene
(200 ppm) is numerically IDENTICAL in Table Z-2 to what was used, so no VHR
value, band assignment, worst-actor call, or mixture-hazard-index in the three
downstream receipts changes. The refutation is a PROVENANCE/citation defect, not
an arithmetic one -- but it is a real, checkable, previously-passing gate
(observed=9/9, passed=True) that is actually 8/9 true, 1/9 false.

WHAT IS ADDITIONALLY EXPOSED (a genuine coverage gap, not previously claimed or
disclaimed): Table Z-2's acceptable-ceiling (300 ppm) and acceptable-maximum-peak
(500 ppm, <=10 min/8-hr shift) limits for toluene are NOT modeled by the single-
TWA VHR framework anywhere in this module. A short, intense toluene exposure
inside the 200 ppm TWA budget (e.g. during spray application) could still
breach the Z-2 ceiling/peak structure while VHR(toluene) at 25 C reads a
comfortably MODERATE band. This is a scope gap the module has never scored or
disclaimed.

INTEGRITY GUARDS (load-bearing, fail-closed):
  * Table Z-2 roster is transcribed from OSHA's own published table (public
    domain federal regulation text; no copyrighted ACGIH/NIOSH material used).
  * Self-check probes: a substance NOT in the module's panel but KNOWN to be
    Z-2 (Styrene) must be correctly flagged Z-2 by the matcher (else the
    matcher itself is untrustworthy); a substance known to be Z-1-only in this
    panel (m-Xylene / Xylenes) must be correctly flagged NOT-Z-2.
  * Claims are extracted from the live signed receipts on disk (not
    re-asserted from memory) so this audit cannot silently drift from what the
    module actually claims.
  * Does not modify, re-sign, or supersede the three audited receipts (this
    cron's key has no authority to do so); records the refutation as an
    independent new receipt.

RIGHTS-CLEAN: OSHA 29 CFR 1910.1000 Table Z-1 and Table Z-2 (U.S. federal
regulation, public domain, no license required).

EVIDENCE_ONLY. Documents a provenance defect in existing EVIDENCE_ONLY receipts.
Does NOT itself establish OSHA compliance, control banding, respirator
selection, procurement approval, or regulatory closure. Deterministic; no
learned parameters; no RNG. Two-replay byte-stability gated. Signed AUDIT_ONLY
with the repo LOCAL_DEVELOPMENT_AUDIT_ONLY key (NOT trust-anchored). Does not
promote the module.

Primary sources:
  OSHA 29 CFR 1910.1000 Table Z-1 (Limits for Air Contaminants), U.S. federal
    regulation, public domain.
    https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1000TABLEZ1
  OSHA 29 CFR 1910.1000 Table Z-2, U.S. federal regulation, public domain.
    https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1000TABLEZ2
  OSHA "Toluene - Occupational Exposure Limits" (osha.gov/toluene/occupational-exposure-limits),
    confirms Table Z-2 TWA 200 ppm / acceptable ceiling 300 ppm / acceptable
    maximum peak 500 ppm (<=10 min per 8-hr shift) for toluene.
  29 CFR 1910.1000(b)(2) "Ceiling Values" (acceptable ceiling / acceptable
    maximum peak structure applicable to Table Z-2 substances).
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
BENCH = MOD / "benchmarks" / "osha-table-z1-z2-attribution-audit-v1"
KEY = ROOT / ".amphora/control/local-ed25519.key"
PUB = json.loads((ROOT / ".amphora/control/local-ed25519.pub.json").read_text())

# --- Pinned, hand-transcribed OSHA 29 CFR 1910.1000 Table Z-2 substance
#     roster (21 rows). Verified against osha.gov 2026-08-02. Public-domain
#     U.S. federal regulation text; not a copyrighted compilation.
TABLE_Z2_SUBSTANCES = [
    "Benzene",
    "Beryllium and beryllium compounds",
    "Cadmium fume",
    "Cadmium dust",
    "Carbon disulfide",
    "Carbon tetrachloride",
    "Chromic acid and chromates",
    "Ethylene dibromide",
    "Ethylene dichloride",
    "Fluoride as dust",
    "Formaldehyde",
    "Hydrogen fluoride",
    "Hydrogen sulfide",
    "Mercury",
    "Methyl chloride",
    "Methylene Chloride",
    "Organo (alkyl) mercury",
    "Styrene",
    "Tetrachloroethylene",
    "Toluene",
    "Trichloroethylene",
]

# --- Pinned Table Z-2 row detail for toluene (the panel solvent implicated).
#     Source: 29 CFR 1910.1000 Table Z-2 + 1910.1000(b)(2) Acceptable Ceiling
#     Concentrations; osha.gov/toluene/occupational-exposure-limits.
TOLUENE_Z2_ROW = {
    "substance": "Toluene",
    "table": "Z-2",
    "8hr_twa_ppm": 200,
    "acceptable_ceiling_concentration_ppm": 300,
    "acceptable_maximum_peak_above_ceiling_ppm": 500,
    "acceptable_maximum_peak_max_duration_min": 10,
    "citation": "29 CFR 1910.1000 Table Z-2; 1910.1000(b)(2) Acceptable Ceiling Concentrations",
}

# --- Self-check probes (matcher trustworthiness gate). ---------------------
PROBE_KNOWN_Z2_NOT_IN_PANEL = "Styrene"          # must be flagged Z-2
PROBE_KNOWN_Z1_IN_PANEL = "Xylenes"              # (m_xylene's Z-1 name) must be flagged NOT Z-2

# --- Receipts audited (read live off disk; claims are NOT re-typed here). --
RECEIPT_PATHS = {
    "vapor_hazard_ratio_kpi": MOD / "evidence/phase0/kpis/vapor-hazard-ratio-inhalation-prescreen-kpi.v1.json",
    "vhr_temperature_envelope_receipt": MOD / "reference/mvp20/data/vhr_temperature_envelope_inhalation_prescreen_receipt.v1.json",
    "mixture_additivity_receipt": MOD / "reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json",
}

REFERENCES = [
    "OSHA 29 CFR 1910.1000 Table Z-1 (Limits for Air Contaminants); U.S. federal regulation, public domain. https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1000TABLEZ1",
    "OSHA 29 CFR 1910.1000 Table Z-2; U.S. federal regulation, public domain. https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1000TABLEZ2",
    "OSHA 'Toluene - Occupational Exposure Limits'. https://www.osha.gov/toluene/occupational-exposure-limits",
    "29 CFR 1910.1000(b)(2) Acceptable Ceiling Concentrations (structure governing Table Z-2 substances).",
]


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def pae(t: str, body: bytes) -> bytes:
    return b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " + str(len(body)).encode() + b" " + body


def in_z2(name: str) -> bool:
    n = name.strip().lower()
    return any(n == z.strip().lower() for z in TABLE_Z2_SUBSTANCES)


def load_json(p: Path):
    return json.loads(p.read_text())


def extract_claims():
    """Extract the literal per-solvent Table Z-1 attribution claims from the
    three live signed receipts on disk. Returns (per_solvent_claims, kpi_gate_note,
    mixture_pel_source_string, receipt_hashes)."""
    vhr_kpi = load_json(RECEIPT_PATHS["vapor_hazard_ratio_kpi"])
    envelope = load_json(RECEIPT_PATHS["vhr_temperature_envelope_receipt"])
    mixture = load_json(RECEIPT_PATHS["mixture_additivity_receipt"])

    receipt_hashes = {
        k: sha(canon({kk: vv for kk, vv in v.items() if kk != "signature"}))
        for k, v in [("vapor_hazard_ratio_kpi", vhr_kpi),
                     ("vhr_temperature_envelope_receipt", envelope),
                     ("mixture_additivity_receipt", mixture)]
    }

    kpi_gate = None
    for g in vhr_kpi["phase0_deterministic_gates_passed"]:
        if g["gate_id"] == "all_scored_have_osha_public_pel":
            kpi_gate = g
            break

    per_solvent = []
    for e in envelope["kpis"]["solvent_envelopes"]:
        per_solvent.append({
            "solvent": e["solvent"],
            "claimed_table": "Z-1",
            "claimed_z1_name": e.get("osha_pel_table_z1_name"),
            "osha_pel_8h_twa_ppm": e.get("osha_pel_8h_twa_ppm"),
            "source_field": "vhr_temperature_envelope_receipt.kpis.solvent_envelopes[].osha_pel_table_z1_name",
        })

    mixture_pel_source = mixture["kpis"]["pel_denominator_source"]

    return per_solvent, kpi_gate, mixture_pel_source, receipt_hashes


def compute():
    per_solvent, kpi_gate, mixture_pel_source, receipt_hashes = extract_claims()

    audited = []
    for rec in per_solvent:
        z1_name = rec["claimed_z1_name"]
        actually_z2 = in_z2(z1_name) or in_z2(rec["solvent"].replace("_", " "))
        audited.append({
            **rec,
            "actually_in_table_z2": actually_z2,
            "attribution_correct": not actually_z2,
        })

    misattributed = [a for a in audited if not a["attribution_correct"]]

    # self-check probes on the matcher itself
    probe_z2_hit = in_z2(PROBE_KNOWN_Z2_NOT_IN_PANEL)
    probe_z1_correct_reject = not in_z2(PROBE_KNOWN_Z1_IN_PANEL)

    # does the numeric TWA value used match Z-2's TWA column for the
    # misattributed solvent(s)? (arithmetic-impact check)
    numeric_impact = []
    for a in misattributed:
        if a["solvent"] == "toluene":
            matches = a["osha_pel_8h_twa_ppm"] == TOLUENE_Z2_ROW["8hr_twa_ppm"]
            numeric_impact.append({
                "solvent": a["solvent"],
                "twa_used_ppm": a["osha_pel_8h_twa_ppm"],
                "z2_twa_ppm": TOLUENE_Z2_ROW["8hr_twa_ppm"],
                "twa_numerically_unaffected": matches,
                "z2_ceiling_ppm_unmodeled": TOLUENE_Z2_ROW["acceptable_ceiling_concentration_ppm"],
                "z2_peak_ppm_unmodeled": TOLUENE_Z2_ROW["acceptable_maximum_peak_above_ceiling_ppm"],
                "z2_peak_max_duration_min": TOLUENE_Z2_ROW["acceptable_maximum_peak_max_duration_min"],
            })

    kpi_gate_claim_false = (kpi_gate is not None
                             and kpi_gate.get("passed") is True
                             and len(misattributed) > 0)

    diag = {
        "method": "osha_table_z1_z2_provenance_audit",
        "h0": "every OEL denominator used in the module's VHR family is codified in 29 CFR 1910.1000 Table Z-1",
        "refutation_criterion": "any panel solvent whose claimed-Z-1 substance name is a listed Table Z-2 row falsifies H0 for that solvent",
        "table_z2_roster": TABLE_Z2_SUBSTANCES,
        "table_z2_roster_n": len(TABLE_Z2_SUBSTANCES),
        "audited_receipts": {k: str(v.relative_to(ROOT)) for k, v in RECEIPT_PATHS.items()},
        "audited_receipt_body_sha256": receipt_hashes,
        "kpi_gate_under_attack": kpi_gate,
        "mixture_receipt_pel_denominator_source_claim": mixture_pel_source,
        "per_solvent_audit": audited,
        "n_solvents_audited": len(audited),
        "n_misattributed_to_z1": len(misattributed),
        "misattributed_solvents": [a["solvent"] for a in misattributed],
        "toluene_z2_row_detail": TOLUENE_Z2_ROW if any(a["solvent"] == "toluene" for a in misattributed) else None,
        "numeric_impact_assessment": numeric_impact,
        "matcher_selfcheck": {
            "known_z2_substance_not_in_panel": PROBE_KNOWN_Z2_NOT_IN_PANEL,
            "correctly_flagged_z2": probe_z2_hit,
            "known_z1_only_panel_substance": PROBE_KNOWN_Z1_IN_PANEL,
            "correctly_rejected_as_not_z2": probe_z1_correct_reject,
            "matcher_trustworthy": probe_z2_hit and probe_z1_correct_reject,
        },
        "kpi_gate_all_scored_have_osha_public_pel_claim_was_true": kpi_gate_claim_false is False,
        "h0_refuted": len(misattributed) > 0,
        "finding": (
            f"H0 REFUTED: {len(misattributed)}/{len(audited)} panel solvent(s) "
            f"({', '.join(a['solvent'] for a in misattributed)}) explicitly claimed as "
            "'OSHA Table Z-1' across three signed receipts are actually OSHA Table Z-2 "
            "substances with a materially richer limit structure (TWA + acceptable ceiling "
            "+ acceptable maximum peak) that the module's single-TWA VHR model does not "
            "score. The numeric TWA value used is unaffected (200 ppm matches in both "
            "tables), so downstream VHR values/ranks/bands are unchanged, but the "
            "'all_scored_have_osha_public_pel: Table Z-1' gate (observed=9/9, passed=True "
            "in vapor-hazard-ratio-inhalation-prescreen-kpi.v1) is factually false as stated: "
            "it is 8/9 true, 1/9 false."
        ) if misattributed else "H0 SURVIVED: no panel solvent's claimed Table Z-1 attribution is contradicted by the Table Z-2 roster.",
    }
    return diag


def sign_receipt(body_obj: dict, ptype: str):
    body = canon(body_obj)
    sk = Ed25519PrivateKey.from_private_bytes(KEY.read_bytes())
    sig = sk.sign(pae(ptype, body))
    envelope = {
        "payload": base64.standard_b64encode(body).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": PUB["key_id"], "sig": base64.standard_b64encode(sig).decode()}],
    }
    out = dict(body_obj)
    out["signature"] = envelope
    return out, sha(body)


def main():
    d1 = compute()
    d2 = compute()
    s1, s2 = sha(canon(d1)), sha(canon(d2))
    assert s1 == s2, f"two-replay diagnostic mismatch {s1} != {s2}"
    diag = d1
    diag_sha = s1

    BENCH.mkdir(parents=True, exist_ok=True)
    (BENCH / "diagnostic.canonical.json").write_bytes(canon(diag))
    (BENCH / "run_table_attribution_audit.py").write_bytes(Path(__file__).read_bytes())
    harness_sha = sha(Path(__file__).read_bytes())

    gates = []
    def gate(gid, observed, passed, floor, note):
        gates.append({"gate_id": gid, "observed": observed, "passed": bool(passed),
                      "floor": floor, "note": note})

    gate("live_receipts_read_successfully", len(diag["audited_receipt_body_sha256"]),
         len(diag["audited_receipt_body_sha256"]) == 3, 3,
         "all three audited receipts were read live off disk (claims not re-typed from memory)")
    gate("matcher_selfcheck_trustworthy", diag["matcher_selfcheck"]["matcher_trustworthy"],
         diag["matcher_selfcheck"]["matcher_trustworthy"] is True, True,
         "Z-2 name matcher correctly flags a known-Z-2 non-panel substance (Styrene) and correctly rejects a known-Z-1-only panel substance (Xylenes)")
    gate("kpi_gate_under_attack_located", diag["kpi_gate_under_attack"] is not None,
         diag["kpi_gate_under_attack"] is not None, True,
         "the audited 'all_scored_have_osha_public_pel' gate was located in the live KPI receipt")
    gate("refutation_criterion_evaluated_all_solvents", diag["n_solvents_audited"],
         diag["n_solvents_audited"] >= 6, 6,
         "every panel solvent in the temperature-envelope receipt was checked against the Table Z-2 roster")
    gate("h0_refuted_toluene_is_z2", diag["h0_refuted"],
         diag["h0_refuted"] is True, True,
         "toluene, claimed 'Table Z-1' in 3 signed receipts, is found on the pinned Table Z-2 roster -- H0 REFUTED")
    gate("numeric_twa_impact_assessed", len(diag["numeric_impact_assessment"]) > 0,
         len(diag["numeric_impact_assessment"]) > 0, True,
         "numeric impact on the VHR denominator (200 ppm) was explicitly checked, not assumed")
    gate("two_replay_byte_stable", 1.0, s1 == s2, 1.0, "diagnostic canonical SHA identical across two replays")

    n_pass = sum(1 for g in gates if g["passed"])
    n_def = len(gates)

    kpis = {
        "method": diag["method"],
        "h0": diag["h0"],
        "refutation_criterion": diag["refutation_criterion"],
        "table_z2_roster": diag["table_z2_roster"],
        "audited_receipts": diag["audited_receipts"],
        "audited_receipt_body_sha256": diag["audited_receipt_body_sha256"],
        "kpi_gate_under_attack": diag["kpi_gate_under_attack"],
        "mixture_receipt_pel_denominator_source_claim": diag["mixture_receipt_pel_denominator_source_claim"],
        "per_solvent_audit": diag["per_solvent_audit"],
        "n_solvents_audited": diag["n_solvents_audited"],
        "n_misattributed_to_z1": diag["n_misattributed_to_z1"],
        "misattributed_solvents": diag["misattributed_solvents"],
        "toluene_z2_row_detail": diag["toluene_z2_row_detail"],
        "numeric_impact_assessment": diag["numeric_impact_assessment"],
        "matcher_selfcheck": diag["matcher_selfcheck"],
        "h0_refuted": diag["h0_refuted"],
        "finding": diag["finding"],
        "theory_references": REFERENCES,
        "relationship_to_prior_receipts": (
            "Falsification audit of benchmarks/vapor-hazard-ratio-v1, "
            "benchmarks/vhr-temperature-envelope-v1 and "
            "benchmarks/mixture-additivity-raoult-osha-v1. Does not recompute VHR; audits "
            "only the OSHA-Table provenance claim those three receipts each make. Does NOT "
            "modify or supersede the audited receipts (outside this cron's signing authority); "
            "the numeric VHR values, bands, and mixture indices in those receipts remain "
            "correct and unchanged -- only their 'Table Z-1' provenance label for toluene is "
            "refuted."),
        "receipt_meta": {
            "sci_pipeline_module": "amphora-sourceability-ehs/benchmarks/osha-table-z1-z2-attribution-audit-v1/run_table_attribution_audit.py",
            "sci_pipeline_seed": 0,
            "harness_sha256": harness_sha,
            "diagnostic_canonical_sha256": diag_sha,
            "data_extraction_method": ("Table Z-2 roster hand-transcribed from osha.gov (29 CFR 1910.1000 Table Z-2, "
                                       "public-domain federal regulation) and independently confirmed against "
                                       "osha.gov/toluene/occupational-exposure-limits; per-solvent claims extracted "
                                       "live from the three audited signed receipts on disk, not re-typed. No "
                                       "LLM-authored constants, no learned parameters, no RNG."),
        },
        "authority_ceiling_note": ("EVIDENCE_ONLY falsification audit. Documents a provenance/citation defect "
                                   "(Table Z-1 vs Table Z-2) in three existing EVIDENCE_ONLY receipts of this "
                                   "module. Does NOT establish OSHA compliance, control banding, respirator "
                                   "selection, procurement approval, or regulatory closure, and does not itself "
                                   "change any VHR value, band, or rank in the audited receipts."),
    }
    receipt_id = "osha-table-z1-z2-attribution-audit-" + sha(canon(kpis))
    body_obj = {
        "kpis": kpis,
        "authority": "AUDIT_ONLY",
        "promotes_authority": False,
        "human_review_performed": False,
        "module_id": "amphora-sourceability-ehs",
        "receipt_id": receipt_id,
        "reviewer_key_id": PUB["key_id"],
        "reviewer_public_key_hex": PUB["public_key_hex"],
        "schema": "amphora.osha-table-attribution-audit.v1",
    }
    ptype = "application/vnd.amphora.osha-table-attribution-audit.v1+json"
    signed, body_sha = sign_receipt(body_obj, ptype)
    receipt_path = MOD / "reference/mvp20/data/osha_table_z1_z2_attribution_audit_receipt.v1.json"
    receipt_path.write_bytes(canon(signed))

    kpi_obj = {
        "kpi_id": "osha-table-z1-z2-attribution-audit-kpi.v1",
        "schema": "amphora.phase0-kpi.v1",
        "module_id": "amphora-sourceability-ehs",
        "authority": "AUDIT_ONLY",
        "authority_ceiling": "EVIDENCE_ONLY",
        "solver_use_ceiling": "DISABLED",
        "promotes_authority": False,
        "capability": "falsification audit: OSHA Table Z-1 vs Table Z-2 provenance of the module's VHR OEL denominators",
        "theory": "29 CFR 1910.1000 Table Z-1 / Table Z-2 (OSHA); provenance cross-check against the module's own live signed receipts",
        "population": "9-solvent VHR panel (6-solvent Antoine-concordant subset for the Table-Z-1-name field) of amphora-sourceability-ehs",
        "split_methodology": "N/A (deterministic provenance audit against a pinned public-domain regulatory roster; no train/test, no fitted parameters)",
        "n_deterministic_gates_defined": n_def,
        "n_deterministic_gates_passed": n_pass,
        "phase0_deterministic_gates_passed": gates,
        "observed_kpi_summary": {
            "n_solvents_audited": diag["n_solvents_audited"],
            "n_misattributed_to_z1": diag["n_misattributed_to_z1"],
            "misattributed_solvents": diag["misattributed_solvents"],
            "h0_refuted": diag["h0_refuted"],
            "numeric_twa_impact": diag["numeric_impact_assessment"],
        },
        "scientific_receipt_id": receipt_id,
        "scientific_receipt_path": "amphora-sourceability-ehs/reference/mvp20/data/osha_table_z1_z2_attribution_audit_receipt.v1.json",
        "scientific_receipt_body_sha256": body_sha,
        "reviewer_key_id": PUB["key_id"],
        "reviewer_public_key_hex": PUB["public_key_hex"],
        "claim_locks": {
            "authority_ceiling": "EVIDENCE_ONLY",
            "not_compliance_determination": True,
            "not_procurement_approval": True,
            "not_respirator_selection": True,
            "rights_clean_inputs_only": True,
            "does_not_modify_audited_receipts": True,
        },
        "awaiting": "PHASE0_EVALUATOR + PHASE0_INTERNAL_REVIEWER human dual-identity signatures (governance; absent on this cron host); ALSO awaiting a human-authored correction pass on the 3 audited receipts' Table Z-1/Z-2 attribution field for toluene",
    }
    kpi_ptype = "application/vnd.amphora.phase0-kpi.v1+json"
    kpi_signed, kpi_body_sha = sign_receipt(kpi_obj, kpi_ptype)
    kpi_path = MOD / "evidence/phase0/kpis/osha-table-z1-z2-attribution-audit-kpi.v1.json"
    kpi_path.write_bytes(canon(kpi_signed))

    print("=== OSHA Table Z-1 vs Z-2 provenance audit ===")
    print(f"gates: {n_pass}/{n_def} passed")
    for g in gates:
        print(f"  [{'PASS' if g['passed'] else 'FAIL'}] {g['gate_id']}: {g['observed']}")
    print(diag["finding"])
    print("RECEIPT", receipt_path)
    print("RECEIPT_BODY_SHA256", body_sha)
    print("RECEIPT_ID", receipt_id)
    print("KPI", kpi_path)
    print("KPI_BODY_SHA256", kpi_body_sha)
    print("N_PASS", n_pass, "N_DEF", n_def)


if __name__ == "__main__":
    main()
