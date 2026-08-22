#!/usr/bin/env python3
"""R-A04 interactive repair: supersede (byte-intact) the three signed
amphora-sourceability-ehs receipts that misattribute toluene's OSHA PEL to
Table Z-1 (it is a Table Z-2 substance) with ONE corrected superseding
receipt. No existing artifact is modified or deleted. DSSE Ed25519 signed
with the phase0 evaluator key; two-replay sha256 gated; self-verified.

Runs SYNCHRONOUSLY. Writes ONLY under:
  amphora-sourceability-ehs/evidence/phase0/repairs/R-A04/{work,done}/
  amphora-sourceability-ehs/evidence/phase0/kpis/RETRACTION-INDEX.md (append)
"""
import base64
import hashlib
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-sourceability-ehs"
REPAIR = MOD / "evidence/phase0/repairs/R-A04"
WORK = REPAIR / "work"
DONE = REPAIR / "done"
SEED = Path("/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed")
TRUST = ROOT / "config/phase0-trust-store.v1.json"

REPAIR_ITEM = "R-A04"
REPAIR_MODE = "interactive-2026-08-03"
REPAIR_DATE = "2026-08-03"

# --- Superseded receipts (byte-intact) with pinned pre-repair sha256. ------
SUPERSEDED = [
    {
        "superseded_path": "amphora-sourceability-ehs/reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json",
        "superseded_sha256": "24b2311523613eab44f6b356748aba6574768e3ac502491009ef3af552d8f5b4",
        "superseded_deleted_or_modified": False,
        "reason": "kpis.pel_denominator_source and kpis.solvent_cards_ranked[toluene].osha_pel_table_z1_name attribute toluene's 200 ppm PEL to OSHA 29 CFR 1910.1000 Table Z-1; toluene is codified in Table Z-2 (TWA 200 ppm + acceptable ceiling 300 ppm + acceptable maximum peak 500 ppm <=10 min). Provenance/citation defect only; every numeric value in the receipt is unaffected.",
    },
    {
        "superseded_path": "amphora-sourceability-ehs/reference/mvp20/data/vhr_temperature_envelope_inhalation_prescreen_receipt.v1.json",
        "superseded_sha256": "33d8a165ec537f31a5f4c1b19ecaef0607034a998c89b07dff62fea281f4872a",
        "superseded_deleted_or_modified": False,
        "reason": "kpis.solvent_envelopes[toluene].osha_pel_table_z1_name ('Toluene') attributes the 200 ppm PEL denominator to OSHA Table Z-1; toluene is a Table Z-2 substance. Provenance/citation defect only; every numeric value in the receipt is unaffected.",
    },
    {
        "superseded_path": "amphora-sourceability-ehs/reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json",
        "superseded_sha256": "70c406e5be98144edb85d2a376914c1315ca42281bec1f20689a7e5ba4814441",
        "superseded_deleted_or_modified": False,
        "reason": "kpis.pel_denominator_source claims all PEL denominators come from OSHA 29 CFR 1910.1000 Table Z-1; the toluene denominator (200 ppm) is actually the Table Z-2 TWA. Provenance/citation defect only; every numeric value in the receipt is unaffected.",
    },
]

REFUTING = {
    "audit_receipt": {
        "path": "amphora-sourceability-ehs/reference/mvp20/data/osha_table_z1_z2_attribution_audit_receipt.v1.json",
        "sha256": "1001f14d85dd064e85a3ec57e6b9e4981676720f82c6eb0435bf4695c35547a9",
    },
    "audit_kpi": {
        "path": "amphora-sourceability-ehs/evidence/phase0/kpis/osha-table-z1-z2-attribution-audit-kpi.v1.json",
        "sha256": "47863834bce63443243660895a1ce83739dc4b2eb3025ed74b0ff7cf2c903611",
    },
}

VHR_KPI_PATH = MOD / "evidence/phase0/kpis/vapor-hazard-ratio-inhalation-prescreen-kpi.v1.json"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


def pae(t: str, body: bytes) -> bytes:
    return (b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
            str(len(body)).encode() + b" " + body)


def load_seed(p: Path) -> bytes:
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


def fsha(p: Path) -> str:
    return sha(p.read_bytes())


def main():
    # ---- 0. Pre-hash gate: superseded + refuting files must match pins. ----
    pre = {}
    for s in SUPERSEDED:
        p = ROOT / s["superseded_path"]
        h = fsha(p)
        assert h == s["superseded_sha256"], f"PRE-HASH MISMATCH {p}: {h}"
        pre[s["superseded_path"]] = h
    for k, r in REFUTING.items():
        h = fsha(ROOT / r["path"])
        assert h == r["sha256"], f"REFUTING-HASH MISMATCH {r['path']}: {h}"

    # ---- 1. Load refuting audit evidence (roster read live, not re-typed). -
    audit = json.loads((ROOT / REFUTING["audit_receipt"]["path"]).read_text())
    roster = audit["kpis"]["table_z2_roster"]
    z2_row = audit["kpis"]["toluene_z2_row_detail"]
    assert len(roster) == 21 and "Toluene" in roster
    assert z2_row["table"] == "Z-2" and z2_row["8hr_twa_ppm"] == 200
    assert z2_row["acceptable_ceiling_concentration_ppm"] == 300
    assert z2_row["acceptable_maximum_peak_above_ceiling_ppm"] == 500
    assert z2_row["acceptable_maximum_peak_max_duration_min"] == 10

    def in_z2(name: str) -> bool:
        n = (name or "").strip().lower()
        return any(n == z.strip().lower() for z in roster)

    # ---- 2. RE-ATTACK: re-run the refuting receipt's check live. ----------
    vhr = json.loads((ROOT / SUPERSEDED[0]["superseded_path"]).read_text())
    env = json.loads((ROOT / SUPERSEDED[1]["superseded_path"]).read_text())
    mix = json.loads((ROOT / SUPERSEDED[2]["superseded_path"]).read_text())
    vhr_kpi = json.loads(VHR_KPI_PATH.read_text())

    body_shas = {}
    for name, doc in (("vapor_hazard_ratio_receipt", vhr),
                      ("vhr_temperature_envelope_receipt", env),
                      ("mixture_additivity_receipt", mix)):
        body_shas[name] = sha(base64.standard_b64decode(doc["signature"]["payload"]))

    # matcher self-check probes (same as refuting harness)
    probe_z2 = in_z2("Styrene")           # known Z-2, not in panel -> True
    probe_z1 = not in_z2("Xylenes")       # known Z-1-only panel name -> True
    matcher_ok = probe_z2 and probe_z1

    # live per-solvent claims: envelope receipt (6 solvents)
    env_audit = []
    for e in env["kpis"]["solvent_envelopes"]:
        z1n = e.get("osha_pel_table_z1_name")
        hit = in_z2(z1n) or in_z2(e["solvent"].replace("_", " "))
        env_audit.append({"solvent": e["solvent"], "claimed_z1_name": z1n,
                          "osha_pel_8h_twa_ppm": e.get("osha_pel_8h_twa_ppm"),
                          "actually_in_table_z2": hit,
                          "attribution_correct": not hit})
    # live per-solvent claims: VHR receipt (9 solvents)
    vhr_audit = []
    for c in vhr["kpis"]["solvent_cards_ranked"]:
        z1n = c.get("osha_pel_table_z1_name")
        hit = in_z2(z1n) or in_z2(c["solvent"].replace("_", " "))
        vhr_audit.append({"solvent": c["solvent"], "claimed_z1_name": z1n,
                          "osha_pel_8h_twa_ppm": c.get("osha_pel_8h_twa_ppm"),
                          "actually_in_table_z2": hit,
                          "attribution_correct": not hit})

    env_mis = [a["solvent"] for a in env_audit if not a["attribution_correct"]]
    vhr_mis = [a["solvent"] for a in vhr_audit if not a["attribution_correct"]]
    assert env_mis == ["toluene"], f"re-attack (envelope) expected [toluene], got {env_mis}"
    assert vhr_mis == ["toluene"], f"re-attack (vhr) expected [toluene], got {vhr_mis}"
    assert matcher_ok, "matcher self-check failed"

    tol_vhr = next(c for c in vhr["kpis"]["solvent_cards_ranked"] if c["solvent"] == "toluene")
    tol_env = next(e for e in env["kpis"]["solvent_envelopes"] if e["solvent"] == "toluene")
    assert tol_vhr["osha_pel_8h_twa_ppm"] == z2_row["8hr_twa_ppm"] == 200
    assert tol_env["osha_pel_8h_twa_ppm"] == 200

    kpi_gate = next(g for g in vhr_kpi["phase0_deterministic_gates_passed"]
                    if g["gate_id"] == "all_scored_have_osha_public_pel")

    reattack = {
        "method": "re-run of the refuting osha_table_z1_z2_attribution_audit check: Table Z-2 roster (21 rows) read live from the refuting audit receipt on disk (not re-typed); per-solvent 'Table Z-1' claims extracted live from the three superseded receipts on disk; case-insensitive exact-name membership matcher with two self-check probes",
        "roster_source": REFUTING["audit_receipt"]["path"],
        "roster_rows": len(roster),
        "matcher_selfcheck": {
            "known_z2_substance_not_in_panel": "Styrene",
            "correctly_flagged_z2": probe_z2,
            "known_z1_only_panel_substance": "Xylenes",
            "correctly_rejected_as_not_z2": probe_z1,
            "matcher_trustworthy": matcher_ok,
        },
        "observed": {
            "envelope_receipt_solvents_audited": len(env_audit),
            "envelope_receipt_misattributed_to_z1": env_mis,
            "vhr_receipt_solvents_audited": len(vhr_audit),
            "vhr_receipt_misattributed_to_z1": vhr_mis,
            "toluene_actually_in_table_z2": True,
            "toluene_twa_used_ppm": tol_vhr["osha_pel_8h_twa_ppm"],
            "toluene_z2_twa_ppm": z2_row["8hr_twa_ppm"],
            "twa_numerically_unaffected": True,
            "mixture_receipt_pel_denominator_source_still_claims_z1": "Table Z-1" in mix["kpis"]["pel_denominator_source"],
            "vhr_kpi_gate_under_attack": kpi_gate,
            "audited_receipt_body_sha256": body_shas,
        },
        "result": "REFUTATION REPRODUCED against the live superseded receipts: toluene (claimed 'Table Z-1' in all three) is on the 21-row 29 CFR 1910.1000 Table Z-2 roster; the other 5/6 envelope-panel and 8/9 VHR-panel attributions are correctly Z-1-only. The corrected attribution in THIS receipt (toluene = Table Z-2) is consistent with the re-run: this receipt itself passes the audit's refutation criterion by no longer claiming Z-1 for toluene.",
    }

    # cross-check against refuting audit's own recorded observations
    assert audit["kpis"]["misattributed_solvents"] == ["toluene"]
    assert audit["kpis"]["audited_receipt_body_sha256"]["vhr_temperature_envelope_receipt"] == body_shas["vhr_temperature_envelope_receipt"]
    assert audit["kpis"]["audited_receipt_body_sha256"]["mixture_additivity_receipt"] == body_shas["mixture_additivity_receipt"]

    # ---- 3. Build the superseding payload (twice, for two-replay gate). ---
    def build_payload():
        return {
            "schema": "amphora.repair.osha-table-z2-attribution-correction.v1",
            "receipt_id": "r-a04-osha-table-z2-attribution-correction-v1",
            "module_id": "amphora-sourceability-ehs",
            "repair_item": REPAIR_ITEM,
            "repair_mode": REPAIR_MODE,
            "date": REPAIR_DATE,
            "generated_on_host": "xbabe2",
            "authority": "AUDIT_ONLY",
            "authority_ceiling": "EVIDENCE_ONLY",
            "phase": "PRE_PHASE_0",
            "human_review_performed": False,
            "modifies_existing_receipts": False,
            "modifies_manifest": False,
            "promotes_authority": False,
            "flips_scientific_readiness": False,
            "trust_anchored_in_phase0_store": True,
            "claim": (
                "SUPERSEDING CORRECTION covering three signed amphora-sourceability-ehs "
                "receipts (superseded byte-intact, never modified or deleted) that "
                "attribute toluene's OSHA PEL to 29 CFR 1910.1000 Table Z-1. CORRECTED "
                "ATTRIBUTION: toluene (CAS 108-88-3) is codified in 29 CFR 1910.1000 "
                "Table Z-2 with an 8-hr TWA of 200 ppm, an acceptable ceiling of 300 ppm, "
                "and an acceptable maximum peak of 500 ppm for at most 10 minutes in any "
                "8-hr shift (29 CFR 1910.1000(b)(2)). The Table Z-2 TWA (200 ppm) is "
                "numerically identical to the TWA the three receipts used as the VHR "
                "denominator, so EVERY numeric VHR value, screening band, rank, "
                "temperature-envelope amplification, and mixture-hazard index in the "
                "superseded receipts is UNCHANGED; only the table attribution (and the "
                "'all Z-1' provenance language quoted below) is corrected. LIMITATION "
                "(stated, still open): the module's single-TWA VHR framework does NOT "
                "model Table Z-2's acceptable-ceiling (300 ppm) or acceptable-maximum-"
                "peak (500 ppm, <=10 min) limit structure for toluene; a short, intense "
                "toluene exposure inside the 200 ppm TWA budget could breach the Z-2 "
                "ceiling/peak structure while the VHR band is unchanged. That gap "
                "remains unmodeled by this repair, which corrects provenance only."),
            "supersedes": SUPERSEDED,
            "refuted_by": {
                "refuting_receipt": REFUTING["audit_receipt"],
                "refuting_kpi": REFUTING["audit_kpi"],
                "refutation_summary": "H0 ('every OEL denominator in the module's VHR family is codified in 29 CFR 1910.1000 Table Z-1') REFUTED 2026-08-02: toluene is a Table Z-2 substance; the 'all_scored_have_osha_public_pel: Table Z-1' gate note (observed 9/9) is actually 8/9 true, 1/9 false.",
            },
            "corrected_attribution": {
                "solvent": "toluene",
                "cas": "108-88-3",
                "pubchem_cid": 1140,
                "incorrect_claim_as_signed": {
                    "vapor_hazard_ratio_receipt": {
                        "kpis.pel_denominator_source": vhr["kpis"]["pel_denominator_source"],
                        "kpis.solvent_cards_ranked[toluene].osha_pel_table_z1_name": tol_vhr["osha_pel_table_z1_name"],
                    },
                    "vhr_temperature_envelope_receipt": {
                        "kpis.solvent_envelopes[toluene].osha_pel_table_z1_name": tol_env["osha_pel_table_z1_name"],
                    },
                    "mixture_additivity_receipt": {
                        "kpis.pel_denominator_source": mix["kpis"]["pel_denominator_source"],
                    },
                },
                "corrected_claim": "toluene's OSHA PEL is codified in 29 CFR 1910.1000 TABLE Z-2 (not Table Z-1): 8-hr TWA 200 ppm; acceptable ceiling concentration 300 ppm; acceptable maximum peak above ceiling 500 ppm for a maximum duration of 10 minutes in an 8-hr shift (29 CFR 1910.1000(b)(2)). Still a public-domain U.S. federal-regulation limit, so the module's rights-clean denominator policy is unaffected.",
                "corrected_table_z2_row": z2_row,
                "derivation": {
                    "step_1": "Pinned 21-row OSHA 29 CFR 1910.1000 Table Z-2 substance roster read live from the refuting audit receipt (hand-transcribed there from osha.gov, public-domain federal regulation; confirmed against osha.gov/toluene/occupational-exposure-limits).",
                    "step_2": "Per-solvent claimed-Z-1 substance names extracted live from the three superseded signed receipts on disk (osha_pel_table_z1_name fields and pel_denominator_source strings; not re-typed).",
                    "step_3": "Case-insensitive exact-name membership check of each claimed name against the Z-2 roster; matcher validated by two self-check probes (Styrene, a known Z-2 non-panel substance, flagged; Xylenes, a known Z-1-only panel name, rejected).",
                    "step_4": "'Toluene' matches Table Z-2 roster row 'Toluene' -> attribution Z-1 is FALSE for toluene; all other claimed names (Methyl alcohol, 2-Butanone (MEK), Ethylbenzene, Xylenes, Butyl alcohol, and the remaining VHR-panel names) do not match any Z-2 row -> their Z-1 attributions stand.",
                    "step_5": "Numeric consequence: Table Z-2 TWA for toluene = 200 ppm = the TWA used in all three receipts (checked, not assumed) -> zero numeric impact; ceiling 300 ppm / peak 500 ppm <=10 min are additional Z-2 limits the single-TWA model does not score -> recorded as an open limitation.",
                    "references": audit["kpis"]["theory_references"],
                },
                "corrected_correct_attributions_unchanged": "8/9 VHR-panel and 5/6 envelope-panel Table Z-1 attributions were verified correct in the refuting audit and re-verified in this repair's re-attack; they are NOT modified by this correction.",
            },
            "numeric_values_unchanged": {
                "statement": "EVERY numeric value in the three superseded receipts is UNCHANGED by this correction: all VHR values, saturated-vapor concentrations, screening bands, ranks, worst/lowest-actor calls, VP-uncertainty separability counts, temperature-envelope profiles and amplifications, band-migration findings, mixture hazard indices, crossover mass fractions, and molar-mass records. The superseded files are byte-intact (sha256 verified identical before and after this repair). Basis: the corrected Table Z-2 TWA for toluene (200 ppm) is numerically identical to the denominator already used.",
                "superseded_file_sha256": {s["superseded_path"]: s["superseded_sha256"] for s in SUPERSEDED},
                "superseded_signed_body_sha256": body_shas,
                "spot_anchors_unchanged": {
                    "vhr.toluene.vapor_hazard_ratio_25C": tol_vhr["vapor_hazard_ratio"],
                    "vhr.toluene.rank": tol_vhr["rank"],
                    "vhr.toluene.screening_band": tol_vhr["screening_band"],
                    "vhr.aggregate.worst_actor_solvent": vhr["kpis"]["aggregate"]["worst_actor_solvent"],
                    "vhr.aggregate.worst_actor_vhr": vhr["kpis"]["aggregate"]["worst_actor_vhr"],
                    "envelope.toluene.amplification_15to40": tol_env["amplification_15to40"],
                    "envelope.toluene.band_migrates_in_envelope": tol_env["band_migrates_in_envelope"],
                    "mixture.aggregate.crossover_predicted_mass_fraction_25C": mix["kpis"]["aggregate"]["crossover_predicted_mass_fraction_25C"],
                },
            },
            "stated_limitation_z2_ceiling_peak_unmodeled": {
                "limitation": "The single-TWA VHR framework in this module does not model OSHA Table Z-2's acceptable ceiling concentration (toluene: 300 ppm) or acceptable maximum peak above ceiling (toluene: 500 ppm, <=10 min per 8-hr shift, 29 CFR 1910.1000(b)(2)). Short, intense exposures within the 200 ppm TWA budget (e.g. during spray application) could breach the ceiling/peak structure while VHR-band screening is unchanged. This repair corrects the table attribution and DISCLOSES this gap; it does NOT close it. Any future ceiling/peak-aware scoring must be a new, separately signed receipt.",
                "status": "OPEN_UNMODELED",
            },
            "reattack": reattack,
            "mission_prose_check": {
                "file": "amphora-sourceability-ehs/docs/mission.md",
                "z1_claim_found": False,
                "action": "no edit required: grep for 'Z-1'/'Z-2'/'Table Z' over docs/mission.md returned no matches; front-matter untouched per repair rules",
            },
            "authority_ceiling_note": "EVIDENCE_ONLY superseding correction. Does NOT establish OSHA compliance, control banding, respirator selection, procurement approval, or regulatory closure; does not modify, delete, or re-sign the superseded receipts, the refuting audit artifacts, the ledger, any mission front-matter, or the master manifest; does not promote module authority or flip scientific_readiness.",
            "reproducibility": {
                "two_replay_sha256_gate": "PASS",
                "replay_method": "payload dict constructed twice from the same live on-disk inputs, serialized twice with json.dumps(sort_keys=True, separators=(',',':')), asserted byte-equal; sha256 of the canonical bytes recorded (the exact bytes signed)",
            },
        }

    p1 = build_payload()
    p2 = build_payload()
    b1 = canon(p1)
    b2 = canon(p2)
    assert b1 == b2, "two-replay bytes differ"
    payload_sha = sha(b1)

    # embed the two-replay sha and re-canonicalize (deterministic, so re-run twice again)
    p1["reproducibility"]["canonical_payload_sha256_pre_embed"] = payload_sha
    p2["reproducibility"]["canonical_payload_sha256_pre_embed"] = payload_sha
    body1 = canon(p1)
    body2 = canon(p2)
    assert body1 == body2, "two-replay bytes differ after embed"
    body_sha = sha(body1)
    body = body1

    # ---- 4. Sign (DSSE Ed25519, phase0 evaluator key, trust-anchored). ----
    seed = load_seed(SEED)
    sk = Ed25519PrivateKey.from_private_bytes(seed)
    pub = sk.public_key().public_bytes_raw()
    key_id = f"phase0-evaluator-{sha(pub)}"
    assert key_id.startswith("phase0-evaluator-3ef6b35"), key_id
    trust = json.loads(TRUST.read_text())
    pinned = {k.get("role"): k.get("key_id") for k in trust["keys"]}
    assert key_id == pinned.get("PHASE0_EVALUATOR"), "evaluator key not pinned in phase0 trust store"

    ptype = "application/vnd.amphora.repair.osha-table-z2-attribution-correction+json"
    sig = sk.sign(pae(ptype, body))
    envelope = {
        "payload": base64.standard_b64encode(body).decode(),
        "payloadType": ptype,
        "signatures": [{"keyid": key_id, "sig": base64.standard_b64encode(sig).decode()}],
    }
    receipt = {
        "evaluator_key_id": key_id,
        "evaluator_public_key_hex": pub.hex(),
        "signature": envelope,
    }

    DONE.mkdir(parents=True, exist_ok=True)
    WORK.mkdir(parents=True, exist_ok=True)
    out = DONE / "r-a04-osha-table-z2-attribution-correction-receipt.v1.dsse.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

    # ---- 5. SELF-VERIFY from disk. ----------------------------------------
    reloaded = json.loads(out.read_text())
    env2 = reloaded["signature"]
    rbody = base64.standard_b64decode(env2["payload"])
    assert sha(rbody) == body_sha, "reloaded payload sha mismatch"
    rp = json.loads(rbody)
    assert rp["repair_item"] == REPAIR_ITEM and rp["repair_mode"] == REPAIR_MODE
    assert env2["signatures"][0]["keyid"].startswith("phase0-evaluator-3ef6b35")
    pub2 = Ed25519PublicKey.from_public_bytes(
        Ed25519PrivateKey.from_private_bytes(load_seed(SEED)).public_key().public_bytes_raw())
    pub2.verify(base64.standard_b64decode(env2["signatures"][0]["sig"]),
                pae(env2["payloadType"], rbody))
    self_verified = True

    # ---- 6. Post-hash gate: superseded + refuting files still byte-intact.
    post = {}
    intact = True
    for s in SUPERSEDED:
        h = fsha(ROOT / s["superseded_path"])
        post[s["superseded_path"]] = h
        intact = intact and (h == s["superseded_sha256"])
    for k, r in REFUTING.items():
        intact = intact and (fsha(ROOT / r["path"]) == r["sha256"])
    assert intact, "a superseded/refuting file changed during repair"

    # ---- 7. Work artifacts. ------------------------------------------------
    (WORK / "reattack_diagnostic.json").write_text(
        json.dumps(reattack, indent=2, sort_keys=True))
    (WORK / "repair_run_log.json").write_text(json.dumps({
        "repair_item": REPAIR_ITEM,
        "repair_mode": REPAIR_MODE,
        "date": REPAIR_DATE,
        "pre_sha256": pre,
        "post_sha256": post,
        "byte_intact_after": intact,
        "canonical_payload_sha256": body_sha,
        "two_replay_sha256_gate": "PASS",
        "receipt_path": str(out.relative_to(ROOT)),
        "receipt_file_sha256": fsha(out),
        "evaluator_key_id": key_id,
        "self_verified": self_verified,
    }, indent=2, sort_keys=True))

    # ---- 8. RETRACTION-INDEX append. --------------------------------------
    idx = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
    section = (
        "\n## R-A04 (2026-08-03) - toluene OSHA table attribution corrected Z-1 -> Z-2\n\n"
        "| claim | refuted-by receipt | superseded-by | date |\n"
        "|---|---|---|---|\n")
    refby = (REFUTING["audit_receipt"]["path"].replace("amphora-sourceability-ehs/", "") +
             " (+ kpi: " + REFUTING["audit_kpi"]["path"].replace("amphora-sourceability-ehs/", "") + ")")
    supby = "evidence/phase0/repairs/R-A04/done/r-a04-osha-table-z2-attribution-correction-receipt.v1.dsse.json"
    claims = [
        ("toluene PEL 'OSHA Table Z-1' in kpis.pel_denominator_source + solvent_cards_ranked[toluene]", "reference/mvp20/data/vapor_hazard_ratio_inhalation_prescreen_receipt.v1.json"),
        ("toluene PEL 'OSHA Table Z-1' in kpis.solvent_envelopes[toluene].osha_pel_table_z1_name", "reference/mvp20/data/vhr_temperature_envelope_inhalation_prescreen_receipt.v1.json"),
        ("all mixture PEL denominators 'OSHA Table Z-1' in kpis.pel_denominator_source", "reference/mvp20/data/mixture_additivity_raoult_osha_inhalation_prescreen_receipt.v1.json"),
    ]
    for claim, path in claims:
        section += f"| {claim} (in {path}; superseded byte-intact, toluene is Table Z-2: TWA 200 ppm + ceiling 300 ppm + peak 500 ppm/10 min, numerics unchanged) | {refby} | {supby} | 2026-08-03 |\n"
    if idx.exists():
        prev = idx.read_text()
        if "## R-A04 " not in prev:
            idx.write_text(prev + section)
    else:
        idx.write_text("# amphora-sourceability-ehs RETRACTION INDEX\n\n"
                       "Refuted claims in signed artifacts of this module, the refuting "
                       "receipt, and the superseding correction. Superseded artifacts are "
                       "kept byte-intact; nothing is rewritten.\n" + section)

    print(json.dumps({
        "ok": True,
        "receipt": str(out),
        "receipt_file_sha256": fsha(out),
        "canonical_payload_sha256": body_sha,
        "evaluator_key_id": key_id,
        "self_verified": self_verified,
        "byte_intact_after": intact,
        "post_sha256": post,
        "retraction_index": str(idx),
    }, indent=2))


if __name__ == "__main__":
    main()
