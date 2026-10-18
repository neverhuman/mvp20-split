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

from .core import (EvidencePin, HistoricalExport, Rejected, bounded_read, canonical,
                   closed, local_file, require, strict_json, validate_claims,
                   verify_manifest)


class MissingEnvironment(RuntimeError):
    pass


def run_checker(argv, *, cwd, pythonpath=None):
    env = os.environ.copy()
    env.pop("PYTHONOPTIMIZE", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if pythonpath:
        env["PYTHONPATH"] = str(pythonpath)
    else:
        env.pop("PYTHONPATH", None)
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                            text=True, timeout=120)
    require(result.returncode == 0, "required_checker_failed")
    try:
        report = json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        raise Rejected("invalid_checker_report") from None
    return report


def verify_capsule(root: Path, bootstrap=False):
    start = time.monotonic()
    if sys.version_info < (3, 12):
        raise MissingEnvironment("python_312_required")
    require(sys.flags.optimize == 0, "assertions_required_for_original_checker")
    if bootstrap and importlib.util.find_spec("numpy") is None:
        raise MissingEnvironment("requested_numpy_unavailable")
    manifest = verify_manifest(root)
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
        platform = run_checker([sys.executable, "-B", "-m", "acceptance", "--ledger",
                                str(directory / "Acceptance_Ledger.json"),
                                "--evidence-directory", str(directory)], cwd=root,
                               pythonpath=checker_root)
    require(platform.get("status") == "verified" and len(platform.get("gates", [])) == 12,
            "historical_gate_failure")
    argv = [sys.executable, "-B", str(root / "source/docs/review/plga/verify_evidence.py"),
            "--evidence", str(root / "source/docs/review/plga/evidence")]
    if bootstrap:
        argv.append("--bootstrap")
    science = run_checker(argv, cwd=root)
    require(science.get("status") == "PASS", "scientific_evidence_failure")
    return {"format": "amphora-diligence-verification.v1", "status": "verified",
            "audience": "internal_engineering", "investor_release_qualified": False,
            "source_revision": manifest["source_revision"],
            "claims_checked": count, "payload_files_checked": len(manifest["files"]),
            "historical_evidence": platform, "byte_reconstruction": reconstructed,
            "plga": science, "bootstrap": "recomputed" if bootstrap else "not_requested",
            "source_boundary_check": "not_rerun_in_capsule",
            "python": sys.version.split()[0], "elapsed_seconds": round(time.monotonic() - start, 3),
            "model_fits": 0, "provider_calls": 0, "services_started": False,
            "interpretation": "Frozen evidence consistency and named arithmetic, not current service health, scientific authenticity, or an investor publication approval."}
