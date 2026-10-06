"""Declared offline inputs; Artifact and image labels carry no owner authority."""

import json
from hashlib import sha256
from itertools import product

from amphora_contracts_search import EvaluationRequest, search_checkpoint_schema

SEARCH_IMAGE = "d" * 64
EVALUATOR_IMAGE = "e" * 64
SCOPE = {"tenant_id": "comparison-fixture", "project_id": "numeric-v1"}


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode()


def artifact(raw, schema, prefix):
    digest = sha256(raw).hexdigest()
    return {"artifact_id": prefix + digest, "scope": SCOPE, "sha256": digest,
            "size_bytes": len(raw), "media_type": "application/json", "schema_ref": schema}


def specification(protocol, dimension, seed, policy, binding):
    lower, upper = protocol["bounds"]
    return {"schema_version": "1", "scope": SCOPE, "search_id": f"comparison-{dimension}-{seed}",
            "representation": {"schema_id": "search.numeric-vector", "version": "1", "sha256": "a" * 64},
            "variables": [{"variable_id": f"x{i}", "unit": "dimensionless", "lower": lower, "upper": upper}
                          for i in range(dimension)],
            "objectives": [{"objective_id": "cost", "unit": "dimensionless", "direction": "minimize"}],
            "evaluator": {"tool": binding, "constraints": policy, "context": [],
                          "completion": "all_frozen_members_terminal"},
            "operators": {"selection": "constrained-pareto-feasible-v1", "variation": "box-convex-uniform-v1",
                          "rng": "sha256-counter-u53-v1", **{k: protocol[k] for k in
                          ("crossover_probability", "mutation_probability", "mutation_fraction")}},
            "budget": {"population_size": protocol["population_size"], "max_generations": protocol["max_generations"],
                       "max_evaluations": protocol["evaluator_attempt_limit"], "unchanged_front_limit": None},
            "implementations": [{"name": "numeric-search", "version": protocol["search_release"], "sha256": SEARCH_IMAGE}],
            "seed": f"{seed:064x}"}


def context(spec, raw):
    return {"original_specification": spec, "checkpoint": json.loads(raw),
            "checkpoint_artifact": artifact(raw, search_checkpoint_schema().model_dump(mode="json"), "offline-checkpoint-")}


def grid(protocol, dimension):
    lower, upper = protocol["bounds"]
    count = protocol["baseline_axis_counts"][str(dimension)]
    axis = tuple(lower + (upper - lower) * (i + 0.5) / count for i in range(count))
    return tuple(product(axis, repeat=dimension))


def baseline_request(spec, ordinal, genes):
    # Baseline provenance is independent of numeric search checkpoint identity.
    digest = sha256(encode(spec)).hexdigest()
    identity = sha256(encode(["midpoint-grid-v1", digest, ordinal, genes])).hexdigest()
    data = {"schema_version": "1", "scope": spec["scope"], "evaluation_id": "ev-" + identity,
            "specification_sha256": digest,
            "candidate": {"candidate_id": identity, "generation": 0, "ordinal": ordinal, "operator": "seed",
                          "genes": list(genes), "parents": [], "draws": {"start": 0, "end": len(genes)},
                          "disposition": "proposed", "reason_code": None, "duplicate_of": None},
            "objectives": spec["objectives"], "evaluator": spec["evaluator"]}
    return EvaluationRequest.model_validate_json(encode(data)).model_dump(mode="json")
