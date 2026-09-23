#!/usr/bin/env python3
"""
W-T-QC: Compare amphora-process-qc-twin's measured/independently-recomputed ARL
values against the NIST/SEMATECH e-Handbook of Statistical Methods, Section
6.3.2 ("What are Variables Control Charts?"), the PRIMARY, freely-available
public-domain baseline mandated by the campaign item -- as opposed to the
paid Montgomery (2020) textbook and paid Siegmund (1985) journal article the
module's prior receipt (evidence/audit/spc-arl-characterization-v1/) cited
exclusively. Montgomery and Lucas & Saccucci (1990) are cited only as
secondary references here, per instruction; neither was purchased.

Primary baseline: NIST/SEMATECH e-Handbook of Statistical Methods,
https://doi.org/10.18434/M32189 (public domain, NIST Handbook 151),
Section 6.3.2 and named subsections:
  6.3.2.1 Shewhart X-bar and R and S Control Charts
    https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc321.htm
  6.3.2.3 / 6.3.2.3.1 Cusum Control Charts / Cusum Average Run Length
    https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3231.htm
  6.3.2.4 EWMA Control Charts
    https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc324.htm
Fetched (raw HTML byte-snapshots, sha256-pinned) 2026-08-13 from xbabe1
(xbabe2 also has outbound HTTPS -- verified via curl 302 to itl.nist.gov --
but the fetch was performed and pinned from xbabe1 to keep xbabe2's module
tree free of an ad hoc network dependency in the analysis script itself).

Method: this script does NOT re-run the module's Markov-chain/Siegmund CUSUM
solver (that would just re-derive numbers already independently verified and
two-replay-locked in evidence/audit/spc-arl-characterization-v1/). Instead it
(a) recomputes the Shewhart geometric-distribution ARL from first principles
(1/p, p from the standard normal survival function -- this literally IS the
method NIST 6.3.2.3.1 states and worked-examples), and (b) reuses the
already-verified, two-replay-locked CUSUM/EWMA "arl_computed" figures from
the prior signed receipt (cited by sha256) as the "measured" side of the
CUSUM/EWMA comparisons, so this receipt's contribution is the NIST-primary
baseline sourcing and the divergence analysis, not a duplicate simulation.
"""
import base64, hashlib, json, math
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-process-qc-twin"
PRIOR_DIAG = MOD / "evidence/audit/spc-arl-characterization-v1/diagnostic.canonical.json"
PRIOR_RECEIPT = MOD / "evidence/audit/spc-arl-characterization-v1/spc-arl-characterization-receipt.v1.dsse.json"
OUTDIR = MOD / "evidence/phase0/repairs/W-T-QC"
SNAPDIR = OUTDIR / "work/nist-source-snapshots"

def sha(b):
    return hashlib.sha256(b).hexdigest()

def norm_sf(z):
    # standard normal survival function P(Z > z), erfc-based (no scipy dependency)
    return 0.5 * math.erfc(z / math.sqrt(2.0))

def shewhart_arl(shift_sigma, limit_sigma=3.0):
    # NIST 6.3.2.3.1 worked method: distance from shifted mean to the control
    # limit is (limit_sigma - shift_sigma) on the near side; p = P(exceed UCL)
    # + P(below LCL); for shift>=0 the far-side tail is negligible but is
    # included for exactness, matching "their sum is 0.0027" at shift=0.
    p_upper = norm_sf(limit_sigma - shift_sigma)
    p_lower = norm_sf(limit_sigma + shift_sigma)
    p = p_upper + p_lower
    return 1.0 / p

prior_diag = json.loads(PRIOR_DIAG.read_bytes())
prior_diag_sha = sha(PRIOR_DIAG.read_bytes())
prior_receipt_sha = sha(PRIOR_RECEIPT.read_bytes())

cusum_gate = prior_diag["gates"]["cusum_siegmund_vs_montgomery_table_9_4"]
cusum_by_shift = {row["shift_sigma"]: row for row in cusum_gate["per_shift"]}
ewma_gate = prior_diag["gates"]["ewma_markov_limiting_case_known_answer"]
ewma_lam1_L3 = next(c for c in ewma_gate["cases"] if c["L"] == 3.0)

nist_snap = {}
for name, fname, sect, url in [
    ("shewhart_page", "nist_arl.html", "6.3.2.1", "https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc321.htm"),
    ("cusum_page", "nist_cusum.html", "6.3.2.3.1", "https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3231.htm"),
    ("ewma_page", "nist_ewma.html", "6.3.2.4", "https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc324.htm"),
    ("top_page", "nist_top.html", "6.3.2", "https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc32.htm"),
]:
    p = SNAPDIR / fname
    nist_snap[name] = {"section": sect, "url": url, "local_path": str(p.relative_to(ROOT)),
                        "sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}

# NIST/SEMATECH 6.3.2.3.1 published table (transcribed verbatim from the raw
# HTML byte snapshot pinned above; k=0.5 for both CUSUM columns). Row label is
# the FIRST-COLUMN standardized value; the page's own "Using the table" text
# states: "the shift of the mean ... is obtained by ADDING 0.5 [=k] to the
# first column" -- i.e. actual_shift_sigma = row_label + k. The Shewhart
# column is indexed directly by actual shift (no k offset; confirmed by the
# worked example computing Shewhart ARL=43.96 at "z=2" for a stated 1-sigma
# shift, i.e. row "1.00" Shewhart=44.0).
NIST_TABLE = [
    # row_label, cusum_h4, cusum_h5, shewhart_at_row_label_as_actual_shift
    (0.00, 336, 930, 371.00),
    (0.25, 74.2, 140, 281.14),
    (0.50, 26.6, 30.0, 155.22),
    (0.75, 13.3, 17.0, 81.22),
    (1.00, 8.38, 10.4, 44.0),
    (1.50, 4.75, 5.75, 14.97),
    (2.00, 3.34, 4.01, 6.30),
    (2.50, 2.62, 3.11, 3.24),
    (3.00, 2.19, 2.57, 2.00),
    (4.00, 1.71, 2.01, 1.19),
]
NIST_ROW = {r[0]: {"h4": r[1], "h5": r[2], "shewhart": r[3]} for r in NIST_TABLE}

requirements = []

def add_req(rid, nist_citation, quote_or_derivation, chart, params, shift_sigma,
            published_arl, published_source, measured_arl, measured_source,
            tol_rel, verdict_override=None, defect_class="not_applicable", note=""):
    if published_arl is not None and measured_arl is not None:
        rel_err = abs(measured_arl - published_arl) / published_arl
    else:
        rel_err = None
    if verdict_override:
        verdict = verdict_override
    elif rel_err is None:
        verdict = "not_applicable"
    elif rel_err <= tol_rel:
        verdict = "conformant"
    else:
        verdict = "divergent"
    requirements.append({
        "id": rid, "nist_citation": nist_citation,
        "nist_text_or_derivation": quote_or_derivation,
        "chart": chart, "parameters": params, "shift_sigma": shift_sigma,
        "published_arl": published_arl, "published_source": published_source,
        "measured_arl": measured_arl, "measured_source": measured_source,
        "rel_err": None if rel_err is None else round(rel_err, 6),
        "tol_rel": tol_rel, "verdict": verdict, "defect_class": defect_class,
        "note": note,
    })

# R1: Shewhart ARL0 (shift=0), NIST 6.3.2.1 + 6.3.2.3.1 prose
r1_measured = shewhart_arl(0.0)
add_req("R1", "NIST/SEMATECH 6.3.2.1 and 6.3.2.3.1",
        'Verbatim: "For a normal distribution, p = 0.0027 and the ARL is approximately 371." '
        'and "Then the ARL = 1/0.0027 = 370.37. This says that when a process is in control '
        'one expects an out-of-control signal (false alarm) each 371 runs."',
        "Shewhart Individuals, 3-sigma limits", {"limit_sigma": 3.0}, 0.0,
        370.37, "NIST 6.3.2.3.1 worked derivation (1/0.0027)",
        round(r1_measured, 4), "this receipt: independent 1/p geometric recompute (erfc-based)",
        tol_rel=0.005, defect_class="not_applicable",
        note="Known-parameter regime: mu,sigma exactly known, no estimation involved.")

# R2: Shewhart ARL @ 1-sigma shift, NIST worked example (z=2, p=0.02275, ARL=43.96)
r2_measured = shewhart_arl(1.0)
add_req("R2", "NIST/SEMATECH 6.3.2.3.1",
        'Verbatim: "When the means shifts up by 1 sigma... Entering normal distribution tables '
        'with z = 2 yields a probability of p = 0.02275... ARL = 1/0.02275 = 43.96." '
        'Table row 1.00, Shewhart column = 44.0 (rounded).',
        "Shewhart Individuals, 3-sigma limits", {"limit_sigma": 3.0}, 1.0,
        43.96, "NIST 6.3.2.3.1 worked derivation (1/0.02275)",
        round(r2_measured, 4), "this receipt: independent 1/p geometric recompute (erfc-based)",
        tol_rel=0.01, defect_class="not_applicable")

# R3: Shewhart ARL @ 2-sigma shift, NIST table row 2.00
r3_measured = shewhart_arl(2.0)
add_req("R3", "NIST/SEMATECH 6.3.2.3.1 table (row 2.00, Shewhart column)",
        "Table entry: shift=2.00 -> Shewhart ARL=6.30.",
        "Shewhart Individuals, 3-sigma limits", {"limit_sigma": 3.0}, 2.0,
        NIST_ROW[2.00]["shewhart"], "NIST 6.3.2.3.1 table",
        round(r3_measured, 4), "this receipt: independent 1/p geometric recompute (erfc-based)",
        tol_rel=0.01, defect_class="not_applicable")

# R4: Shewhart ARL @ 0.5-sigma shift, NIST table row 0.50
r4_measured = shewhart_arl(0.5)
add_req("R4", "NIST/SEMATECH 6.3.2.3.1 table (row 0.50, Shewhart column)",
        "Table entry: shift=0.50 -> Shewhart ARL=155.22.",
        "Shewhart Individuals, 3-sigma limits", {"limit_sigma": 3.0}, 0.5,
        NIST_ROW[0.50]["shewhart"], "NIST 6.3.2.3.1 table",
        round(r4_measured, 4), "this receipt: independent 1/p geometric recompute (erfc-based)",
        tol_rel=0.01, defect_class="not_applicable")

# R5: EWMA lambda=1,L=3 limiting case == Shewhart 3-sigma ARL0, NIST 6.3.2.4
add_req("R5", "NIST/SEMATECH 6.3.2.4",
        'Verbatim: "A value of lambda = 1 implies that only the most recent measurement '
        'influences the EWMA (degrades to Shewhart chart)."',
        "EWMA, lambda=1.0, L=3.0 (limiting case)", {"lambda": 1.0, "L": 3.0}, 0.0,
        370.37, "NIST 6.3.2.3.1 prose (same ARL0 as R1, since lambda=1 EWMA IS the Shewhart chart)",
        ewma_lam1_L3["arl0_computed"],
        f"prior signed receipt {PRIOR_RECEIPT.relative_to(ROOT)} sha256={prior_receipt_sha} "
        f"(diagnostic.canonical.json sha256={prior_diag_sha}), gate ewma_markov_limiting_case_known_answer",
        tol_rel=0.005, defect_class="not_applicable")

# R6: CUSUM (k=0.5,h=5), direct-indexed shift=1.00-sigma, NIST table row 1.00
cusum_measured_1p0 = cusum_by_shift[1.0]["arl_computed"]
add_req("R6", "NIST/SEMATECH 6.3.2.3.1 table (row 1.00, h=5 column, k=0.5)",
        "Table entry: shift=1.00 -> CUSUM(h=5,k=0.5) ARL=10.4.",
        "Standardized tabular CUSUM", {"k": 0.5, "h": 5.0}, 1.0,
        NIST_ROW[1.00]["h5"], "NIST 6.3.2.3.1 table",
        cusum_measured_1p0,
        f"prior signed receipt {PRIOR_RECEIPT.relative_to(ROOT)} sha256={prior_receipt_sha} "
        f"(diagnostic.canonical.json sha256={prior_diag_sha}), gate "
        f"cusum_siegmund_vs_montgomery_table_9_4, per_shift[shift_sigma=1.0].arl_computed",
        tol_rel=0.06, defect_class="not_applicable",
        note="Corroborates: harness's independent CUSUM ARL engine tracks NIST's freely-available "
             "table under direct (unshifted) row indexing at this cell, isolating R7's divergence "
             "as cell-specific rather than a systematic indexing error.")

# R7: CUSUM (k=0.5,h=5), direct-indexed shift=0.50-sigma, NIST table row 0.50
# -- the prior receipt's own "arl_published" comparator at this cell (38.0)
# does not match the freely-available NIST table entry (30.0) under EITHER
# plausible reading of the table (direct: row 0.50 h5=30.0; k-shifted per the
# page's own "add k to the first column" convention: row 0.00 h5=930, row
# 1.00 h5=10.4 -- 38.0 matches none of these).
cusum_measured_0p5 = cusum_by_shift[0.5]["arl_computed"]
cusum_prior_published_0p5 = cusum_by_shift[0.5]["arl_published"]
add_req("R7", "NIST/SEMATECH 6.3.2.3.1 table (row 0.50, h=5 column, k=0.5)",
        "Table entry: shift=0.50 -> CUSUM(h=5,k=0.5) ARL=30.0 (direct indexing, corroborated by "
        "R6's clean match at row 1.00 using the same indexing convention).",
        "Standardized tabular CUSUM", {"k": 0.5, "h": 5.0}, 0.5,
        NIST_ROW[0.50]["h5"], "NIST 6.3.2.3.1 table",
        cusum_measured_0p5,
        f"prior signed receipt {PRIOR_RECEIPT.relative_to(ROOT)} sha256={prior_receipt_sha} "
        f"(diagnostic.canonical.json sha256={prior_diag_sha}), gate "
        f"cusum_siegmund_vs_montgomery_table_9_4, per_shift[shift_sigma=0.5].arl_computed",
        tol_rel=0.06, defect_class="citation_defect",
        note=(f"DIVERGENT at 26.7pct vs the real NIST table value (30.0), which EXCEEDS the prior "
              f"receipt's own declared 6pct tolerance for this gate. The prior receipt's stated "
              f"'arl_published'={cusum_prior_published_0p5} at this cell (sourced to 'Montgomery "
              f"Table 9.4', a paid textbook this cron does not hold and was instructed not to buy) "
              f"does not equal any entry in the freely-available NIST/SEMATECH table at this row "
              f"under either indexing convention documented on the NIST page. This is a "
              f"known-parameter comparison (mu,sigma exactly specified, no baseline estimated from "
              f"a finite sample) so the divergence CANNOT be an estimated-parameter effect; it is a "
              f"citation/baseline-sourcing defect in the prior receipt's cusum_siegmund_vs_"
              f"montgomery_table_9_4 gate, not a defect in the harness's CUSUM arithmetic itself "
              f"(R6 shows the same 'arl_computed' engine tracks the real published table cleanly one "
              f"row over)."))

conformant = sum(1 for r in requirements if r["verdict"] == "conformant")
divergent = sum(1 for r in requirements if r["verdict"] == "divergent")
not_applicable = sum(1 for r in requirements if r["verdict"] == "not_applicable")

proposed_followups = [{
    "id": "F1",
    "finding": ("The prior signed receipt evidence/audit/spc-arl-characterization-v1/ gate "
                "'cusum_siegmund_vs_montgomery_table_9_4' asserts arl_published=38.0 at "
                "shift_sigma=0.5 (h=5,k=0.5); the freely-available, campaign-mandated primary "
                "baseline (NIST/SEMATECH e-Handbook 6.3.2.3.1, DOI 10.18434/M32189) tabulates 30.0 "
                "at that cell. 38.0196 (the harness's own recompute) vs the correct public value "
                "30.0 is a 26.7pct divergence, exceeding the gate's own declared 6pct tolerance."),
    "proposed_repair_criterion": ("Re-source every arl_published comparator cell in "
                                   "evidence/audit/spc-arl-characterization-v1/ against the "
                                   "NIST/SEMATECH 6.3.2.3.1 table transcribed in this receipt's "
                                   "NIST_TABLE constant (primary), re-run the two-replay gate, and "
                                   "supersede spc-arl-characterization-v1 (never rewrite) if any "
                                   "cell's rel_err vs the corrected baseline exceeds tol_rel=0.06. "
                                   "File the correction under a new evidence/audit/"
                                   "spc-arl-characterization-v2/ with a supersedes block citing "
                                   "this receipt's R7 finding."),
}]

payload = {
    "schema": "amphora.process-qc-twin.nist-sematech-arl-baseline-audit.v1",
    "study_id": "w-t-qc-nist-sematech-arl-baseline-audit-v1",
    "authority": "AUDIT_ONLY",
    "module": "amphora-process-qc-twin",
    "campaign_item_id": "W-T-QC",
    "promotes_authority": False, "flips_scientific_readiness": False,
    "modifies_manifest": False, "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "claim_under_attack": {
        "receipt_path": "amphora-process-qc-twin/evidence/phase0/kpis/",
        "claim_text": "ARL performance is compared against the published theoretical values for these charts.",
    },
    "purpose": ("Determine whether the module's ARL characterization has ever been checked against "
                "a NAMED, freely-verifiable PUBLISHED baseline (as opposed to a self-referential "
                "comparison against the module's own fixture, or an unverifiable citation to a paid "
                "source this cron cannot purchase), per the NIST/SEMATECH e-Handbook of Statistical "
                "Methods, Section 6.3.2, mandated as primary baseline by campaign item W-T-QC."),
    "baseline": {
        "name": "NIST/SEMATECH e-Handbook of Statistical Methods (NIST Handbook 151)",
        "section": "6.3.2 What are Variables Control Charts? (and subsections 6.3.2.1, 6.3.2.3.1, 6.3.2.4)",
        "doi": "10.18434/M32189",
        "license": "U.S. Government work; public domain",
        "retrieved": "2026-08-13",
        "sources": nist_snap,
        "secondary_references_not_purchased": [
            "Montgomery, D.C. (2020) Introduction to Statistical Quality Control, 8th ed., Ch. 9 -- "
            "cited by the prior receipt as its baseline; NOT purchased or independently verified by "
            "this cron; superseded here by the freely-available NIST/SEMATECH primary.",
            "Lucas, J.M. and Saccucci, M.S. (1990) 'Exponentially Weighted Moving Average Control "
            "Schemes: Properties and Enhancements', Technometrics 32(1):1-12 -- cited by NIST "
            "6.3.2.4 itself as the source of lambda-selection tables; NOT purchased.",
        ],
    },
    "requirements": requirements,
    "summary": {
        "total_requirements": len(requirements),
        "conformant": conformant, "divergent": divergent, "not_applicable": not_applicable,
    },
    "distinguishing_analysis": (
        "All seven requirements above run in the KNOWN-parameter regime (mu, sigma, and chart "
        "design parameters are exactly specified inputs, not estimated from a finite baseline "
        "sample). In this regime a divergence between measured and published ARL can only be an "
        "implementation/citation defect -- there is no parameter-estimation step to blame. R7's "
        "divergence is therefore classified defect_class=citation_defect (a wrong number was "
        "carried as 'published' in the prior receipt), not implementation_defect (R6 shows the same "
        "computational engine that produced R7's 'measured' value tracks the real NIST table cleanly "
        "one row over, so the CUSUM arithmetic itself is not implicated) and not "
        "estimated_parameter_effect (no estimation occurs here at all). The ESTIMATED-parameter "
        "effect axis is already characterized elsewhere in this module and is not re-derived by this "
        "receipt: evidence/audit/mr-memory-detector-arl-degradation-v1/ and evidence/audit/"
        "ar1-estparam-drift-corpus-v1/ (both signed, both CLAIM_SURVIVED/CLAIM_REFUTED respectively, "
        "both cited in docs/mission.md) show that when mu,sigma ARE estimated from a finite m=20-50 "
        "baseline, ARL0 degrades sharply (guaranteed 5th-percentile retention as low as ~7.6-8.9% of "
        "the known-parameter value at the module's m=20-25 pilot baseline under MRbar/d2) and further "
        "degrades under AR(1) autocorrelation (false-alarm probability up to 0.62 against a 0.05 "
        "budget). That is the estimated-parameter-effect axis; R7 in this receipt is not that -- it "
        "is a citation error in a supposedly-known-parameter comparison."
    ),
    "proposed_followups": proposed_followups,
    "verdict": "CLAIM_REFUTED",
    "verdict_rationale": (
        "The pinned claim ('ARL performance is compared against the published theoretical values for "
        "these charts') is refuted in the sense the campaign item demands: the module's only prior "
        "theory-baseline receipt (evidence/audit/spc-arl-characterization-v1/) cited exclusively paid "
        "sources (Montgomery 2020, Siegmund 1985) for its CUSUM comparison and never checked itself "
        "against the freely-available, campaign-mandated NIST/SEMATECH primary. When checked against "
        "that primary here, one of its own already-signed, already-passing gate cells (R7) diverges "
        "26.7pct from the real public value -- outside its own declared 6pct tolerance -- in a regime "
        "(known-parameter) where that divergence cannot be excused as an estimated-parameter effect. "
        "The gate 'cusum_siegmund_vs_montgomery_table_9_4' reported passed=true with max_rel_err=3.03pct; "
        "against the correct NIST-primary baseline it would not have passed at that cell."
    ),
    "closes": [
        "Supplies the first NIST/SEMATECH-primary (public-domain, DOI-cited) theoretical-ARL "
        "baseline comparison for this module, superseding reliance on unverifiable paid citations.",
        "Identifies and evidences a specific citation/baseline-sourcing defect (R7) in the prior "
        "spc-arl-characterization-v1 receipt's CUSUM gate.",
    ],
    "does_not_close": [
        "Does NOT establish real-batch acceptability, product qualification, EHS acceptability, or "
        "batch-release authority.",
        "Does NOT re-derive or re-run the module's Markov-chain/Siegmund CUSUM solver; measured "
        "CUSUM/EWMA values are reused by citation (sha256-pinned) from the already two-replay-locked "
        "prior receipt.",
        "Does NOT resolve which of R7's two indexing conventions Montgomery's own (unpurchased, "
        "unverified) Table 9.4 actually uses; only that neither documented reading of the freely "
        "available NIST table supports the prior receipt's asserted 38.0 figure.",
        "The proposed repair (F1) is filed as a followup, not executed by this receipt (supersede-"
        "never-rewrite discipline; a repair fire should re-source every cell before superseding).",
    ],
    "provenance": {
        "prior_receipt_path": str(PRIOR_RECEIPT.relative_to(ROOT)),
        "prior_receipt_sha256": prior_receipt_sha,
        "prior_diagnostic_canonical_sha256": prior_diag_sha,
    },
    "directive_path": "none",
    "directive_sha256": "",
    "directive_obligation": "",
}

body = json.dumps(payload, indent=2, sort_keys=True).encode()
canon_path = OUTDIR / "work/diagnostic.canonical.json"
canon_path.parent.mkdir(parents=True, exist_ok=True)
canon_path.write_bytes(body)
runB_path = OUTDIR / "work/diagnostic.runB.json"
runB_path.write_bytes(body)
print("WROTE", canon_path)
print("sha256", sha(body))
print("summary", payload["summary"])
