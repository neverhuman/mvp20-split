"""Run an owned module suite, optionally measuring its line and branch coverage."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).absolute().parents[1]
SCOPES = json.loads((ROOT / "dev/test_scopes.json").read_text())


def ownership_issues(root=ROOT, scopes=SCOPES):
    issues = []
    owners = [root / item["tests"] for item in scopes.values()]
    for folder in ("contracts", "services", "tools", "sdk", "dev/tests", "tests/integration"):
        for path in (root / folder).rglob("test_*.py"):
            if any(part.startswith(".") for part in path.relative_to(root).parts):
                continue
            matches = [owner for owner in owners if path.is_relative_to(owner)]
            if len(matches) != 1:
                issues.append(f"Expected one test owner: {path.relative_to(root).as_posix()}")
    for name, item in scopes.items():
        if not list((root / item["tests"]).rglob("test_*.py")):
            issues.append(f"Empty test scope: {name}")
    return issues


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", choices=sorted(SCOPES))
    parser.add_argument("--area", choices=["graph", "admission", "api", "baseline", "persistence", "lifecycle", "completion", "delivery", "inspection", "publication", "storage", "retention", "maintenance", "acceptance", "descriptors", "routing", "transport", "executable", "compiler", "scheduling", "aggregation", "waits", "bindings", "successors"])
    parser.add_argument("--coverage", action="store_true")
    args, pytest_args = parser.parse_known_args()
    areas = {"runtime": {"successors", "bindings", "waits", "aggregation", "scheduling", "compiler", "graph", "admission", "api", "baseline", "persistence", "lifecycle", "completion", "delivery", "inspection", "acceptance"},
             "data-artifacts": {"persistence", "publication", "storage", "retention", "maintenance", "acceptance"},
             "registry": {"descriptors", "persistence", "api", "routing"},
             "worker-sdk": {"transport", "lifecycle", "acceptance"}, "campaigns": {"executable"}}
    if args.area and args.area not in areas.get(args.module, set()):
        parser.error("--area must belong to the selected module")
    findings = ownership_issues()
    if findings:
        raise SystemExit("\n".join(findings))
    selected = {args.module: SCOPES[args.module]} if args.module else SCOPES
    command = [sys.executable, "-m", "pytest", "-c", str(ROOT / "dev/pyproject.toml"), "-q"]
    for item in selected.values():
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
        for item in selected.values():
            for source in item["coverage_sources"]:
                command.append("--cov=" + str(ROOT / source if "/" in source else source))
        command.extend(["--cov-branch", "--cov-report=term-missing",
                        f"--cov-report=json:{output / 'coverage.json'}",
                        f"--junitxml={output / 'tests.xml'}"])
    command.extend(pytest_args)
    raise SystemExit(subprocess.run(command, cwd=ROOT, env=env).returncode)


if __name__ == "__main__":
    main()
