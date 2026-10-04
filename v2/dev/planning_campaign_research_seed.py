"""Research-owned synthetic fixtures only; no registration or scientific claim."""

import json
import os
import sys
from importlib.metadata import version
from pathlib import Path

from amphora_contracts_research import (
    CandidateRevision,
    EvidenceAssessmentProfile,
    EvidenceAssessmentRequest,
    EvidenceNeed,
    ExperimentDefinition,
    MissingMeasurement,
    ObservationRevision,
    ResearchQuestion,
)
from amphora_research.assessment.boundary import ConfiguredAssessment
from amphora_research.assessment.resolution import ResolvedAssessment
from amphora_research.assessment.store import AssessmentStore
from amphora_research.experiments.store import ExperimentStore
from amphora_research.material_state.store import MaterialStateStore
from amphora_research.observations.store import ObservationStore
from amphora_research.persistence.ledger import IdentityLedger
from amphora_research.transport.assessments import AssessmentOperations
from sqlalchemy import create_engine


def wire(model, value):
    return model.model_validate_json(json.dumps(value))


def run(stage, path):
    assert version("amphora-research") == "0.34.0"
    data = json.loads(path.read_bytes())
    question = wire(ResearchQuestion, data["records"]["question"])
    need = wire(EvidenceNeed, data["records"]["need"])
    experiment = wire(ExperimentDefinition, data["views"]["experiment"])
    first = wire(ObservationRevision, data["views"]["observation"])
    series = wire(ObservationRevision, data["views"]["series"])
    # The shape fixture uses the same observation id for scalar/series examples.
    series = series.model_copy(update={"reference": series.reference.model_copy(update={"observation_id": "series"})})
    scope = question.reference.scope
    engine = create_engine(os.environ["CAMPAIGN_RESEARCH_DB"], connect_args={"options": "-c statement_timeout=5000"})
    try:
        ledger = IdentityLedger(engine)
        observations = ObservationStore(engine)
        if stage == "advance":
            question = question.model_copy(update={"reference": question.reference.model_copy(update={"revision": 2}),
                "supersedes": question.reference, "objective": "Revised criterion focus for a future campaign"})
            ledger.publish(scope, question)
            first = first.model_copy(update={"reference": first.reference.model_copy(update={"revision": 2}),
                "supersedes": first.reference, "value": MissingMeasurement(kind="missing", reason="report_corrected")})
            observations.publish(scope, "fixture", first)
            return {"question": question.model_dump(mode="json"), "observation": first.model_dump(mode="json"), "pid": os.getpid()}
        assert stage == "prepare"
        ledger.publish(scope, question)
        ledger.publish(scope, need)
        for sample in experiment.samples:
            ledger.publish(scope, CandidateRevision(wire_version="1", reference=sample.sample.candidate,
                representation=sample.sample.identity_evidence, supersedes=None))
            if sample.state is not None:
                MaterialStateStore(engine).publish(scope, "fixture", sample.state)
            ledger.publish(scope, sample.sample)
        ExperimentStore(engine).publish(scope, "fixture", experiment)
        observations.publish(scope, "fixture", first)
        observations.publish(scope, "fixture", series)
        profile = wire(EvidenceAssessmentProfile, {"wire_version": "1", "profile_id": "campaign-read", "version": "1",
            "authority": "synthetic", "purpose": "campaign-read", "question": question.model_dump(mode="json"),
            "subject": question.applicability.model_dump(mode="json"),
            "targets": [{"criterion_id": item.criterion_id, "target_sha256": "c" * 64} for item in question.criteria],
            "answer_publishers": ["fixture"], "requirements": [{"need": need.model_dump(mode="json"),
                "categories": ["observation"], "issuers": ["fixture"]}]})
        configured = ConfiguredAssessment.from_wire(profile)
        request = EvidenceAssessmentRequest(wire_version="1", assessment_id="completed", profile=configured.reference,
            question=question.reference, answers=(), receipts=())
        bound = configured.bind(request, "fixture", scope)
        inputs = tuple({question.applicability, need.required_context})
        resolved = ResolvedAssessment(bound.evaluate((), ()), inputs)
        store = AssessmentStore(engine)
        store.begin(bound)
        complete = AssessmentOperations._status(store.complete(bound, resolved))
        pending = configured.bind(request.model_copy(update={"assessment_id": "pending"}), "fixture", scope)
        store.begin(pending)
        return {"pid": os.getpid(), "authority": "synthetic_owner_local_read_fixture_only",
            "question": question.model_dump(mode="json"), "need": need.model_dump(mode="json"),
            "profile": profile.model_dump(mode="json"), "completed": complete.model_dump(mode="json"),
            "pending": pending.request.model_dump(mode="json"), "experiment": experiment.reference.model_dump(mode="json"),
            "observation": first.reference.model_dump(mode="json"), "series": series.reference.model_dump(mode="json")}
    finally:
        engine.dispose()


if __name__ == "__main__":
    try:
        print(json.dumps(run(sys.argv[1], Path(sys.argv[2]))))
    except Exception as error:
        raise SystemExit("Campaign Research fixture failed: " + type(error).__name__) from None
