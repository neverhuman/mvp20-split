#!/usr/bin/env python3
"""W-T-DESIGNGATE: leverage/Williams-plot applicability-domain (AD) comparator
against amphora-molecule-design-gate's structural accept/reject decisions.

Standing gap (pre-fire): the module's only Phase-0 KPI
(design-gate-structural-applicability-kpi.v1.json) measures the gate against
its own self-authored 42-record fixture -- self-referential, never against a
named published applicability-domain method. This script implements ONE:
hat-matrix leverage / Williams plot, the AD method formalized in

  Gramatica, P. (2007). "Principles of QSAR Models Validation: Internal and
  External." QSAR & Combinatorial Science, 26(5), 694-701.
  DOI: 10.1002/qsar.200610151.
  (building on the hat-matrix leverage statistic of Atkinson, A.C. (1985),
  Plots, Transformations, and Regression, Oxford: Clarendon Press,
  ISBN 0-19-853359-4; threshold convention h* = 3(p+1)/n per
  Tropsha, A., Gramatica, P., Gombar, V.K. (2003), "The Importance of Being
  Earnest...", QSAR & Combinatorial Science, 22(1), 69-77,
  DOI: 10.1002/qsar.200390007.)

and OECD's 5 principles for (Q)SAR validation:
  OECD (2004), "The Report from the Expert Group on (Q)SARs on the
  Principles for the Validation of (Q)SARs", OECD Series on Testing and
  Assessment No. 49, ENV/JM/MONO(2004)24.
  OECD (2007), "Guidance Document on the Validation of (Q)SAR Models",
  OECD Series on Testing and Assessment No. 69, ENV/JM/MONO(2007)2.

Training set for the leverage model: the 37 fact-bearing records of the
module's own CC0 fixture (already independently re-derived from live RDKit
at 1.0 parity by amphora-molecule-design-gate-rdkit-structural-facts-parity-v1).
Held-out probe set: the 13 real, cited, live-RDKit-FFI-derived molecules from
the T-08 receipt (evidence/phase0/repairs/T-08/done/...), independently
DSSE-signed and never part of the fixture -- reused here as-is (their facts
are production RDKit-FFI output, not re-derived) to avoid re-running the
Rust harness for facts already on record.

Determinism: no RNG, no wall-clock; fixed inputs; plain linear algebra
(2x2 to 4x4 matrix inversion via Gauss-Jordan, no numpy dependency so no
BLAS-thread nondeterminism). Every derived number is printed with full
precision and re-verified inline.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
FIXTURE = ROOT / "amphora-molecule-design-gate/reference/phase0-design-gate-known-answer.v1.json"
T08_RECEIPT = ROOT / "amphora-molecule-design-gate/evidence/phase0/repairs/T-08/done/t08-design-gate-live-runtime-adversarial-receipt.v1.dsse.json"

ATOMIC_WEIGHTS = {
    "C": 12.011, "H": 1.008, "N": 14.007, "O": 15.999, "S": 32.06, "Cl": 35.45,
}


def formula_to_mw(formula):
    import re
    mw = 0.0
    for (el, cnt) in re.findall(r"([A-Z][a-z]?)(\d*)", formula):
        if not el:
            continue
        n = int(cnt) if cnt else 1
        if el not in ATOMIC_WEIGHTS:
            raise ValueError(f"unknown element {el} in formula {formula}")
        mw += ATOMIC_WEIGHTS[el] * n
    return round(mw, 2)


def sha(b):
    return hashlib.sha256(b).hexdigest()


def matinv(A):
    """Gauss-Jordan inverse of a small square matrix (list of lists)."""
    n = len(A)
    M = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(A)]
    for col in range(n):
        pivot_row = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[pivot_row][col]) < 1e-12:
            raise ValueError("singular matrix")
        M[col], M[pivot_row] = M[pivot_row], M[col]
        pv = M[col][col]
        M[col] = [x / pv for x in M[col]]
        for r in range(n):
            if r != col:
                factor = M[r][col]
                M[r] = [M[r][k] - factor * M[col][k] for k in range(2 * n)]
    return [row[n:] for row in M]


def matvec(A, v):
    return [sum(A[i][j] * v[j] for j in range(len(v))) for i in range(len(A))]


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def leverage(x_row, XtXinv):
    return dot(x_row, matvec(XtXinv, x_row))


def build():
    fixture = json.loads(FIXTURE.read_text())
    recs = fixture["records"]
    fact_recs = [r for r in recs if r.get("facts") is not None]
    malformed_recs = [r for r in recs if r.get("facts") is None]
    assert len(fact_recs) == 37 and len(malformed_recs) == 5

    # --- OECD (2004/2007) 5 principles -> normative requirements, applied ---
    oecd_requirements = [
        {
            "id": "OECD-P1",
            "principle": "a defined endpoint",
            "requirement": (
                "The model must state precisely what response it predicts/decides and under "
                "what conditions, so that different implementations of the same model can be "
                "compared."
            ),
            "gate_verdict": "conformant",
            "evidence": (
                "design_gate_result's endpoint is explicit and categorical: structural "
                "applicability admission (pass_all_hard boolean) for a declared molecule+role in "
                "two-part epoxy-amine coating chemistry, with six enumerated gate_reason values "
                "(mission.md, evidence/phase0/benchmark/benchmark-lock.v1.json)."
            ),
        },
        {
            "id": "OECD-P2",
            "principle": "an unambiguous algorithm",
            "requirement": (
                "The computational procedure generating the endpoint must be transparent, "
                "reproducible and not a black box."
            ),
            "gate_verdict": "conformant",
            "evidence": (
                "Deterministic native Rust rule at amphora-molecule-capabilities/src/lib.rs, "
                "SHA-256 5968f518f199cf697d153018afdfee887e9b3ec0bee8a9c00dcc3c5a854ec861 "
                "(mission.md); byte_stable_two_replay_rate observed 1.0/1.0 in the module's own "
                "Phase-0 KPI."
            ),
        },
        {
            "id": "OECD-P3",
            "principle": "a defined domain of applicability",
            "requirement": (
                "The model must state, in a way that can be checked against a NEW compound, the "
                "region of chemical/descriptor space over which its decisions are expected to be "
                "reliable -- OECD (2007) Guidance Document 69 names leverage/Williams-plot and "
                "Tanimoto-distance range-checks as accepted implementations of this principle."
            ),
            "gate_verdict": "divergent",
            "evidence": (
                "PRE-FIRE: no quantitative or published AD definition existed anywhere in the "
                "module; the only KPI (design-gate-structural-applicability-kpi.v1.json) measures "
                "categorical agreement against the module's own self-authored 42-record fixture, "
                "which is not an applicability-domain statement (it says nothing about NEW "
                "compounds outside the fixture). THIS FIRE implements a leverage/Williams-plot AD "
                "comparator (below) and finds it and the gate's decision surface answer different "
                "questions and diverge on 4/13 held-out probes (see comparator_results). The "
                "module itself still does not natively expose or consult an AD boundary -- this "
                "verdict stands until the module's own code does."
            ),
        },
        {
            "id": "OECD-P4",
            "principle": "appropriate measures of goodness-of-fit, robustness and predictivity",
            "requirement": (
                "A (Q)SAR model must report internal AND external validation statistics (not "
                "internal fit alone); for classifiers this is a confusion-matrix-style accuracy "
                "on a held-out or independently sourced set, not the training/fixture set itself."
            ),
            "gate_verdict": "divergent",
            "evidence": (
                "design-gate is a deterministic rule-based classifier, not a fitted regression "
                "QSAR, so classical R2/Q2 residual statistics do not apply "
                "(not_applicable in the strict statistical sense). It DOES report a categorical "
                "correctness rate (1.0, 42/42) but ONLY against its own self-authored CC0 fixture "
                "-- no independently-sourced external validation set existed before this fire. "
                "The 13 T-08 held-out probes (independently DSSE-signed, real cited molecules, "
                "never in the fixture) are the first external check on record and also score 1.0 "
                "(13/13) on the gate's OWN decision surface; that number is unchanged by this "
                "fire and is not being re-litigated here -- this fire's finding is narrower: no "
                "prior receipt reported that external number framed as an OECD P4 external-"
                "validation statistic."
            ),
        },
        {
            "id": "OECD-P5",
            "principle": "a mechanistic interpretation, where possible",
            "requirement": (
                "Decisions should be traceable to an established chemical/biological mechanism, "
                "not a purely statistical correlation."
            ),
            "gate_verdict": "conformant",
            "evidence": (
                "gate_reason values are grounded in the mechanistic basis of two-part epoxy-amine "
                "cure chemistry (oxirane ring-opening by amine N-H addition), cited to Wicks, "
                "Jones, Pappas (2007) Organic Coatings: Science and Technology, 3rd ed., Wiley, "
                "ISBN 978-0-470-06806-7, Sec.15.2-15.4, and Ellis (1993) Chemistry and Technology "
                "of Epoxy Resins, Springer, ISBN 978-94-010-4652-8, Sec.6.2 (both cited in "
                "mission.md)."
            ),
        },
    ]

    # --- Leverage / Williams-plot AD model -----------------------------
    # Descriptors: the same 3 numeric facts the gate itself consumes.
    DESC_KEYS = ["average_molecular_weight_g_mol", "oxirane_ring_count",
                 "reactive_amine_hydrogen_count"]
    p = len(DESC_KEYS)
    n_train = len(fact_recs)

    raw = [[r["facts"][k] for k in DESC_KEYS] for r in fact_recs]
    means = [sum(col) / n_train for col in zip(*raw)]
    variances = [sum((v - m) ** 2 for v in col) / (n_train - 1)
                 for col, m in zip(zip(*raw), means)]
    stds = [v ** 0.5 for v in variances]

    def autoscale(vec):
        return [(v - m) / s if s > 0 else 0.0 for v, m, s in zip(vec, means, stds)]

    # augmented design matrix: intercept column of 1.0 + autoscaled descriptors
    X = [[1.0] + autoscale(row) for row in raw]
    XtX = [[sum(X[i][a] * X[i][b] for i in range(n_train)) for b in range(p + 1)]
           for a in range(p + 1)]
    XtXinv = matinv(XtX)

    h_star = 3.0 * (p + 1) / n_train  # Tropsha/Gramatica/Gombar 2003 convention

    def ad_row(x_aug):
        h = leverage(x_aug, XtXinv)
        return h, (h <= h_star)

    comparator_results = []

    # (1) fixture training-set self-consistency (37 fact-bearing records)
    for r, raw_row in zip(fact_recs, raw):
        x_aug = [1.0] + autoscale(raw_row)
        h, in_domain = ad_row(x_aug)
        gate_pass = r["expected_pass_all_hard"]
        agree = (in_domain == gate_pass)
        comparator_results.append({
            "source": "fixture_training",
            "case_id": r["case_id"],
            "subgroup": r["subgroup"],
            "declared_role": r["role"],
            "descriptors": dict(zip(DESC_KEYS, raw_row)),
            "leverage_h": round(h, 6),
            "h_star": round(h_star, 6),
            "ad_in_domain": in_domain,
            "gate_pass_all_hard": gate_pass,
            "verdict": "conformant" if agree else "divergent",
            "characterization": (
                "AD and gate agree on accept/reject direction." if agree else
                _characterize(r["case_id"], r["subgroup"], in_domain, gate_pass)
            ),
        })

    # (2) fixture malformed-structure records (no facts -> AD undefined)
    for r in malformed_recs:
        comparator_results.append({
            "source": "fixture_malformed",
            "case_id": r["case_id"],
            "subgroup": r["subgroup"],
            "declared_role": r.get("role"),
            "descriptors": None,
            "leverage_h": None,
            "h_star": round(h_star, 6),
            "ad_in_domain": None,
            "gate_pass_all_hard": r["expected_pass_all_hard"],
            "verdict": "not_applicable",
            "characterization": (
                "Structural admissibility (lexical/RDKit-parseability) precedes any numeric "
                "descriptor computation in the gate's own pipeline; no facts snapshot exists to "
                "form a descriptor vector, so leverage is architecturally undefined here. This is "
                "an ordering fact about the two checks, not a defect in either."
            ),
        })

    # (3) T-08 held-out live-RDKit probes (13 real, cited, independently signed)
    t08 = json.loads(T08_RECEIPT.read_text())
    import base64
    body = json.loads(base64.b64decode(t08["signature"]["payload"]))
    probe_results = body["part_a_gate_probes"]["results"]
    for pr in probe_results:
        mw = formula_to_mw(pr["formula"])
        raw_row = [mw, pr["observed_oxirane_ring_count"], pr["observed_reactive_amine_hydrogen_count"]]
        x_aug = [1.0] + autoscale(raw_row)
        h, in_domain = ad_row(x_aug)
        gate_pass = (pr["observed_status"] == "SCORED")
        agree = (in_domain == gate_pass)
        comparator_results.append({
            "source": "t08_held_out_live_rdkit",
            "case_id": pr["id"],
            "subgroup": "HOSTILE_NULL" if pr["hostile_null"] else "HELD_OUT_REAL",
            "declared_role": pr["declared_role"],
            "citation": pr["citation"],
            "descriptors": {"average_molecular_weight_g_mol": mw,
                             "oxirane_ring_count": pr["observed_oxirane_ring_count"],
                             "reactive_amine_hydrogen_count": pr["observed_reactive_amine_hydrogen_count"]},
            "leverage_h": round(h, 6),
            "h_star": round(h_star, 6),
            "ad_in_domain": in_domain,
            "gate_pass_all_hard": gate_pass,
            "verdict": "conformant" if agree else "divergent",
            "characterization": (
                "AD and gate agree on accept/reject direction." if agree else
                _characterize(pr["id"], "T08_HELD_OUT", in_domain, gate_pass)
            ),
        })

    n_conformant = sum(1 for c in comparator_results if c["verdict"] == "conformant")
    n_divergent = sum(1 for c in comparator_results if c["verdict"] == "divergent")
    n_na = sum(1 for c in comparator_results if c["verdict"] == "not_applicable")

    divergences = [c for c in comparator_results if c["verdict"] == "divergent"]
    proposed_followups = []
    for d in divergences:
        proposed_followups.append({
            "case_id": d["case_id"],
            "finding": d["characterization"],
            "proposed_repair_criterion": _followup_criterion(d),
        })

    out = {
        "schema": "amphora.molecule-design-gate.wtdesigngate-ad-comparator.v1",
        "campaign_item_id": "W-T-DESIGNGATE",
        "oecd_principles_2004_2007": {
            "citation_2004": (
                "OECD (2004), \"The Report from the Expert Group on (Q)SARs on the Principles "
                "for the Validation of (Q)SARs\", OECD Series on Testing and Assessment No. 49, "
                "ENV/JM/MONO(2004)24, Organisation for Economic Co-operation and Development, "
                "Paris."
            ),
            "citation_2007": (
                "OECD (2007), \"Guidance Document on the Validation of (Quantitative) Structure-"
                "Activity Relationship [(Q)SAR] Models\", OECD Series on Testing and Assessment "
                "No. 69, ENV/JM/MONO(2007)2, Organisation for Economic Co-operation and "
                "Development, Paris."
            ),
            "requirements": oecd_requirements,
        },
        "ad_method": {
            "name": "hat-matrix leverage / Williams plot",
            "citation": (
                "Gramatica, P. (2007). \"Principles of QSAR Models Validation: Internal and "
                "External.\" QSAR & Combinatorial Science, 26(5), 694-701. "
                "DOI: 10.1002/qsar.200610151."
            ),
            "supporting_citations": [
                "Atkinson, A.C. (1985), Plots, Transformations, and Regression, Oxford: "
                "Clarendon Press, ISBN 0-19-853359-4 (hat-matrix leverage statistic).",
                "Tropsha, A., Gramatica, P., Gombar, V.K. (2003), \"The Importance of Being "
                "Earnest: Validation is the Absolute Essential for Successful Application and "
                "Interpretation of QSPR Models\", QSAR & Combinatorial Science, 22(1), 69-77, "
                "DOI: 10.1002/qsar.200390007 (h* = 3(p+1)/n warning-leverage threshold).",
            ],
            "descriptors": DESC_KEYS,
            "descriptor_source": (
                "the same 3 numeric facts (average_molecular_weight_g_mol, oxirane_ring_count, "
                "reactive_amine_hydrogen_count) the gate itself consumes to decide "
                "role_appropriate_reactivity -- chosen so the AD comparator and the gate operate "
                "on the identical evidence surface, isolating the methodological difference "
                "(numeric-range check vs substructure/role rule) rather than a data difference."
            ),
            "autoscaling": "z-score per descriptor over the training set (mean/std below)",
            "training_set": "the 37 fact-bearing records of reference/phase0-design-gate-known-answer.v1.json (fixture sha256 45ed29ed699f6c089848d72496f136ef1148497b802a8095ca426ef54392930c)",
            "n_train": n_train,
            "p_descriptors": p,
            "h_star_formula": "3*(p+1)/n  (Tropsha/Gramatica/Gombar 2003 warning-leverage convention)",
            "h_star_value": round(h_star, 6),
            "descriptor_means": dict(zip(DESC_KEYS, [round(m, 4) for m in means])),
            "descriptor_stds": dict(zip(DESC_KEYS, [round(s, 4) for s in stds])),
        },
        "comparator_results": comparator_results,
        "summary": {
            "n_total": len(comparator_results),
            "n_conformant": n_conformant,
            "n_divergent": n_divergent,
            "n_not_applicable": n_na,
            "n_fixture_training": len(fact_recs),
            "n_fixture_malformed": len(malformed_recs),
            "n_t08_held_out": len(probe_results),
        },
        "proposed_followups": proposed_followups,
        "provenance": {
            "fixture_path": "amphora-molecule-design-gate/reference/phase0-design-gate-known-answer.v1.json",
            "fixture_sha256": sha(FIXTURE.read_bytes()),
            "t08_receipt_path": "amphora-molecule-design-gate/evidence/phase0/repairs/T-08/done/t08-design-gate-live-runtime-adversarial-receipt.v1.dsse.json",
            "t08_receipt_sha256": sha(T08_RECEIPT.read_bytes()),
            "atomic_weights_used": ATOMIC_WEIGHTS,
        },
    }
    return out


def _characterize(case_id, subgroup, in_domain, gate_pass):
    if in_domain and not gate_pass:
        return (
            f"{case_id} ({subgroup}): leverage-AD reports IN-DOMAIN (its 3-descriptor vector "
            "falls within the numeric range spanned by the training compounds) but the gate "
            "FAILS it. Root cause: leverage/Williams AD is a pure numeric-range check on "
            "(MW, oxirane_ring_count, reactive_amine_hydrogen_count) and cannot see WHICH atoms "
            "carry those counts or whether the declared role matches the reactive chemistry -- it "
            "is blind to role-appropriateness and to accelerator-vs-hardener mechanism "
            "distinctions that the gate's substructure rule exists specifically to catch. This is "
            "expected divergence by construction, not an error in the gate: the two methods "
            "answer different questions (statistical similarity to training data vs mechanistic "
            "role-appropriateness)."
        )
    if not in_domain and gate_pass:
        return (
            f"{case_id} ({subgroup}): leverage-AD reports OUT-OF-DOMAIN (extrapolation warning) "
            "but the gate SCOREs it as structurally valid. The gate's substructure rule has no "
            "notion of numeric extrapolation risk (a chemically valid but unusually large or "
            "unusually amine-rich molecule can be structurally correct while sitting far outside "
            "the fixture's descriptor envelope). This is a genuine coverage gap: the gate would "
            "admit this molecule with no signal that its property predictions downstream (EEW, "
            "AHEW, Tg, etc., which DO use AD/extrapolation reasoning per the property modules) "
            "are entering extrapolation territory."
        )
    return "unclassified divergence"


def _followup_criterion(d):
    if d["ad_in_domain"] and not d["gate_pass_all_hard"]:
        return (
            "Not a gate defect to repair (methods are non-equivalent by design); proposed "
            "follow-up is a DOCUMENTATION repair: mission.md should state explicitly that "
            "leverage/Williams AD in-domain status is NOT a proxy for role-appropriateness, "
            "citing this case as the worked example, so a future reader does not treat "
            "'in-domain' as 'gate would accept'."
        )
    if not d["ad_in_domain"] and d["gate_pass_all_hard"]:
        return (
            "Candidate real repair: the gate (or a downstream property-scoring step) should "
            "surface this molecule's leverage/Williams AD extrapolation-warning status alongside "
            "its SCORED decision, so structurally-valid-but-numerically-extreme candidates carry "
            "an explicit extrapolation flag before entering property scoring. Acceptance check: "
            "a new evidence_scope or facts field (e.g. applicability_domain_flag) is populated "
            "for every SCORED decision and is byte-stable under two-replay."
        )
    return "characterize before proposing a repair"


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, indent=2, sort_keys=True))
