"""Independent fixed-box arithmetic and exact protocol chain inside offline images."""

import hashlib
import importlib.util
import json

from amphora_contracts_search import SearchSpec

from check_boundaries import ROOT


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def verify_golden(run, images):
    numeric, evaluator = images
    releases = {**numeric["descriptors"], **evaluator["descriptors"]}
    path = ROOT / "services/campaign_runtime/tests/numeric_search/specification.py"
    loader = importlib.util.spec_from_file_location("image_specification", path)
    fixture = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(fixture)
    scope = {"tenant_id": "image-golden", "project_id": "fixed-box"}
    policy_bytes = b'{"profile":"synthetic-quadratic-v1"}'
    policy = {"artifact_id": "image-policy", "scope": scope, "media_type": "application/json",
        "schema_ref": releases["evaluate"]["tool"]["inputs"][1]["schema_ref"],
        "sha256": hashlib.sha256(policy_bytes).hexdigest(), "size_bytes": len(policy_bytes)}
    raw = fixture.specification(scope, releases, policy, population=1, generations=1, fixed=True)
    spec = SearchSpec.model_validate_json(json.dumps(raw)).model_dump(mode="json")
    spec_hash = hashlib.sha256(canonical(spec)).hexdigest()

    def step(operation, payload):
        return run(["docker", "run", "--rm", "--network", "none", "-i", numeric["tag"], "compute",
                    "--operation", operation, "--image-sha256", numeric["image_manifest_digest"].removeprefix("sha256:")], canonical(payload))

    def context(body):
        checkpoint = json.loads(body)
        reference = {"artifact_id": "image-checkpoint-" + hashlib.sha256(body).hexdigest(), "scope": scope,
            "sha256": hashlib.sha256(body).hexdigest(), "size_bytes": len(body), "media_type": "application/json",
            "schema_ref": releases["seed"]["tool"]["outputs"][0]["schema_ref"]}
        return {"original_specification": spec, "checkpoint": checkpoint, "checkpoint_artifact": reference}

    seeded = step("seed", spec)
    state = json.loads(seeded)
    expected_id = hashlib.sha256(canonical(["numeric-attempt-v1", spec_hash, 0, 0, "seed", [float(0).hex()], [], 0, 1])).hexdigest()
    assert state["attempts"][0]["candidate_id"] == expected_id and state["attempts"][0]["genes"] == [0.0]
    assert state["rng"]["counter"] == 1 and state["phase"] == "awaiting_evaluations"
    request = json.loads(step("requests", context(seeded)))["requests"][0]
    assert request["evaluation_id"] == "ev-" + expected_id
    assert run(["docker", "run", "--rm", "--network", "none", evaluator["tag"], "policy"]) == policy_bytes
    # Exercise the public CLI with a private temporary file inside the nonroot container.
    script = "import pathlib,runpy,sys; pathlib.Path('/tmp/policy.json').write_bytes(" + repr(policy_bytes) + "); "
    script += "sys.argv=" + repr(["amphora_synthetic_objectives", "compute", "--policy-file", "/tmp/policy.json",
        "--image-sha256", evaluator["image_manifest_digest"].removeprefix("sha256:")]) + "; "
    script += "runpy.run_module('amphora_synthetic_objectives',run_name='__main__')"
    observed = json.loads(run(["docker", "run", "--rm", "--network", "none", "-i", "--entrypoint", "python",
                              evaluator["tag"], "-c", script], canonical(request)))
    assert observed["outcome"]["objectives"] == [{"objective_id": "cost", "unit": "dimensionless", "value": 0.0}]
    assert observed["outcome"]["quality"] == "synthetic" and observed["outcome"]["evidence"] == [policy]
    selected = step("collect", {**context(seeded), "results": [observed]})
    assert json.loads(selected)["population"] == [expected_id]
    varied = step("vary", context(selected))
    assert json.loads(varied)["rng"]["counter"] == 7
    assert json.loads(step("requests", context(varied)))["requests"] == []
    final = json.loads(step("collect", {**context(varied), "results": []}))
    assert final["phase"] == "stopped" and final["stop_reason"] == "generation_budget"
    assert final["progress"]["evaluations_issued"] == 1 and final["rng"]["counter"] == 7
    assert final["population"] == [expected_id]
    return {"profile": "fixed-zero-box-v1", "specification": spec, "seed_candidate_id": expected_id,
            "observation": observed, "final": final, "claim": "Offline image arithmetic/CLI only; Artifact references are declared fixture metadata."}
