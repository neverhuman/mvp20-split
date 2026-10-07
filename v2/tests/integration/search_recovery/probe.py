"""Public-only controller for baseline and interrupted reconstructed-worker campaigns."""

import hashlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main():
    assert all(importlib.util.find_spec(name) is None for name in ("sqlalchemy", "amphora_campaign_runtime", "amphora_evolution_search", "amphora_synthetic_objectives"))
    root = Path(__file__).absolute().parents[3]
    helpers = root / "services/campaign_runtime/tests/numeric_search/acceptance"
    environment = load("partial_numeric_environment", helpers / "environment.py")
    execution = load("partial_numeric_execution", helpers / "execution.py")
    failure = load("partial_numeric_failure", Path(__file__).with_name("partial_evaluation.py"))
    manifest = load("partial_numeric_manifest", Path(__file__).with_name("manifest.py"))
    config = json.loads(Path(sys.argv[1]).read_bytes())
    output = Path(config["evidence"])
    output.mkdir(parents=True, exist_ok=False)
    e = environment.NumericEnvironment(config, output)
    try:
        e.setup()
        e.admit()
        baseline = execution.execute(e, environment.HTTP)
        e.admit(reuse=True)
        injection = failure.PartialEvaluationInterruption()
        resumed = execution.execute(e, environment.HTTP, failure=injection)
        assert injection.verified
        def trace(result):
            return manifest.CheckpointTrace([manifest.CheckpointEvidence.from_bytes(record["artifact"], e.bytes(record["artifact"]))
                for record in result["reports"] if record["artifact"]["schema_ref"]["schema_id"] == "search.checkpoint"])
        equivalent = trace(baseline).equivalent(trace(resumed))
        evidence = {"timestamp_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "status": "passed", "scope": e.scope,
            "adapter_sha256": hashlib.sha256(Path(config["reconstructed_adapter"]).read_bytes()).hexdigest(), "packages": config["packages"],
            "baseline": baseline, "resumed": resumed, "checkpoint_equivalence": equivalent,
            "limits": ["Reconstructed test companion uses declared fixture image pins, not prior production image qualification",
                       "Actual Windows worker/Runtime/Data HTTP; no target-host deployment or scientific claim"], "paid_calls": 0}
        (output / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("Partial-evaluation recovery and full checkpoint equivalence passed", flush=True)
    finally:
        e.close()


if __name__ == "__main__":
    main()
