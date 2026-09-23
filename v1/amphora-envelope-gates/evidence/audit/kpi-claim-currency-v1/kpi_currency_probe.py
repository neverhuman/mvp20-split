#!/usr/bin/env python3
"""kpi-claim-currency-v1 :: amphora-envelope-gates

Attacks a DIFFERENT claim than T-03 or W-D-ENVGATE: not the oracle code itself,
but whether the module's machine-readable, portfolio-relied-upon Phase-0 KPI
register (evidence/phase0/kpis/envelope-gates-constraint-envelope-kpi.v1.json)
is a CURRENT, non-stale summary of that oracle's fail-closed behavior.

T-03 (2026-08-05, CLAIM_REFUTED, signed) proved that 3 of the KPI's 6
fail-closed metrics were never actually exercised as the KPI's own notes
claim, and that when exercised, 2 of them (envelope_bound_inversion,
trusted_feature_substitution) do not hold. mission.md prose was updated to
record this. The KPI JSON itself -- the machine-readable artifact any
downstream consumer (candidate-contract, optimizer-orchestrator, redteam-audit
subsumption sweeps, etc.) would actually parse, not the human prose -- was
never superseded, retracted, or edited: this fire independently confirms (by
byte-identical sha256 against T-03's own recorded provenance) that the KPI
file and the oracle file are UNCHANGED since before T-03 fired, and then
fresh-executes today (2026-08-15, 10 days later) the exact 3 sub-probes the
KPI's own envelope_bound_inversion_fail_closed_rate note names verbatim
("lower > upper, lower = NaN, upper = Infinity. All return Err.") against the
live, unmodified evaluate_gate(), to check whether the KPI's claim is true
right now, not just whether it was ever true.

AUDIT_ONLY. Imports (does not reimplement) the real evaluate_gate(). Does not
touch the runtime, KAT fixture, KPI, manifest, or mission.md.
"""
import hashlib, json, math, sys
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
MOD = ROOT / "amphora-envelope-gates"
ORACLE_PATH = MOD / "benchmarks/constraint-envelope-oracle-v1/run_envelope_gates.py"
KPI_PATH = MOD / "evidence/phase0/kpis/envelope-gates-constraint-envelope-kpi.v1.json"
KAT_PATH = MOD / "reference/phase0-envelope-gates-known-answer.v1.json"
T03_RECEIPT = MOD / "evidence/phase0/repairs/T-03/done/t03-adversarial-attack-receipt.v1.dsse.json"

sys.path.insert(0, str(ORACLE_PATH.parent))
from run_envelope_gates import evaluate_gate  # real, unmodified oracle under test

def sha(b): return hashlib.sha256(b).hexdigest()

# ---------------------------------------------------------------------------
# Step 1: byte-provenance continuity check against T-03's own signed record.
# ---------------------------------------------------------------------------
import base64
t03_env = json.loads(T03_RECEIPT.read_bytes())["signature"]
t03_body = json.loads(base64.b64decode(t03_env["payload"]))
t03_oracle_sha = t03_body["provenance"]["oracle_under_test_sha256"]
t03_kpi_sha = t03_body["provenance"]["kpi_examined_sha256"]

oracle_bytes = ORACLE_PATH.read_bytes()
kpi_bytes = KPI_PATH.read_bytes()
kpi = json.loads(kpi_bytes)
oracle_sha_now = sha(oracle_bytes)
kpi_sha_now = sha(kpi_bytes)

oracle_unchanged_since_t03 = (oracle_sha_now == t03_oracle_sha)
kpi_unchanged_since_t03 = (kpi_sha_now == t03_kpi_sha)

# Locate the KPI metric + verbatim note under test.
inv_metric = next(m for m in kpi["metrics"] if m["name"] == "envelope_bound_inversion_fail_closed_rate")
kpi_claimed_observed = inv_metric["observed"]
kpi_claimed_passed = inv_metric["passed"]
kpi_claimed_note = inv_metric["note"]

# ---------------------------------------------------------------------------
# Step 2: fresh-execute, TODAY, the exact 3 sub-probes the note names.
# Use the real, registered dgeba-teta-primer-9to1 policy + a full nominal
# snapshot (same construction T-03 used) so this is a live, in-tree policy,
# not a synthetic strawman.
# ---------------------------------------------------------------------------
kat = json.loads(KAT_PATH.read_bytes())
teta = next(e for e in kat["envelopes"] if e["envelope_id"] == "dgeba-teta-primer-9to1")
BASE_POLICY = teta["policy"]

def full_snapshot(feature=None, value=None, unit="g"):
    values = {
        "mass.part_A_g": {"value": 180.0, "unit": "g"},
        "mass.part_B_g": {"value": 20.0, "unit": "g"},
        "mass.total_g": {"value": 200.0, "unit": "g"},
    }
    if feature is not None:
        values[feature] = {"value": value, "unit": unit}
    return {"trusted": True, "schema": "amphora.trusted-arithmetic-snapshot.v1", "values": values}

def policy_with_bounds(lo, hi, feature="mass.part_A_g"):
    import copy
    p = copy.deepcopy(BASE_POLICY)
    p["authoritative"] = False
    for c in p["constraints"]:
        if c["feature_path"] == feature:
            c["lower_inclusive"] = lo
            c["upper_inclusive"] = hi
    return p

probes = []

# sub-probe A: lower > upper (on the real feature bound, well-formed value)
pA = policy_with_bounds(200.0, 100.0)  # inverted: lower=200 > upper=100
vA, mA, rA = evaluate_gate(pA, full_snapshot())
probes.append({
    "sub_probe": "lower_gt_upper",
    "policy_bounds": {"lower_inclusive": 200.0, "upper_inclusive": 100.0},
    "verdict": vA, "binding_margin": (mA if mA is None or (isinstance(mA, float) and math.isfinite(mA)) else str(mA)),
    "reasons": rA,
    "kpi_expected": "Err (REJECT)",
    "fired_as_expected": (vA == "REJECT"),
})

# sub-probe B: lower = NaN (upper stays a real finite bound)
pB = policy_with_bounds(float("nan"), 189.0)
vB, mB, rB = evaluate_gate(pB, full_snapshot())
probes.append({
    "sub_probe": "lower_is_nan",
    "policy_bounds": {"lower_inclusive": "NaN", "upper_inclusive": 189.0},
    "verdict": vB,
    "binding_margin": (mB if mB is None else (str(mB) if isinstance(mB, float) and math.isnan(mB) else mB)),
    "reasons": rB,
    "kpi_expected": "Err (REJECT)",
    "fired_as_expected": (vB == "REJECT"),
})

# sub-probe C: upper = Infinity (lower stays a real finite bound)
pC = policy_with_bounds(171.0, float("inf"))
vC, mC, rC = evaluate_gate(pC, full_snapshot())
probes.append({
    "sub_probe": "upper_is_infinity",
    "policy_bounds": {"lower_inclusive": 171.0, "upper_inclusive": "Infinity"},
    "verdict": vC,
    "binding_margin": (mC if mC is None or (isinstance(mC, float) and math.isfinite(mC)) else str(mC)),
    "reasons": rC,
    "kpi_expected": "Err (REJECT)",
    "fired_as_expected": (vC == "REJECT"),
})

n_fired_as_expected = sum(1 for p in probes if p["fired_as_expected"])
n_probes = len(probes)
observed_rate_today = n_fired_as_expected / n_probes
kpi_note_is_currently_true = (n_fired_as_expected == n_probes)
kpi_metric_is_stale = (not kpi_note_is_currently_true) and bool(kpi_claimed_passed) and (kpi_claimed_observed == 1.0)

# ---------------------------------------------------------------------------
# Step 3: retraction/supersession-chain search -- does anything in-tree mark
# this KPI as retracted, corrected, or superseded?
# ---------------------------------------------------------------------------
retraction_index_path = MOD / "evidence/phase0/kpis/RETRACTION-INDEX.md"
retraction_index_exists = retraction_index_path.exists()

def grep_tree_for(needle, roots):
    hits = []
    for root in roots:
        for p in root.rglob("*"):
            if p.is_file() and p.suffix in (".md", ".json") and "__pycache__" not in str(p):
                try:
                    txt = p.read_text(errors="ignore")
                except Exception:
                    continue
                if needle in txt:
                    hits.append(str(p.relative_to(ROOT)))
    return hits

kpi_rel = str(KPI_PATH.relative_to(ROOT))
supersession_hits = grep_tree_for(kpi_rel, [MOD / "evidence"])
supersession_hits = [h for h in supersession_hits if h != kpi_rel]

result = {
    "study_id": "kpi-claim-currency-v1",
    "module": "amphora-envelope-gates",
    "run_date": "2026-08-15",
    "days_since_t03": 10,
    "provenance_continuity": {
        "t03_recorded_oracle_sha256": t03_oracle_sha,
        "oracle_sha256_now": oracle_sha_now,
        "oracle_unchanged_since_t03": oracle_unchanged_since_t03,
        "t03_recorded_kpi_sha256": t03_kpi_sha,
        "kpi_sha256_now": kpi_sha_now,
        "kpi_unchanged_since_t03": kpi_unchanged_since_t03,
    },
    "kpi_claim_under_test": {
        "metric_name": "envelope_bound_inversion_fail_closed_rate",
        "kpi_claimed_observed": kpi_claimed_observed,
        "kpi_claimed_passed": kpi_claimed_passed,
        "kpi_claimed_note_verbatim": kpi_claimed_note,
    },
    "fresh_probe_results_2026_08_15": probes,
    "n_probes": n_probes,
    "n_fired_as_expected": n_fired_as_expected,
    "observed_rate_today": observed_rate_today,
    "kpi_note_is_currently_true": kpi_note_is_currently_true,
    "kpi_metric_is_currently_stale_and_false": kpi_metric_is_stale,
    "retraction_index_exists": retraction_index_exists,
    "supersession_or_retraction_references_to_kpi_file": supersession_hits,
    "n_supersession_or_retraction_references": len(supersession_hits),
}
print(json.dumps(result, indent=2, sort_keys=True))
