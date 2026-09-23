#!/usr/bin/env python3
"""
amphora-process-qc-twin : Average-Run-Length (ARL) performance characterization
of the module's live SPC detector stack (AUDIT_ONLY).

Motivation
----------
The live module (amphora-formulation-capabilities/src/lib.rs, capability
`audit_process_qc`) runs three detectors at fixed designs:
  * Shewhart Individuals, symmetric 3-sigma limits
  * EWMA, lambda = 0.20, L = 3
  * standardized tabular CUSUM, k = 0.5, h = 5
The existing signed Phase-0 KPI receipt establishes only ARITHMETIC
correctness (bit-exact recompute of the three recursions) and binary
seeded-shift RECALL on 10 self-authored synthetic universes. It does NOT
characterize the detectors' RUN-LENGTH performance -- i.e. how often each
detector false-alarms on an in-control process (ARL0) and how quickly it
detects a sustained mean shift (ARL1). ARL is the canonical, published metric
that governs the module's own locked KPI target ("false alarms <= 5%,
seeded-control recall >= 90%, zero false releases"). This audit supplies the
FIRST published-theory second-signal for those thresholds.

Non-circular published baselines
--------------------------------
[Shewhart]  Geometric run-length. For symmetric L-sigma limits on i.i.d.
            N(delta,1) individuals, ARL(delta) = 1 / [Phi(-L+delta)+Phi(-L-delta)].
            Anchor ARL0(3-sigma) = 370.4.
            Source: Shewhart 1931; Montgomery 2020, "Introduction to Statistical
            Quality Control" 8th ed., Ch. 6; NIST/SEMATECH e-Handbook 6.3.1.
[CUSUM]     Siegmund's (1985) closed-form ARL approximation for the one-sided
            standardized CUSUM: ARL = [exp(-2*D*b) + 2*D*b - 1] / (2*D^2), with
            b = h + 1.166 (continuity correction) and D = delta - k. Two-sided
            ARL0 = one-sided/2. Anchor (Montgomery 2020 Table 9.4, two-sided,
            k=1/2, h=5): {0:465, 0.25:139, 0.5:38.0, 0.75:17.0, 1.0:10.4,
            1.5:5.75, 2.0:4.01}.
            Source: Page 1954; Siegmund 1985, "Sequential Analysis" (Springer,
            ISBN 978-0-387-96134-7); Montgomery 2020, Ch. 9.1.
[EWMA]      Brook-Evans (1972) / Lucas-Saccucci (1990) Markov-chain ARL. The
            in-control band [-L*sigma_z, +L*sigma_z] with sigma_z =
            sqrt(lambda/(2-lambda)) is discretized into N states; the run length
            solves (I - R) * mu = 1. Validated at the limiting case lambda -> 1
            (EWMA collapses to Shewhart), which must reproduce the exact
            geometric ARL0.
            Source: Roberts 1959; Brook & Evans 1972 Biometrika 59(3):539-549;
            Lucas & Saccucci 1990 Technometrics 32(1):1-12; Crowder 1987
            Technometrics 29(4):401-407.

Honest ceiling
--------------
ARL theory assumes i.i.d. normal in-control data with KNOWN mu, sigma. Real
batch QC estimates the limits from a finite baseline; the estimated-parameter
Individuals chart has a materially SHORTER in-control ARL0 and a highly
right-skewed ARL distribution (Quesenberry 1993 J.Qual.Technol. 25(4):237-247;
Jensen et al. 2006). This characterization therefore bounds the BEST-CASE
(known-parameter) run-length performance only; it does not establish real-batch
acceptability and does not grant release authority.
"""
import base64, hashlib, json, math, sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-process-qc-twin"
HERE = MOD / "evidence/audit/spc-arl-characterization-v1"

# ------------------------------------------------------------------ helpers
def Phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# ------------------------------------------------------------------ Shewhart
def shewhart_arl(L, delta):
    p = Phi(-L + delta) + Phi(-L - delta)
    return 1.0 / p

# ------------------------------------------------------------------ CUSUM (Siegmund 1985)
def cusum_arl_oneside(k, h, delta):
    b = h + 1.166
    D = delta - k
    if abs(D) < 1e-9:
        return b * b            # analytic limit as D -> 0
    return (math.exp(-2.0 * D * b) + 2.0 * D * b - 1.0) / (2.0 * D * D)

# ------------------------------------------------------------------ EWMA Markov chain
def ewma_arl(lam, L, delta, m):
    """Brook-Evans / Lucas-Saccucci discretized ARL. sigma=1, start at z0=0."""
    sig_z = math.sqrt(lam / (2.0 - lam))     # asymptotic EWMA sigma
    H = L * sig_z
    N = 2 * m + 1
    w = 2.0 * H / N
    mids = [-H + (i + 0.5) * w for i in range(N)]
    R = [[0.0] * N for _ in range(N)]
    for i in range(N):
        base = (1.0 - lam) * mids[i]
        for j in range(N):
            lo = -H + j * w
            hi = lo + w
            xl = (lo - base) / lam
            xh = (hi - base) / lam
            R[i][j] = Phi(xh - delta) - Phi(xl - delta)
    # solve (I - R) mu = 1 by Gaussian elimination with partial pivoting
    A = [[(1.0 if i == j else 0.0) - R[i][j] for j in range(N)] for i in range(N)]
    bvec = [1.0] * N
    for c in range(N):
        pr, piv = c, abs(A[c][c])
        for r in range(c + 1, N):
            if abs(A[r][c]) > piv:
                pr, piv = r, abs(A[r][c])
        if pr != c:
            A[c], A[pr] = A[pr], A[c]
            bvec[c], bvec[pr] = bvec[pr], bvec[c]
        pivot = A[c][c]
        for r in range(N):
            if r != c and A[r][c] != 0.0:
                f = A[r][c] / pivot
                for kk in range(c, N):
                    A[r][kk] -= f * A[c][kk]
                bvec[r] -= f * bvec[c]
    return bvec[m] / A[m][m]     # center state = z0 = 0

# ------------------------------------------------------------------ published anchors
SHEWHART_PUB = {0.0: 370.4, 0.5: 155.2, 1.0: 43.9, 1.5: 15.0, 2.0: 6.30, 3.0: 2.00}  # Montgomery 2020 Ch.6
CUSUM_PUB = {0.0: 465.0, 0.25: 139.0, 0.5: 38.0, 0.75: 17.0, 1.0: 10.4, 1.5: 5.75, 2.0: 4.01}  # Montgomery Table 9.4 (2-sided k=1/2 h=5)
SHEWHART_TOL = 0.01     # geometric formula vs rounded published table
CUSUM_TOL = 0.06        # Siegmund documented approximation, small-shift regime
EWMA_LIMIT_TOL = 0.005  # limiting-case discretization error

def relerr(a, b):
    return abs(a - b) / abs(b)

def build():
    # ---- Shewhart known-answer -------------------------------------------
    L_shew = 3.0
    shew = []
    for d in sorted(SHEWHART_PUB):
        got = shewhart_arl(L_shew, d)
        pub = SHEWHART_PUB[d]
        shew.append({"shift_sigma": d, "arl_computed": round(got, 4),
                     "arl_published": pub, "rel_err": round(relerr(got, pub), 5),
                     "within_tol": relerr(got, pub) <= SHEWHART_TOL})
    shew_pass = all(r["within_tol"] for r in shew)
    shew_maxerr = max(r["rel_err"] for r in shew)

    # ---- CUSUM known-answer (Siegmund vs Montgomery Table 9.4) ------------
    k_c, h_c = 0.5, 5.0
    cus = []
    for d in sorted(CUSUM_PUB):
        pub = CUSUM_PUB[d]
        if d == 0.0:
            got = cusum_arl_oneside(k_c, h_c, 0.0) / 2.0   # two-sided in-control
        else:
            got = cusum_arl_oneside(k_c, h_c, d)           # detecting arm dominates
        cus.append({"shift_sigma": d, "arl_computed": round(got, 4),
                    "arl_published": pub, "rel_err": round(relerr(got, pub), 5),
                    "within_tol": relerr(got, pub) <= CUSUM_TOL})
    cus_pass = all(r["within_tol"] for r in cus)
    cus_maxerr = max(r["rel_err"] for r in cus)
    # informational large-shift (Siegmund known to degrade; Shewhart dominates here)
    cusum_largeshift_info = {str(d): round(cusum_arl_oneside(k_c, h_c, d), 3) for d in [3.0, 4.0]}

    # ---- EWMA Markov-chain validation via limiting case ------------------
    ewma_limit = []
    for (lam, L, expect, label) in [(1.0, 3.0, shewhart_arl(3.0, 0.0), "lambda->1 recovers Shewhart 3-sigma"),
                                    (1.0, 2.7, shewhart_arl(2.7, 0.0), "lambda->1 recovers Shewhart 2.7-sigma")]:
        got = ewma_arl(lam, L, 0.0, m=60)
        ewma_limit.append({"lambda": lam, "L": L, "arl0_computed": round(got, 4),
                           "arl0_exact_geometric": round(expect, 4),
                           "rel_err": round(relerr(got, expect), 6),
                           "within_tol": relerr(got, expect) <= EWMA_LIMIT_TOL,
                           "note": label})
    ewma_limit_pass = all(r["within_tol"] for r in ewma_limit)

    # ---- EWMA module-design characterization (computed, grid-converged) ---
    lam_m, L_m = 0.20, 3.0
    m1, m2 = 100, 200
    arl0_m1 = ewma_arl(lam_m, L_m, 0.0, m=m1)
    arl0_m2 = ewma_arl(lam_m, L_m, 0.0, m=m2)
    ewma_shifts = []
    for d in [0.5, 1.0, 1.5, 2.0]:
        a1 = ewma_arl(lam_m, L_m, d, m=m1)
        a2 = ewma_arl(lam_m, L_m, d, m=m2)
        ewma_shifts.append({"shift_sigma": d, "arl_m100": round(a1, 4),
                            "arl_m200": round(a2, 4), "grid_rel_change": round(relerr(a1, a2), 6)})
    ewma_module = {
        "design": {"lambda": lam_m, "L": L_m, "sigma_z_asymptotic": round(math.sqrt(lam_m/(2.0-lam_m)), 6),
                   "asymptotic_limit_sigma_units": round(L_m*math.sqrt(lam_m/(2.0-lam_m)), 6)},
        "arl0_m100": round(arl0_m1, 3), "arl0_m200": round(arl0_m2, 3),
        "arl0_grid_rel_change": round(relerr(arl0_m1, arl0_m2), 6),
        "arl1_by_shift": ewma_shifts,
        "interpretation": ("L=3 is a CONSERVATIVE EWMA design: computed ARL0 ~%.0f exceeds the "
                           "canonical lambda=0.2 tuning (L=2.86 -> ARL0=370), i.e. FEWER false "
                           "alarms at the cost of slightly slower small-shift detection. Reported "
                           "as a computed characterization (grid-converged), cross-anchored by the "
                           "lambda->1 limiting case above." % arl0_m2),
    }

    # ---- KPI-relevant derived quantities (ties ARL theory to locked KPI) --
    # module monitoring windows are 20-50 obs; locked KPI budgets <=5% false alarms
    arl0 = {"shewhart_3sigma": shewhart_arl(3.0, 0.0),
            "cusum_k0.5_h5_two_sided": cusum_arl_oneside(0.5, 5.0, 0.0)/2.0,
            "ewma_lam0.2_L3": arl0_m2}
    windows = [20, 30, 50]
    fa = {det: {str(n): round(n/arl, 4) for n in windows} for det, arl in arl0.items()}
    # union upper bound (Bonferroni) expected false alarms per 30-batch window
    union_fa_30 = round(sum(30.0/arl for arl in arl0.values()), 4)
    # detection speed at a 1-sigma sustained shift
    arl1_1sig = {"shewhart_3sigma": round(shewhart_arl(3.0, 1.0), 3),
                 "cusum_k0.5_h5": round(cusum_arl_oneside(0.5, 5.0, 1.0), 3),
                 "ewma_lam0.2_L3": round(ewma_arl(0.2, 3.0, 1.0, m=m2), 3)}
    kpi_link = {
        "module_locked_kpi": "prospective 30-batch pilot: seeded-control recall >=90%, false alarms <=5%, zero false releases",
        "expected_false_alarms_per_window": fa,
        "union_expected_false_alarms_per_30_batch_bonferroni_upper_bound": union_fa_30,
        "false_alarm_budget_5pct_of_30_batches": 1.5,
        "union_within_5pct_budget_known_parameter": union_fa_30 <= 1.5,
        "arl1_at_1sigma_shift": arl1_1sig,
        "small_shift_ranking": ("memory detectors dominate: at 1-sigma CUSUM (~%.0f) ~ EWMA (~%.0f) "
                                "detect ~4x faster than Shewhart (~%.0f); the three-detector UNION is "
                                "justified because Shewhart in turn dominates for large (>=3-sigma) jumps."
                                % (arl1_1sig["cusum_k0.5_h5"], arl1_1sig["ewma_lam0.2_L3"], arl1_1sig["shewhart_3sigma"])),
        "caveat_estimated_parameters": ("The <=5% budget check holds for KNOWN mu,sigma. With limits "
                                        "estimated from a finite baseline (Individuals chart) the true "
                                        "in-control ARL0 is materially shorter and right-skewed "
                                        "(Quesenberry 1993), so real per-window false alarms will EXCEED "
                                        "these known-parameter figures. Closing this is the Phase-1 gap."),
    }

    diag = {
        "schema": "amphora.process-qc-twin.spc-arl-characterization.v1",
        "study_id": "spc-arl-characterization-v1",
        "module": "amphora-process-qc-twin",
        "run_type": "SPC_RUN_LENGTH_CHARACTERIZATION_AUDIT",
        "authority": "AUDIT_ONLY",
        "purpose": ("First published-theory second-signal for the module's SPC detector RUN-LENGTH "
                    "performance (false-alarm ARL0 and detection ARL1), grounding the module's own "
                    "locked KPI thresholds (<=5% false alarms, >=90% recall) in Average-Run-Length theory."),
        "non_circularity": ("ARL baselines are closed-form / Markov-chain results from the SPC literature "
                            "(Shewhart geometric, Siegmund 1985 CUSUM, Brook-Evans/Lucas-Saccucci EWMA), "
                            "independent of the module's self-authored synthetic universes and of the "
                            "existing arithmetic-correctness KPI receipt."),
        "detector_designs": {
            "shewhart": {"type": "Individuals", "limits_sigma": 3.0},
            "ewma": {"lambda": 0.20, "L": 3.0},
            "cusum": {"standardized_tabular": True, "k": 0.5, "h": 5.0},
        },
        "theory_reference": {
            "shewhart": "Shewhart 1931; Montgomery 2020 8th ed. Ch.6; NIST/SEMATECH e-Handbook 6.3.1",
            "cusum": "Page 1954 Biometrika 41:100-115; Siegmund 1985 (ISBN 978-0-387-96134-7); Montgomery 2020 Ch.9.1 Table 9.4",
            "ewma": "Roberts 1959 Technometrics 1:239-250; Brook & Evans 1972 Biometrika 59:539-549; Lucas & Saccucci 1990 Technometrics 32:1-12",
            "estimated_parameter_ceiling": "Quesenberry 1993 J.Qual.Technol. 25:237-247; Jensen et al. 2006",
        },
        "gates": {
            "shewhart_geometric_known_answer": {
                "tol_rel": SHEWHART_TOL, "max_rel_err": round(shew_maxerr, 6),
                "passed": bool(shew_pass), "per_shift": shew},
            "cusum_siegmund_vs_montgomery_table_9_4": {
                "tol_rel": CUSUM_TOL, "max_rel_err": round(cus_maxerr, 6),
                "passed": bool(cus_pass), "regime": "small-shift 0..2 sigma (module-relevant)",
                "per_shift": cus, "large_shift_informational": cusum_largeshift_info,
                "large_shift_note": "Siegmund approximation degrades for shifts >=3 sigma; Shewhart dominates that regime, so it is reported informationally, not gated."},
            "ewma_markov_limiting_case_known_answer": {
                "tol_rel": EWMA_LIMIT_TOL, "passed": bool(ewma_limit_pass), "cases": ewma_limit},
        },
        "ewma_module_design_characterization": ewma_module,
        "kpi_linkage": kpi_link,
        "all_known_answer_gates_passed": bool(shew_pass and cus_pass and ewma_limit_pass),
        "headline": None,
        "closes": [
            "Supplies the first published-theory characterization of the module's detector run-length behavior (ARL0/ARL1).",
            "Independently reproduces the Shewhart geometric ARL table (max rel err %.3f%%) and the Montgomery Table 9.4 two-sided CUSUM ARL profile via Siegmund 1985 (max rel err %.2f%%, 0..2-sigma)." % (shew_maxerr*100, cus_maxerr*100),
            "Validates an independent EWMA Markov-chain ARL solver against the lambda->1 Shewhart limiting case.",
            "Grounds the module's locked <=5%% false-alarm / detection-speed KPI in run-length theory (known-parameter regime).",
        ],
        "does_not_close": [
            "Does NOT establish real-batch acceptability, product qualification, EHS acceptability, or batch-release authority.",
            "ARL results assume i.i.d. normal in-control data with KNOWN mu,sigma; the module estimates limits from a finite baseline, so real ARL0 is shorter and right-skewed (Quesenberry 1993) -- known-parameter figures are a BEST-CASE bound.",
            "No prospective time-ordered 30-batch pilot is checked in; recall/false-alarm on OWNED synthetic universes is unchanged by this receipt.",
            "Siegmund CUSUM ARL is an approximation (gated only over the module-relevant 0..2-sigma small-shift regime).",
        ],
        "modifies_manifest": False,
        "modifies_signed_phase0_kpi": False,
        "modifies_locked_dataset": False,
        "promotes_authority": False,
        "flips_scientific_readiness": False,
        "human_review_performed": False,
    }
    diag["headline"] = (
        "Independent ARL run-length characterization of the live process-QC detector stack: "
        "Shewhart geometric table reproduced to <=%.2f%%, two-sided CUSUM (k=0.5,h=5) Siegmund ARL "
        "matches Montgomery Table 9.4 to <=%.1f%% over 0..2-sigma, and an independent EWMA Markov-chain "
        "solver recovers the lambda->1 Shewhart limit. Known-parameter false-alarm budget (union <=%.2f "
        "expected/30 batches) sits inside the module's 5%% target; estimated-parameter degradation "
        "(Quesenberry 1993) is the explicit Phase-1 gap."
        % (shew_maxerr*100, cus_maxerr*100, union_fa_30)
    )
    return diag

def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()

if __name__ == "__main__":
    d1 = canon(build()); h1 = hashlib.sha256(d1).hexdigest()
    d2 = canon(build()); h2 = hashlib.sha256(d2).hexdigest()
    assert d1 == d2, "TWO-REPLAY BYTE MISMATCH"
    if len(sys.argv) > 1 and sys.argv[1] == "--emit":
        HERE.mkdir(parents=True, exist_ok=True)
        (HERE / "diagnostic.canonical.json").write_bytes(d1)
        (HERE / "diagnostic.runB.json").write_bytes(d2)
    print("replay_sha256:", h1, "| byte_stable:", h1 == h2)
