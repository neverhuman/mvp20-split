"""Two isolated wheel installations reproduce original live history without API access."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

from sqlalchemy import URL

from install_owner_peer import install
from postgres_fixture import ROOT, owned_state


def verify(output):
    output.mkdir(parents=True, exist_ok=False)
    copied = output / "root"
    support = copied / "dev"
    support.mkdir(parents=True)
    for name in ("openai_evaluation_bundle.py", "run_openai_evaluation.py", "postgres_fixture.py"):
        shutil.copyfile(ROOT / "dev" / name, support / name)
    shutil.copytree(ROOT / "dev/evaluation_corpora", support / "evaluation_corpora")
    tests = copied / "tests"
    shutil.copytree(ROOT / "services/agent_planning/tests", tests,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    state = owned_state()
    host, port = state["endpoint"].split(":")
    url = URL.create("postgresql+psycopg", username="planning_service", password=state["password"],
                     host=host, port=int(port), database=state["database"])
    environment = {key: value for key, value in os.environ.items() if key.upper() in {
        "SYSTEMROOT", "WINDIR", "PATH", "TEMP", "TMP", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "COMSPEC"}}
    environment.update(PYTHONUTF8="1", EVALUATION_READ_SQL=url.render_as_string(hide_password=False))
    records = []

    def run(args):
        result = subprocess.run([str(a) for a in args], cwd=output, env=environment,
                                capture_output=True, text=True, encoding="utf-8", timeout=180,
                                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        with (output / "verification.log").open("a", encoding="utf-8") as stream:
            stream.write(result.stdout + result.stderr)
        assert result.returncode == 0, "Independent evaluation verification failed; inspect verification.log"

    bootstrap = "import sys; sys.path.insert(0," + repr(str(support)) + "); "
    for label in ("initial", "replacement"):
        python = install(output / label, "amphora-agent-planning",
                         ["amphora_campaign_runtime", "amphora_research", "amphora_knowledge", "amphora_data_artifacts"])
        run([ROOT / ".venv/Scripts/uv.exe", "pip", "install", "--python", python, "pytest>=8,<9", "jsonschema>=4,<5"])
        xml = output / (label + ".xml")
        selected = [str(tests / area) for area in ("evaluation", "openai_provider", "campaign_output")]
        arguments = [*selected, "--confcutdir=" + str(tests), "--import-mode=importlib", "-m", "not postgres",
                     "-q", "--tb=short", "--junitxml=" + str(xml)]
        run([python, "-I", "-c", bootstrap + "import pytest; raise SystemExit(pytest.main(" + repr(arguments) + "))"])
        replay = output / (label + "-history.json")
        worker = tests / "evaluation_execution/replay_probe.py"
        run([python, "-I", "-c", bootstrap + "import runpy; runpy.run_path(" + repr(str(worker)) + ")[\"verify\"](" + repr(str(replay)) + ")"])
        import xml.etree.ElementTree as ET
        suites = ET.parse(xml).getroot().findall("testsuite")
        assert all(int(s.attrib[key]) == 0 for s in suites for key in ("errors", "failures", "skipped"))
        records.append({"label": label, "python": str(python), "tests": sum(int(s.attrib["tests"]) for s in suites),
                        "history_sha256": hashlib.sha256(replay.read_bytes()).hexdigest(),
                        "installation": json.loads((output / label / "manifest.json").read_bytes())})
        print(json.dumps({"label": label, "tests": records[-1]["tests"], "read_only_replay": "passed"}), flush=True)
    assert records[0]["history_sha256"] == records[1]["history_sha256"]
    assert records[0]["installation"]["wheels"] == records[1]["installation"]["wheels"]
    evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
                "installations": records, "same_original_history": True,
                "limits": ["No migrations, SQL mutations, live API calls or OpenAI credentials",
                           "Both processes enforce read-only transactions; predecessor failures and costs retained",
                           "Copied test support only; production modules run from independently installed wheels",
                           "Runtime/Studio replacement and actual browser evidence are separate retained proofs"]}
    (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    verify(parser.parse_args().output.absolute())
