"""SDK-only controller; uses actual peers and two independently built browser consumers."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).absolute().parents[3]
spec = importlib.util.spec_from_file_location("studio_observed_peers",
    ROOT / "services/campaign_runtime/tests/graph_inspection/acceptance/probe.py")
OBSERVED = importlib.util.module_from_spec(spec)
spec.loader.exec_module(OBSERVED)


class BrowserEnvironment(OBSERVED.ObservedEnvironment):
    def setup(self):
        super().setup()
        self.browser_history = {}
        self.tokens["studio"] = uuid.uuid4().hex
        config = json.loads(Path(self.runtime.config).read_bytes())
        config["principals"].append(self.principal("studio", ["read"]))
        port = self.runtime.port
        self.runtime.close()
        self.runtime = self.host("runtime", "amphora_campaign_runtime", config, "AMPHORA_RUNTIME_DATABASE_URL", port)

    def browser(self, run, expected, *, replacement=False, old=None):
        label = "replacement" if replacement else "original"
        env = {key: value for key, value in os.environ.items() if key.upper() in {
            "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC", "USERPROFILE", "LOCALAPPDATA", "APPDATA"}}
        env["STUDIO_OBSERVER_TOKEN"] = self.tokens["studio"]
        staged = Path(self.config["studio"][label])
        output = Path(self.config["evidence"]) / self.scope["project_id"] / (run + "-" + label)
        result = subprocess.run([self.config["node"], "tests/integration/browser.mjs"], cwd=staged, env=env,
            input=json.dumps({"endpoint": self.runtime.endpoint, "scope": self.scope, "run": run,
                "expected": expected, "old": old, "output": str(output)}),
            text=True, capture_output=True, encoding="utf-8", timeout=180, check=False,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        assert result.returncode == 0, "Actual-owner browser failed: " + result.stderr[-2500:] + result.stdout[-1000:]
        return json.loads(result.stdout)

    def execute(self):
        result = super().execute()
        run = self.active_run
        actual = self.browser(run, self.observations[run]["full"])
        self.browser_history[run] = actual
        self.record("STUDIO-ACTUAL-OWNER", {"run": run, "cut": actual["cut"], "nodes": len(actual["nodes"]),
            "details": len(actual["details"]), "browser": actual["browser"], "read_only_principal": True,
            "browser_owner_credentials_absent": True, "screenshot": actual["screenshot"]})
        return result

    def replace_runtime(self):
        super().replace_runtime()
        for run, old in self.browser_history.items():
            actual = self.browser(run, self.observations[run]["full"], replacement=True, old=old)
            assert actual["cut"] == old["cut"] and actual["nodes"] == old["nodes"] and actual["details"] == old["details"]
            self.record("STUDIO-REPLACEMENT", {"run": run, "cut": actual["cut"], "nodes": len(actual["nodes"]),
                "details": len(actual["details"]), "independent_browser_and_runtime_replaced": True,
                "old_snapshot_and_event_cursor_preserved": True, "screenshot": actual["screenshot"]})


def main():
    assert importlib.util.find_spec("amphora_campaign_runtime") is None
    assert importlib.util.find_spec("sqlalchemy") is None
    config = json.loads(Path(sys.argv[1]).read_bytes())
    with tempfile.TemporaryDirectory(prefix="amphora-studio-owners-") as directory:
        e = BrowserEnvironment(config, Path(directory))
        try:
            e.setup()
            OBSERVED.SOLVER.scenarios(e)
            e.record("STUDIO-INDEPENDENT-BUILDS", config["studio_pins"])
            e.save("passed")
            print("Actual-owner Studio and Runtime replacement passed; scope " + e.scope["project_id"], flush=True)
        except BaseException:
            e.save("failed")
            raise
        finally:
            e.close()


if __name__ == "__main__":
    main()
