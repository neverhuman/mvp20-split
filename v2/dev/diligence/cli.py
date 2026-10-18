"""Offline workplan checks and internal capsule preparation. No public publishing."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from diligence.core import (SOURCE_REVISION, EvidencePin, Rejected, bounded_read,
                            canonical, closed, local_file, relative_name, require,
                            sha, strict_json, validate_claims, validate_ledger)
from diligence.capsule import MissingEnvironment, run_checker, verify_capsule

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "v2/docs/Diligence/2026-10-18"


def git_source(name):
    relative_name(name)
    lock = strict_json(bounded_read(DOCS / "source_lock.json"))
    pins = {item["path"]: EvidencePin.parse(item) for item in lock["files"]}
    require(name in pins, "source_not_allowlisted")
    result = subprocess.run(["git", "-C", str(ROOT), "show", SOURCE_REVISION + ":" + name],
                            capture_output=True, timeout=30)
    require(result.returncode == 0, "pinned_blob_unavailable")
    pins[name].check(result.stdout)
    # These two navigation/handoff documents receive an explicit local DD-01 overlay.
    # Historical claim pins still bind their exact Git blobs; production/science inputs
    # must remain identical in the working tree.
    overlays = {"v2/Restore.md", "v2/docs/Build Plans/Master Build Tracker.md"}
    if name not in overlays:
        require(bounded_read(local_file(ROOT, name)) == result.stdout, "working_source_drift")
    return result.stdout


def check_plan():
    ledger = strict_json(bounded_read(DOCS / "task_ledger.json"))
    result = validate_ledger(ledger, ROOT)
    registry = strict_json(bounded_read(DOCS / "claims.json"))
    result["claims_checked"] = validate_claims(registry, git_source)
    result["status"] = "verified"
    result["source_revision"] = SOURCE_REVISION
    result["interpretation"] = "Plan/registry consistency; queued investor deliverables are not completed by this check."
    return result


def build_capsule(output):
    output = output.absolute()
    require(not output.exists(), "output_exists")
    require(not output.is_relative_to(ROOT.resolve()), "external_output_required")
    profile = strict_json(bounded_read(DOCS / "capsule_allowlist.json"))
    closed(profile, {"format", "source_revision", "files"})
    require(profile["format"] == "amphora-internal-capsule-allowlist.v1" and
            profile["source_revision"] == SOURCE_REVISION, "unsupported_capsule_profile")
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.parent.is_symlink(), "linked_output")
    output.mkdir()
    paths = set()

    def write(name, raw):
        relative_name(name); require(name not in paths, "export_collision"); paths.add(name)
        path = output / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)

    for name in profile["files"]:
        write("source/" + name, git_source(name))
    for name in ["claims.json", "byte_reconstruction.v1.json"]:
        write(name, bounded_read(DOCS / name))
    mapping = strict_json(bounded_read(DOCS / "byte_reconstruction.v1.json"))
    for spec in mapping["checker_sources"]:
        pin = EvidencePin.parse(spec["source"]); write(spec["capsule_path"], git_source(pin.path))
    for name in ["core.py", "capsule.py", "__init__.py"]:
        write("diligence/" + name, bounded_read(Path(__file__).parent / name))
    write("verify.py", b'''import sys,json,argparse\nfrom pathlib import Path\nsys.dont_write_bytecode=True\nfrom diligence.capsule import verify_capsule,MissingEnvironment\nfrom diligence.core import Rejected\np=argparse.ArgumentParser();p.add_argument('--bootstrap',action='store_true');a=p.parse_args()\ntry:\n r=verify_capsule(Path(__file__).resolve().parent,a.bootstrap);code=0\nexcept MissingEnvironment as e:r={'status':'environment_unavailable','reason':str(e)};code=3\nexcept (Rejected,OSError,ValueError,TimeoutError) as e:r={'status':'rejected','reason':str(e) if isinstance(e,Rejected) else 'verification_failed'};code=2\nprint(json.dumps(r,sort_keys=True));raise SystemExit(code)\n''')
    write("START_HERE.md", b'''# Amphora | Internal engineering verification capsule\n\nRun `python3 verify.py` (Python 3.12+) offline. Optional `--bootstrap` requires NumPy; nothing is installed automatically. This development capsule verifies retained evidence and original assertions. It is not the investor release. Historical records contain their original host/profile context; external disclosure review remains a separate planned gate. No model fits or service starts occur. Source dependency checks are checkout-only. SHA-256 binds integrity, not publisher authenticity.\n\nPLGA attribution and original license travel under source/docs/review/plga/NOTICE.md and source/v1/LICENSE.\n''')
    files = [{"path": name, "bytes": (output / name).stat().st_size,
              "sha256": sha((output / name).read_bytes())} for name in sorted(paths)]
    manifest = {"format": "amphora-capsule-manifest.v1", "source_revision": SOURCE_REVISION,
                "audience": "internal_engineering", "release_qualified": False, "files": files}
    (output / "MANIFEST.json").write_bytes(canonical(manifest))
    (output / "MANIFEST.sha256").write_text(sha((output / "MANIFEST.json").read_bytes()) + "\n")
    result = verify_capsule(output)
    result["capsule_directory"] = str(output)
    return result


def archive_capsule(directory, archive):
    verify_capsule(directory)
    require(not archive.exists(), "output_exists")
    require(not archive.is_relative_to(directory), "archive_inside_payload")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(directory.rglob("*")):
            if p.is_file():
                item = zipfile.ZipInfo("Amphora_Engineering_Capsule/" + p.relative_to(directory).as_posix(),
                                       (2026, 10, 18, 0, 0, 0))
                item.external_attr = 0o100644 << 16; item.create_system = 3
                item.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(item, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return {"status": "verified", "archive_sha256": sha(archive.read_bytes()),
            "archive_bytes": archive.stat().st_size, "audience": "internal_engineering"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    commands.add_parser("check-plan")
    inspect = commands.add_parser("inspect-task"); inspect.add_argument("task_id")
    verify = commands.add_parser("verify-source"); verify.add_argument("--bootstrap", action="store_true")
    build = commands.add_parser("build-capsule"); build.add_argument("--output", type=Path, required=True)
    package = commands.add_parser("archive-capsule"); package.add_argument("--capsule", type=Path, required=True); package.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if sys.version_info < (3, 12):
            raise MissingEnvironment("python_312_required")
        if args.mode == "check-plan":
            report = check_plan()
        elif args.mode == "inspect-task":
            ledger = strict_json(bounded_read(DOCS / "task_ledger.json"))
            rows = [t for t in ledger["tasks"] if t["id"] == args.task_id]
            require(len(rows) == 1, "unknown_task"); report = rows[0]
        elif args.mode == "build-capsule":
            report = build_capsule(args.output)
        elif args.mode == "archive-capsule":
            report = archive_capsule(args.capsule.absolute(), args.output.absolute())
        else:
            plan = check_plan()
            with tempfile.TemporaryDirectory(prefix="amphora-diligence-check-") as tmp:
                path = Path(tmp) / "capsule"; build_capsule(path)
                report = verify_capsule(path, args.bootstrap)
            boundary = subprocess.run([sys.executable, "-B", str(ROOT / "v2/dev/check_boundaries.py")], cwd=ROOT, capture_output=True, text=True, timeout=120)
            require(boundary.returncode == 0 and "Production dependency boundaries verified" in boundary.stdout,
                    "source_boundary_failure")
            report["source_boundary_check"] = "fresh_static_check_passed"
            report["plan"] = plan
        print(json.dumps(report, sort_keys=True)); return 0
    except MissingEnvironment as error:
        print(json.dumps({"status": "environment_unavailable", "reason": str(error)})); return 3
    except (Rejected, OSError, ValueError, subprocess.TimeoutExpired):
        error = sys.exception()
        print(json.dumps({"status": "rejected", "reason": str(error) if isinstance(error, Rejected) else "verification_failed"})); return 2


if __name__ == "__main__":
    raise SystemExit(main())
