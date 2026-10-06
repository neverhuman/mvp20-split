"""Separate CLI processes, retained bytes, and no implicit evaluator retries."""

import json
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

from amphora_contracts_search import EvaluationObservation

from .accounting import AttemptLedger, compare
from .fixtures import (EVALUATOR_IMAGE, SEARCH_IMAGE, artifact, baseline_request,
                       context, encode, grid, specification)


class ToolFailure(Exception):
    pass


class ToolCLI:
    def call(self, module, args, payload=b""):
        try:
            result = subprocess.run([sys.executable, "-m", module, *args], input=payload,
                                    capture_output=True, timeout=30, check=False)
        except (subprocess.TimeoutExpired, OSError):
            raise ToolFailure("tool_transport_failed") from None
        if result.returncode != 0 or len(result.stdout) > 262144:
            raise ToolFailure("tool_rejected_or_oversized")
        return result.stdout

    def search(self, operation, data):
        return self.call("amphora_evolution_search", ["compute", "--operation", operation,
                         "--image-sha256", SEARCH_IMAGE], encode(data))


class Arm:
    def __init__(self, output, protocol, cli, policy_path):
        self.output, self.cli, self.policy_path = output, cli, policy_path
        output.mkdir()
        self.ledger = AttemptLedger(protocol["evaluator_attempt_limit"])
        self.step = 0

    def retain(self, name, raw):
        (self.output / name).write_bytes(raw)

    def event(self, event):
        with (self.output / "attempts.jsonl").open("ab") as stream:
            stream.write(encode(event) + b"\n")
            stream.flush()

    def evaluate(self, request, position):
        raw = encode(request)
        digest = sha256(raw).hexdigest()
        index = self.ledger.begin(digest)
        self.retain(f"attempt-{index + 1:03}-request.json", raw)
        self.event(dict(self.ledger.rows[index]))  # Charged before starting the process.
        try:
            result = self.cli.call("amphora_synthetic_objectives", ["compute", "--image-sha256", EVALUATOR_IMAGE,
                                   "--policy-file", str(self.policy_path)], raw)
            self.retain(f"attempt-{index + 1:03}-response.json", result)
            observation = EvaluationObservation.model_validate_json(result)
            outcome = observation.outcome
            if (observation.scope.model_dump(mode="json") != request["scope"]
                    or observation.evaluation_id != request["evaluation_id"]
                    or observation.candidate_id != request["candidate"]["candidate_id"]
                    or observation.request_sha256 != digest or outcome.status != "evaluated"
                    or outcome.evaluator.model_dump(mode="json") != request["evaluator"]["tool"]
                    or outcome.constraints_sha256 != request["evaluator"]["constraints"]["sha256"]
                    or tuple(e.model_dump(mode="json") for e in outcome.evidence) != (request["evaluator"]["constraints"],)
                    or outcome.constraint_violation != 0 or outcome.quality != "synthetic"
                    or len(outcome.objectives) != 1 or outcome.objectives[0].objective_id != "cost"
                    or outcome.objectives[0].unit != "dimensionless"):
                raise ToolFailure("evaluation_binding_mismatch")
            self.ledger.finish(index, cost=outcome.objectives[0].value)
            self.event(dict(self.ledger.rows[index]))
            return observation.model_dump(mode="json")
        except (ToolFailure, ValueError):
            self.ledger.finish(index, reason="evaluation_unavailable")
            self.event(dict(self.ledger.rows[index]))
            return {"kind": "missing", "member_id": str(position), "reason_code": "tool_failed"}

    def search(self, operation, data):
        self.step += 1
        prefix = f"step-{self.step:03}-{operation}"
        self.retain(prefix + "-input.json", encode(data))
        raw = self.cli.search(operation, data)
        self.retain(prefix + "-output.json", raw)
        return raw

    def evolution(self, spec):
        try:
            raw = self.search("seed", spec)
            for _ in range(spec["budget"]["max_generations"] + 1):
                current = context(spec, raw)
                batch = json.loads(self.search("requests", current))
                results = [self.evaluate(request, i) for i, request in enumerate(batch["requests"])]
                raw = self.search("collect", {**current, "results": results})
                record = json.loads(raw)
                if record["phase"] == "stopped":
                    return self.ledger.report(record["stop_reason"])
                raw = self.search("vary", context(spec, raw))
            raise ToolFailure("search_transition_ceiling")
        except (ToolFailure, ValueError, KeyError, TypeError):
            return self.ledger.report("search_failed", transport_error="search_transport_or_protocol_failure")

    def baseline(self, spec, protocol, dimension):
        for i, genes in enumerate(grid(protocol, dimension)):
            self.evaluate(baseline_request(spec, i, genes), i)
        return self.ledger.report("evaluation_budget")


def run(output, *, cli=None):
    cli = cli or ToolCLI()
    protocol_raw = Path(__file__).with_name("protocol.json").read_bytes()
    protocol = json.loads(protocol_raw)
    output = Path(output).absolute()
    output.mkdir(parents=True, exist_ok=False)
    (output / "protocol.json").write_bytes(protocol_raw)
    declaration = {"profile": protocol["profile"], "protocol_sha256": sha256(protocol_raw).hexdigest(),
                   "authority": protocol["authority"], "status": "started"}
    (output / "declaration.json").write_bytes(encode(declaration))
    # Configuration is captured before any evaluator attempt. A setup failure leaves
    # a started declaration, never a completed benchmark report.
    policy = cli.call("amphora_synthetic_objectives", ["policy"])
    if json.loads(policy) != protocol["policy"]:
        raise ValueError("comparison_policy_changed")
    policy_path = output / "policy.json"
    policy_path.write_bytes(policy)
    descriptor = json.loads(cli.call("amphora_synthetic_objectives", ["describe", "--image-sha256", EVALUATOR_IMAGE]))
    binding = descriptor["tool"]["binding"]
    search_descriptor = json.loads(cli.call("amphora_evolution_search", ["describe", "--operation", "seed",
                                          "--image-sha256", SEARCH_IMAGE]))
    if binding["release"] != protocol["evaluator_release"] or search_descriptor["tool"]["binding"]["release"] != protocol["search_release"]:
        raise ValueError("comparison_release_changed")
    (output / "descriptors.json").write_bytes(encode({"search": search_descriptor, "evaluator": descriptor}))
    schema = next(port["schema_ref"] for port in descriptor["tool"]["inputs"] if port["name"] == "policy")
    policy_ref = artifact(policy, schema, "offline-policy-")
    pairs = []
    for dimension in protocol["dimensions"]:
        for seed in protocol["seeds"]:
            spec = specification(protocol, dimension, seed, policy_ref, binding)
            path = output / f"d{dimension}-seed{seed}"
            path.mkdir()
            (path / "specification.json").write_bytes(encode(spec))
            evolution = Arm(path / "evolution", protocol, cli, policy_path).evolution(spec)
            baseline = Arm(path / "baseline", protocol, cli, policy_path).baseline(spec, protocol, dimension)
            pair = {"dimension": dimension, "seed": seed, "evolution": evolution, "baseline": baseline,
                    "comparison": compare(evolution, baseline)}
            (path / "result.json").write_bytes(encode(pair))
            pairs.append(pair)
            print(f"dimension={dimension} seed={seed} {pair['comparison']['outcome']}", flush=True)
    report = {**declaration, "status": "completed", "pairs": pairs, "paid_calls": 0,
              "image_identity": "declared_offline_fixture_only",
              "artifact_authority": "no_data_owner_authentication",
              "counts": {outcome: sum(p["comparison"]["outcome"] == outcome for p in pairs)
                         for outcome in ("gain", "loss", "tie", "incomplete")}}
    (output / "report.json").write_bytes(encode(report))
    return report
