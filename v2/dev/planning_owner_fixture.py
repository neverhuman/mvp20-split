"""Actual published v2 extraction inputs for combined owner acceptance."""

import copy
import hashlib
import json

from amphora_contracts_artifacts import ContentDescriptor
from amphora_contracts_core import Scope
from amphora_contracts_planning import extraction_edit_schema
from amphora_tool_protocol import ArtifactClient, HttpTransport, WorkerIdentity

from planning_publication_fixture import PLANNING, populate

VOCABULARY = {"wire_version": "1", "vocabulary_id": "fixture", "version": "1", "entity_types": ["fixture"],
    "predicates": [{"predicate_id": "correlates_with", "description": "Synthetic association",
                    "subject_types": ["fixture"], "object_types": ["fixture"]}]}
POLICY = {"policy_id": "synthetic-structural", "version": "1", "authority": "structural_only",
    "max_entities": 4096, "max_assertions": 8192, "max_aliases": 4096, "max_retractions": 8192}


def result_profiles(output, config):
    for relative, identifier in (("repair/feedback-publication-v1.schema.json", "planning.repair-feedback-publication-content"),
            ("result_publication/candidate-answer-v1.schema.json", "planning.candidate-answer-content")):
        schema = (PLANNING / "src/amphora_agent_planning" / relative).read_bytes()
        path = output / relative.split("/")[-1]
        path.write_bytes(schema)
        config["profiles"].append({"media_type": "application/json", "schema_id": identifier,
            "version": "1", "sha256": hashlib.sha256(schema).hexdigest(), "schema_path": path.name})


def fixture(host, output, scope, profile):
    path, rights, source, _ = populate(host, output, scope, profile)
    raw = json.loads(path.read_bytes())
    client = ArtifactClient(HttpTransport(host.endpoint, host.token), WorkerIdentity("fixture", Scope.model_validate(scope)))

    def publish(key, body):
        descriptor = ContentDescriptor.model_validate_json(json.dumps({"sha256": hashlib.sha256(body).hexdigest(),
            "size_bytes": len(body), "media_type": "text/plain",
            "schema_ref": {key: profile[key] for key in ("schema_id", "version", "sha256")}}))
        upload = client.begin(descriptor, "combined-" + key)
        client.stream(upload, body)
        return client.finalize(upload, "combined-final-" + key).artifact.model_dump(mode="json")

    context = raw["request"]["context"]
    context["prompt"] = publish("prompt-v2", (PLANNING /
        "src/amphora_agent_planning/extraction/prompts/domain-decomposition-v2.txt").read_bytes())
    context["output_schema"] = extraction_edit_schema().model_dump(mode="json")
    applicability = publish("applicability", b"Synthetic association; no scientific adequacy claim")
    context["entries"].append({"artifact": applicability, "role": "constraint", "required": True})
    raw["task"].update(schema_version="2", existing_assertions=[])
    raw["task"]["target"]["applicability"] = applicability
    draft = raw["draft"]
    draft.update(schema_version="2", edits=[])
    draft["entities"][0]["context"] = applicability
    second = copy.deepcopy(draft["entities"][0])
    second.update(local_id="b", label="β")
    draft["entities"].append(second)
    attribution = copy.deepcopy(second["attribution"])
    draft["assertions"] = [{"local_id": key, "subject": "a", "predicate": "correlates_with", "object": "b",
        "statement": "Synthetic contradictory association", "polarity": polarity, "posture": "hypothesis",
        "applicability": applicability, "attribution": copy.deepcopy(attribution)}
        for key, polarity in (("affirmed", "affirmed"), ("negated", "negated"))]
    method = {"schema_id": "fixture.assay", "version": "1", "sha256": "c" * 64}
    draft["questions"] = [{"local_id": "q", "objective": "Does A correlate with B?", "applicability": applicability,
        "criteria": [{"criterion_id": "association", "description": "Explore uncertain association"}], "attribution": attribution}]
    draft["answers"] = [{"local_id": "a", "question_local_id": "q", "question": None,
        "answer": "Uncertain synthetic association", "validation_method": method, "context": applicability, "attribution": attribution}]
    draft["evidence_needs"] = [{"local_id": "n", "question_local_id": "q", "question": None,
        "criterion_ids": ["association"], "method": method, "required_context": applicability, "attribution": attribution}]
    path.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path, rights, source
