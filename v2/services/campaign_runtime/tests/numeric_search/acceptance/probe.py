"""Controller executes in an isolated SDK installation without Runtime or SQL."""

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    assert importlib.util.find_spec("amphora_campaign_runtime") is None
    assert importlib.util.find_spec("sqlalchemy") is None
    environment = load("numeric_http_environment", Path(__file__).with_name("environment.py"))
    execution = load("numeric_http_execution", Path(__file__).with_name("execution.py"))
    failure = load("numeric_http_failure", Path(__file__).with_name("failure.py"))
    config = json.loads(Path(sys.argv[1]).read_bytes())
    root = Path(config["evidence"])
    root.mkdir()
    e = environment.NumericEnvironment(config, root)
    try:
        e.setup()
        e.admit()
        result = execution.execute(e, environment.HTTP)
        recovery = None
        if config.get("recovery"):
            e.admit(reuse=True)
            injection = failure.FinalizationInterruption()
            recovery = execution.execute(e, environment.HTTP, failure=injection)
            assert injection.verified
            comparable = lambda state: {key: value for key, value in state.items() if key != "previous"}
            assert comparable(result["final"]["result"]) == comparable(recovery["final"]["result"])
        evidence = {"timestamp_local": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed",
            "scope": e.scope, "packages": config["packages"], "profile": "independent Windows wheels; declared fixture image pins only",
            "result": result, "recovery": recovery}
        (root / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("Numeric HTTP acceptance passed: " + str(root / "evidence.json"), flush=True)
    finally:
        e.close()


if __name__ == "__main__":
    main()
