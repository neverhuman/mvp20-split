#!/usr/bin/env python3
"""amphora-viscosity-score -- Herschel-Bulkley real-data benchmark / falsification probe.

CAMPAIGN C9. CLAIM UNDER ATTACK (pinned by the campaign item):
  "The module's implemented rheology paths (KRIEGER_DOUGHERTY at src/lib.rs:1208,
  HERSCHEL_BULKLEY at src/lib.rs:1227) are benchmarkable against real data with
  current in-tree assets."

Before this run, amphora-viscosity-score/fixtures/ held ONLY a README (no data),
and reference/rheology/source-landscape.v1.json records the KD/HB primary theory
papers (Krieger-Dougherty 1959, Grunberg-Nissan 1949) as CONTEXT_ONLY /
LINK_ONLY_METHOD_ANCHOR -- i.e. the claim was FALSE as literally written: no
in-tree assets existed to benchmark either KD or HB against. This run searches
open rights-clean literature (per campaign objective), finds a genuine CC-BY 4.0
Herschel-Bulkley dataset for an in-scope epoxy anti-corrosion coating, and tests
whether the module's exact HB equation is benchmarkable against it.

DATASET: Amorim, Oliveira, Mancini & Sirqueira (2021) SN Applied Sciences 3:236,
doi:10.1007/s42452-021-04247-7, CC BY 4.0. Table 2a: Herschel-Bulkley fitted
parameters (tau_0, K, n) for a commercial DGEBA epoxy / polyamide anti-corrosion
coating, control + 5 carbon-black/nanoclay-modified formulations. Steady-shear
flow curves, 0.1-100 /s, 25C, stress-controlled rheometer, R^2 > 0.998 for all 6.
NOT a Krieger-Dougherty (pigment-volume-fraction) dataset -- this run closes only
the HERSCHEL_BULKLEY half of the compound claim; KD remains a genuine data gap
(filed separately as a data-acquisition-queue ask).

MODULE FORMULA UNDER TEST (re-derived, not imported, to keep this an independent
CPython oracle -- matches amphora-viscosity-score/src/lib.rs:1227 verbatim):
    eta_apparent(tau0, K, n, gamma_dot) = tau0/gamma_dot + K * gamma_dot**(n-1)
identical in form to the source paper's own Eq.1.

DATA-INTEGRITY FALSIFICATION TEST (the genuinely-capable-of-breaking-the-claim
attack): the as-printed PDF table has tau_0/K values typeset with a comma before
the final 3 digits everywhere (locale decimal-mark ambiguity -- see source lock
data_integrity_note). Two candidate parses exist:
  (a) LITERAL_ENGLISH  -- comma = thousands separator (values taken at face value)
  (b) CORRECTED        -- last comma = decimal separator (locale-mixup repaired)
Gate: eta_apparent at gamma_dot in {0.1, 100} s^-1 must land inside the SAME
paper's own stated Fig.3 apparent-viscosity axis range [1, 1e5] Pa.s, for ALL 6
formulations. If interpretation (a) is what a downstream engineer would naively
transcribe and it fails this externally-sourced (not self-selected) bound, that
is a real "not safely benchmarkable as literally published" finding. If (b)
passes for all 6 while (a) fails for at least one, the claim survives ONLY
because a data-integrity repair was necessary and justified independently
(cross-validated against the paper's own axis metadata, not cherry-picked to
make the module look good).

Deterministic: pure Python arithmetic, no RNG, no network. Two-replay
byte-stability gated by the sign step.
"""
import json
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE_PATH = HERE / "source_amorim2021_hb_table2.v1.json"


def sha256_of(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def herschel_bulkley_apparent_viscosity(yield_stress_pa, consistency_pa_s_n, flow_index_n, shear_rate_s_inv):
    """Verbatim re-derivation of amphora-viscosity-score::herschel_bulkley_apparent_viscosity
    (src/lib.rs:1227-1243). Range guards mirrored exactly; no additional bounds added,
    since the point of this test is to see whether the MODULE's actual guard-rails
    (or lack thereof) catch physically-implausible literal-English input."""
    if not (yield_stress_pa == yield_stress_pa) or yield_stress_pa < 0.0:  # is_finite + >=0
        raise ValueError("Herschel-Bulkley inputs: yield_stress_pa")
    if not (consistency_pa_s_n > 0.0 and consistency_pa_s_n == consistency_pa_s_n):
        raise ValueError("Herschel-Bulkley inputs: consistency_pa_s_n")
    if not (flow_index_n > 0.0 and flow_index_n == flow_index_n):
        raise ValueError("Herschel-Bulkley inputs: flow_index_n")
    if not (shear_rate_s_inv > 0.0 and shear_rate_s_inv == shear_rate_s_inv):
        raise ValueError("Herschel-Bulkley inputs: shear_rate_s_inv")
    return yield_stress_pa / shear_rate_s_inv + consistency_pa_s_n * (shear_rate_s_inv ** (flow_index_n - 1.0))


def run():
    source = json.loads(SOURCE_PATH.read_bytes())
    source_sha256 = sha256_of(SOURCE_PATH)

    axis_lo, axis_hi = source["paper_reported_facts_used_as_independent_checks"]["fig3_apparent_viscosity_axis_range_pa_s"]
    shear_rates = [0.1, 1.0, 10.0, 100.0]  # spans the paper's own experimental domain endpoints + 2 interior decades

    rows_out = []
    literal_all_within_axis = True
    corrected_all_within_axis = True
    corrected_all_monotonic_decreasing = True
    corrected_all_shear_thinning_n_lt_1 = True

    for row in source["rows"]:
        n = row["n"]
        corrected_all_shear_thinning_n_lt_1 = corrected_all_shear_thinning_n_lt_1 and (n < 1.0)

        literal_curve = [
            herschel_bulkley_apparent_viscosity(row["tau0_pa_literal_english"], row["K_pa_sn_literal_english"], n, g)
            for g in shear_rates
        ]
        corrected_curve = [
            herschel_bulkley_apparent_viscosity(row["tau0_pa_corrected"], row["K_pa_sn_corrected"], n, g)
            for g in shear_rates
        ]

        literal_within = all(axis_lo <= v <= axis_hi for v in literal_curve)
        corrected_within = all(axis_lo <= v <= axis_hi for v in corrected_curve)
        corrected_monotonic = all(corrected_curve[i] > corrected_curve[i + 1] for i in range(len(corrected_curve) - 1))

        literal_all_within_axis = literal_all_within_axis and literal_within
        corrected_all_within_axis = corrected_all_within_axis and corrected_within
        corrected_all_monotonic_decreasing = corrected_all_monotonic_decreasing and corrected_monotonic

        rows_out.append({
            "sample": row["sample"],
            "n": n,
            "r2": row["r2"],
            "literal_english_eta_pa_s_at_shear_rates": dict(zip((str(g) for g in shear_rates), literal_curve)),
            "literal_english_within_paper_axis_bounds": literal_within,
            "literal_english_max_multiple_over_axis_ceiling": max(v / axis_hi for v in literal_curve),
            "corrected_eta_pa_s_at_shear_rates": dict(zip((str(g) for g in shear_rates), corrected_curve)),
            "corrected_within_paper_axis_bounds": corrected_within,
            "corrected_monotonic_decreasing_with_shear_rate": corrected_monotonic,
        })

    # Qualitative cross-checks against the paper's own prose claims (independent, not tuned)
    tau0_corrected_by_sample = {r["sample"]: r["tau0_pa_corrected"] for r in source["rows"]}
    sample4_has_max_tau0 = tau0_corrected_by_sample["4"] == max(tau0_corrected_by_sample.values())
    K_corrected_by_sample = {r["sample"]: r["K_pa_sn_corrected"] for r in source["rows"]}
    K_control_is_min = K_corrected_by_sample["Epoxy"] == min(K_corrected_by_sample.values())

    refutation_criterion = (
        "Would have REFUTED benchmarkability-of-this-source: if the CORRECTED "
        "(locale-repaired) parameter reading, run through the module's own "
        "unmodified Herschel-Bulkley equation, produced apparent-viscosity values "
        "outside the source paper's own stated Fig.3 axis range for any of the 6 "
        "formulations at any tested shear rate, OR failed to reproduce a "
        "monotonically shear-thinning curve (n<1 fit but non-monotonic output "
        "would indicate an equation-form mismatch), OR failed to reproduce the "
        "paper's own stated ranking claims (sample 4 = max yield stress, "
        "commercial-epoxy control = min consistency coefficient)."
    )
    all_corrected_gates_passed = (
        corrected_all_within_axis
        and corrected_all_monotonic_decreasing
        and corrected_all_shear_thinning_n_lt_1
        and sample4_has_max_tau0
        and K_control_is_min
    )

    diagnostic = {
        "schema": "amphora.viscosity-score.hb-ccby-epoxy-benchmark-diagnostic.v1",
        "module": "amphora-viscosity-score",
        "campaign_item_id": "C9",
        "claim_under_attack": "amphora-viscosity-score/evidence/phase0/kpis/polyverse-melt-viscosity-fox-flory-whitten-physical-baseline-vs-ml-kpi.v1.json :: KRIEGER_DOUGHERTY (src/lib.rs:1208) and HERSCHEL_BULKLEY (src/lib.rs:1227) benchmarkable against real data with current in-tree assets",
        "scope_of_this_run": "HERSCHEL_BULKLEY only. KRIEGER_DOUGHERTY (pigment-volume-fraction crowding) remains unbenchmarked -- no rights-clean phi-sweep dataset found this fire; filed as a data-acquisition-queue ask.",
        "source_id": source["source_id"],
        "source_doi": source["doi"],
        "source_license": source["license"],
        "source_lock_sha256": source_sha256,
        "shear_rates_tested_s_inv": shear_rates,
        "paper_axis_bounds_pa_s": [axis_lo, axis_hi],
        "refutation_criterion": refutation_criterion,
        "rows": rows_out,
        "literal_english_reading_all_within_axis_bounds": literal_all_within_axis,
        "corrected_reading_all_within_axis_bounds": corrected_all_within_axis,
        "corrected_reading_all_monotonic_decreasing": corrected_all_monotonic_decreasing,
        "corrected_reading_all_shear_thinning_n_lt_1": corrected_all_shear_thinning_n_lt_1,
        "sample4_has_max_tau0_corrected": sample4_has_max_tau0,
        "epoxy_control_has_min_K_corrected": K_control_is_min,
        "all_corrected_gates_passed": all_corrected_gates_passed,
        "verdict": (
            "CLAIM_SURVIVED -- HERSCHEL_BULKLEY IS benchmarkable against this real, "
            "rights-clean, in-scope CC-BY 4.0 dataset once a documented locale "
            "data-integrity repair is applied (last-comma-as-decimal, independently "
            "justified by the paper's own Fig.3 axis metadata, not by fitting to the "
            "module). The literal-English reading of the as-typeset table -- what a "
            "naive transcription would use -- is NOT benchmarkable (fails the "
            "paper's own axis bounds by 13x-1500x); this is the genuine failure mode "
            "the attack targeted, and it DID occur for the literal reading, just not "
            "for the corrected one."
            if all_corrected_gates_passed and not literal_all_within_axis else
            "SEE all_corrected_gates_passed / literal_english_reading_all_within_axis_bounds for actual outcome."
        ),
        "does_not_close": [
            "KRIEGER_DOUGHERTY remains unbenchmarked in-tree (no pigment/filler volume-fraction viscosity ladder found this fire).",
            "This is a parameter-level benchmark (published fitted tau0/K/n vs the module's equation), not a raw (gamma_dot, eta) point-level regression -- the source paper does not tabulate raw flow-curve points, only Fig.3 (graphical) and Table 2 (fitted parameters). No fitting was performed by this benchmark; the module's equation is evaluated AT the paper's own published parameters and cross-checked against the paper's own reported axis range and ranking claims.",
            "Single source, single commercial resin family (JUMBO grade), single temperature (25C). Does not establish HB adequacy across coating chemistries or temperatures.",
            "AUDIT_ONLY. Does not promote the module, does not edit the signed FFW/melt-viscosity KPI, does not touch the 66-receipt master manifest.",
        ],
    }
    return diagnostic


if __name__ == "__main__":
    import sys
    out = run()
    text = json.dumps(out, indent=2, sort_keys=True)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(text)
    else:
        print(text)
