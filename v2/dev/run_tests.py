"""Run an owned module suite, optionally measuring its line and branch coverage."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
SCOPES = json.loads((ROOT / "dev/test_scopes.json").read_text())


def ownership_issues(root=ROOT, scopes=SCOPES):
    issues = []
    owners = [root / item["tests"] for item in scopes.values()]
    locations = [(folder, "test_*.py") for folder in ("contracts", "services", "tools", "sdk", "dev/tests", "tests/integration")]
    locations.append(("studio/tests", "*.test.ts"))
    for folder, pattern in locations:
        for path in (root / folder).rglob(pattern):
            if any(part.startswith(".") for part in path.relative_to(root).parts):
                continue
            matches = [owner for owner in owners if path.is_relative_to(owner)]
            if len(matches) != 1:
                issues.append(f"Expected one test owner: {path.relative_to(root).as_posix()}")
    for name, item in scopes.items():
        runner = item.get("runner", "pytest")
        if runner not in {"pytest", "node"}:
            issues.append(f"Unknown test runner: {name}")
        if not list((root / item["tests"]).rglob("*.test.ts" if runner == "node" else "test_*.py")):
            issues.append(f"Empty test scope: {name}")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", choices=sorted(SCOPES))
    parser.add_argument("--area", choices=["exploration", "representations", "retrieval", "interpretation_api", "observations/interpretation", "observations/quality", "observations/normalization", "scientific_api", "scientific_publication", "synthesis", "eligibility", "material_state", "experiments", "observations", "corrections", "assessment", "derivations", "reasoning", "rebuild", "validation", "authoring", "replay", "identity", "acquisition", "source_rights", "graph", "admission", "api", "baseline", "persistence", "lifecycle", "completion", "delivery", "inspection", "graph_inspection", "graph_navigation", "definitions", "publication", "storage", "retention", "maintenance", "acceptance", "descriptors", "routing", "transport", "executable", "compiler", "scheduling", "aggregation", "waits", "bindings", "successors", "contracts", "page_models"])
    parser.add_argument("--coverage", action="store_true")
    args, pytest_args = parser.parse_known_args()
    areas = {"knowledge": {"exploration", "corrections", "publication", "reasoning", "rebuild", "authoring", "replay", "persistence", "validation", "api", "acceptance"}, "research": {"exploration", "interpretation_api", "observations/interpretation", "observations/quality", "observations/normalization", "scientific_api", "scientific_publication", "synthesis", "eligibility", "material_state", "experiments", "observations", "publication", "corrections", "assessment", "identity", "persistence", "api"}, "runtime": {"successors", "bindings", "waits", "aggregation", "scheduling", "compiler", "graph", "admission", "api", "baseline", "persistence", "lifecycle", "completion", "delivery", "inspection", "graph_inspection", "graph_navigation", "definitions", "acceptance"},
             "data-artifacts": {"representations", "retrieval", "derivations", "source_rights", "acquisition", "persistence", "publication", "storage", "retention", "maintenance", "acceptance"},
             "registry": {"descriptors", "persistence", "api", "routing"},
             "worker-sdk": {"transport", "lifecycle", "acceptance"}, "campaigns": {"executable"},
             "studio": {"contracts", "transport", "page_models"}}
    if args.area and args.area not in areas.get(args.module, set()):
        parser.error("--area must belong to the selected module")
    findings = ownership_issues()
    if findings:
        raise SystemExit("\n".join(findings))
    selected = {args.module: SCOPES[args.module]} if args.module else SCOPES
    python_scopes = {name: item for name, item in selected.items() if item.get("runner", "pytest") == "pytest"}
    node_scopes = {name: item for name, item in selected.items() if item.get("runner") == "node"}
    if node_scopes and pytest_args:
        parser.error("Pytest-only extra arguments cannot be applied to a Node suite")
    command = [sys.executable, "-m", "pytest", "-c", str(ROOT / "dev/pyproject.toml"), "-q"]
    for item in python_scopes.values():
        path = ROOT / item["tests"]
        command.append(str(path / args.area if args.area else path))
    env = os.environ.copy()
    if args.coverage:
        label = args.module or "all"
        if args.area:
            label += "-" + args.area
        output = ROOT / ".test-results" / label
        output.mkdir(parents=True, exist_ok=True)
        env["COVERAGE_FILE"] = str(output / ".coverage")
        for item in python_scopes.values():
            for source in item["coverage_sources"]:
                command.append("--cov=" + str(ROOT / source if "/" in source else source))
        command.extend(["--cov-branch", "--cov-report=term-missing",
                        f"--cov-report=json:{output / 'coverage.json'}",
                        f"--junitxml={output / 'tests.xml'}"])
    command.extend(pytest_args)
    if python_scopes:
        result = subprocess.run(command, cwd=ROOT, env=env)
        if result.returncode:
            raise SystemExit(result.returncode)
    for item in node_scopes.values():
        node = shutil.which("node")
        if node is None:
            raise SystemExit("Studio tests require Node24 and npm ci in v2/studio")
        script = ROOT / item["entrypoint"]
        command = [node, str(script)]
        if args.area:
            command.append("--area=" + args.area)
        if args.coverage:
            command.append("--coverage")
        result = subprocess.run(command, cwd=script.parent.parent, env=env)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
