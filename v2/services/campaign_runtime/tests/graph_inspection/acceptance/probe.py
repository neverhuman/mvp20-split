"""Actual solver/owner peers observed by separate DTO-only installs across replacement."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("observed_solver_probe", Path(__file__).parents[2] / "baseline/acceptance/probe.py")
SOLVER = importlib.util.module_from_spec(spec)
spec.loader.exec_module(SOLVER)


class ObservedEnvironment(SOLVER.ENV.SolverEnvironment):
    def setup(self):
        self.observations = {}
        super().setup()

    def observe(self, run, operation, *, replacement=False, **payload):
        environment = {key: value for key, value in os.environ.items() if key.upper() in {
            "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "PATH", "COMSPEC"}}
        environment["OBSERVER_TOKEN"] = self.tokens["admin"]
        result = subprocess.run([self.config["observer_replacement" if replacement else "observer"], "-I",
            str(Path(__file__).with_name("reader.py"))], input=json.dumps({"operation": operation, "run": run,
            "endpoint": self.runtime.endpoint, **payload}), env=environment, text=True, capture_output=True,
            encoding="utf-8", timeout=120, creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        assert result.returncode == 0, "Independent observer failed: " + result.stderr[-2500:]
        return json.loads(result.stdout)

    def execute(self):
        run = self.active_run
        initial = self.observe(run, "snapshot")
        result = super().execute()
        first = self.observe(run, "snapshot")
        full = self.observe(run, "resume", first=first)
        events = self.observe(run, "events", cursor=initial["snapshot"]["event_cursor"])
        assert [entry["revision"] for entry in events["entries"]] == list(range(
            initial["snapshot"]["cut"]["revision"] + 1, first["snapshot"]["cut"]["revision"] + 1))
        assert len({entry["event_id"] for entry in events["entries"]}) == len(events["entries"])
        assert first["snapshot"]["status"] == "completed"
        self.observations[run] = {"initial": initial, "first": first, "full": full, "events": events}
        self.record("GRAPH-OBSERVATION-COMPLETE", {"run": run, "observations": full, "events": events,
            "reader_private_imports_absent": True, "schema_validation": "public graph-runtime 0.5.0 DTOs"})
        return result

    def replace_runtime(self):
        super().replace_runtime()
        for run, old in self.observations.items():
            full = self.observe(run, "resume", replacement=True, first=old["first"])
            events = self.observe(run, "events", replacement=True, cursor=old["initial"]["snapshot"]["event_cursor"])
            assert full == old["full"] and events == old["events"]
            self.record("GRAPH-OBSERVATION-REPLACEMENT", {"run": run, "cut": full["cut"], "nodes": len(full["nodes"]),
                "events": len(events["entries"]), "old_page_and_event_cursors_preserved": True,
                "all_detail_attempt_value_records_equal": True, "independent_reader_and_runtime_replaced": True})


def main():
    assert importlib.util.find_spec("amphora_campaign_runtime") is None
    assert importlib.util.find_spec("sqlalchemy") is None
    config = json.loads(Path(sys.argv[1]).read_bytes())
    with tempfile.TemporaryDirectory(prefix="amphora-observation-peers-") as directory:
        e = ObservedEnvironment(config, Path(directory))
        try:
            e.setup()
            SOLVER.scenarios(e)
            e.save("passed")
            print("Installed observer/solver/owner replacement passed; scope " + e.scope["project_id"], flush=True)
        except BaseException:
            e.save("failed")
            raise
        finally:
            e.close()


if __name__ == "__main__":
    main()
