#!/usr/bin/env python3

import base64
import fcntl
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
cli = importlib.machinery.SourceFileLoader("amphora_cli", str(ROOT / "bin" / "amphora")).load_module()
policy = importlib.machinery.SourceFileLoader(
    "amphora_policy", str(ROOT / "policy" / "staged_file_policy.py")).load_module()
recon = importlib.machinery.SourceFileLoader(
    "amphora_recon", str(ROOT / "tools" / "recon_invariants.py")).load_module()


class OpsTests(unittest.TestCase):
    def test_environment_overrides_config(self):
        with tempfile.TemporaryDirectory() as td:
            envfile = Path(td) / "cron.env"
            envfile.write_text("AMPHORA_MODEL=file-model\n")
            with mock.patch.dict(os.environ, {"AMPHORA_CONFIG_FILE": str(envfile),
                                              "AMPHORA_MODEL": "env-model"}, clear=False):
                self.assertEqual(cli.config()["AMPHORA_MODEL"], "env-model")

    def test_cron_update_preserves_unrelated_lines(self):
        old = "# header\n7 * * * * unrelated\n0 * * * * /home/ubuntu/amphora-cron/claude-hourly-loop.sh\n"
        entries = cli.cron_entries(dict(cli.DEFAULTS))
        new = cli.update_cron(old, ("launcher",), entries, False, "HANDOFF-TEST")
        self.assertIn("# header\n7 * * * * unrelated\n", new)
        self.assertIn("AMPHORA_MANAGED_DISABLED HANDOFF-TEST", new)
        self.assertNotIn("amphora-cron/claude-hourly-loop.sh", new)

    def test_foreign_hard_stop_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = dict(cli.DEFAULTS)
            cfg["AMPHORA_STATE_ROOT"] = td
            path = Path(td) / "state" / "HARD_STOP"
            path.parent.mkdir()
            path.write_text("FOREIGN-STOP\n")
            with self.assertRaises(cli.OperatorError):
                cli.require_matching_stop(cfg, "OWNED-STOP")

    def test_install_is_dry_run_without_apply(self):
        proc = subprocess.run([str(ROOT / "bin" / "amphora"), "install"],
                              stdout=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("DRY-RUN", proc.stdout)

    def test_snapshot_defaults_to_dry_run(self):
        proc = subprocess.run([str(ROOT / "reviewed-snapshot.sh")],
                              stdout=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("DRY-RUN reviewed snapshot", proc.stdout)

    def test_drain_requires_every_controller_lock(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = dict(cli.DEFAULTS)
            cfg["AMPHORA_STATE_ROOT"] = td
            lock = Path(td) / "state" / "locks" / "fleet.lock"
            lock.parent.mkdir(parents=True)
            with lock.open("a") as handle:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                self.assertFalse(cli.controller_locks_available(cfg))
            self.assertTrue(cli.controller_locks_available(cfg))

    def test_manifest_rejects_unlisted_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            tracked = root / "tracked.txt"
            tracked.write_text("tracked\n")
            digest = hashlib.sha256(tracked.read_bytes()).hexdigest()
            (root / "controller-tree.sha256").write_text(f"{digest}  tracked.txt\n")
            self.assertTrue(cli.verify_manifest(root)[0])
            (root / "unexpected.txt").write_text("unexpected\n")
            ok, detail = cli.verify_manifest(root)
            self.assertFalse(ok)
            self.assertIn("unlisted", detail)

    def test_policy_blocks_forbidden_secret_binary_and_large(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "logs").mkdir()
            (repo / "logs" / "runtime.log").write_text("x")
            (repo / "credential.txt").write_text("x")
            (repo / "binary.dat").write_bytes(b"x\0y")
            (repo / "large.txt").write_bytes(b"x" * ((1 << 20) + 1))
            _, violations = policy.evaluate(repo, [("A", "logs/runtime.log"),
                                                    ("A", "credential.txt"),
                                                    ("A", "binary.dat"),
                                                    ("A", "large.txt")], "publication")
            self.assertEqual(len(violations), 4)

    def test_policy_allows_controller_source(self):
        approved, violations = policy.evaluate(REPO, [("A", "ops/amphora-controller/bin/amphora")],
                                               "publication")
        self.assertEqual(violations, [])
        self.assertEqual(approved, ["ops/amphora-controller/bin/amphora"])

    def test_dsse_payload_decodes_top_level_and_nested(self):
        payload = base64.b64encode(b'{"fire_id":"fire-1"}').decode()
        with tempfile.TemporaryDirectory() as td:
            top = Path(td) / "top.json"
            nested = Path(td) / "nested.json"
            top.write_text(json.dumps({"payload": payload}))
            nested.write_text(json.dumps({"signature": {"payload": payload}}))
            self.assertIn("fire-1", recon.dsse_payload_text(top))
            self.assertIn("fire-1", recon.dsse_payload_text(nested))

    def test_dynamic_fd_checker(self):
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / "fd.sh"
            script.write_text("close_it() { eval \"exec $LOCK_FD>&-\"; }\nexec {LOCK_FD}>>/tmp/x\nclose_it\n")
            proc = subprocess.run(["python3", str(ROOT / "tools" / "check_unbound.py"), str(script)])
            self.assertEqual(proc.returncode, 0)

    def test_campaign_baseline_has_no_new_violations(self):
        proc = subprocess.run(["python3", str(ROOT / "tools" / "campaign_invariants.py"),
                               str(ROOT / "bootstrap" / "campaign.json"), "--json"],
                              stdout=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(json.loads(proc.stdout)["new_violations"], 0)

    def test_checkpoint_binds_frozen_files(self):
        checkpoint = json.loads((ROOT / "bootstrap" / "campaign-chain-checkpoint.json").read_text())
        for key, name in (("campaign", "campaign.json"),
                          ("acquisition_queue", "data-acquisition-queue.jsonl")):
            digest = hashlib.sha256((ROOT / "bootstrap" / name).read_bytes()).hexdigest()
            self.assertEqual(checkpoint[key]["sha256"], digest)

    def test_freeze_record_hashes_crontabs(self):
        freeze_root = ROOT / "bootstrap" / "freeze"
        record = json.loads((freeze_root / "record.json").read_text())
        for row in record["crontabs"]:
            for phase in ("before", "after"):
                digest = hashlib.sha256((freeze_root / row[phase]).read_bytes()).hexdigest()
                self.assertEqual(row[phase + "_sha256"], digest)

    def test_excluded_legacy_debris_absent(self):
        paths = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")}
        self.assertNotIn("module-queue.json", paths)
        self.assertFalse(any(".bak" in path for path in paths))
        self.assertFalse(any(path.startswith("logs/") or path.startswith("state/") for path in paths))

    def test_autocommit_guard_never_pushes(self):
        text = (ROOT / "autocommit-guard.sh").read_text()
        self.assertNotRegex(text, r"\bgit\s+push\b")
        self.assertIn("AUTOCOMMIT_DRAIN", text)
        self.assertIn("QUARANTINED_SCHEMA_FLIP", text)

    def test_sandbox_transports_are_fail_closed(self):
        harness = (ROOT / "tools" / "tests" / "harness.sh").read_text()
        launcher = (ROOT / "claude-hourly-loop.sh").read_text()
        self.assertIn("for transport in ssh scp", harness)
        self.assertIn('exec timeout 25s $SSH "$XBABE2_HOST"', launcher)
        self.assertNotIn("exec timeout 25s ssh -o", launcher)

    def test_operator_surface_is_complete(self):
        help_text = subprocess.run([str(ROOT / "bin" / "amphora"), "--help"],
                                   stdout=subprocess.PIPE, text=True).stdout
        for command in ("doctor", "status", "test", "pause", "drain", "resume", "install"):
            self.assertIn(command, help_text)


if __name__ == "__main__":
    unittest.main()
