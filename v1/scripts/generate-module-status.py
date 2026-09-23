#!/usr/bin/env python3
"""Generate the human handoff's per-module/model status table from pinned registries."""

from collections import Counter
from datetime import datetime, timezone
import argparse
import json
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--captured-at")
    args = parser.parse_args()
    root = args.repo.resolve()
    output = args.output or root / "docs" / "MODULE-STATUS.md"
    captured = args.captured_at or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    manifest = json.loads((root / "module-manifest.json").read_text())
    inventory_doc = json.loads((root / "config/module-evidence-inventory.json").read_text())
    inventory = {row["module_id"]: row for row in inventory_doc["modules"]}
    rows = []
    refuted_total = 0
    model_ids = set()
    for module in manifest["modules"]:
        name = module["project"]
        evidence = inventory[name]
        adapter = evidence["runtime_integration"].get("adapter_policy") or {}
        model_id = adapter.get("model_id", "—")
        if model_id != "—":
            model_ids.add(model_id)
        mission = (root / module["documentation"]).read_text()
        refuted = len(re.findall(r"\bCLAIM_REFUTED\b", mission))
        refuted_total += refuted
        retraction = root / name / "evidence/phase0/kpis/RETRACTION-INDEX.md"
        impl = evidence["implementation"]["path"]
        benchmark = evidence["current_benchmark"]["status"]
        rows.append((
            name, module["lane"], impl, model_id,
            adapter.get("model_readiness_status", module["model_readiness_ceiling"]),
            module["operational_readiness"], module["scientific_readiness"],
            module["authority_ceiling"], "yes" if module["ranking_eligible"] else "no",
            len(evidence["artifacts"]), len(evidence["tests"]), refuted,
            "yes" if retraction.is_file() else "no", benchmark,
        ))

    campaign = json.loads((root / "ops/amphora-controller/bootstrap/campaign.json").read_text())
    items = campaign.get("items", campaign.get("campaign", []))
    item_status = Counter(row.get("status", "unknown") for row in items)
    lanes = Counter(row["lane"] for row in manifest["modules"])
    operational = Counter(row["operational_readiness"] for row in manifest["modules"])
    scientific = Counter(row["scientific_readiness"] for row in manifest["modules"])
    amphora_dirs = len([path for path in root.glob("amphora-*") if path.is_dir()])
    dsse = len(list(root.rglob("*.dsse.json")))
    retractions = len(list(root.glob("amphora-*/evidence/phase0/kpis/RETRACTION-INDEX.md")))
    supersessions = len([path for path in root.rglob("supersession-*") if path.is_dir()])

    def counts(values):
        return ", ".join("%s=%d" % item for item in sorted(values.items()))

    lines = [
        "# Module and model status",
        "",
        "Generated from `module-manifest.json`, `config/module-evidence-inventory.json`, and",
        "each registered module's mission document. Regenerate with:",
        "",
        "```bash",
        "python3 scripts/generate-module-status.py --captured-at %s" % captured,
        "```",
        "",
        "## Portfolio totals",
        "",
        "| Statistic | Value |",
        "|---|---:|",
        "| Capture date | %s |" % captured,
        "| Registered capability modules | %d |" % len(manifest["modules"]),
        "| `amphora-*` directories | %d (15 workspace crates, 2 other code-bearing modules, 24 evidence/documentation trees) |" % amphora_dirs,
        "| Distinct declared adapter/model IDs | %d |" % len(model_ids),
        "| Ranking-eligible modules | %d |" % sum(bool(row["ranking_eligible"]) for row in manifest["modules"]),
        "| Lanes | %s |" % counts(lanes),
        "| Operational readiness | %s |" % counts(operational),
        "| Scientific readiness | %s |" % counts(scientific),
        "| Signed DSSE files | %d |" % dsse,
        "| `CLAIM_REFUTED` mission verdicts | %d |" % refuted_total,
        "| Retraction indexes | %d |" % retractions,
        "| Supersession directories | %d |" % supersessions,
        "| Frozen campaign | %d items (%s) |" % (len(items), counts(item_status)),
        "",
        "The adapter/model IDs below are declared runtime interfaces. They are not all separately",
        "trained ML models: many are deterministic equations, policy gates, evidence validators, or",
        "explicit unavailable-model sentinels. `Rank=no` is the important handoff fact: none currently",
        "has authority to rank a real candidate.",
        "",
        "## Per-module status",
        "",
        "| Module | Lane | Implementation | Adapter/model ID | Model readiness | Ops | Science | Authority | Rank | Artifacts | Test pins | Refuted | Retraction | Benchmark |",
        "|---|---|---|---|---|---|---|---|:---:|---:|---:|---:|:---:|---|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(map(str, row)) + " |")
    lines.extend([
        "",
        "`Artifacts` and `Test pins` are counts from the global evidence inventory, not payload row",
        "counts. Read a module's `docs/mission.md` and retraction index before relying on a result.",
        "The known stale source-lock exception remains documented in `BUILD.md`; this table does not",
        "promote or reinterpret it.",
        "",
    ])
    output.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
