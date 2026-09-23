#!/usr/bin/env python3
"""02_score.py — apply the 0-100 rubric to every amphora-* module and emit rank.json.

S = 25·R + 20·P + 15·V + 15·B + 10·U + 10·G + 5·D

Deterministic. No network. Reads data/*.json produced by 01_pull_data.sh.
"""
import json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/reports/portfolio-status-2026-08-03")
DATA = ROOT / "data"

modules = [l.strip() for l in open(DATA / "modules.txt") if l.strip()]
frontmatter = json.load(open(DATA / "frontmatter.json"))
kpi_by = json.load(open(DATA / "kpi_by_module.json"))
receipts_by = json.load(open(DATA / "receipts_by_module.json"))
readmes = json.load(open(DATA / "readme_summary.json"))
manifest = json.load(open(DATA / "manifest.json"))
mani_kpis = manifest.get("kpis", {})
per_mod_manifest_receipts = mani_kpis.get("receipts_per_module", {})

fire_lines = [json.loads(l) for l in open(DATA / "fire_summary.jsonl") if l.strip()]
fires_by_module = Counter(f.get("module") for f in fire_lines if f.get("module"))
receipts_added_by_module = defaultdict(int)
signing_violations_by_module = defaultdict(int)
for f in fire_lines:
    m = f.get("module")
    if not m:
        continue
    receipts_added_by_module[m] += int(f.get("receipts_added", 0) or 0)
    signing_violations_by_module[m] += int(f.get("signing_violations", 0) or 0)

# --- feature keyword banks ----------------------------------------------------
EXTERNAL_CORPUS = [
    "bigsoldb", "openpoly", "radonpy", "omg", "polyverse", "polyuniverse",
    "corr-data", "corr_data", "nist", "bicerano", "ecfr", "echa", "pubchem",
    "epa", "tsca", "reach", "usbr", "asm", "astm",
]
PHYSICS = [
    "van krevelen", "van_krevelen", "bicerano", "clausius", "hansen",
    "flory", "huggins", "fedors", "owens", "wendt", "kaelble", "arrhenius",
    "bondi", "kissinger", "cassie", "baier", "young-dupr", "fickian",
    "nielsen", "cussler", "boyer",
]
UQ = ["conformal", "bootstrap", "prediction interval", "cqr", "quantile", "coverage"]
REDTEAM = [
    "redteam", "red-team", "red team", "attack", "adversarial", "audit",
    "diagnostic", "tamper", "malformed",
]

def _module_text(m):
    """Concatenate every textual field we can inspect for keyword detection."""
    parts = [readmes.get(m, "")]
    for k in kpi_by.get(m, []):
        parts.append(k.get("capability", "") or "")
        parts.append(k.get("kpi_id", "") or "")
        parts.append(json.dumps(k.get("observed_kpi_summary", {})))
        parts.append(json.dumps(k.get("theory", {})))
        parts.append(json.dumps(k.get("metrics", {})))
    for r in receipts_by.get(m, []):
        parts.append(r.get("path", "") or "")
        parts.append(r.get("schema", "") or "")
        parts.append(r.get("payload_type", "") or "")
    parts.append(json.dumps(frontmatter.get(m, {})))
    return " ".join(parts).lower()

def has_any(text, keys): return any(k in text for k in keys)

# --- N_leader for receipt-density normalization -------------------------------
N_LEADER = max(
    max((len(kpi_by.get(m, [])) for m in modules), default=1),
    max((len(receipts_by.get(m, [])) for m in modules), default=1),
    1,
)

def score(m):
    text = _module_text(m)
    fm = frontmatter.get(m, {})
    phase = fm.get("phase", "NONE")
    readiness = fm.get("scientific_readiness", "NONE")
    n_kpi = len(kpi_by.get(m, []))
    n_receipts = len(receipts_by.get(m, []))
    n_manifest = per_mod_manifest_receipts.get(m, 0)
    n_receipts_total = max(n_kpi, n_receipts)

    # --- R: receipt density (0-1)
    R = min(n_receipts_total / N_LEADER, 1.0)

    # --- P: phase weight (0-1)
    if phase == "PHASE_1":
        P = 1.0
    elif phase == "PHASE_0" and readiness == "LOCKED_INTERNAL":
        P = 0.9
    elif phase == "PHASE_0" and readiness == "NOT_APPLICABLE":
        P = 0.5
    elif phase == "PRE_PHASE_0" and (n_receipts > 0 or n_kpi > 0):
        P = 0.3
    elif phase == "PRE_PHASE_0":
        P = 0.1
    else:
        P = 0.0

    # --- V: external validation
    V = 1.0 if has_any(text, EXTERNAL_CORPUS) else (0.5 if n_kpi > 0 or n_receipts > 0 else 0.0)

    # --- B: published physics baseline
    B = 1.0 if has_any(text, PHYSICS) else (0.5 if n_kpi > 0 or n_receipts > 0 else 0.0)

    # --- U: UQ present
    has_conformal = "conformal" in text or "cqr" in text
    has_bootstrap = "bootstrap" in text
    if has_conformal and has_bootstrap:
        U = 1.0
    elif has_conformal or has_bootstrap:
        U = 0.5
    elif any(k in text for k in ["coverage", "prediction interval", "quantile"]):
        U = 0.3
    else:
        U = 0.0

    # --- G: red-team gate
    if m == "amphora-redteam-audit":
        G = 1.0
    elif has_any(text, REDTEAM):
        G = 0.5
    else:
        G = 0.0

    # --- D: DSSE signing discipline
    n_sig_valid = sum(1 for r in receipts_by.get(m, []) if r.get("is_signed"))
    n_sig_total = len(receipts_by.get(m, []))
    if n_sig_total == 0:
        D = 0.5 if n_kpi > 0 else 0.0  # KPI-only modules get partial credit
    elif n_sig_valid == n_sig_total:
        D = 1.0
    elif n_sig_valid > 0:
        D = 0.5
    else:
        D = 0.0

    S = 25*R + 20*P + 15*V + 15*B + 10*U + 10*G + 5*D

    return {
        "module": m,
        "phase": phase,
        "scientific_readiness": readiness,
        "authority_ceiling": fm.get("authority_ceiling"),
        "operational_readiness": fm.get("operational_readiness"),
        "has_mission_md": bool(fm),
        "n_kpi_files": n_kpi,
        "n_signed_receipts_on_disk": n_receipts,
        "n_receipts_in_master_manifest": n_manifest,
        "n_signed_valid_receipts": n_sig_valid,
        "cron_fires_since_2026_07_26": fires_by_module.get(m, 0),
        "cron_receipts_added": receipts_added_by_module.get(m, 0),
        "cron_signing_violations": signing_violations_by_module.get(m, 0),
        "R": round(R, 4), "P": round(P, 4), "V": round(V, 4),
        "B": round(B, 4), "U": round(U, 4), "G": round(G, 4), "D": round(D, 4),
        "score": round(S, 2),
        "has_external_validation": has_any(text, EXTERNAL_CORPUS),
        "has_physics_baseline": has_any(text, PHYSICS),
        "has_uq": has_conformal or has_bootstrap,
        "has_redteam_gate": has_any(text, REDTEAM) or m == "amphora-redteam-audit",
    }

def tier(r):
    """Founder-facing 3-tier classification with sub-labels."""
    phase = r["phase"]
    readiness = r["scientific_readiness"]
    has_evidence = r["n_signed_receipts_on_disk"] > 0 or r["n_kpi_files"] > 0

    if phase == "PHASE_1":
        return {"tier": "Tier 1", "sub": "Human parity", "code": "T1"}
    if phase == "PHASE_0" and readiness == "LOCKED_INTERNAL":
        return {"tier": "Tier 0", "sub": "Science", "code": "T0S"}
    if phase == "PHASE_0" and readiness == "NOT_APPLICABLE":
        return {"tier": "Tier 0", "sub": "Infrastructure", "code": "T0I"}
    if phase == "PHASE_0":
        return {"tier": "Tier 0", "sub": "Other", "code": "T0X"}
    if phase == "PRE_PHASE_0" and has_evidence:
        return {"tier": "Pre-Tier 0", "sub": "Signed evidence", "code": "PT0E"}
    if phase == "PRE_PHASE_0":
        return {"tier": "Pre-Tier 0", "sub": "No evidence", "code": "PT0N"}
    if not r["has_mission_md"]:
        return {"tier": "Infra", "sub": "No mission.md", "code": "INF"}
    return {"tier": "Unclassified", "sub": "?", "code": "U"}

ranked = [score(m) for m in modules]
for r in ranked:
    r.update(tier(r))
ranked.sort(key=lambda r: (-r["score"], -r["n_signed_receipts_on_disk"], r["module"]))

tier_counts = Counter(r["code"] for r in ranked)

# --- top-level founder headline counts
headline = {
    "Tier 1": tier_counts.get("T1", 0),
    "Tier 0": tier_counts.get("T0S", 0) + tier_counts.get("T0I", 0) + tier_counts.get("T0X", 0),
    "Pre-Tier 0": tier_counts.get("PT0E", 0) + tier_counts.get("PT0N", 0),
    "Infra (no mission.md)": tier_counts.get("INF", 0),
}
sub_counts = {
    "Tier 0 Science (LOCKED_INTERNAL)": tier_counts.get("T0S", 0),
    "Tier 0 Infrastructure (NOT_APPLICABLE)": tier_counts.get("T0I", 0),
    "Pre-Tier 0 with signed evidence": tier_counts.get("PT0E", 0),
    "Pre-Tier 0 no evidence": tier_counts.get("PT0N", 0),
}

manifest_sha256 = open(DATA / "manifest.sha256").read().strip()

out = {
    "generated_at": None,  # filled by caller with `date -Iseconds` if desired
    "manifest_sha256": manifest_sha256,
    "n_modules_total": len(ranked),
    "n_receipts_in_master_manifest": mani_kpis.get("n_receipts_indexed"),
    "n_modules_in_master_manifest": mani_kpis.get("n_amphora_modules_covered"),
    "headline": headline,
    "sub_counts": sub_counts,
    "tier_counts_raw": dict(tier_counts),
    "cron_fires_total": sum(fires_by_module.values()),
    "cron_receipts_added_total": sum(receipts_added_by_module.values()),
    "cron_signing_violations_total": sum(signing_violations_by_module.values()),
    "ranked": ranked,
}
with open(DATA / "rank.json", "w") as f:
    json.dump(out, f, indent=2)

print(f"n_modules = {len(ranked)}")
print(f"headline: {headline}")
print(f"sub_counts: {sub_counts}")
print(f"cron: {sum(fires_by_module.values())} fires, {sum(receipts_added_by_module.values())} receipts added, {sum(signing_violations_by_module.values())} signing violations")
print(f"\nTop 15 by score:")
for r in ranked[:15]:
    print(f"  [{r['code']:4s}] {r['score']:5.1f}  {r['module']:38s}  KPI={r['n_kpi_files']:2d}  SCI={r['n_signed_receipts_on_disk']:2d}  V={r['V']}  B={r['B']}  U={r['U']}  G={r['G']}")
print(f"\nBottom 10:")
for r in ranked[-10:]:
    print(f"  [{r['code']:4s}] {r['score']:5.1f}  {r['module']:38s}  KPI={r['n_kpi_files']:2d}  SCI={r['n_signed_receipts_on_disk']:2d}")
