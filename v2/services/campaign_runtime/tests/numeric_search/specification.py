"""Small synthetic campaign input, bound to this test's actual policy Artifact."""


def specification(scope, releases, policy, *, generations=2, population=2, evaluations=20, fixed=False):
    numeric = releases["seed"]["tool"]["binding"]
    return {"schema_version": "1", "scope": scope, "search_id": "graph-numeric-fixture",
        "representation": {"schema_id": "search.numeric-vector", "version": "1", "sha256": "a" * 64},
        "variables": [{"variable_id": "x", "unit": "dimensionless", "lower": 0.0, "upper": 0.0 if fixed else 1.0}],
        "objectives": [{"objective_id": "cost", "unit": "dimensionless", "direction": "minimize"}],
        "evaluator": {"tool": releases["evaluate"]["tool"]["binding"], "constraints": policy,
                      "context": [], "completion": "all_frozen_members_terminal"},
        "operators": {"selection": "constrained-pareto-feasible-v1", "variation": "box-convex-uniform-v1",
                      "rng": "sha256-counter-u53-v1", "crossover_probability": 1.0,
                      "mutation_probability": 1.0, "mutation_fraction": 0.1},
        "budget": {"population_size": population, "max_generations": generations,
                   "max_evaluations": evaluations, "unchanged_front_limit": None},
        "implementations": [{"name": "numeric-search", "version": numeric["release"], "sha256": numeric["image_sha256"]}],
        "seed": "0" * 64}
