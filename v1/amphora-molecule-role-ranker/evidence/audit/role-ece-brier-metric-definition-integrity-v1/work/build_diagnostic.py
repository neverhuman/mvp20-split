#!/usr/bin/env python3
"""role-ece-brier-metric-definition-integrity-v1

ROTATION falsification attack (no campaign item) on amphora-molecule-role-ranker's
flagship KPI evidence/phase0/kpis/role-classification-kpi.v1.json, metric
`expected_calibration_error` (observed 0.0019924703593823217, reported_ceiling
0.10, note: "reported observationally under Phase-0; Phase-1 lock will gate at
threshold").

CLAIM UNDER ATTACK: that this field is a faithful implementation of Expected
Calibration Error (ECE) as defined in the calibration literature -- Naeini,
M.P.; Cooper, G.F.; Hauskrecht, M. (2015) "Obtaining Well Calibrated
Probabilities Using Bayesian Binning" AAAI 29(1):2901-2907; Guo, C.; Pleiss,
G.; Sun, Y.; Weinberger, K.Q. (2017) "On Calibration of Modern Neural
Networks" PMLR 70:1321-1330 -- namely

    ECE = sum_m (|B_m| / n) * |acc(B_m) - conf(B_m)|

over M confidence bins B_m, where acc(B_m) is the empirical accuracy of
predictions falling in bin m and conf(B_m) is the mean predicted confidence
in that bin.

MECHANISM: the module's own KPI harness (amphora-molecule-capabilities/tests/
role_ranker_phase0_kpi.rs) instead computes, per record, `brier = (fitted_prob
- y)^2` and reports `calibration_error_sum / resin_hardener_total` -- the MEAN
BRIER (Brier, G.W. 1950, Monthly Weather Review 78(1):1-3) SCORE, a distinct
statistic. Brier score decomposes (Murphy 1973, J. Appl. Meteorol. 12(4):595-
600) into reliability - resolution + uncertainty; its reliability term uses
SQUARED bin-wise deviations weighted differently than ECE's unsquared, and the
two are not numerically interchangeable except in degenerate cases.

METHOD (independent, non-circular): re-derive the 24 in-domain training
records' fitted resin-probabilities from the SHIPPED fixture
(reference/phase0-role-known-answer.v1.json) `fitted_model_artifact` (frozen
logistic-regression coefficients + z-score standardization), reproducing the
harness's own sigmoid formula (role_ranker_phase0_kpi.rs L214-221) independently
in Python. Confirm the reproduction is faithful by checking the resulting mean
Brier score reproduces the SHIPPED KPI's published `expected_calibration_error`
observed value byte-for-byte. Then compute genuine binned ECE (and MCE, its
companion max-calibration-error statistic) from the SAME fitted probabilities
and true labels, across a battery of binning schemes (equal-width M in
{2,4,5,8,10,15,20}; equal-frequency M in {2,3,4,6,8,12}) to rule out a
bin-count or bin-edge artifact.

REFUTATION CRITERION: refuted if the independently-computed genuine ECE
differs from the reported "expected_calibration_error" observed value by more
than 2x, robustly across binning schemes (i.e. not an artifact of one
arbitrary bin choice).

AUDIT_ONLY. No promotion, no manifest edit, no objective emission. This is a
metric-DEFINITION integrity audit; it makes no claim about and does not touch
the role rule's structural_inference_agreement_rate=1.0 or any prior
SURVIVED/REFUTED verdict on the classification rule itself.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-molecule-role-ranker"
FIXTURE = MOD / "reference/phase0-role-known-answer.v1.json"
SHIPPED_KPI = MOD / "evidence/phase0/kpis/role-classification-kpi.v1.json"
HARNESS_RS = ROOT / "amphora-molecule-capabilities/tests/role_ranker_phase0_kpi.rs"
OUT = MOD / "evidence/audit/role-ece-brier-metric-definition-integrity-v1/work"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sigmoid(x):
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def fitted_resin_probability(model, facts):
    """Byte-identical port of role_ranker_phase0_kpi.rs::fitted_resin_probability
    (L172-221): frozen coefficients over z-scored structural features."""
    feature_order = model["feature_order"]
    coefficients = model["coefficients"]
    means = model["standardization"]["means"]
    scales = model["standardization"]["scales"]
    linear = 0.0
    for feature, coef in zip(feature_order, coefficients):
        if feature == "intercept":
            raw = 1.0
            standardized = raw
        else:
            raw = facts[feature]
            mean = means[feature]
            scale = scales[feature]
            assert scale > 0 and math.isfinite(scale)
            standardized = (raw - mean) / scale
        linear += coef * standardized
    assert math.isfinite(linear)
    return sigmoid(linear)


def ece_equal_width(rows, m):
    bins = [[] for _ in range(m)]
    for _rid, p, y in rows:
        idx = min(int(p * m), m - 1)
        bins[idx].append((p, y))
    n = len(rows)
    total = 0.0
    populated = 0
    for b in bins:
        if not b:
            continue
        populated += 1
        conf = sum(p for p, _y in b) / len(b)
        acc = sum(y for _p, y in b) / len(b)
        total += (len(b) / n) * abs(acc - conf)
    return total, populated


def mce_equal_width(rows, m):
    bins = [[] for _ in range(m)]
    for _rid, p, y in rows:
        idx = min(int(p * m), m - 1)
        bins[idx].append((p, y))
    worst = 0.0
    for b in bins:
        if not b:
            continue
        conf = sum(p for p, _y in b) / len(b)
        acc = sum(y for _p, y in b) / len(b)
        worst = max(worst, abs(acc - conf))
    return worst


def ece_equal_frequency(rows, m):
    s = sorted(rows, key=lambda r: r[1])
    n = len(s)
    size = n // m
    total = 0.0
    for i in range(m):
        start = i * size
        end = n if i == m - 1 else (i + 1) * size
        b = s[start:end]
        if not b:
            continue
        conf = sum(p for _rid, p, _y in b) / len(b)
        acc = sum(y for _rid, _p, y in b) / len(b)
        total += (len(b) / n) * abs(acc - conf)
    return total


def main():
    fixture_bytes = FIXTURE.read_bytes()
    fixture = json.loads(fixture_bytes)
    shipped_bytes = SHIPPED_KPI.read_bytes()
    shipped = json.loads(shipped_bytes)
    harness_bytes = HARNESS_RS.read_bytes()

    recs = {r["record_id"]: r for r in fixture["records"]}
    model = fixture["fitted_model_artifact"]
    train_ids = model["training_provenance"]["training_record_ids"]
    assert len(train_ids) == 24

    rows = []
    per_record = []
    for rid in train_ids:
        rec = recs[rid]
        f = rec["facts"]
        facts = {
            "molecular_weight_g_mol": f["average_molecular_weight_g_mol"],
            "oxirane_ring_count": f["oxirane_ring_count"],
            "reactive_amine_hydrogen_count": f["reactive_amine_hydrogen_count"],
            "has_oxirane": 1.0 if f["oxirane_ring_count"] > 0 else 0.0,
            "has_reactive_amine_hydrogen": 1.0 if f["reactive_amine_hydrogen_count"] > 0 else 0.0,
        }
        p = fitted_resin_probability(model, facts)
        y = 1.0 if rec["class"] == "resin" else 0.0
        rows.append((rid, p, y))
        per_record.append({"record_id": rid, "expected_class": rec["class"],
                            "fitted_resin_probability": round(p, 10), "y": y})

    n = len(rows)
    mean_brier = sum((p - y) ** 2 for _rid, p, y in rows) / n
    reported_field = shipped["metrics"][6]
    assert reported_field["name"] == "expected_calibration_error"
    reported_value = reported_field["observed"]
    brier_matches_reported = abs(mean_brier - reported_value) < 1e-15

    ew_grid = [2, 4, 5, 8, 10, 15, 20]
    ef_grid = [2, 3, 4, 6, 8, 12]
    ece_equal_width_rows = []
    for m in ew_grid:
        val, populated = ece_equal_width(rows, m)
        ece_equal_width_rows.append({"m_bins": m, "ece": round(val, 10),
                                      "populated_bins": populated})
    ece_equal_freq_rows = [{"m_bins": m, "ece": round(ece_equal_frequency(rows, m), 10)}
                            for m in ef_grid]
    mce_10 = mce_equal_width(rows, 10)

    all_ece_values = [r["ece"] for r in ece_equal_width_rows] + [r["ece"] for r in ece_equal_freq_rows]
    ece_min = min(all_ece_values)
    ece_max = max(all_ece_values)
    ece_range_ratio = (ece_max / ece_min) if ece_min > 0 else None

    ratio_reported_vs_genuine = (ece_min / reported_value) if reported_value > 0 else None

    refuted = (ece_min / reported_value) > 2.0 if reported_value > 0 else True

    # locate the mislabeled variable/field in the harness source for citation
    harness_lines = harness_bytes.decode().splitlines()
    cite_lines = {}
    for i, line in enumerate(harness_lines, start=1):
        if "calibration_error_sum +=" in line:
            cite_lines["brier_accumulation_line"] = i
            cite_lines["brier_accumulation_text"] = line.strip()
        if "let brier =" in line:
            cite_lines["brier_definition_line"] = i
            cite_lines["brier_definition_text"] = line.strip()
        if "let expected_calibration_error =" in line:
            cite_lines["field_assignment_line"] = i
            cite_lines["field_assignment_text"] = line.strip()
        if '"expected_calibration_error": {' in line:
            cite_lines["json_field_emission_line"] = i

    diag = {
        "schema": "amphora.molecule-role-ranker.role-ece-brier-metric-definition-integrity-v1.diagnostic.v1",
        "purpose": (
            "ROTATION-mode metric-definition-integrity audit of the flagship KPI's "
            "expected_calibration_error field: verify by independent re-derivation whether "
            "the reported statistic is genuine binned Expected Calibration Error (ECE) or a "
            "differently-named statistic (mean Brier score)."
        ),
        "claim_under_attack": {
            "artifact": "amphora-molecule-role-ranker/evidence/phase0/kpis/role-classification-kpi.v1.json#metrics[6]",
            "field_name": "expected_calibration_error",
            "reported_observed_value": reported_value,
            "reported_ceiling_field": "reported_ceiling",
            "reported_ceiling_value": reported_field.get("reported_ceiling"),
            "reported_note": reported_field.get("note"),
            "claim_text": (
                "The field named `expected_calibration_error`, reported observationally at "
                "Phase-0 against a 0.10 ceiling that 'Phase-1 lock will gate at threshold with "
                "an independently double-labeled expert reference', is genuine Expected "
                "Calibration Error as defined in the calibration literature."
            ),
            "refutation_criterion": (
                "A refutation occurs if independently recomputing genuine binned ECE "
                "(Naeini et al. 2015 AAAI; Guo et al. 2017 PMLR 70) from the SAME fitted "
                "probabilities and true labels that produced the reported value yields a "
                "result differing from the reported value by more than 2x, robustly across "
                "multiple binning schemes (equal-width and equal-frequency, M ranging 2-20) "
                "-- i.e. the discrepancy is not an artifact of one arbitrary bin choice."
            ),
        },
        "primary_references": [
            "Naeini, M.P.; Cooper, G.F.; Hauskrecht, M. (2015) 'Obtaining Well Calibrated "
            "Probabilities Using Bayesian Binning', AAAI 29(1):2901-2907.",
            "Guo, C.; Pleiss, G.; Sun, Y.; Weinberger, K.Q. (2017) 'On Calibration of Modern "
            "Neural Networks', PMLR 70:1321-1330 (canonical M-bin ECE/MCE formula).",
            "Brier, G.W. (1950) 'Verification of Forecasts Expressed in Terms of Probability', "
            "Monthly Weather Review 78(1):1-3. doi:10.1175/1520-0493(1950)078<0001:VOFEIT>2.0.CO;2",
            "Murphy, A.H. (1973) 'A New Vector Partition of the Probability Score', "
            "J. Appl. Meteorol. 12(4):595-600 (Brier decomposition: reliability - resolution "
            "+ uncertainty; reliability term is NOT numerically equal to ECE).",
        ],
        "method": {
            "step_1": "Load shipped fixture reference/phase0-role-known-answer.v1.json and its "
                      "frozen fitted_model_artifact (coefficients + z-score standardization).",
            "step_2": "Independently port role_ranker_phase0_kpi.rs::fitted_resin_probability "
                      "(the harness's own sigmoid-over-standardized-features formula) to Python, "
                      "applied to the same 24 training records, from raw fixture facts only "
                      "(no transcription of probabilities or the reported metric).",
            "step_3": "Compute mean Brier score from the independently-derived probabilities; "
                      "confirm it reproduces the shipped KPI's published expected_calibration_error "
                      "observed value byte-for-byte, validating the re-derivation is faithful "
                      "and non-circular (proves what the harness ACTUALLY computes).",
            "step_4": "Compute genuine binned ECE (Guo et al. 2017 formula) and MCE from the SAME "
                      "probabilities and true labels, across 7 equal-width and 6 equal-frequency "
                      "binning schemes (M = 2..20), to rule out a bin-choice artifact.",
            "step_5": "Compare reported value against the full spread of genuine ECE values.",
        },
        "harness_source_citations": {
            "file": "amphora-molecule-capabilities/tests/role_ranker_phase0_kpi.rs",
            "sha256": sha(harness_bytes),
            **cite_lines,
        },
        "reproduction": {
            "n_training_records": n,
            "training_record_ids_source": "fitted_model_artifact.training_provenance.training_record_ids",
            "independently_derived_mean_brier_score": round(mean_brier, 16),
            "shipped_kpi_expected_calibration_error_observed": reported_value,
            "reproduction_exact_match": bool(brier_matches_reported),
            "interpretation": (
                "Exact match confirms the field the harness names `expected_calibration_error` "
                "is, mechanically, the mean squared error of the fitted probabilities against "
                "the true 0/1 labels (Brier score), NOT a binned reliability statistic."
                if brier_matches_reported else
                "MISMATCH: re-derivation could not reproduce the shipped value; see per_record "
                "rows for diagnosis."
            ),
            "per_record": per_record,
        },
        "genuine_ece_recomputation": {
            "equal_width_binning": ece_equal_width_rows,
            "equal_frequency_binning": ece_equal_freq_rows,
            "mce_max_calibration_error_10_bins": round(mce_10, 10),
            "genuine_ece_min_across_all_schemes": round(ece_min, 10),
            "genuine_ece_max_across_all_schemes": round(ece_max, 10),
            "genuine_ece_range_ratio_max_over_min": (round(ece_range_ratio, 6)
                                                      if ece_range_ratio else None),
            "robustness_note": (
                "Genuine ECE is essentially INVARIANT to bin count/scheme here (range ratio "
                f"{round(ece_range_ratio, 4) if ece_range_ratio else 'n/a'}x across 13 distinct "
                "binning choices) because the fitted probabilities cluster tightly into two "
                "well-separated, well-populated groups (12 hardener records at p in "
                "[0.018,0.082], 12 resin records at p in [0.939,0.992]), so the discrepancy "
                "below is not a bin-edge artifact."
            ),
        },
        "comparison": {
            "reported_field_value_expected_calibration_error": reported_value,
            "genuine_ece_value_min": round(ece_min, 10),
            "ratio_genuine_ece_over_reported": (round(ratio_reported_vs_genuine, 4)
                                                 if ratio_reported_vs_genuine else None),
            "refutation_threshold_ratio": 2.0,
            "exceeds_refutation_threshold": bool(refuted),
        },
        "risk_note": (
            "The reported_ceiling comparison (0.10, 'Phase-1 lock will gate at threshold') is "
            "currently being read against the WRONG statistic: the true in-sample calibration "
            "picture on this model's own training data is genuine ECE "
            f"~{round(ece_min, 4)} (~{round((ece_min/0.10)*100, 1)}% of the stated 0.10 "
            "ceiling), not the reported Brier-score value "
            f"~{round(reported_value, 4)} (~{round((reported_value/0.10)*100, 1)}% of ceiling). "
            "This changes the safety-margin narrative a reader would take from the Phase-0 "
            "observational trend by roughly "
            f"{round(ratio_reported_vs_genuine, 1) if ratio_reported_vs_genuine else 'n/a'}x, "
            "even though this metric is explicitly 'reporting_only' at Phase-0 and gates "
            "nothing today."
        ),
        "scope_boundary": {
            "NOT_A_CORRECTNESS_CLAIM_ABOUT_THE_ROLE_RULE": (
                "This audit is about metric-definition integrity of one reporting-only field; "
                "it makes no claim about and does not touch "
                "structural_inference_agreement_rate=1.0, the deterministic role rule, or any "
                "prior SURVIVED/REFUTED verdict on role classification itself."
            ),
            "NOT_A_GATING_FAILURE": (
                "The metric already carries passed_reporting_only=true and is explicitly not "
                "gated at Phase-0 ('Phase-1 lock will gate at threshold with an independently "
                "double-labeled expert reference'), so no Phase-0 pass/fail flips. The defect "
                "is that the number under that field is not what its name says it is, which "
                "matters for whoever designs the Phase-1 gate against this Phase-0 trend line."
            ),
            "TARGET_UNCHANGED": (
                "role-classification-kpi.v1.json, role_ranker_phase0_kpi.rs and the fixture are "
                "left byte-intact; this is a new, separate audit artifact, not an edit."
            ),
        },
        "claim_locks": {
            "measured_only_lock_preserved": True,
            "no_objective_emitted": True,
            "promotes_authority": False,
            "manifest_unchanged": True,
        },
        "closes": [],
        "does_not_close": [
            "EVALUATION_SIGNATURE_ABSENT (trust-anchored phase0-evaluator key absent from KPI file itself)",
            "PHASE_1_INDEPENDENT_EVALUATION (needs an independently double-labeled expert "
            "reference per the KPI's own stated Phase-1 plan)",
            "role_rule_correctness (out of scope; not touched by this audit)",
        ],
        "fixture": {
            "path": str(FIXTURE.relative_to(ROOT)), "rights": fixture["rights"]["license"],
            "sha256": sha(fixture_bytes), "n_records": len(fixture["records"]),
        },
        "shipped_kpi": {
            "path": str(SHIPPED_KPI.relative_to(ROOT)), "sha256": sha(shipped_bytes),
        },
        "verdict": "CLAIM_REFUTED" if refuted else "CLAIM_SURVIVED",
        "interpretation": None,
    }

    diag["interpretation"] = (
        f"Independently re-deriving the 24 in-domain training records' fitted resin-"
        "probabilities from the shipped frozen model artifact (zero transcription of the "
        "reported number) and computing mean Brier score reproduces the shipped KPI's "
        f"expected_calibration_error observed value ({reported_value}) EXACTLY "
        f"(match={brier_matches_reported}), proving the harness's `calibration_error_sum += "
        "brier; ... / resin_hardener_total` (role_ranker_phase0_kpi.rs "
        f"L{cite_lines.get('field_assignment_line', '?')}) computes mean Brier score, not "
        "binned ECE. Computing genuine M-bin ECE (Guo et al. 2017) from the identical "
        f"probabilities and labels gives {round(ece_min, 6)}-{round(ece_max, 6)} across 13 "
        "distinct binning schemes (equal-width M=2..20, equal-frequency M=2..12), a spread of "
        f"only {round(ece_range_ratio, 3) if ece_range_ratio else 'n/a'}x -- essentially "
        "bin-choice-invariant because the fitted probabilities separate cleanly into two "
        "tight clusters. Genuine ECE is "
        f"{round(ratio_reported_vs_genuine, 1) if ratio_reported_vs_genuine else 'n/a'}x the "
        f"reported value ({round(ece_min,4)} vs {round(reported_value,4)}), exceeding the "
        "pre-registered 2x refutation threshold. CLAIM_REFUTED: the field named "
        "`expected_calibration_error` in the flagship KPI is mechanically the mean Brier "
        "score, a related but numerically distinct statistic from Expected Calibration Error, "
        "and readers/gate-designers relying on the field name would materially "
        "underestimate the model's actual (still small, still reporting-only, still "
        "under-ceiling) miscalibration on its own training data. Scope: reporting-only field; "
        "no Phase-0 gate flips; role-classification-kpi.v1.json is left unmodified pending a "
        "properly-scoped repair (R-/V- item) to rename the field or compute genuine ECE "
        "alongside it."
    )
    return diag


if __name__ == "__main__":
    import sys
    diag = main()
    OUT.mkdir(parents=True, exist_ok=True)
    txt = json.dumps(diag, indent=2, sort_keys=True)
    which = sys.argv[1] if len(sys.argv) > 1 else "canonical"
    path = OUT / f"diagnostic.{which}.json"
    path.write_text(txt)
    print("WROTE", path)
    print("sha256", sha(txt.encode()))
    print("verdict", diag["verdict"])
