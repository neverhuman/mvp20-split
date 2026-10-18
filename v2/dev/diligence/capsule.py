"""Verify an internal engineering capsule using unchanged selected checkers."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import threading

from .core import (EvidencePin, HistoricalExport, Rejected, bounded_read, canonical,
                   closed, local_file, require, strict_json, validate_claims,
                   verify_manifest, sha)
from .policy import POLICY_INPUT_SHA256


class MissingEnvironment(RuntimeError):
    pass


def run_checker(argv, *, cwd, pythonpath=None, timeout=120, json_output=True):
    env = os.environ.copy()
    env.pop("PYTHONOPTIMIZE", None)
    env.pop("PYTHONHOME", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if pythonpath:
        env["PYTHONPATH"] = str(pythonpath)
    else:
        env.pop("PYTHONPATH", None)
    require(timeout > 0, "verification_deadline_exceeded")
    process = subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    limit = threading.Event(); buffers = [bytearray(), bytearray()]

    def drain(stream, number, maximum):
        while True:
            chunk = stream.read(4096)
            if not chunk:
                break
            if len(buffers[number]) + len(chunk) > maximum:
                limit.set(); process.kill(); break
            buffers[number].extend(chunk)
        stream.close()

    workers = [threading.Thread(target=drain, args=(stream, index, maximum), daemon=True)
               for index, (stream, maximum) in enumerate([(process.stdout, 65536),
                                                          (process.stderr, 32768)])]
    for worker in workers: worker.start()
    try:
        code = process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill(); process.wait()
        for worker in workers: worker.join(timeout=2)
        raise Rejected("checker_timeout") from None
    for worker in workers: worker.join(timeout=2)
    require(not limit.is_set(), "checker_output_limit")
    require(code == 0, "required_checker_failed")
    if not json_output:
        return bytes(buffers[0]).decode("utf-8", errors="strict").strip()
    report = strict_json(bytes(buffers[0]).strip())
    require(isinstance(report, dict), "invalid_checker_report")
    return report


def verify_capsule(root: Path, bootstrap=False, *, expected_manifest=None):
    start = time.monotonic()
    if sys.version_info < (3, 12):
        raise MissingEnvironment("python_312_required")
    require(sys.flags.optimize == 0, "assertions_required_for_original_checker")
    if bootstrap and importlib.util.find_spec("numpy") is None:
        raise MissingEnvironment("requested_numpy_unavailable")
    if bootstrap:
        try:
            __import__('numpy')
        except (ImportError, OSError):
            raise MissingEnvironment('requested_numpy_unavailable') from None
    manifest = verify_manifest(root, expected_manifest)
    for name, expected in POLICY_INPUT_SHA256.items():
        require(sha(bounded_read(local_file(root, name))) == expected, "reviewed_policy_mismatch")
    allowlist = strict_json(bounded_read(root / "capsule_allowlist.json"))
    lock = strict_json(bounded_read(root / "source_lock.json"))
    pinned = {p["path"]: EvidencePin.parse(p) for p in lock["files"]}
    for name in allowlist["files"]:
        require(name in pinned, "source_not_allowlisted")
        pinned[name].check(bounded_read(local_file(root / "source", name)))
    registry = strict_json(bounded_read(local_file(root, "claims.json")))
    count = validate_claims(registry, lambda name: bounded_read(local_file(root / "source", name)))
    mapping = strict_json(bounded_read(local_file(root, "byte_reconstruction.v1.json")))
    closed(mapping, {"format", "source_revision", "ledger", "checker_sources", "entries"})
    require(mapping["format"] == "amphora-bp09-byte-map.v1" and
            mapping["source_revision"] == manifest["source_revision"], "unsupported_byte_map")
    ledger_pin = EvidencePin.parse(mapping["ledger"])
    ledger_raw = bounded_read(local_file(root / "source", ledger_pin.path)); ledger_pin.check(ledger_raw)
    ledger = strict_json(ledger_raw)
    gates = set(ledger["evidence"])
    require(len(gates) == 12 and len(mapping["entries"]) == 12, "required_gate_set_mismatch")
    require({item["gate"] for item in mapping["entries"]} == gates, "required_gate_set_mismatch")
    checker_root = root / "checker"
    for spec in mapping["checker_sources"]:
        closed(spec, {"source", "capsule_path"})
        pin = EvidencePin.parse(spec["source"])
        pin.check(bounded_read(local_file(root, spec["capsule_path"])))
    expected_members = {"source/" + name for name in allowlist["files"]} | {
        "claims.json", "byte_reconstruction.v1.json", "source_lock.json", "capsule_allowlist.json",
        "verify.py", "START_HERE.md", "diligence/core.py", "diligence/capsule.py",
        "diligence/policy.py", "diligence/__init__.py"} | {
            spec["capsule_path"] for spec in mapping["checker_sources"]}
    require({item["path"] for item in manifest["files"]} == expected_members,
            "reviewed_allowlist_mismatch")
    reconstructed = []
    with tempfile.TemporaryDirectory(prefix="amphora-historical-evidence-") as temp:
        directory = Path(temp)
        (directory / "Acceptance_Ledger.json").write_bytes(ledger_raw)
        for item in mapping["entries"]:
            closed(item, {"gate", "source", "transform", "historical_sha256", "output_name"})
            pin = EvidencePin.parse(item["source"])
            require(item["historical_sha256"] == ledger["evidence"][item["gate"]],
                    "historical_pin_replaced")
            raw = bounded_read(local_file(root / "source", pin.path))
            output = HistoricalExport(pin, item["transform"], item["historical_sha256"]).reconstruct(raw)
            require(Path(item["output_name"]).name == item["output_name"], "path_escape")
            (directory / item["output_name"]).write_bytes(output)
            reconstructed.append({"gate": item["gate"], "transform": item["transform"],
                                  "source_sha256": pin.sha256,
                                  "historical_sha256": item["historical_sha256"]})
        runner = "import sys;sys.path.insert(0,sys.argv.pop(1));from acceptance.__main__ import main;raise SystemExit(main())"
        platform = run_checker([sys.executable, "-I", "-B", "-c", runner, str(checker_root), "--ledger",
                                str(directory / "Acceptance_Ledger.json"),
                                "--evidence-directory", str(directory)], cwd=root,
                               timeout=120-(time.monotonic()-start))
    require(platform.get("status") == "verified" and
            {g.get("gate") for g in platform.get("gates", [])} == gates and
            len(platform["gates"]) == 12 and all(g.get("status") == "verified" for g in platform["gates"])
            and platform.get("profile") == ledger["profile"]
            and platform.get("baseline") == ledger["baseline"]
            and platform.get("limitations") == ledger["limitations"]
            and platform.get("provider_calls") == 0 and platform.get("services_started") is False,
            "historical_gate_failure")
    argv = [sys.executable, "-I", "-B", str(root / "source/docs/review/plga/verify_evidence.py"),
            "--evidence", str(root / "source/docs/review/plga/evidence")]
    if bootstrap:
        argv.append("--bootstrap")
    science = run_checker(argv, cwd=root, timeout=120-(time.monotonic()-start))
    require(science.get("status") == "PASS", "scientific_evidence_failure")
    return {"format": "amphora-diligence-verification.v2", "status": "verified",
            "audience": "internal_engineering", "investor_release_qualified": False,
            "source_revision": manifest["source_revision"],
            "claims_checked": count, "payload_files_checked": len(manifest["files"]),
            "historical_evidence": platform, "byte_reconstruction": reconstructed,
            "plga": science, "bootstrap": "recomputed" if bootstrap else "not_requested",
            "source_boundary_check": "not_rerun_in_capsule",
            "checks_executed": ["reviewed_policy_and_allowlist", "source_pins", "original_historical_assertions", "plga_aggregate"] + (["plga_bootstrap_holm"] if bootstrap else []),
            "historical_only": ["original BP-09 process execution", "original PLGA fitting/replay"],
            "not_executed": ["current installed-owner recovery", "PLGA engine integration", "prospective science", "customer value", "source dependency scan in capsule"],
            "trust_model": "Trusted reviewed verifier/policy from the identified Git revision, trusted interpreter and local directory. Checksums do not authenticate a wholly replaced verifier or prove scientific truth; offline execution is not a sandbox.",
            "external_manifest_pin_checked": expected_manifest is not None,
            "manifest_sha256": sha(bounded_read(root / 'MANIFEST.json')),
            "python": sys.version.split()[0], "elapsed_seconds": round(time.monotonic() - start, 3),
            "model_fits": 0, "provider_calls": 0, "services_started": False,
            "interpretation": "Frozen evidence consistency and named arithmetic, not current service health, scientific authenticity, or an investor publication approval."}
