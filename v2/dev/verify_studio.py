"""Rebuild the Studio consumer with its locked dependencies outside the checkout."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).absolute().parents[1]


def stage_source(workspace):
    source = ROOT / "studio"
    copied = {}
    staged = workspace / "studio"
    staged.mkdir()
    files = [source / name for name in ("package.json", "package-lock.json", "tsconfig.json")]
    files.extend(path for folder in ("src", "tests", "scripts", "spikes") for path in (source / folder).rglob("*")
                 if path.is_file() and path.suffix not in {".py", ".pyc"} and "__pycache__" not in path.parts)
    for path in files:
        target = staged / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        copied[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = json.loads((source / "src/contracts/generated/manifest.json").read_text(encoding="utf-8"))
    for group in ("authoring", "knowledge", "research", "provenance", "feedback", "supervision", "followup"):
        entries = json.loads((source / "src/contracts/generated" / group / "manifest.json").read_text(encoding="utf-8"))
        manifest.update({group + "." + key: entry for key, entry in entries.items()})
    profiles = json.loads((source / "src/contracts/generated/followup/profiles.json").read_text(encoding="utf-8"))
    for key, pin in profiles.items():
        manifest["followup.validation." + key] = {
            "source": manifest["followup." + key]["source"].replace(".serialization.json", ".validation.json"),
            "sha256": pin["sha256"],
        }
    for entry in manifest.values():
        path = (ROOT / entry["source"]).absolute()
        assert ".." not in Path(entry["source"]).parts
        assert path.is_relative_to((ROOT / "contracts/schemas").absolute())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], "Published schema drift"
        target = workspace / entry["source"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    return staged, copied, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--explore-browser", action="store_true", help="Run the owned Explore browser acceptance in the isolated source install")
    args = parser.parse_args()
    node, npm = shutil.which("node"), shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not node or not npm:
        raise SystemExit("Studio verification requires Node24 and npm")
    env = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "HOME"}}
    output = ROOT / ".test-results/studio-isolated" / uuid.uuid4().hex
    output.mkdir(parents=True)
    with tempfile.TemporaryDirectory(prefix="amphora-studio-build-") as directory:
        workspace = Path(directory).resolve()
        assert workspace.is_relative_to(Path(tempfile.gettempdir()).resolve())
        staged, copied, manifest = stage_source(workspace)
        commands = [("install", [npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund"]),
                    ("verify", [node, "scripts/verify.mjs", "--coverage"])]
        if args.explore_browser:
            commands.append(("explore-browser", [node, "tests/browser/explore.mjs"]))
        test_output = ""
        for label, command in commands:
            result = subprocess.run(command, cwd=staged, env=env, capture_output=True, text=True,
                encoding="utf-8", timeout=180, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            (output / (label + ".log")).write_text(result.stdout + result.stderr, encoding="utf-8")
            if result.returncode:
                raise SystemExit(f"Isolated Studio {label} failed: " + result.stdout[-1800:] + result.stderr[-1800:])
            if label == "verify":
                test_output = result.stdout
        count = re.search(r"(?:tests|pass)\s+(\d+)", test_output)
        evidence = {"verified_at": datetime.now(ZoneInfo("America/Chicago")).strftime("%Y-%m-%d %H:%M:%S"),
            "status": "passed", "scope": "isolated Node dependency install, schema regeneration check, TypeScript build and owned tests",
            "tests": int(count.group(1)) if count else None, "source_sha256": copied, "public_schema_pins": manifest,
            "limits": ["No checkout imports or Python/service source copied", "No browser/live backend acceptance claim"]}
        if args.explore_browser:
            browser_root = workspace / ".test-results/studio-explore-browser"
            assert browser_root.is_relative_to(workspace)
            shutil.copytree(browser_root, output / "explore-browser")
            manifests = list((output / "explore-browser").glob("*/manifest.json"))
            assert len(manifests) == 1
            evidence["explore_browser"] = json.loads(manifests[0].read_text(encoding="utf-8"))
            evidence["limits"] = ["No checkout imports or Python/service source copied",
                                  "Scripted public HTTP browser fixture; actual-owner integration is separate"]
        (output / "manifest.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("Isolated Studio build passed; evidence " + str(output / "manifest.json"))


if __name__ == "__main__":
    main()
