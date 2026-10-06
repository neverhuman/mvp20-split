import json
import subprocess
from hashlib import sha256
from pathlib import Path

import pytest

from numeric_comparison import runner
from numeric_comparison.fixtures import baseline_request, encode, grid, specification


PROTOCOL = json.loads(Path(runner.__file__).with_name("protocol.json").read_bytes())


def request():
    policy = {"artifact_id": "policy", "scope": {"tenant_id": "comparison-fixture", "project_id": "numeric-v1"},
              "sha256": "a" * 64, "size_bytes": 1, "media_type": "application/json",
              "schema_ref": {"schema_id": "policy", "version": "1", "sha256": "b" * 64}}
    binding = {"capability_id": "synthetic.numeric-objectives", "release": "0.2.0",
               "image_sha256": "e" * 64, "contract_version": "1"}
    return baseline_request(specification(PROTOCOL, 1, 0, policy, binding), 0, (0.25,))


class ScriptedCLI:
    def __init__(self, change=None, failure=False):
        self.change, self.failure, self.calls = change, failure, 0

    def call(self, module, args, payload):
        self.calls += 1
        if self.failure:
            raise runner.ToolFailure("timeout")
        req = json.loads(payload)
        data = {"schema_version": "1", "scope": req["scope"], "evaluation_id": req["evaluation_id"],
                "candidate_id": req["candidate"]["candidate_id"], "request_sha256": sha256(payload).hexdigest(),
                "outcome": {"status": "evaluated", "evaluator": req["evaluator"]["tool"],
                            "objectives": [{"objective_id": "cost", "unit": "dimensionless", "value": 0.0625}],
                            "constraint_violation": 0.0, "constraints_sha256": req["evaluator"]["constraints"]["sha256"],
                            "quality": "synthetic", "evidence": [req["evaluator"]["constraints"]]}}
        if self.change:
            self.change(data)
        return encode(data)


def test_declared_grid_counts_order_bounds_and_independent_minima():
    one, two = grid(PROTOCOL, 1), grid(PROTOCOL, 2)
    assert len(one) == len(two) == PROTOCOL["evaluator_attempt_limit"] == 16
    assert one[0] == (-0.9375,) and one[-1] == (0.9375,)
    assert two[:2] == ((-0.75, -0.75), (-0.75, -0.25))
    assert min(x[0] ** 2 for x in one) == 1 / 256
    assert min(sum(v * v for v in x) for x in two) == 1 / 8
    assert PROTOCOL["seeds"] == [0, 1, 17, 42, 1234]


def test_actual_attempt_is_journaled_before_dispatch_and_cannot_retry(tmp_path):
    class Checking(ScriptedCLI):
        def call(self, *args):
            assert json.loads((tmp_path / "arm/attempts.jsonl").read_text().splitlines()[0])["status"] == "pending"
            return super().call(*args)
    cli = Checking()
    arm = runner.Arm(tmp_path / "arm", PROTOCOL, cli, tmp_path / "policy")
    result = arm.evaluate(request(), 0)
    assert result["outcome"]["objectives"][0]["value"] == 0.0625
    assert cli.calls == 1 and arm.ledger.report("done")["failures"] == 0
    assert len((tmp_path / "arm/attempts.jsonl").read_text().splitlines()) == 2


@pytest.mark.parametrize("field", ["request_sha256", "candidate_id", "evaluation_id"])
def test_wrong_response_identity_charged_as_failure(tmp_path, field):
    cli = ScriptedCLI(lambda data: data.update({field: "b" * 64}))
    arm = runner.Arm(tmp_path / "arm", PROTOCOL, cli, tmp_path / "policy")
    assert arm.evaluate(request(), 3) == {"kind": "missing", "member_id": "3", "reason_code": "tool_failed"}
    assert arm.ledger.report("done")["failures"] == 1 and cli.calls == 1


@pytest.mark.parametrize("change", [
    lambda d: d["outcome"].update(quality="measured"),
    lambda d: d["outcome"].update(constraint_violation=1.0),
    lambda d: d["outcome"].update(evidence=[]),
    lambda d: d["outcome"]["objectives"][0].update(unit="kg"),
    lambda d: d["outcome"]["evaluator"].update(release="0.1.0"),
], ids=["quality", "constraint", "evidence", "unit", "evaluator"])
def test_wrong_evidence_policy_never_becomes_comparable(tmp_path, change):
    arm = runner.Arm(tmp_path / "arm", PROTOCOL, ScriptedCLI(change), tmp_path / "policy")
    assert arm.evaluate(request(), 0)["kind"] == "missing"
    assert arm.ledger.report("done")["best_successful_cost"] is None


def test_baseline_failures_do_not_remove_seeds_or_save_budget(tmp_path):
    cli = ScriptedCLI(failure=True)
    arm = runner.Arm(tmp_path / "arm", PROTOCOL, cli, tmp_path / "policy")
    req = request()
    spec = specification(PROTOCOL, 1, 0, req["evaluator"]["constraints"], req["evaluator"]["tool"])
    result = arm.baseline(spec, PROTOCOL, 1)
    assert result["attempts"] == result["failures"] == cli.calls == 16
    assert result["best_successful_cost"] is None


def test_existing_output_is_never_overwritten(tmp_path):
    with pytest.raises(FileExistsError):
        runner.run(tmp_path)


@pytest.mark.parametrize("mode", ["timeout", "exit", "oversize", "oserror"])
def test_cli_failures_are_bounded_and_not_retried(monkeypatch, mode):
    calls = []
    def execute(*args, **kwargs):
        calls.append(args)
        assert kwargs["timeout"] == 30
        if mode == "timeout":
            raise subprocess.TimeoutExpired("tool", 30)
        if mode == "oserror":
            raise OSError("secret must not propagate")
        return subprocess.CompletedProcess(args, 2 if mode == "exit" else 0,
                                           stdout=b"x" * (262145 if mode == "oversize" else 0))
    monkeypatch.setattr(runner.subprocess, "run", execute)
    with pytest.raises(runner.ToolFailure):
        runner.ToolCLI().call("fixture", [])
    assert len(calls) == 1
