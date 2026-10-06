import json
from hashlib import sha256
from pathlib import Path

import pytest
from amphora_contracts_search import SearchCheckpoint, SearchSpec
from amphora_evolution_search import OriginalSearch


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


@pytest.fixture
def checkpoint_data():
    spec = json.loads((Path(__file__).parents[1] / "specification/synthetic_specification.json").read_text())
    # .NET independently calculated the first zero-seed draw.
    gene = 5377210515782559 / 9007199254740992
    candidate_id = digest(["numeric-attempt-v1", digest(spec), 0, 0, "seed", [gene.hex()], [], 0, 1])
    candidate = {"candidate_id": candidate_id, "generation": 0, "ordinal": 0, "operator": "seed",
                     "genes": [gene], "parents": [], "draws": {"start": 0, "end": 1}, "disposition": "proposed",
                     "reason_code": None, "duplicate_of": None}
    request = {"schema_version": "1", "scope": spec["scope"], "evaluation_id": "ev-" + candidate_id,
                   "specification_sha256": digest(spec), "candidate": candidate,
                   "objectives": spec["objectives"], "evaluator": spec["evaluator"]}
    return {"schema_version": "1", "specification": spec, "specification_sha256": digest(spec), "previous": None,
                "generation": 0, "phase": "awaiting_evaluations", "rng": {"algorithm": "sha256-counter-u53-v1", "seed": spec["seed"], "counter": 1},
                "attempts": [candidate], "population": [], "pending": [{"evaluation_id": request["evaluation_id"],
                "candidate_id": candidate_id, "request_sha256": digest(request)}], "observations": [], "selection": None,
                "progress": {"evaluations_issued": 1, "evaluations_terminal": 0, "generations_completed": 0,
                              "unchanged_front_generations": 0}, "stop_reason": None}


@pytest.fixture
def original_search(checkpoint_data):
    return OriginalSearch(SearchSpec.model_validate_json(json.dumps(checkpoint_data["specification"])))


@pytest.fixture
def decode_record():
    return lambda data: SearchCheckpoint.model_validate_json(json.dumps(data))


@pytest.fixture
def evaluated_data(checkpoint_data):
    pending = checkpoint_data["pending"].pop()
    spec = checkpoint_data["specification"]
    observation = dict(schema_version="1", scope=spec["scope"], **pending,
                       outcome={"status": "evaluated", "evaluator": spec["evaluator"]["tool"],
                                    "objectives": [{"objective_id": "cost", "unit": "dimensionless", "value": 2.0}],
                                    "constraint_violation": 0.0, "constraints_sha256": spec["evaluator"]["constraints"]["sha256"],
                                    "quality": "synthetic", "evidence": [spec["evaluator"]["constraints"]]})
    checkpoint_data["observations"] = [observation]
    checkpoint_data["progress"]["evaluations_terminal"] = 1
    checkpoint_data["phase"] = "ready_to_select"
    return checkpoint_data


@pytest.fixture
def selected_data(evaluated_data):
    candidate_id = evaluated_data["attempts"][0]["candidate_id"]
    evaluated_data["phase"] = "selected"
    evaluated_data["population"] = [candidate_id]
    evaluated_data["selection"] = {"policy": "constrained-pareto-feasible-v1", "membership_sha256": digest([candidate_id]),
                                       "requested": 1, "selected": [candidate_id],
                                       "ranks": [{"candidate_id": candidate_id, "front": 0, "boundary": False, "distance": 0.0, "feasible": True}],
                                       "disposition": "selected"}
    return evaluated_data
