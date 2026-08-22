#!/usr/bin/env python3
"""R-A01 interactive repair harness (repair_mode interactive-2026-08-03).

Module: amphora-ingredient-library. AUDIT_ONLY. Covers TWO refuted defects:

Defect 1 (REFUTED 2026-08-02T22:06 by phase0-mission-evidence-parity-v1):
  mission.md's "Honest current state" cited a stale result.v1.json SHA-256
  (2afb9213...) and a Phase-0 KPI receipt path absent from the live tree.
  Fix: re-run the real Rust Phase-0 harness TWICE (independent processes,
  same command as the parity receipt), confirm the byte-stable live sha,
  correct mission.md PROSE citations (front-matter untouched).

Defect 2 (REFUTED 2026-08-03T14:06 by eew-solid-band-mislabel-gap-v1):
  constant-crosscheck-v1 Check-1's solid_type1_epoxy EEW admissibility band
  [383.5, 667.8] is 2.84x wider than the Hexion HCD-4022 manufacturer TDS
  band; 4/4 gap-zone probes pass undetected. Fix: supersede (never rewrite)
  with the TDS band read from the refuting receipt's SIGNED PAYLOAD BYTES,
  and re-attack: the same 4 probes must now be rejected.

SUPERSEDE-NEVER-REWRITE: this script modifies ONLY docs/mission.md prose.
It never touches any signed artifact, the falsification ledger, mission
front-matter, the master manifest, or /home/ubuntu/amphora-cron. The Rust
harness re-execution regenerates result.v1.json byte-identically (asserted).
"""
import base64, hashlib, json, re, subprocess, sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-ingredient-library"
WORK = MOD / "evidence/phase0/repairs/R-A01/work"
MISSION = MOD / "docs/mission.md"
RESULT = MOD / "evidence/phase0/benchmark/result.v1.json"
FACTS = MOD / "reference/mvp20/data/facts.json"
CC_DIR = MOD / "evidence/audit/constant-crosscheck-v1"
CC_RECEIPT = CC_DIR / "constant-crosscheck-receipt.v1.dsse.json"
GAP_RECEIPT = (MOD / "evidence/audit/eew-solid-band-mislabel-gap-v1"
               / "eew-solid-band-mislabel-gap-receipt.v1.dsse.json")
PARITY_RECEIPT = (MOD / "evidence/audit/phase0-mission-evidence-parity-v1"
                  / "phase0-mission-evidence-parity-receipt.v1.dsse.json")

STALE_SHA = "2afb9213103d34e7754a6699d3df9ee113ea08ba679506331d01cdc6ca9dd732"
EXPECTED_LIVE_SHA = "06229682503e25a26da0391dac29c4f44e8ad46948c4b9ad77f76101b109fc1e"

# sha256 baselines recorded interactively BEFORE this repair started
BEFORE = {
    "mission.md": "01f55dfa865ef8eb8516ef1d1ad9a3fa52768d28a0f2a7dcd656fe543f9cd185",
    "result.v1.json": EXPECTED_LIVE_SHA,
    "constant-crosscheck-receipt.v1.dsse.json":
        "85b207a9f5d0c2d07b1d2b78c8635250d8d29cd3402ff2ce546942f61d28a50f",
    "constant-crosscheck diagnostic.canonical.json":
        "25e441b56901d126b473386af61b22d3b6823a6716d0584ca1b57518e93d9e68",
    "run_crosscheck.py":
        "ea99c0a2eefbc5e3cc36c64ada54c131d2e38833f6821a65ad3f09f68e81aedb",
    "eew-solid-band-mislabel-gap-receipt.v1.dsse.json":
        "31e7346be117f7152198755df3203717fdef41e3a69767ae94c065b9759231bc",
    "phase0-mission-evidence-parity-receipt.v1.dsse.json":
        "f15a15693e51dca8f707e77671c97af3f0d7aaf7ede43f1f431854ea127e49d2",
    "facts.json": "0af2456a443692093fc4a89174e5cc87da86323108b14c3aa20cc3af159f06fb",
}

# ---- Check-1 structural constants, replayed VERBATIM from run_crosscheck.py
M0 = 340.42     # g/mol  C21H24O4  bisphenol-A diglycidyl ether
MREP = 284.35   # g/mol  C18H20O3  epoxy repeat unit
FUNC = 2
EEW0 = M0 / FUNC
N_LIQUID_MAX = 0.20
EEW_LIQ_HI = (M0 + N_LIQUID_MAX * MREP) / FUNC


def sha(b):
    return hashlib.sha256(b).hexdigest()


def eew_to_n(eew):
    return (FUNC * eew - M0) / MREP


OLD_PROSE = """`evidence/phase0/benchmark/result.v1.json` (SHA-256
`2afb9213103d34e7754a6699d3df9ee113ea08ba679506331d01cdc6ca9dd732`). The
Phase-0 KPI receipt lives at
`evidence/phase0/kpis/ingredient-library-ledger-quarantine-kpi.v1.json`.
"""

NEW_PROSE = """`evidence/phase0/benchmark/result.v1.json` (SHA-256
`06229682503e25a26da0391dac29c4f44e8ad46948c4b9ad77f76101b109fc1e`). This
citation was corrected on 2026-08-03 by repair R-A01 after the signed
`evidence/audit/phase0-mission-evidence-parity-v1` audit refuted the
previously cited stale result hash (preserved verbatim inside that receipt
and inside the R-A01 done-receipt); two fresh independent re-executions of
the Rust Phase-0 harness reproduce `result.v1.json` byte-identically at the
SHA-256 cited above. The Phase-0 KPI receipt formerly cited at
`evidence/phase0/kpis/ingredient-library-ledger-quarantine-kpi.v1.json` is
not present in the live tree: it was superseded with reason
`STALE_UNSIGNED_PREPARATION_REISSUE` and survives only under
`evidence/superseded/supersession-6aba291aa333b4c3ae40d584ebe0fe2955e6949a33cb2506a5e7113021fff1c1/phase0/kpis/ingredient-library-ledger-quarantine-kpi.v1.json`;
see `evidence/phase0/repairs/R-A01/done/` for the signed supersession trail.
"""


def front_matter(text):
    # front-matter = everything from the opening --- fence through the closing
    # --- fence (first two fences of the file); NEVER modified.
    parts = text.split("---\n")
    assert text.startswith("---\n") and len(parts) >= 3, "front-matter fences missing"
    return "---\n" + parts[1] + "---\n"


def fix_mission():
    text = MISSION.read_text()
    fm_before = front_matter(text)
    if OLD_PROSE in text:
        assert BEFORE["mission.md"] == sha(text.encode()), \
            "mission.md drifted from recorded baseline"
        text = text.replace(OLD_PROSE, NEW_PROSE, 1)
        MISSION.write_text(text)
    else:
        assert NEW_PROSE in text, "mission.md has neither old nor corrected prose"
    after = MISSION.read_text()
    assert front_matter(after) == fm_before, "FRONT-MATTER CHANGED - forbidden"
    assert STALE_SHA[:8] not in after, "stale hash prefix still present in mission prose"
    assert NEW_PROSE in after
    # sha_before is the interactively recorded pre-repair baseline so that the
    # second replay (mission already repaired) reports identical bytes.
    return BEFORE["mission.md"], sha(after.encode()), fm_before


def run_cargo_test():
    # Same re-execution command as recorded/used by the signed
    # phase0-mission-evidence-parity-v1 receipt's harness (flock timeout
    # widened for a possibly-active concurrent cron fire).
    env_cmd = (
        'export PATH="$HOME/.cargo/bin:$PATH"; cd '
        + str(ROOT)
        + " && flock -w 240 .cron.lock -c "
        "'cargo test --workspace --locked --package amphora-formulation-capabilities "
        "--test ingredient_library_phase0_kpi 2>&1'"
    )
    proc = subprocess.run(["bash", "-c", env_cmd], capture_output=True, text=True, timeout=580)
    ok = "test result: ok. 1 passed" in proc.stdout
    m = re.search(r"test result: .*$", proc.stdout, re.MULTILINE)
    stable = m.group(0) if m else None
    if stable:
        stable = re.sub(r"; finished in [0-9.]+s", "", stable)
    return ok, stable, proc.stdout


def main():
    WORK.mkdir(parents=True, exist_ok=True)

    # ---- baseline integrity of everything this repair supersedes/relies on
    # (mission.md is checked inside fix_mission: strict baseline before the
    # prose edit, corrected-prose recognition on idempotent replays)
    watched = {
        "result.v1.json": RESULT,
        "constant-crosscheck-receipt.v1.dsse.json": CC_RECEIPT,
        "constant-crosscheck diagnostic.canonical.json": CC_DIR / "diagnostic.canonical.json",
        "run_crosscheck.py": CC_DIR / "run_crosscheck.py",
        "eew-solid-band-mislabel-gap-receipt.v1.dsse.json": GAP_RECEIPT,
        "phase0-mission-evidence-parity-receipt.v1.dsse.json": PARITY_RECEIPT,
        "facts.json": FACTS,
    }
    for name, p in watched.items():
        got = sha(p.read_bytes())
        assert got == BEFORE[name], f"PRE-CHECK drift on {name}: {got}"

    # ================= DEFECT 1 =================
    mission_sha_before, mission_sha_after, _fm = fix_mission()

    run1_ok, run1_tail, run1_out = run_cargo_test()
    (WORK / "run1.stdout.txt").write_text(run1_out)
    run1_sha = sha(RESULT.read_bytes())
    run2_ok, run2_tail, run2_out = run_cargo_test()
    (WORK / "run2.stdout.txt").write_text(run2_out)
    run2_sha = sha(RESULT.read_bytes())

    assert run1_ok and run2_ok, "harness run failed"
    assert run1_sha == run2_sha == EXPECTED_LIVE_SHA, \
        f"harness byte-agreement FAILED: {run1_sha} {run2_sha}"

    # re-attack defect 1: re-run the parity receipt's own citation checks
    mission_text = MISSION.read_text()
    m = re.search(
        r"evidence/phase0/benchmark/result\.v1\.json`\s*\(SHA-256\s*\n?`([0-9a-f]{64})`\)",
        mission_text,
    )
    cited_now = m.group(1) if m else None
    kpi_path = "evidence/phase0/kpis/ingredient-library-ledger-quarantine-kpi.v1.json"
    superseded_kpi = ("evidence/superseded/supersession-6aba291aa333b4c3ae40d584ebe0fe295"
                     "5e6949a33cb2506a5e7113021fff1c1/phase0/kpis/"
                     "ingredient-library-ledger-quarantine-kpi.v1.json")
    d1_reattack = {
        "method": ("Replay of phase0-mission-evidence-parity-v1's own checks against the "
                   "repaired mission.md: regex-extract the cited result sha (same regex), "
                   "compare to two fresh independent cargo-test re-executions; grep for the "
                   "stale hash; verify the superseded KPI receipt location is disclosed."),
        "mission_cited_result_sha256": cited_now,
        "live_run1_sha256": run1_sha,
        "live_run2_sha256": run2_sha,
        "two_runs_byte_agree": run1_sha == run2_sha,
        "mission_citation_matches_live_result": cited_now == run1_sha,
        "stale_hash_absent_from_mission_prose": STALE_SHA[:8] not in mission_text,
        "kpi_path_no_longer_claimed_live": (kpi_path + "` is\nnot present in the live tree") in mission_text,
        "superseded_kpi_location_disclosed": superseded_kpi in mission_text,
        "run1_log_tail": run1_tail,
        "run2_log_tail": run2_tail,
    }
    assert all(v is True for k, v in d1_reattack.items()
               if k in ("two_runs_byte_agree", "mission_citation_matches_live_result",
                        "stale_hash_absent_from_mission_prose",
                        "kpi_path_no_longer_claimed_live",
                        "superseded_kpi_location_disclosed")), d1_reattack

    # ================= DEFECT 2 =================
    # Read the corrected band from the REFUTING RECEIPT'S SIGNED PAYLOAD BYTES
    gap_env = json.loads(GAP_RECEIPT.read_bytes())["signature"]
    gap_payload = json.loads(base64.standard_b64decode(gap_env["payload"]))
    bwc = gap_payload["results"]["band_width_comparison"]
    tds_band = bwc["true_manufacturer_tds_band_g_per_eq"]
    assert tds_band == [450.0, 550.0], f"unexpected TDS band in refuting receipt: {tds_band}"
    EEW_SOLID_LO, EEW_SOLID_HI = tds_band
    n_window = [round(eew_to_n(EEW_SOLID_LO), 4), round(eew_to_n(EEW_SOLID_HI), 4)]
    assert n_window == bwc["true_band_implied_n_window"], n_window
    probes = [pv["probe_eew_g_per_eq"]
              for pv in gap_payload["results"]["mutation_replay"]["probe_values"]]
    assert sorted(probes) == [400.0, 420.0, 600.0, 650.0], probes
    old_band = bwc["cc_v1_selfcomputed_band_g_per_eq"]

    # corrected Check-1 replay over the full facts.json EEW constant family
    facts = json.loads(FACTS.read_text())
    ent = facts["entries"]
    per_constant = []
    for k in sorted(x for x in ent if x.endswith(".eew") or x.endswith(".eew_on_nv")):
        eew = float(ent[k]["value"])
        liquid = k.startswith("resin.dgeba_")
        if liquid:
            admissible = (EEW0 - 1e-6) <= eew <= (EEW_LIQ_HI + 1e-6)
            band = [round(EEW0, 3), round(EEW_LIQ_HI, 3)]
            klass = "liquid_DGEBA"
        else:
            admissible = EEW_SOLID_LO <= eew <= EEW_SOLID_HI   # CORRECTED predicate
            band = [EEW_SOLID_LO, EEW_SOLID_HI]
            klass = "solid_type1_epoxy"
        per_constant.append({
            "constant": k, "catalog_eew_g_per_eq": eew,
            "implied_oligomer_n": round(eew_to_n(eew), 4),
            "resin_class": klass, "admissible_eew_band": band,
            "within_admissible_band": bool(admissible),
        })
    assert all(r["within_admissible_band"] for r in per_constant), per_constant

    # re-attack defect 2: replay the refuting receipt's 4 gap-zone probes
    # against the CORRECTED predicate - all must now be rejected
    probe_results = []
    for p in sorted(probes):
        inside = EEW_SOLID_LO <= p <= EEW_SOLID_HI
        probe_results.append({
            "probe_eew_g_per_eq": p,
            "implied_n": round(eew_to_n(p), 4),
            "in_corrected_band": bool(inside),
            "flagged_by_corrected_predicate": bool(not inside),
            "was_admitted_by_superseded_band": bool(old_band[0] <= p <= old_band[1]),
        })
    n_rejected = sum(1 for r in probe_results if r["flagged_by_corrected_predicate"])
    assert n_rejected == 4, probe_results

    corrected_width = round(EEW_SOLID_HI - EEW_SOLID_LO, 4)
    d2 = {
        "superseded_receipt": {
            "path": "amphora-ingredient-library/evidence/audit/constant-crosscheck-v1/"
                    "constant-crosscheck-receipt.v1.dsse.json",
            "sha256": BEFORE["constant-crosscheck-receipt.v1.dsse.json"],
            "deleted_or_modified": False,
            "superseded_sub_check": "check1_dgeba_eew_admissibility, resin_class=solid_type1_epoxy",
            "superseded_band_g_per_eq": old_band,
            "superseded_n_window": bwc["cc_v1_selfcomputed_n_window"],
        },
        "refuting_receipt": {
            "path": "amphora-ingredient-library/evidence/audit/eew-solid-band-mislabel-gap-v1/"
                    "eew-solid-band-mislabel-gap-receipt.v1.dsse.json",
            "sha256": BEFORE["eew-solid-band-mislabel-gap-receipt.v1.dsse.json"],
            "band_verified_from_signed_payload_bytes": True,
        },
        "corrected_band": {
            "resin_class": "solid_type1_epoxy",
            "fact_key": "resin.solid_cut_1001x75.eew_on_nv",
            "eew_band_g_per_eq": [EEW_SOLID_LO, EEW_SOLID_HI],
            "band_width_g_per_eq": corrected_width,
            "implied_n_window": n_window,
            "derivation": {
                "source": "Hexion HCD-4022 EPON Resin 1001-X-75 TDS, EEW 450-550 g/eq on "
                          "nonvolatiles, as transcribed in facts.json's own "
                          "single_source_waiver note for resin.solid_cut_1001x75.eew_on_nv "
                          "and as carried in the refuting receipt's signed payload "
                          "(results.band_width_comparison.true_manufacturer_tds_band_g_per_eq).",
                "n_window_formula": "n(EEW) = (FUNC*EEW - M0)/MREP with M0=340.42 g/mol "
                                    "(C21H24O4), MREP=284.35 g/mol (C18H20O3), FUNC=2",
                "n_at_450": round(eew_to_n(450.0), 4),
                "n_at_550": round(eew_to_n(550.0), 4),
                "replaces_unsourced_n_window": "[1.5, 3.5] (not tabulated in Ellis 1993 / "
                                               "Lee & Neville 1967, per refuting receipt)",
            },
            "width_ratio_vs_tds_band": round(corrected_width / (tds_band[1] - tds_band[0]), 4),
            "strictly_wider_than_tds_band": bool(corrected_width > (tds_band[1] - tds_band[0])),
            "gap_lo_zone_now": "empty ([450.0, 450.0])",
            "gap_hi_zone_now": "empty ([550.0, 550.0])",
        },
        "corrected_check1_per_constant": per_constant,
        "catalog_value_status": {
            "catalog_value_g_per_eq": float(ent["resin.solid_cut_1001x75.eew_on_nv"]["value"]),
            "within_corrected_band": True,
        },
        "reattack_gap_zone_probes": {
            "method": "The refuting receipt's own 4 probe EEW values (read from its signed "
                      "payload bytes) replayed against the corrected admissibility "
                      "predicate 450.0 <= EEW <= 550.0.",
            "probe_values": probe_results,
            "n_probes_now_rejected": n_rejected,
            "all_previously_undetected_probes_now_rejected": n_rejected == 4,
        },
        "liquid_dgeba_subcheck_unchanged": {
            "band_g_per_eq": [round(EEW0, 3), round(EEW_LIQ_HI, 3)],
            "note": "Liquid n in [0, 0.20] band is tight and literature-anchored; the "
                    "refuting receipt explicitly does not attack it. Unmodified.",
        },
    }

    diag = {
        "schema": "amphora.ingredient-library.repair-R-A01-diagnostic.v1",
        "module": "amphora-ingredient-library",
        "repair_item": "R-A01",
        "repair_mode": "interactive-2026-08-03",
        "date": "2026-08-03",
        "run_type": "AUDIT_ONLY",
        "authority": "AUDIT_ONLY",
        "generated_on_host": "xbabe2",
        "defect1_mission_citation_repair": {
            "refuting_receipt": {
                "path": "amphora-ingredient-library/evidence/audit/"
                        "phase0-mission-evidence-parity-v1/"
                        "phase0-mission-evidence-parity-receipt.v1.dsse.json",
                "sha256": BEFORE["phase0-mission-evidence-parity-receipt.v1.dsse.json"],
                "refuted_at": "2026-08-02T22:06",
            },
            "stale_cited_result_sha256": STALE_SHA,
            "corrected_cited_result_sha256": EXPECTED_LIVE_SHA,
            "parity_audit_confirmed_13_numeric_bullets_correct": True,
            "mission_md_sha256_before": mission_sha_before,
            "mission_md_sha256_after": mission_sha_after,
            "front_matter_unchanged": True,
            "edit_scope": "PROSE ONLY: single citation block in 'Current benchmark result'",
            "reattack": d1_reattack,
        },
        "defect2_solid_band_tightening": d2,
        "headline": (
            "R-A01 repair: (1) mission.md citations corrected to the live byte-stable "
            "result.v1.json sha 06229682... confirmed by two fresh independent Rust "
            "harness re-executions, with the superseded Phase-0 KPI receipt location "
            "disclosed; (2) constant-crosscheck-v1's solid_type1_epoxy EEW admissibility "
            "band superseded by the Hexion HCD-4022 TDS band [450.0, 550.0] g/eq "
            "(width 100.0, ratio 1.0 vs TDS), under which all 4 previously-undetected "
            "gap-zone probes (400/420/600/650 g/eq) are now rejected while the catalog "
            "value 500.0 and all liquid-DGEBA constants remain admissible."
        ),
        "closes": [
            "mission.md 'Honest current state' artifact citations are again verifiable by "
            "independent re-execution (defect refuted 2026-08-02T22:06).",
            "solid_type1_epoxy EEW gross-error detection gap (defect refuted "
            "2026-08-03T14:06): the corrected band has zero undetected gap zone versus "
            "the manufacturer TDS band.",
        ],
        "does_not_close": [
            "Does not establish product qualification, wet-lab performance, supplier "
            "closure, or dataset rights.",
            "Does not re-audit the 13 KPI numeric bullets (parity receipt already "
            "confirmed them correct).",
            "The corrected solid band inherits single-source (TDS) provenance as recorded "
            "in facts.json's single_source_waiver; no independent second physical source "
            "for the solid cut is claimed.",
            "Does not modify facts.json, any signed receipt, the falsification ledger, "
            "the module manifest, or the master manifest.",
        ],
        "modifies_existing_receipts": False,
        "modifies_manifest": False,
        "modifies_module_manifest": False,
        "modifies_locked_dataset": False,
        "modifies_signed_phase0_kpi": False,
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
    }
    return diag


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


if __name__ == "__main__":
    d1 = main()
    b1 = canon(d1)
    d2 = main()          # full second replay (mission fix path is idempotent)
    b2 = canon(d2)
    assert b1 == b2, "two-replay byte MISMATCH"
    (WORK / "diagnostic.canonical.json").write_bytes(b1)
    (WORK / "diagnostic.runB.json").write_bytes(b2)
    print("diagnostic_sha256:", sha(b1))
    print("byte_stable:", b1 == b2)
