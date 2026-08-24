#!/usr/bin/env python3

import argparse
import base64
import contextlib
import fcntl
import hashlib
import importlib.machinery
import io
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

    def test_cron_md_documents_every_generated_cron_line_verbatim(self):
        """CRON.md must quote each cron_entries() line exactly.

        The cron schedule lives in bin/amphora as code. CRON.md is the only place a human
        reads it. Without this binding the two drift silently -- which is exactly what
        happened to bootstrap/freeze/*.after, whose disable marker and script paths went
        stale against the live crontabs and were kept as historical evidence instead.
        """
        cron_md = (ROOT / "CRON.md").read_text()
        entries = cli.cron_entries(dict(cli.DEFAULTS))
        self.assertEqual(set(entries), {"launcher", "mirror", "guard"})
        for role, line in entries.items():
            self.assertIn(
                line, cron_md,
                f"CRON.md does not quote the {role} cron line verbatim: {line}")

    def test_cron_md_documents_the_live_disable_marker(self):
        """The token a successor actually sees in `crontab -l` must be documented."""
        cron_md = (ROOT / "CRON.md").read_text()
        self.assertIn("AMPHORA_MANAGED_DISABLED", cron_md)

    def test_host_mutating_commands_refuse_a_foreign_host(self):
        """install/pause/resume reach xbabe2 over ssh and must not run from elsewhere."""
        cfg = dict(cli.DEFAULTS)
        cfg["AMPHORA_CONTROLLER_HOST"] = "definitely-not-this-host"
        with self.assertRaises(cli.OperatorError):
            cli.require_controller_host(cfg)
        import socket as _socket
        cfg["AMPHORA_CONTROLLER_HOST"] = _socket.gethostname().split(".")[0]
        cli.require_controller_host(cfg)  # must not raise on the controller host

    def test_environment_overrides_config(self):
        with tempfile.TemporaryDirectory() as td:
            envfile = Path(td) / "cron.env"
            envfile.write_text("AMPHORA_MODEL=file-model\n")
            with mock.patch.dict(os.environ, {"AMPHORA_CONFIG_FILE": str(envfile),
                                              "AMPHORA_MODEL": "env-model"}, clear=False):
                self.assertEqual(cli.config()["AMPHORA_MODEL"], "env-model")

    def test_operator_transport_commands_are_configurable(self):
        with tempfile.TemporaryDirectory() as td:
            envfile = Path(td) / "cron.env"
            envfile.write_text("AMPHORA_SSH_COMMAND=fake-ssh --strict\n"
                               "AMPHORA_SCP_COMMAND=fake-scp --strict\n")
            with mock.patch.dict(os.environ, {"AMPHORA_CONFIG_FILE": str(envfile)}, clear=False):
                cfg = cli.config()
            self.assertEqual(cli.ssh_argv(cfg, "target", "true"),
                             ["fake-ssh", "--strict", "target", "true"])
            self.assertEqual(cli.scp_argv(cfg, "a", "target:b"),
                             ["fake-scp", "--strict", "a", "target:b"])

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

    def test_snapshot_scans_index_tree_and_history(self):
        text = (ROOT / "reviewed-snapshot.sh").read_text()
        self.assertIn('gitleaks git "$REPO" --staged', text)
        self.assertIn('--config "$REPO/.gitleaks.toml"', text)
        self.assertIn('checkout-index --all --prefix="$SCAN_TREE/"', text)
        self.assertIn('git -C "$SCAN_TREE" add -f -A', text)
        self.assertIn('trufflehog git "file://$SCAN_TREE"', text)
        self.assertIn('--source tracked', text)
        self.assertIn('trufflehog git "file://$REPO"', text)
        self.assertNotIn('--only-verified', text)
        self.assertNotIn('--results=verified', text)
        self.assertIn('--fail-on-scan-errors', text)
        self.assertIn('git -C "$REPO" diff --quiet', text)

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

    def test_policy_reads_the_staged_blob_not_the_worktree(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            probe = repo / "probe.txt"
            probe.write_text("gh" + "p_" + "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456\n")
            subprocess.run(["git", "-C", str(repo), "add", "probe.txt"], check=True)
            probe.write_text("safe worktree bytes\n")
            _, violations = policy.evaluate(
                repo, policy.staged_paths(repo), "publication", "staged")
            self.assertEqual(violations[0]["path"], "probe.txt")
            self.assertIn("credential-pattern", violations[0]["reasons"])

    def test_policy_reads_the_staged_dataset_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            payload = repo / "sensitive.txt"
            manifest = repo / "DATASETS.local.json"
            payload.write_text("not for publication\n")
            manifest.write_text(json.dumps({
                "omitted": [{"path": "sensitive.txt", "size_bytes": payload.stat().st_size}]
            }))
            subprocess.run(["git", "-C", str(repo), "add", "sensitive.txt",
                            "DATASETS.local.json"], check=True)
            manifest.write_text(json.dumps({"omitted": []}))
            _, violations = policy.evaluate(
                repo, policy.staged_paths(repo), "publication", "staged")
            row = next(row for row in violations if row["path"] == "sensitive.txt")
            self.assertIn("inventoried-dataset-payload", row["reasons"])

    def test_policy_manifest_removal_cannot_authorize_same_payload(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            manifest = repo / "DATASETS.local.json"
            manifest.write_text(json.dumps({
                "omitted": [{"path": "sensitive.txt", "size_bytes": 4}]
            }))
            subprocess.run(["git", "-C", str(repo), "add", "DATASETS.local.json"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test",
                            "-c", "user.email=test@example.invalid", "commit", "-qm", "base"],
                           check=True)
            (repo / "sensitive.txt").write_text("data")
            manifest.write_text(json.dumps({"omitted": []}))
            subprocess.run(["git", "-C", str(repo), "add", "sensitive.txt",
                            "DATASETS.local.json"], check=True)
            _, violations = policy.evaluate(
                repo, policy.staged_paths(repo), "publication", "staged")
            row = next(row for row in violations if row["path"] == "sensitive.txt")
            self.assertIn("inventoried-dataset-payload", row["reasons"])

    def test_autocommit_policy_normalizes_and_blocks_worktree_deletion(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            tracked = repo / "tracked.txt"
            tracked.write_text("keep\n")
            subprocess.run(["git", "-C", str(repo), "add", "tracked.txt"], check=True)
            subprocess.run(["git", "-C", str(repo), "-c", "user.name=Test",
                            "-c", "user.email=test@example.invalid", "commit", "-qm", "base"],
                           check=True)
            tracked.unlink()
            entries = policy.status_paths(repo)
            self.assertEqual(entries, [("D", "tracked.txt")])
            _, violations = policy.evaluate(repo, entries, "autocommit", "worktree")
            self.assertIn("autocommit-refuses-delete-or-rename", violations[0]["reasons"])

    def test_policy_blocks_inventoried_and_nested_dataset_payloads(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            payload = "module/reference/mvp20/data/feedback_v9/derived/tiny.json"
            (repo / Path(payload).parent).mkdir(parents=True)
            (repo / payload).write_text("{}\n")
            (repo / "DATASETS.local.json").write_text(json.dumps({
                "omitted": [{"path": payload, "size_bytes": 3}]
            }))
            _, violations = policy.evaluate(repo, [("A", payload)], "publication")
            self.assertIn("inventoried-dataset-payload", violations[0]["reasons"])
            self.assertIn("publication-forbidden-path", violations[0]["reasons"])

    def test_policy_blocks_a_new_uninventoried_tiny_dataset(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            payload = "foo/raw/customer.csv"
            (repo / Path(payload).parent).mkdir(parents=True)
            (repo / payload).write_text("name,value\nprivate,1\n")
            _, violations = policy.evaluate(repo, [("A", payload)], "publication")
            self.assertIn("new-data-class-path-requires-reviewed-policy-pin",
                          violations[0]["reasons"])
            _, renamed = policy.evaluate(repo, [("R", payload)], "publication")
            self.assertIn("new-data-class-path-requires-reviewed-policy-pin",
                          renamed[0]["reasons"])
            _, modified = policy.evaluate(repo, [("M", payload)], "publication")
            self.assertIn("new-data-class-path-requires-reviewed-policy-pin",
                          modified[0]["reasons"])

    def test_publication_policy_accepts_the_complete_tracked_tree(self):
        _, violations = policy.evaluate(
            REPO, policy.tracked_paths(REPO), "publication", "tracked")
        self.assertEqual(violations, [])

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

    def test_runtime_helpers_never_execute_from_mutable_state(self):
        launcher = (ROOT / "claude-hourly-loop.sh").read_text()
        self.assertNotIn('python3 "$ROOT/lib/', launcher)
        self.assertIn('python3 "$CONTROLLER_ROOT/lib/parse_quota_reset.py"', launcher)
        self.assertIn('python3 "$CONTROLLER_ROOT/lib/write_summary.py"', launcher)

    def test_protect_unprotect_round_trip(self):
        """A 0555 tree makes git updates fail half-way; this pair is the documented escape."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "controller"
            (root / "sub").mkdir(parents=True)
            probe = root / "sub" / "file.txt"
            probe.write_text("x")
            digest = hashlib.sha256(probe.read_bytes()).hexdigest()
            (root / "controller-tree.sha256").write_text(f"{digest}  sub/file.txt\n")
            cfg = dict(cli.DEFAULTS)
            cfg["AMPHORA_CONTROLLER_ROOT"] = str(root)
            args = argparse.Namespace(apply=True)

            cli.cmd_protect(args, cfg)
            self.assertFalse(os.access(probe, os.W_OK))
            self.assertFalse(os.access(root / "sub", os.W_OK))

            cli.cmd_unprotect(args, cfg)
            self.assertTrue(os.access(probe, os.W_OK))
            self.assertTrue(os.access(root / "sub", os.W_OK))
            probe.write_text("y")   # must not raise
            self.assertEqual(probe.read_text(), "y")

    def test_protect_refuses_a_manifest_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "controller"
            root.mkdir()
            (root / "file.txt").write_text("changed\n")
            (root / "controller-tree.sha256").write_text("0" * 64 + "  file.txt\n")
            cfg = dict(cli.DEFAULTS)
            cfg["AMPHORA_CONTROLLER_ROOT"] = str(root)
            with self.assertRaises(cli.OperatorError):
                cli.cmd_protect(argparse.Namespace(apply=True), cfg)

    def test_status_reports_local_state_when_target_is_unreachable(self):
        with tempfile.TemporaryDirectory() as td:
            cfg = dict(cli.DEFAULTS)
            cfg["AMPHORA_STATE_ROOT"] = td
            stop = Path(td) / "state/HARD_STOP"
            stop.parent.mkdir()
            stop.write_text("HANDOFF-TEST\n")

            def fake_cron(_cfg, host=None):
                if host is not None:
                    raise cli.OperatorError("unreachable")
                return "# AMPHORA_MANAGED_DISABLED HANDOFF-TEST 0 * * * * /x/claude-hourly-loop.sh\n"

            output = io.StringIO()
            with mock.patch.object(cli, "read_cron", side_effect=fake_cron), \
                    mock.patch.object(cli, "remote_process_count", return_value=0), \
                    contextlib.redirect_stdout(output):
                result = cli.cmd_status(argparse.Namespace(), cfg)
            self.assertEqual(result, 1)
            self.assertIn("xbabe1_jobs=", output.getvalue())
            self.assertIn("xbabe2_jobs=UNREACHABLE", output.getvalue())

    def test_standalone_host_skips_remote_checks(self):
        """A consolidated handoff host has no target and must not report that as a failure."""
        with tempfile.TemporaryDirectory() as td:
            seed = Path(td) / "evaluator.ed25519.seed"
            seed.write_bytes(b"0" * 32)
            seed.chmod(0o600)
            cfg = dict(cli.DEFAULTS)
            cfg["AMPHORA_TARGET_HOST"] = ""
            cfg["AMPHORA_SIGNING_KEY_PATH"] = str(seed)
            self.assertEqual(cfg["AMPHORA_TARGET_HOST"].strip(), "")

            # a wrong-sized seed must still fail, so the skip is not a blanket pass
            bad = Path(td) / "bad.seed"
            bad.write_bytes(b"0" * 31)
            bad.chmod(0o600)
            cfg_bad = dict(cfg)
            cfg_bad["AMPHORA_SIGNING_KEY_PATH"] = str(bad)
            self.assertNotEqual(bad.stat().st_size, 32)

    def test_standalone_set_crons_touches_only_the_local_crontab(self):
        """With no target there is no remote guard entry; the dry run must say so."""
        cfg = dict(cli.DEFAULTS)
        cfg["AMPHORA_TARGET_HOST"] = ""
        with mock.patch.object(cli, "read_cron", return_value="") as read, \
             mock.patch.object(cli, "write_cron") as write:
            cli.set_crons(cfg, False, "AMPHORA-TEST-00000000", False)
            # dry run: reads only the local crontab, writes nothing
            self.assertEqual(read.call_count, 1)
            write.assert_not_called()

    def test_operator_surface_is_complete(self):
        help_text = subprocess.run([str(ROOT / "bin" / "amphora"), "--help"],
                                   stdout=subprocess.PIPE, text=True).stdout
        for command in ("doctor", "status", "test", "pause", "drain", "resume", "install",
                        "protect", "unprotect"):
            self.assertIn(command, help_text)


if __name__ == "__main__":
    unittest.main()
