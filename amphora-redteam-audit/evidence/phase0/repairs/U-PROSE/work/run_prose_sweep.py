#!/usr/bin/env python3
"""U-PROSE: portfolio-wide mission-prose staleness sweep.

Mechanical stage (fully reproducible): for each of the 29 mission.md-bearing
modules, extract numeric tokens from (a) that module's RETRACTION-INDEX.md
rows, (b) logs/claims-requiring-retraction.jsonl entries scoped to the module,
and (c) REFUTED falsification-ledger.jsonl verdicts for the module; then check
whether those numeric tokens (the ones that distinguish the refuted claim, not
generic thresholds) still appear verbatim in the module's CURRENT docs/mission.md.

Human-verification stage (recorded, not re-derived): every mechanical
candidate hit was read in its live mission.md context window and classified
into one of:
  ADVERTISES_RETRACTED_RESULT - prose still states the refuted number/finding
      as a current, uncaveated positive result.
  DISCLOSURE_GAP - prose numbers are locally accurate (e.g. on a fixture) but
      omit a known REFUTED generalization/caveat that the module's own
      RETRACTION-INDEX.md already records.
  ALREADY_REPAIRED - prose already carries an inline correction/retraction
      marker adjacent to the number (verified by reading the excerpt).
  NO_STALE_CLAIM_DETECTED - either zero numeric-token overlap found by the
      mechanical stage, or (molecule-generator) the matched token was a
      coincidental match against an unrelated locked-target figure, not the
      refuted quantity.
The classification and its supporting excerpt are hardcoded below as the
receipt of what a human (this fire) read; the mechanical candidate-generation
step is re-run live and must reproduce the same candidate set, or the script
aborts (protects against the classification going stale vs the live sweep).
"""
import hashlib
import json
import os
import re

ROOT = "/home/ubuntu/amphora/build/mvp20-split"
os.chdir(ROOT)

MODULES = """amphora-barrier-corrosion-score
amphora-candidate-contract
amphora-cro-protocol-packager
amphora-cure-potlife-gate
amphora-design-rule-score
amphora-envelope-gates
amphora-evidence-intake-validator
amphora-formulation-arithmetic
amphora-formulation-universe
amphora-ingredient-library
amphora-ip-fto-guard
amphora-known-answer-benchmarks
amphora-model-card-authority
amphora-molecule-design-gate
amphora-molecule-generator
amphora-molecule-novelty
amphora-molecule-property
amphora-molecule-role-ranker
amphora-optimizer-orchestrator
amphora-process-qc-twin
amphora-public-corrosion-benchmark
amphora-redteam-audit
amphora-report-packager
amphora-run-provenance
amphora-solvency-score
amphora-sourceability-ehs
amphora-source-ledger
amphora-tolerance-robustness
amphora-viscosity-score""".split()
assert len(MODULES) == 29


def sha(b):
    return hashlib.sha256(b).hexdigest()


NUM_RE = re.compile(r"-?\d+\.\d+|\d+%")


def nums(text):
    return set(NUM_RE.findall(text or ""))


def parse_retraction_index(text):
    if not text:
        return []
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0].lower() in ("claim",) or set(cells[0]) <= {"-", ":"}:
            continue
        rows.append(cells)
    return rows


ledger_refuted = {m: [] for m in MODULES}
with open("logs/falsification-ledger.jsonl") as f:
    ledger_bytes = f.read().encode()
for line in ledger_bytes.decode().splitlines():
    line = line.strip()
    if not line:
        continue
    rec = json.loads(line)
    mod = rec.get("module")
    if mod in ledger_refuted and rec.get("verdict") == "REFUTED":
        ledger_refuted[mod].append(
            {
                "fire_id": rec.get("fire_id"),
                "claim": rec.get("claim"),
                "attack": rec.get("attack"),
                "receipt": rec.get("receipt"),
                "ts": rec.get("ts"),
            }
        )
ledger_sha256 = sha(ledger_bytes)

crr_by_module = {m: [] for m in MODULES}
crr_path = "logs/claims-requiring-retraction.jsonl"
crr_raw = open(crr_path, "rb").read()
crr_sha256 = sha(crr_raw)
for line in crr_raw.decode().splitlines():
    line = line.strip()
    if not line:
        continue
    rec = json.loads(line)
    f_ = rec.get("file", "")
    for m in MODULES:
        if f_.startswith(m + "/"):
            crr_by_module[m].append(rec)
            break

module_info = {}
for m in MODULES:
    mission_path = f"{m}/docs/mission.md"
    ri_path = f"{m}/evidence/phase0/kpis/RETRACTION-INDEX.md"
    mission_present = os.path.exists(mission_path)
    mission_text = open(mission_path).read() if mission_present else ""
    mission_sha256 = sha(mission_text.encode()) if mission_present else None
    ri_present = os.path.exists(ri_path)
    ri_text = open(ri_path).read() if ri_present else ""
    ri_sha256 = sha(ri_text.encode()) if ri_present else None
    ri_rows = parse_retraction_index(ri_text)
    module_info[m] = {
        "mission_present": mission_present,
        "mission_sha256": mission_sha256,
        "retraction_index_present": ri_present,
        "retraction_index_sha256": ri_sha256,
        "n_retraction_index_rows": len(ri_rows),
        "n_refuted_ledger_verdicts": len(ledger_refuted[m]),
        "n_claims_requiring_retraction": len(crr_by_module[m]),
        "mission_text": mission_text,
        "ri_rows": ri_rows,
    }

# --- mechanical candidate detection (re-derived live every run) ---
candidates = []
for m in MODULES:
    info = module_info[m]
    mission_text = info["mission_text"]
    if not info["mission_present"]:
        continue
    for row in info["ri_rows"]:
        claim_cell = row[0] if row else ""
        hit = {n for n in nums(claim_cell) if n in mission_text}
        if hit:
            candidates.append(
                {"module": m, "kind": "retraction_index_row", "matched_numbers": sorted(hit),
                 "source_cell": claim_cell}
            )
    for crr in crr_by_module[m]:
        stale_only = nums(crr.get("claim_text", "")) - nums(crr.get("corrected_statement", ""))
        hit = {n for n in stale_only if n in mission_text}
        if hit:
            candidates.append(
                {"module": m, "kind": "claims_requiring_retraction", "matched_numbers": sorted(hit),
                 "crr_file": crr.get("file"), "claim_text": crr.get("claim_text")}
            )
    for lv in ledger_refuted[m]:
        text = " ".join(filter(None, [lv.get("claim"), lv.get("attack")]))
        cand = {n for n in nums(text) if len(n.replace("-", "").replace(".", "").replace("%", "")) >= 3}
        hit = {n for n in cand if n in mission_text}
        if hit:
            candidates.append(
                {"module": m, "kind": "ledger_refuted_verdict", "matched_numbers": sorted(hit),
                 "fire_id": lv.get("fire_id"), "claim": lv.get("claim"), "receipt": lv.get("receipt")}
            )

candidate_modules = sorted({c["module"] for c in candidates})
EXPECTED_CANDIDATE_MODULES = sorted([
    "amphora-barrier-corrosion-score", "amphora-cure-potlife-gate", "amphora-design-rule-score",
    "amphora-evidence-intake-validator", "amphora-molecule-generator", "amphora-molecule-property",
    "amphora-molecule-role-ranker", "amphora-public-corrosion-benchmark", "amphora-solvency-score",
    "amphora-viscosity-score",
])
assert candidate_modules == EXPECTED_CANDIDATE_MODULES, (
    "live mechanical sweep candidate-module set has drifted from the set this fire "
    f"hand-verified: live={candidate_modules} expected={EXPECTED_CANDIDATE_MODULES}. "
    "Re-run the human-verification pass before signing."
)

# --- human-verified classification, keyed by module (this fire's read of every
# candidate's live mission.md excerpt; see attack_description for the excerpts) ---
VERIFIED = {
    "amphora-design-rule-score": {
        "status": "ADVERTISES_RETRACTED_RESULT",
        "severity_rank": 1,
        "stale_claim": (
            "docs/mission.md line ~202, under the header 'HONEST INTERPRETATION': "
            "\"Full HistGBM (R² = +0.8555, matching parent LOIO R² = 0.856 exactly) crushes every "
            "non-ML baseline\" -- presented as the module's current, uncaveated headline finding."
        ),
        "refuting_receipts": [
            "amphora-design-rule-score/evidence/phase0/kpis/purformance-scratch-hardness-dedup-superseding-kpi.v1.json",
        ],
        "refuting_ledger_lines": [
            {"ts": "2026-08-01T02:05:01+00:00", "campaign_item_id": "C6", "verdict": "REFUTED"},
            {"ts": "2026-08-01T03:01:13+00:00", "campaign_item_id": "C6", "verdict": "REFUTED"},
        ],
        "evidence": (
            "Both 2026-08-01 REFUTED ledger lines (campaign C6) show that a leak-free re-baseline "
            "(deduped LOIO on 58 unique observations, correcting a 27/27 and 27/42 per-fold leak) "
            "collapses HistGBM from R2=+0.8555 to R2=-0.0469 (<= the constant-mean floor of -0.0535, "
            "i.e. no skill), and that Guth-Gold 1938 physics (R2=0.2437, concordance C=0.7111, CI "
            "[0.6155,0.7980] excludes chance) becomes the strongest leak-free arm -- the OPPOSITE "
            "ranking from what mission.md's 'HONEST INTERPRETATION' still asserts. "
            "amphora-design-rule-score/evidence/phase0/kpis/RETRACTION-INDEX.md exists but only "
            "records an unrelated signature-identity re-issue (R-A11); it has no row for this "
            "leak/dedup finding at all, so the module's own retraction bookkeeping is incomplete on "
            "top of the prose staleness."
        ),
    },
    "amphora-molecule-role-ranker": {
        "status": "DISCLOSURE_GAP",
        "severity_rank": 2,
        "stale_claim": (
            "docs/mission.md reports `structural_inference_agreement_rate` 1.0 and "
            "`out_of_domain_rejection_rate` 1.0 on the 39-record self-authored fixture with no "
            "caveat anywhere in the file (grepped for 'guanidine', 'DPG', 'DOTG', 'accelerator', "
            "'R-N02', 'generaliz' -- zero hits)."
        ),
        "refuting_receipts": [
            "amphora-molecule-role-ranker/benchmarks/role-guanidine-accelerator-domain-probe-v1/replay_receipt.v1.dsse.json",
        ],
        "refuting_ledger_lines": [],
        "evidence": (
            "The module's OWN evidence/phase0/kpis/RETRACTION-INDEX.md records that the "
            "'generalization inference ... that the deterministic role rule fails closed on real "
            "out-of-domain accelerator/catalyst chemotypes generally' was CLAIM_REFUTED: DPG (CAS "
            "102-06-7) and DOTG (CAS 97-39-2), real guanidine-class accelerators, were classified "
            "`hardener` with `reactive_amine_hydrogen_count`=3 through the real RDKit FFI. The raw "
            "1.0 numbers reported in mission.md are locally true (correct on the 39-record fixture) "
            "so this is NOT an advertised-false-number defect, but the module's own retraction index "
            "already names the caveat and mission.md carries none of it -- a silent disclosure gap "
            "one severity notch below ADVERTISES_RETRACTED_RESULT."
        ),
    },
    "amphora-molecule-generator": {
        "status": "NO_STALE_CLAIM_DETECTED",
        "severity_rank": 4,
        "stale_claim": None,
        "refuting_receipts": [],
        "refuting_ledger_lines": [],
        "evidence": (
            "Mechanical sweep matched token '95%' between a RETRACTION-INDEX row (the "
            "feasible_fraction bootstrap-CI-vs-Clopper-Pearson correction) and mission.md, but the "
            "live mission.md occurrence is the unrelated locked-target sentence 'At least 99% "
            "validity, 95% uniqueness ...' -- a coincidental digit match, not a citation of the "
            "refuted CI. Confirmed false positive on manual read."
        ),
    },
    "amphora-barrier-corrosion-score": {
        "status": "ALREADY_REPAIRED",
        "severity_rank": 3,
        "stale_claim": None,
        "refuting_receipts": [
            "amphora-barrier-corrosion-score/benchmarks/corr-rate-conformal-domain-shift-v1/corr-rate-conformal-domain-shift-receipt.v1.dsse.json",
            "amphora-barrier-corrosion-score/benchmarks/three-series-barrier-ranking-v1/three-series-barrier-ranking-receipt.v1.dsse.json",
        ],
        "refuting_ledger_lines": [],
        "evidence": (
            "mission.md's own text already reports, in the same section as the 0.90/0.80 conformal "
            "targets, a 'REQUIRED honest demonstration that exchangeability fails' with observed "
            "cross-source coverage collapsing to 0.5518 (0.3482 below the 0.90 target), and the "
            "three-series barrier-ranking section states plainly that all 3 series fall below "
            "FEASIBILITY_FLOOR=6 with 'No checked result pro[motable]'. The refuted results are "
            "disclosed, not advertised as passing."
        ),
    },
    "amphora-cure-potlife-gate": {
        "status": "ALREADY_REPAIRED",
        "severity_rank": 3,
        "stale_claim": None,
        "refuting_receipts": [
            "amphora-cure-potlife-gate/evidence/audit/potlife-kpi-envelope-disclosure-gap-v1/potlife-kpi-envelope-disclosure-gap-receipt.v1.dsse.json",
            "amphora-cure-potlife-gate/evidence/audit/rights-integrity-contradiction-v1/rights-integrity-contradiction-receipt.v1.dsse.json",
        ],
        "refuting_ledger_lines": [],
        "evidence": (
            "mission.md carries an explicit 'Qualified temperature-scaling statement (repair R-A02, "
            "2026-08-03; supersedes the earlier blanket claim of under 15% error ...)' with the full "
            "per-leg MAPE breakdown (3.445% / 15.628% / 25.124%) and an explicit warning not to read "
            "the pooled 14.7% as uniform. Fixture rights carries a matching 'under human review' note."
        ),
    },
    "amphora-evidence-intake-validator": {
        "status": "ALREADY_REPAIRED",
        "severity_rank": 3,
        "stale_claim": None,
        "refuting_receipts": [
            "amphora-evidence-intake-validator/evidence/phase0/repairs/V1-REAL-EIV/done/v1-real-eiv-superseding-kpi.v1.dsse.json",
        ],
        "refuting_ledger_lines": [],
        "evidence": (
            "mission.md explicitly states, dated 2026-08-04: 'the shipped 1.0 "
            "positive_scenarios_scored_rate does NOT generalize to the module's own real in-tree "
            "DSSE corpus' with the honest re-measured rate cited alongside."
        ),
    },
    "amphora-molecule-property": {
        "status": "ALREADY_REPAIRED",
        "severity_rank": 3,
        "stale_claim": None,
        "refuting_receipts": [
            "amphora-molecule-property/evidence/phase0/repairs/B3/done/B3.done-receipt.v1.dsse.json",
            "amphora-molecule-property/evidence/audit/dielectric-retraction-v1/dielectric-retraction-superseding-kpi-receipt.v1.dsse.json",
            "amphora-molecule-property/evidence/audit/vk-ridge-ygi-admissibility-w8-v1/vk-ridge-ygi-admissibility-audit-receipt.v1.dsse.json",
            "amphora-molecule-property/evidence/audit/amine-nh-guanidine-conjugation-gap-v1/amine-nh-guanidine-conjugation-gap-receipt.v1.dsse.json",
            "amphora-molecule-property/benchmarks/tg-density-external-validity-c7-v3-final/c7_final_tg_density_external_validity_verdict_receipt.v1.json",
        ],
        "refuting_ledger_lines": [],
        "evidence": (
            "All 8 mechanical candidate hits (dielectric MAE~0.40 claim, VK Y_gi 32.6K claim, "
            "Tg/density C7 6.66x/16.60x transfer numbers, C8 dielectric clean-subset numbers, W8 "
            "sign-reversal -0.52/100%, amine-N-H 100% guanidine gap) resolve to text that is EITHER "
            "(a) an inline block-quoted correction citing the exact refuting receipt (dielectric, "
            "Y_gi, Tg/density all read this way -- this is what B3's repair on 2026-08-04 landed) or "
            "(b) the still-valid narrow/scope-limited residual measurement the correction itself "
            "says remains citable (e.g. MAE 0.4040 on the OpenPoly-only clean subset). This is the "
            "state B3 produced; this fire finds no regression since B3 landed."
        ),
    },
    "amphora-public-corrosion-benchmark": {
        "status": "ALREADY_REPAIRED",
        "severity_rank": 3,
        "stale_claim": None,
        "refuting_receipts": [
            "amphora-public-corrosion-benchmark/evidence/audit/nist-baseline-fold-significance-v1/nist-baseline-fold-significance-receipt.v1.dsse.json",
            "amphora-public-corrosion-benchmark/evidence/audit/nist-baseline-material-group-extrapolation-v1/nist-baseline-material-group-extrapolation-receipt.v1.dsse.json",
        ],
        "refuting_ledger_lines": [],
        "evidence": (
            "Every occurrence of the retracted NIST Ridge-vs-NULL numbers (0.6331/0.6806/0.0475/7.0%) "
            "in mission.md carries an inline '*[RETRACTED 2026-08-03, repair R-A08 -- not "
            "independently reproducible and not fold-robust ...]*' marker plus a '> CORRECTED / "
            "SUPERSEDED' block quoting the honest re-implementation numbers (0.5888/0.6736)."
        ),
    },
    "amphora-solvency-score": {
        "status": "ALREADY_REPAIRED",
        "severity_rank": 3,
        "stale_claim": None,
        "refuting_receipts": [
            "amphora-solvency-score/evidence/audit/flory-hansen-physical-admissibility-v1/flory-hansen-physical-admissibility-audit-receipt.v1.dsse.json",
        ],
        "refuting_ledger_lines": [],
        "evidence": (
            "The Fedors/Van-Krevelen delta_p and Hansen-component ceiling-breach numbers (5.2e9, "
            "5.33e17 vs the 59.9 MPa^0.5 admissibility ceiling) appear in mission.md only inside a "
            "'> ... (campaign item W7, verdict CLAIM_REFUTED) voided this section's KPI' block quote."
        ),
    },
    "amphora-viscosity-score": {
        "status": "ALREADY_REPAIRED",
        "severity_rank": 3,
        "stale_claim": None,
        "refuting_receipts": [
            "amphora-viscosity-score/evidence/audit/polyverse-rights-disclosure-gap-v1/polyverse-rights-disclosure-gap-receipt.v1.dsse.json",
            "amphora-viscosity-score/evidence/audit/ffw-vs-ml-uncertainty-disclosure-gap-v1/ffw-vs-ml-uncertainty-disclosure-gap-receipt.v1.dsse.json",
        ],
        "refuting_ledger_lines": [],
        "evidence": (
            "Every occurrence of the Polyverse R2=0.944 parent figure and the FFW-vs-ML R2 "
            "0.5972/0.4536 pair carries an adjacent '[Polyverse dataset: CONTEXT_ONLY, "
            "promotion_eligible=false, pending counsel]' and/or '[n=13 independent chemistries, no "
            "resampled interval - interval work queued as R-C04]' caveat, matching repair R-A03."
        ),
    },
}

NO_CANDIDATE_MODULES = sorted(set(MODULES) - set(EXPECTED_CANDIDATE_MODULES))
for m in NO_CANDIDATE_MODULES:
    VERIFIED[m] = {
        "status": "NO_STALE_CLAIM_DETECTED",
        "severity_rank": 4,
        "stale_claim": None,
        "refuting_receipts": [],
        "refuting_ledger_lines": [],
        "evidence": (
            "Mechanical sweep found zero numeric-token overlap between this module's "
            "RETRACTION-INDEX.md rows / logs/claims-requiring-retraction.jsonl entries / REFUTED "
            "falsification-ledger.jsonl verdicts and the module's current docs/mission.md prose."
        ),
    }

assert set(VERIFIED.keys()) == set(MODULES)

per_module_table = []
for m in MODULES:
    info = module_info[m]
    v = VERIFIED[m]
    per_module_table.append(
        {
            "module": m,
            "mission_present": info["mission_present"],
            "mission_sha256": info["mission_sha256"],
            "retraction_index_present": info["retraction_index_present"],
            "n_retraction_index_rows": info["n_retraction_index_rows"],
            "n_refuted_ledger_verdicts": info["n_refuted_ledger_verdicts"],
            "n_claims_requiring_retraction": info["n_claims_requiring_retraction"],
            "n_mechanical_candidates": len([c for c in candidates if c["module"] == m]),
            "status": v["status"],
            "stale_claim": v["stale_claim"],
            "refuting_receipts": v["refuting_receipts"],
            "evidence": v["evidence"],
        }
    )

n_advertises_retracted = sum(1 for r in per_module_table if r["status"] == "ADVERTISES_RETRACTED_RESULT")
n_disclosure_gap = sum(1 for r in per_module_table if r["status"] == "DISCLOSURE_GAP")
n_already_repaired = sum(1 for r in per_module_table if r["status"] == "ALREADY_REPAIRED")
n_no_stale = sum(1 for r in per_module_table if r["status"] == "NO_STALE_CLAIM_DETECTED")

verdict = "CLAIM_REFUTED" if n_advertises_retracted > 0 else "CLAIM_SURVIVED"

proposed_followups = [
    {
        "module": "amphora-design-rule-score",
        "defect": (
            "docs/mission.md 'HONEST INTERPRETATION' headline (line ~202) still advertises B5 "
            "HistGBM R2=+0.8555 'crushes every non-ML baseline' with zero mention that the "
            "leak-free re-baseline (2026-08-01, campaign C6, REFUTED x2) collapses it to "
            "R2=-0.0469 (no skill, below the constant-mean floor) and promotes Guth-Gold physics "
            "(R2=0.2437) to strongest leak-free arm. evidence/phase0/kpis/RETRACTION-INDEX.md also "
            "has no row for this finding at all (only the unrelated R-A11 signature reissue)."
        ),
        "proposed_done_criterion": (
            "docs/mission.md's LOIO-CV section is amended (supersede-never-rewrite, new prose "
            "alongside the existing text, not a silent edit) to state the leak-free R2 collapse and "
            "cite purformance-scratch-hardness-dedup-superseding-kpi.v1.json inline, AND "
            "evidence/phase0/kpis/RETRACTION-INDEX.md gains a row for the C6 finding citing both "
            "2026-08-01 REFUTED ledger lines; a re-run of this same numeric cross-reference sweep "
            "against the repaired mission.md finds status=ALREADY_REPAIRED for this module."
        ),
    },
    {
        "module": "amphora-molecule-role-ranker",
        "defect": (
            "docs/mission.md reports structural_inference_agreement_rate=1.0 and "
            "out_of_domain_rejection_rate=1.0 on the 39-record fixture with no mention that the "
            "module's own RETRACTION-INDEX.md records the broader 'fails closed on real "
            "out-of-domain accelerator/catalyst chemotypes generally' inference as CLAIM_REFUTED "
            "(DPG/DOTG guanidine accelerators misclassified as hardener via the real FFI)."
        ),
        "proposed_done_criterion": (
            "docs/mission.md gains a short disclosure note next to the role-classification-kpi "
            "section citing role-guanidine-accelerator-domain-probe-v1/replay_receipt.v1.dsse.json "
            "and the R-N02 coordinated fix, scoping the 1.0 rates to the tested fixture rather than "
            "implying unconditional generalization; re-run finds status=ALREADY_REPAIRED."
        ),
    },
]

diagnostic = {
    "schema": "amphora.redteam-audit.mission-prose-staleness-sweep.v1",
    "campaign_item_id": "U-PROSE",
    "module": "amphora-redteam-audit",
    "claim_under_attack": {
        "receipt_path": "logs/falsification-ledger.jsonl",
        "claim_text": (
            "Every numeric claim in every module's mission.md is consistent with that module's "
            "retraction index and the falsification ledger."
        ),
    },
    "n_modules_total": len(MODULES),
    "modules_covered": MODULES,
    "n_modules_with_mechanical_candidates": len(candidate_modules),
    "mechanical_candidate_modules": candidate_modules,
    "mechanical_candidates": candidates,
    "per_module_table": per_module_table,
    "summary_counts": {
        "ADVERTISES_RETRACTED_RESULT": n_advertises_retracted,
        "DISCLOSURE_GAP": n_disclosure_gap,
        "ALREADY_REPAIRED": n_already_repaired,
        "NO_STALE_CLAIM_DETECTED": n_no_stale,
    },
    "headline": f"{n_advertises_retracted}/{len(MODULES)} modules ADVERTISES_RETRACTED_RESULT",
    "verdict": verdict,
    "proposed_followups": proposed_followups,
    "ledger_snapshot": {"path": "logs/falsification-ledger.jsonl", "sha256": ledger_sha256},
    "claims_requiring_retraction_snapshot": {"path": crr_path, "sha256": crr_sha256},
}

print(json.dumps(diagnostic, indent=2, sort_keys=True))
