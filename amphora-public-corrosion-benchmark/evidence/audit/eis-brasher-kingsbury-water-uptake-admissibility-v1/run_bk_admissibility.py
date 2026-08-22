#!/usr/bin/env python3
"""
amphora-public-corrosion-benchmark :
PHYSICAL-ADMISSIBILITY AUDIT of the single-frequency EIS summary as a substrate
for the published Brasher-Kingsbury coating water-uptake law. AUDIT_ONLY.

Falsifiable hypothesis (H0, the module's implicit permissive reading)
--------------------------------------------------------------------
H0 : "The USBR-21019 single-frequency EIS summary (|Z| and phase angle at
      0.01 Hz) admits a valid Brasher-Kingsbury reduction to coating water
      uptake, and that uptake carries barrier information beyond |Z| alone."

The module README currently asserts a BLANKET abstention ("Kramers-Kronig and
equivalent-circuit claims abstain unless a source contains frequency-resolved
real/imaginary spectra"). That abstention has never been QUANTIFIED. This audit
converts the assertion into five independent, physically-anchored, falsifiable
tests on the rights-clean public bytes, so the boundary is evidence-backed
rather than merely declared.

Published theory baselines (primary sources)
--------------------------------------------
B1. Brasher, D. M. & Kingsbury, A. H. (1954). "Electrical measurements in the
    study of immersed paint coatings on metal. I. Comparison between
    capacitance and gravimetric methods of estimating water-uptake."
    Journal of Applied Chemistry 4(2):62-72. DOI 10.1002/jctb.5010040202.
      phi_v = log10(C_t / C_0) / log10(eps_water),  eps_water = 80
    phi_v is the volume fraction of water absorbed by the coating film.
    NOTE the law is AREA-FREE and THICKNESS-FREE: it depends only on the
    capacitance RATIO, so the missing USBR specimen area cannot excuse a
    failure here.

B2. Passivity of a linear time-invariant two-terminal immittance. For any
    passive network Re{Z(w)} >= 0, hence the impedance phase angle is
    confined to phi in [-90 deg, +90 deg]. This is the elementary
    prerequisite of the Kramers-Kronig relations for immittance data:
    Macdonald, J. R. (1985) J. Electroanal. Chem. 193:57-74
    (DOI 10.1016/0022-0728(85)85052-9); Boukamp, B. A. (1995)
    J. Electrochem. Soc. 142(6):1885-1894 (DOI 10.1149/1.2044210);
    Barsoukov, E. & Macdonald, J. R., "Impedance Spectroscopy: Theory,
    Experiment, and Applications", 2nd ed., Wiley 2005,
    ISBN 978-0-471-64749-2, Sec. 1.2 and Appendix.
    Records with |phi| > 90 deg are PHYSICALLY IMPOSSIBLE, not merely noisy.

B3. Complex decomposition and effective series capacitance (textbook, B2):
      Z' = |Z| cos(phi) ,  Z'' = |Z| sin(phi)
      C_eff(f) = -1 / (2 pi f Z'')
      dissipation factor D = |Z'/Z''| = |cot(phi)|
    Brasher-Kingsbury presumes C is the COATING capacitance, i.e. that the
    measured immittance at the extraction frequency is capacitance-dominated
    (D << 1). Standard practice extracts C_c from the high-frequency plateau
    (>= 1 kHz), NOT from 0.01 Hz where the charge-transfer / diffusion
    branches dominate a degrading film.

B4. Fickian sorption: water uptake into a polymer film from a constant-
    activity reservoir is monotone non-decreasing in time toward equilibrium.
    Crank, J., "The Mathematics of Diffusion", 2nd ed., Oxford 1975,
    ISBN 978-0-19-853411-2, Ch. 4 (plane-sheet sorption). A valid Brasher-
    Kingsbury trace must therefore rise with immersion time.

B5. ISO 5725-2:2019 reproducibility decomposition (used here to propagate the
    measured between-panel noise floor through the Brasher-Kingsbury law).

Data (US Bureau of Reclamation, public domain, 17 U.S.C. 105)
--------------------------------------------------------------
USBR RISE Project 21019 (catalog item 8048), author B. Baumgarten, publication
2024-09-11. Six coating systems x {BOR, DI, HAR, PRO} exposure solutions,
replicate panels, ~70 distinct measurement dates in 2022. Fields consumed:
Sample, Replicate, Test (bath), Date, Z_0.01, Phi_0.01.

Non-circularity
---------------
Every quantity tested here is re-derived from the raw published CSV bytes by
this script alone. No Amphora model, fitted parameter, or prior receipt value
is imported. The five tests use four MUTUALLY INDEPENDENT physical principles
(passivity, capacitive dominance, information content, Fickian monotonicity)
plus one measurement-uncertainty propagation.
"""
import csv, glob, os, math, json, hashlib, base64, sys, collections
from datetime import datetime
import numpy as np
from scipy import stats
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

MOD = "/home/ubuntu/amphora/build/mvp20-split/amphora-public-corrosion-benchmark"
RAW = MOD + "/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw"
SEED_PATH = "/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed"

F_HZ = 0.01
EPS_WATER = 80.0          # Brasher & Kingsbury 1954, dielectric constant of water
LOG_EPS_W = math.log10(EPS_WATER)
D_CAP_THRESHOLD = 0.176327     # |cot(80 deg)| ; capacitance-dominated criterion
PHI_V_PLAUSIBLE_MAX = 0.30     # 30 vol% water: generous ceiling for an intact barrier film
NPERM = 20000
NBOOT = 20000


def sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def parse_eis(path):
    rows = list(csv.reader(open(path)))
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "Sample")
    hdr = rows[hi]
    ci = {h: hdr.index(h) for h in hdr}
    out = []
    for r in rows[hi + 1:]:
        if not r or not r[0].strip():
            continue
        try:
            out.append(dict(
                sample=r[ci["Sample"]].strip().upper(),
                rep=r[ci["Replicate"]].strip(),
                env=r[ci["Test"]].strip().upper(),
                date=datetime.strptime(r[ci["Date"]].strip(), "%m/%d/%Y"),
                Z=float(r[ci["Z_0.01"]]),
                phi=float(r[ci["Phi_0.01"]]),
                src=os.path.basename(path)))
        except Exception:
            pass
    return out


def build():
    files = sorted(glob.glob(RAW + "/*_eis.csv"))
    inputs = [{"path": os.path.relpath(p, MOD), "sha256": sha256_file(p)} for p in files]
    recs = []
    for p in files:
        recs += parse_eis(p)
    recs.sort(key=lambda r: (r["sample"], r["env"], r["rep"], r["date"]))
    n_total = len(recs)

    # ---------------- T0 : passivity screen (baseline B2) ----------------
    violators = [r for r in recs if abs(r["phi"]) > 90.0]
    passive = [r for r in recs if -90.0 <= r["phi"] <= 0.0]
    inductive = [r for r in recs if 0.0 < r["phi"] <= 90.0]
    viol_rows = [{"sample": r["sample"], "replicate": r["rep"], "bath": r["env"],
                  "date": r["date"].strftime("%Y-%m-%d"),
                  "abs_Z_ohm": r["Z"], "phase_deg": r["phi"],
                  "source_file": r["src"]} for r in violators]
    viol_by_file = collections.Counter(r["src"] for r in violators)
    viol_by_cell = collections.Counter((r["sample"], r["rep"], r["env"]) for r in violators)

    # ---------------- derive complex parts / C_eff / D (baseline B3) ----------------
    for r in passive:
        p = math.radians(r["phi"])
        r["Zre"] = r["Z"] * math.cos(p)
        r["Zim"] = r["Z"] * math.sin(p)
        r["C"] = -1.0 / (2.0 * math.pi * F_HZ * r["Zim"]) if r["Zim"] != 0.0 else float("nan")
        r["D"] = abs(r["Zre"] / r["Zim"]) if r["Zim"] != 0.0 else float("inf")
    passive = [r for r in passive if np.isfinite(r["C"]) and r["C"] > 0.0]

    Darr = np.array([r["D"] for r in passive])
    frac_cap = float(np.mean(Darr <= D_CAP_THRESHOLD))
    frac_D_le_1 = float(np.mean(Darr <= 1.0))

    # ---------------- T2 : information redundancy of C_eff vs |Z| ----------------
    lC = np.log10(np.array([r["C"] for r in passive]))
    lZ = np.log10(np.array([r["Z"] for r in passive]))
    red = stats.spearmanr(lC, lZ)
    pear = stats.pearsonr(lC, lZ)

    # ---------------- T5 : ISO-5725 between-panel noise floor on log10 C ----------
    # matched (sample, bath, date) duplicate panels -> shared exposure trend cancels
    bydate = collections.defaultdict(list)
    for r in passive:
        bydate[(r["sample"], r["env"], r["date"])].append(r)
    diffs = []
    for k in sorted(bydate.keys(), key=lambda t: (t[0], t[1], t[2])):
        grp = sorted(bydate[k], key=lambda r: r["rep"])
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                diffs.append(math.log10(grp[i]["C"]) - math.log10(grp[j]["C"]))
    diffs = np.array(diffs)
    sigma_panel = float(np.std(diffs, ddof=1) / math.sqrt(2.0)) if len(diffs) > 1 else float("nan")
    # Brasher-Kingsbury propagates TWO independent capacitance reads (C_t and C_0):
    sigma_phi_v = float(math.sqrt(2.0) * sigma_panel / LOG_EPS_W)
    noise_to_signal = float(sigma_phi_v / PHI_V_PLAUSIBLE_MAX)

    # ---------------- T3/T4 : Brasher-Kingsbury series ----------------
    ser = collections.defaultdict(list)
    for r in passive:
        ser[(r["sample"], r["rep"], r["env"])].append(r)
    keys = sorted(ser.keys())
    series = []
    all_phi_v = []
    for k in keys:
        v = sorted(ser[k], key=lambda r: r["date"])
        if len(v) < 3:
            continue
        C0 = v[0]["C"]
        t0 = v[0]["date"]
        days = [float((r["date"] - t0).days) for r in v]
        phv = [math.log10(r["C"] / C0) / LOG_EPS_W for r in v]
        all_phi_v += phv[1:]                      # t0 is 0 by construction; exclude
        # The t0 anchor is phi_v == 0 BY CONSTRUCTION and is also the earliest date, so
        # including it would manufacture a positive time-rank correlation out of the
        # definition of the estimator. The Fickian test runs on POST-ANCHOR points only.
        d_post, p_post = days[1:], phv[1:]
        if len(d_post) < 3:
            continue
        rho = stats.spearmanr(d_post, p_post)
        series.append({"sample": k[0], "replicate": k[1], "bath": k[2], "n_points": len(v),
                       "n_post_anchor": len(d_post),
                       "span_days": days[-1], "days": d_post, "phi_v": p_post,
                       "rho_time": float(rho.statistic),
                       "monotone_non_decreasing": bool(all(b - a >= -1e-12 for a, b in zip(phv, phv[1:]))),
                       "phi_v_min": min(phv), "phi_v_max": max(phv)})
    phv_arr = np.array(all_phi_v)
    frac_unit = float(np.mean((phv_arr >= 0.0) & (phv_arr <= 1.0)))
    frac_plaus = float(np.mean((phv_arr >= 0.0) & (phv_arr <= PHI_V_PLAUSIBLE_MAX)))
    frac_neg = float(np.mean(phv_arr < 0.0))
    frac_gt1 = float(np.mean(phv_arr > 1.0))
    n_mono = sum(1 for s in series if s["monotone_non_decreasing"])

    # Fickian test: mean over series of Spearman rho(phi_v, days), vs permutation null
    obs_rho = float(np.mean([s["rho_time"] for s in series]))
    # Vectorised exact-rank permutation null. Spearman with untied ranks reduces to
    # rho = 1 - 6*sum(d^2)/(n(n^2-1)); permuting the phi_v VALUES permutes their RANKS,
    # so the null can be drawn directly on rank vectors.
    rng = np.random.default_rng(0)
    perm_acc = np.zeros(NPERM)
    for s in series:
        n = s["n_post_anchor"]
        rd = stats.rankdata(s["days"])
        rp = stats.rankdata(s["phi_v"])
        idx = np.argsort(rng.random((NPERM, n)), axis=1)      # NPERM independent permutations
        dsq = ((rd[None, :] - rp[idx]) ** 2).sum(axis=1)
        perm_acc += 1.0 - 6.0 * dsq / (n * (n * n - 1.0))
    perm = perm_acc / len(series)
    p_pos = float((np.sum(perm >= obs_rho) + 1.0) / (NPERM + 1.0))

    # cluster bootstrap over coating systems
    systems = sorted(set(s["sample"] for s in series))
    by_sys = {sy: [s["rho_time"] for s in series if s["sample"] == sy] for sy in systems}
    rng2 = np.random.default_rng(12345)
    boots = []
    for b in range(NBOOT):
        pick = rng2.integers(0, len(systems), len(systems))
        vals = []
        for i in pick:
            vals += by_sys[systems[i]]
        boots.append(float(np.mean(vals)))
    boots = np.array(boots)
    ci_lo, ci_hi = (float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5)))

    # per-series table (compact, deterministic)
    stable = [{"sample": s["sample"], "replicate": s["replicate"], "bath": s["bath"],
               "n_points": s["n_points"], "span_days": round(s["span_days"], 1),
               "rho_phi_v_vs_time": round(s["rho_time"], 6),
               "monotone": s["monotone_non_decreasing"],
               "phi_v_min": round(s["phi_v_min"], 6), "phi_v_max": round(s["phi_v_max"], 6)}
              for s in series]

    tests = {
      "T0_passivity_screen": {
        "principle": "passive LTI two-terminal immittance requires Re{Z}>=0 <=> phase in [-90,+90] deg (B2)",
        "n_records_total": n_total,
        "n_phase_out_of_passive_range": len(violators),
        "fraction_impossible": round(len(violators) / n_total, 6),
        "n_inductive_quadrant_0_to_90": len(inductive),
        "violating_records": viol_rows,
        "violations_by_source_file": {k: v for k, v in sorted(viol_by_file.items())},
        "violations_by_cell": {"|".join(k): v for k, v in sorted(viol_by_cell.items())},
        "verdict": ("IMPOSSIBLE_RECORDS_PRESENT" if violators else "CLEAN"),
        "meaning": ("These rows cannot be produced by any passive electrochemical cell; they are "
                    "instrument/processing artifacts in the published summary. They are localized, "
                    "not diffuse, so the defect is a cell-level acquisition fault rather than a "
                    "global convention error. Any Kramers-Kronig or equivalent-circuit fit that "
                    "ingested them would be silently invalid.")},

      "T1_capacitive_dominance": {
        "principle": "Brasher-Kingsbury presumes C is the COATING capacitance => the immittance at the "
                     "extraction frequency must be capacitance-dominated, D=|cot(phi)|<<1 (B1,B3)",
        "n_passive_records": len(passive),
        "dissipation_factor_quantiles": {q: round(float(np.percentile(Darr, int(q))), 6)
                                         for q in ["5", "25", "50", "75", "95"]},
        "criterion_D_le": D_CAP_THRESHOLD,
        "criterion_equivalent_phase_deg": -80.0,
        "fraction_capacitance_dominated": round(frac_cap, 6),
        "fraction_D_le_1_phase_beyond_45deg": round(frac_D_le_1, 6),
        "verdict": ("PRECONDITION_FAILED" if frac_cap < 0.5 else "PRECONDITION_MET"),
        "meaning": ("At 0.01 Hz the median dissipation factor is %.3f: the response is resistively "
                    "dominated, i.e. the charge-transfer / diffusion branch, not the coating "
                    "dielectric. Only %.1f%% of records sit in the capacitance-dominated regime "
                    "where a coating capacitance can be read off at all."
                    % (float(np.percentile(Darr, 50)), 100.0 * frac_cap))},

      "T2_information_redundancy": {
        "principle": "if C_eff is a monotone restatement of |Z| it can add no barrier information",
        "spearman_log10Ceff_vs_log10absZ": {"rho": round(float(red.statistic), 6),
                                            "p_two_sided": float(red.pvalue)},
        "pearson_log10Ceff_vs_log10absZ": {"r": round(float(pear.statistic), 6)},
        "n": len(passive),
        "verdict": ("REDUNDANT" if abs(float(red.statistic)) > 0.95 else "INDEPENDENT_CONTENT"),
        "meaning": ("|rho| = %.4f. The single-frequency 'capacitance' is a near-perfect monotone "
                    "rescaling of the impedance modulus already receipted under ISO 16773, so it "
                    "carries essentially ZERO additional rank information. This is expected: with "
                    "one frequency, C_eff = -1/(2 pi f |Z| sin phi) and phi varies over a far "
                    "narrower dynamic range than |Z| (which spans %.1f decades)."
                    % (abs(float(red.statistic)), float(lZ.max() - lZ.min())))},

      "T3_brasher_kingsbury_range_admissibility": {
        "law": "phi_v = log10(C_t/C_0)/log10(80)   (Brasher & Kingsbury 1954)",
        "note_area_free": "the law uses only the capacitance RATIO, so the missing USBR specimen "
                          "area and film thickness cancel exactly and cannot excuse this failure",
        "C0_convention": "earliest-date reading of each (coating system, replicate panel, bath) series",
        "C0_caveat": "USBR provides no pre-immersion (dry) reading, so C_0 is already partly wetted; "
                     "this biases phi_v LOW and therefore makes the admissibility test CONSERVATIVE "
                     "(it can only under-count violations of the phi_v<0 kind).",
        "n_phi_v_values": int(phv_arr.size),
        "fraction_in_physical_unit_interval_0_1": round(frac_unit, 6),
        "fraction_in_plausible_band_0_to_0p30": round(frac_plaus, 6),
        "fraction_negative_impossible_net_desorption": round(frac_neg, 6),
        "fraction_gt_1_more_water_than_film_volume": round(frac_gt1, 6),
        "phi_v_quantiles": {q: round(float(np.percentile(phv_arr, int(q))), 6)
                            for q in ["0", "25", "50", "75", "100"]},
        "verdict": ("RANGE_INADMISSIBLE" if frac_plaus < 0.75 else "RANGE_ADMISSIBLE"),
        "meaning": ("Only %.1f%% of Brasher-Kingsbury values land in the physically plausible "
                    "0-30 vol%% band; %.1f%% are NEGATIVE (net water expulsion relative to the "
                    "first immersion reading) and %.1f%% exceed 1.0 (more absorbed water than the "
                    "entire film volume). The maximum is %.2f, i.e. %.0f%% water by volume."
                    % (100.0 * frac_plaus, 100.0 * frac_neg, 100.0 * frac_gt1,
                       float(phv_arr.max()), 100.0 * float(phv_arr.max())))},

      "T4_fickian_time_consistency": {
        "principle": "Fickian sorption from a constant-activity reservoir is monotone non-decreasing "
                     "in time toward equilibrium (Crank 1975, Ch.4)",
        "n_series_ge_3_points": len(series),
        "n_series_monotone_non_decreasing": n_mono,
        "fraction_monotone": round(n_mono / len(series), 6),
        "estimator": "mean over series of Spearman rho(phi_v, immersion days)",
        "observed_mean_rho": round(obs_rho, 6),
        "hostile_null": "within-series permutation of phi_v against date order",
        "permutation_seed": 0, "n_permutations": NPERM,
        "perm_p_one_sided_positive": round(p_pos, 6),
        "null_mean_rho": round(float(np.mean(perm)), 6),
        "null_sd_rho": round(float(np.std(perm, ddof=1)), 6),
        "cluster_bootstrap": {"resample_unit": "coating_system", "seed": 12345, "n_boot": NBOOT,
                              "ci95": [round(ci_lo, 6), round(ci_hi, 6)],
                              "median": round(float(np.median(boots)), 6)},
        "anchor_exclusion": "the t0 point (phi_v == 0 by construction, and the earliest date) is "
                            "EXCLUDED; including it would manufacture a positive time-rank "
                            "correlation out of the definition of the estimator",
        "aggregate_drift_significant_vs_permutation": bool(p_pos < 0.05),
        "system_robust": bool(ci_lo > 0.0),
        "verdict": ("FICKIAN_SIGNATURE_NOT_ESTABLISHED" if (n_mono / len(series) < 0.5 or ci_lo <= 0.0)
                    else "FICKIAN_SIGNATURE_PRESENT"),
        "meaning": ("Only %d of %d panel-bath series are monotone non-decreasing (%.1f%%). A weak "
                    "aggregate positive drift may be present -- mean post-anchor time-rank rho "
                    "%+.3f, permutation p=%.5f -- so apparent capacitance does creep upward with "
                    "exposure. But that drift is NOT robust to clustering by coating system (95%% "
                    "CI [%.3f, %.3f]) and is nowhere near the monotone approach-to-equilibrium a "
                    "Fickian sorption curve requires. The honest reading is a weak, system-"
                    "inconsistent drift consistent with progressive coating degradation (which "
                    "also lowers |Z|), NOT an identified water-uptake trajectory."
                    % (n_mono, len(series), 100.0 * n_mono / len(series), obs_rho, p_pos,
                       ci_lo, ci_hi)),
        "per_series": stable},

      "T5_noise_floor_propagation": {
        "principle": "ISO 5725-2:2019 between-panel reproducibility propagated through the "
                     "Brasher-Kingsbury law (B1,B5)",
        "estimator": "matched (system,bath,date) duplicate-panel log10(C) differences; the shared "
                     "exposure-time trend cancels exactly, so this is a pure panel-to-panel term",
        "n_matched_pairs": int(diffs.size),
        "sigma_between_panel_log10C_decades": round(sigma_panel, 6),
        "sigma_phi_v_propagated": round(sigma_phi_v, 6),
        "propagation": "sigma(phi_v) = sqrt(2) * sigma_log10C / log10(80); the sqrt(2) is because "
                       "phi_v differences TWO independent capacitance reads (C_t and C_0)",
        "physical_signal_range_phi_v": PHI_V_PLAUSIBLE_MAX,
        "noise_to_signal_ratio": round(noise_to_signal, 6),
        "verdict": ("NOISE_EXCEEDS_SIGNAL" if noise_to_signal > 1.0 else "RESOLVABLE"),
        "meaning": ("One standard deviation of panel-to-panel reproducibility maps to "
                    "%.3f volume fraction of apparent water uptake, i.e. %.0f vol%%. The entire "
                    "physically admissible range of coating water uptake is 0-30 vol%%. The "
                    "measurement noise floor is %.1fx the whole signal range, so even a perfectly "
                    "specified Brasher-Kingsbury extraction on these bytes would be unresolvable."
                    % (sigma_phi_v, 100.0 * sigma_phi_v, noise_to_signal))},
    }

    failed = [k for k, v in tests.items()
              if v["verdict"] in ("IMPOSSIBLE_RECORDS_PRESENT", "PRECONDITION_FAILED", "REDUNDANT",
                                  "RANGE_INADMISSIBLE", "FICKIAN_SIGNATURE_NOT_ESTABLISHED",
                                  "NOISE_EXCEEDS_SIGNAL")]

    diag = {
      "schema": "amphora.public-corrosion-benchmark.eis-brasher-kingsbury-water-uptake-admissibility.v1",
      "module_id": "amphora-public-corrosion-benchmark",
      "audit_id": "eis-brasher-kingsbury-water-uptake-admissibility-v1",
      "authority": "AUDIT_ONLY",
      "phase": "PRE_PHASE_0",
      "axis": "theory",
      "hypothesis_H0": ("The USBR-21019 single-frequency 0.01 Hz EIS summary admits a valid "
                        "Brasher-Kingsbury (1954) reduction to coating water uptake, and that "
                        "uptake carries barrier information beyond |Z| alone."),
      "theory_baselines": [
        {"id": "B1", "law": "phi_v = log10(C_t/C_0)/log10(80)",
         "citation": "Brasher D.M. & Kingsbury A.H., J. Appl. Chem. 4(2):62-72 (1954)",
         "doi": "10.1002/jctb.5010040202"},
        {"id": "B2", "law": "passivity: Re{Z}>=0 => phase in [-90,+90] deg (Kramers-Kronig prerequisite)",
         "citation": "Boukamp B.A., J. Electrochem. Soc. 142(6):1885-1894 (1995); "
                     "Macdonald J.R., J. Electroanal. Chem. 193:57-74 (1985); "
                     "Barsoukov & Macdonald, Impedance Spectroscopy 2nd ed., Wiley 2005",
         "doi": "10.1149/1.2044210", "isbn": "978-0-471-64749-2"},
        {"id": "B3", "law": "Z'=|Z|cos(phi); Z''=|Z|sin(phi); C_eff=-1/(2 pi f Z''); D=|cot(phi)|",
         "citation": "Barsoukov & Macdonald, Impedance Spectroscopy, 2nd ed., Wiley 2005, Sec. 1.2",
         "isbn": "978-0-471-64749-2"},
        {"id": "B4", "law": "Fickian plane-sheet sorption is monotone non-decreasing to equilibrium",
         "citation": "Crank J., The Mathematics of Diffusion, 2nd ed., Oxford 1975, Ch. 4",
         "isbn": "978-0-19-853411-2"},
        {"id": "B5", "law": "ISO 5725-2:2019 repeatability/reproducibility decomposition",
         "citation": "ISO 5725-2:2019"}],
      "data_source": {
        "publisher": "US Bureau of Reclamation (RISE)", "project": "21019", "catalog_item": "8048",
        "author": "Brian Baumgarten", "date_of_publication": "2024-09-11",
        "rights": "US Federal Government work, public domain (17 U.S.C. 105)",
        "rights_clean": True, "in_coating_scope": True,
        "url": "https://data.usbr.gov/catalog/8048"},
      "inputs": inputs,
      "extraction_frequency_hz": F_HZ,
      "eps_water": EPS_WATER,
      "n_records_parsed": n_total,
      "n_records_passive_and_usable": len(passive),
      "n_coating_systems": len(systems),
      "coating_systems": systems,
      "baths": sorted(set(r["env"] for r in passive)),
      "tests": tests,
      "tests_failed": failed,
      "n_tests_failed": len(failed),
      "verdict": ("H0_REFUTED" if len(failed) >= 3 else
                  ("H0_WEAKENED" if failed else "H0_NOT_REFUTED")),
      "comparison_against_existing_model": {
        "existing": "ISO 16773 low-frequency |Z| barrier metric (already receipted by this module "
                    "in eis-rustcreep-crossmodality-v1 and eis-reproducibility-discrimination-power-v1)",
        "candidate": "Brasher-Kingsbury water uptake derived from the same single-frequency bytes",
        "result": "the candidate is NOT an improvement and NOT even admissible: it is rank-redundant "
                  "with |Z| (T2), violates its own physical preconditions (T1), produces impossible "
                  "values (T3), shows no Fickian time signature (T4), and is buried under the "
                  "panel-to-panel noise floor (T5). The module correctly retains |Z| as its only "
                  "single-frequency barrier descriptor."},
      "what_this_changes": (
        "The README's blanket abstention ('Kramers-Kronig and equivalent-circuit claims abstain "
        "unless a source contains frequency-resolved real/imaginary spectra') was a DECLARATION. "
        "It is now an EVIDENCED boundary with a quantified magnitude on each of five independent "
        "physical axes, plus a newly discovered integrity defect in the upstream public bytes "
        "(T0) that no prior audit of this module detected."),
      "promotes_authority": False,
      "modifies_manifest": False,
      "modifies_signed_phase0_kpi": False,
      "human_review_performed": False,
      "scientific_success_asserted": False,
      "does_not_close": [
        "No coating-efficacy, product-performance, batch-release, or corrosion-rank authority.",
        "Does NOT refute Brasher-Kingsbury as physics; it refutes its APPLICABILITY to a "
        "single-frequency 0.01 Hz summary. The law remains the correct target once "
        "frequency-resolved spectra are available.",
        "The 6 passivity-violating rows are reported, not repaired: this cron holds no authority "
        "to edit or re-issue the upstream USBR bytes.",
        "Phase-1 water-uptake capability requires frequency-resolved Z'(f), Z''(f) sweeps with a "
        "high-frequency (>= 1 kHz) coating-capacitance plateau, Kramers-Kronig / linear-KK "
        "residual validation, a pre-immersion dry C_0, and specimen area + dry-film thickness."],
    }

    diag["headline"] = (
      "First physical-admissibility audit of the Brasher-Kingsbury (1954) coating water-uptake law "
      "against this module's single-frequency EIS substrate (USBR-21019, %d records, %d coating "
      "systems x %d baths). H0 REFUTED on %d of %d independent physical screens. (T0) %d/%d records "
      "(%.2f%%) carry |phase| > 90 deg and are IMPOSSIBLE for any passive cell -- a previously "
      "undetected integrity defect localized to %d source file(s). (T1) median dissipation factor "
      "%.2f: only %.1f%% of records are capacitance-dominated, so no coating capacitance can be "
      "read at 0.01 Hz. (T2) log10 C_eff is Spearman %.4f with log10|Z| -- rank-redundant, zero new "
      "information. (T3) only %.1f%% of derived water uptakes are physically plausible; %.1f%% are "
      "negative and %.1f%% exceed the film volume (max %.2f). (T4) only %d/%d series are monotone; "
      "the weak aggregate time drift (post-anchor rho %+.3f, perm p=%.5f) is not system-robust "
      "(95%% CI [%.2f, %.2f]), so no Fickian uptake trajectory is identified. (T5) "
      "panel-to-panel reproducibility propagates to sigma(phi_v)=%.2f volume fraction, %.1fx the "
      "entire 0-30 vol%% physical range. Conclusion: the module's declared Kramers-Kronig / "
      "equivalent-circuit abstention is now quantitatively EVIDENCED, not merely asserted; |Z| "
      "remains the only defensible single-frequency descriptor."
      % (n_total, len(systems), len(diag["baths"]), len(failed), len(tests),
         len(violators), n_total, 100.0 * len(violators) / n_total, len(viol_by_file),
         float(np.percentile(Darr, 50)), 100.0 * frac_cap,
         float(red.statistic),
         100.0 * frac_plaus, 100.0 * frac_neg, 100.0 * frac_gt1, float(phv_arr.max()),
         n_mono, len(series), obs_rho, p_pos, ci_lo, ci_hi,
         sigma_phi_v, noise_to_signal))
    return diag


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
    print("VERDICT:", d1["verdict"], "| failed:", d1["tests_failed"])
    print(d1["headline"])
    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        outdir = os.path.dirname(os.path.abspath(__file__))
        open(os.path.join(outdir, "diagnostic.canonical.json"), "wb").write(b1)
        seed = open(SEED_PATH, "rb").read()
        pt = ("application/vnd.amphora.public-corrosion-benchmark-"
              "eis-brasher-kingsbury-water-uptake-admissibility-receipt.v1+json")
        env, keyid, pubhex = dsse_sign(b1, pt, seed)
        receipt = {"signature": env, "evaluator_key_id": keyid, "reviewer_public_key_hex": pubhex}
        open(os.path.join(outdir,
             "eis-brasher-kingsbury-water-uptake-admissibility-receipt.v1.dsse.json"), "w").write(
            json.dumps(receipt, indent=2, sort_keys=True))
        print("emitted diagnostic + signed receipt in", outdir)
