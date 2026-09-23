#!/usr/bin/env python3
"""Compute deterministic module ranking per plan §1.

S = 25*R + 20*P + 15*V + 15*B + 10*U + 10*G + 5*S_readiness
"""
import json, re
from collections import Counter
from pathlib import Path

DATA = Path("/home/ubuntu/amphora/build/mvp20-split/reports/portfolio-status-2026-07-23/data")
manifest = json.load(open(DATA / "manifest.json"))
frontmatter = json.load(open(DATA / "frontmatter.json"))
kpi_by = json.load(open(DATA / "kpi_by_module.json"))
readmes = json.load(open(DATA / "readme_summary.json"))
modules = [l.strip() for l in open(DATA / "modules.txt") if l.strip()]

# Portfolio receipt counts per module (from manifest)
per_mod_receipts = manifest["kpis"].get("receipts_per_module", {})

# --- Feature detection heuristics from receipts + KPI text ---------------
def _kpi_text(m):
    return " ".join(
        (k.get("capability","") + " " + json.dumps(k.get("observed_kpi_summary",{})))
        for k in kpi_by.get(m, [])
    ).lower()

EXTERNAL_CORPUS_KEYS = ["openpoly", "radonpy", "omg", "polyverse", "corr-data", "corr_data", "polyuniverse", "nist", "bicerano", "usbr"]
PHYSICS_KEYS = ["van krevelen", "van_krevelen", "vk", "bicerano", "clausius", "hansen", "flory", "huggins", "fedors", "owens", "wendt", "kaelble", "arrhenius", "bondi", "young-dupr", "kissinger", "cassie", "baier"]
UQ_KEYS = ["conformal", "bootstrap", "prediction interval", "cqr", "quantile"]
REDTEAM_KEYS = ["redteam", "red-team", "red team", "attack", "audit", "adversarial", "diagnostic"]

def has_key(text, keys): return any(k in text for k in keys)

def scoring(m):
    text = _kpi_text(m) + " " + (readmes.get(m) or "").lower() + " " + str(frontmatter.get(m,{})).lower()
    n_receipts = per_mod_receipts.get(m, 0)
    R = min(n_receipts / 27.0, 1.0)
    fm = frontmatter.get(m, {})
    phase = fm.get("phase")
    P = 1.0 if phase == "PHASE_1" else (0.7 if phase == "PHASE_0" else (0.3 if phase == "PRE_PHASE_0" else 0))
    V = 1.0 if has_key(text, EXTERNAL_CORPUS_KEYS) else (0.5 if kpi_by.get(m) else 0.0)
    B = 1.0 if has_key(text, PHYSICS_KEYS) else (0.5 if kpi_by.get(m) else 0.0)
    U = 1.0 if (any(k in text for k in ["conformal","cqr"]) and "bootstrap" in text) else (0.5 if any(k in text for k in UQ_KEYS) else 0)
    G = 1.0 if "amphora-redteam-audit" == m else (0.5 if has_key(text, REDTEAM_KEYS) else 0.0)
    sr = fm.get("scientific_readiness")
    S_readiness = 1.0 if sr == "LOCKED_INTERNAL" else (0.5 if sr == "NOT_APPLICABLE" else 0.0)
    S = 25*R + 20*P + 15*V + 15*B + 10*U + 10*G + 5*S_readiness
    return {
        "module": m,
        "n_signed_portfolio_receipts": n_receipts,
        "n_kpi_files": len(kpi_by.get(m, [])),
        "phase": phase,
        "operational_readiness": fm.get("operational_readiness"),
        "scientific_readiness": sr,
        "authority_ceiling": fm.get("authority_ceiling"),
        "has_external_validation": has_key(text, EXTERNAL_CORPUS_KEYS),
        "has_physics_baseline": has_key(text, PHYSICS_KEYS),
        "has_uq": has_key(text, UQ_KEYS),
        "has_redteam_gate": has_key(text, REDTEAM_KEYS),
        "R": R, "P": P, "V": V, "B": B, "U": U, "G": G, "S_readiness": S_readiness,
        "score": round(S, 2),
        "has_mission_md": fm.get("has_mission_md", False),
    }

ranked = sorted([scoring(m) for m in modules], key=lambda r: (-r["score"], -r["n_signed_portfolio_receipts"], r["module"]))

def tier(r):
    s = r["score"]
    if s >= 70: return "S"
    if s >= 50: return "A"
    if s >= 30: return "B"
    if s == 0 and not r["has_mission_md"]: return "C"   # pure infrastructure
    return "D"

for r in ranked:
    r["tier"] = tier(r)

# Explicit meta/infrastructure grouping (Tier C hint)
INFRA_MOD_LIST = {
    "amphora-core","amphora-engine","amphora-cli","amphora-assurance-capabilities",
    "amphora-formulation-capabilities","amphora-molecule-capabilities",
    "amphora-rdkit-ffi","amphora-bridge","amphora-tui","amphora-ord-codec",
    "amphora-phase0-reviewer"
}
for r in ranked:
    if r["module"] in INFRA_MOD_LIST and r["tier"] == "D":
        r["tier"] = "C"

out = {"n_modules": len(ranked), "ranked": ranked,
       "tier_counts": Counter(r["tier"] for r in ranked)}
with open(DATA / "rank.json", "w") as f:
    json.dump(out, f, indent=2)

print(f"n_modules = {len(ranked)}")
print(f"tier counts: {out['tier_counts']}")
print("Top 15 by score:")
for r in ranked[:15]:
    print(f"  {r['tier']}  {r['score']:5.1f}  {r['module']:38s}  n_receipts={r['n_signed_portfolio_receipts']:2d}  phase={r['phase']}")
print("\nBottom 15:")
for r in ranked[-15:]:
    print(f"  {r['tier']}  {r['score']:5.1f}  {r['module']:38s}  n_receipts={r['n_signed_portfolio_receipts']:2d}  phase={r['phase']}")
