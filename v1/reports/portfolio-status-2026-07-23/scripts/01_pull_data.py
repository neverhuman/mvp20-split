#!/usr/bin/env python3
"""Pull portfolio data from mvp20-split into report data/ directory.

- data/manifest.json — master portfolio manifest
- data/frontmatter.json — mission.md front-matter per amphora-* module
- data/receipt_digest.json — per-KPI kpi_summary/kpi_id/observed metrics
- data/modules.txt — all 37 module names
"""
import glob, json, os, re
from pathlib import Path

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
OUT = Path(ROOT / "reports/portfolio-status-2026-07-23/data")
OUT.mkdir(parents=True, exist_ok=True)

# 1. Master manifest ------------------------------------------------------
MANIFEST_PATH = ROOT / "amphora-molecule-property/reference/mvp20/data/amphora_coating_scientific_receipts_manifest.v1.json"
manifest = json.load(open(MANIFEST_PATH))
with open(OUT / "manifest.json", "w") as f:
    json.dump(manifest, f, indent=2)
print(f"manifest: n_receipts={manifest['kpis']['n_receipts_indexed']}, n_modules={manifest['kpis']['n_amphora_modules_covered']}")

# 2. Enumerate all amphora-* modules --------------------------------------
modules = sorted(d.name for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("amphora-"))
print(f"modules: {len(modules)}")
with open(OUT / "modules.txt", "w") as f:
    for m in modules: f.write(m + "\n")

# 3. Front-matter per module (parse from mission.md line 2) ---------------
frontmatter = {}
for m in modules:
    mm = ROOT / m / "docs/mission.md"
    if not mm.exists():
        frontmatter[m] = {"phase": None, "authority_ceiling": None, "solver_use_ceiling": None,
                          "operational_readiness": None, "scientific_readiness": None,
                          "purpose": None, "has_mission_md": False}
        continue
    lines = mm.read_text().splitlines()
    fm = {"has_mission_md": True}
    # front-matter JSON is typically on line 2 (between --- fences)
    # scan for a JSON object line
    for line in lines[:30]:
        s = line.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                obj = json.loads(s)
                for k in ("phase","authority_ceiling","solver_use_ceiling","operational_readiness","scientific_readiness","lane","module_id"):
                    if k in obj: fm[k] = obj[k]
                break
            except Exception:
                pass
    # purpose from first H1 or first non-empty line under H1
    hdr_idx = next((i for i,l in enumerate(lines) if l.startswith("# ")), None)
    if hdr_idx is not None:
        for j in range(hdr_idx+1, min(len(lines), hdr_idx+30)):
            s = lines[j].strip()
            if s and not s.startswith("#") and not s.startswith("---"):
                fm["purpose"] = s[:300]
                break
    # README fallback purpose
    readme = ROOT / m / "README.md"
    if fm.get("purpose") is None and readme.exists():
        r_lines = [l.strip() for l in readme.read_text().splitlines()]
        for l in r_lines[1:20]:
            if l and not l.startswith("#") and not l.startswith("```"):
                fm["purpose"] = l[:300]; break
    frontmatter[m] = fm
with open(OUT / "frontmatter.json", "w") as f:
    json.dump(frontmatter, f, indent=2)

# 4. Enumerate KPI receipts per module --------------------------------------
kpi_by_module = {}
for m in modules:
    kdir = ROOT / m / "evidence/phase0/kpis"
    if not kdir.exists():
        kpi_by_module[m] = []; continue
    kpis = []
    for kf in sorted(kdir.glob("*.json")):
        try:
            d = json.load(open(kf))
            kpi = {
                "filename": kf.name,
                "kpi_id": d.get("kpi_id"),
                "capability": (d.get("capability") or "")[:400],
                "phase0_deterministic_gates_passed": d.get("phase0_deterministic_gates_passed"),
                "n_deterministic_gates_defined": d.get("n_deterministic_gates_defined"),
                "n_deterministic_gates_passed": d.get("n_deterministic_gates_passed"),
                "observed_kpi_summary": d.get("observed_kpi_summary", {}),
            }
            kpis.append(kpi)
        except Exception as e:
            kpis.append({"filename": kf.name, "error": str(e)})
    kpi_by_module[m] = kpis
with open(OUT / "kpi_by_module.json", "w") as f:
    json.dump(kpi_by_module, f, indent=2)
print(f"kpi files enumerated: {sum(len(v) for v in kpi_by_module.values())} across {sum(1 for v in kpi_by_module.values() if v)} modules")

# 5. README first-paragraph per module -------------------------------------
readme_summary = {}
for m in modules:
    r = ROOT / m / "README.md"
    if not r.exists(): readme_summary[m] = None; continue
    lines = [l.strip() for l in r.read_text().splitlines()]
    para = []
    for l in lines[1:40]:
        if l.startswith("```"): break
        if l.startswith("#") and para: break
        if l and not l.startswith("#"): para.append(l)
        if para and not l: break
    readme_summary[m] = " ".join(para)[:500] if para else None
with open(OUT / "readme_summary.json", "w") as f:
    json.dump(readme_summary, f, indent=2)

print("done.")
