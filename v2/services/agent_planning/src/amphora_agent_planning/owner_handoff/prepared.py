"""First validated owner request and bounded historical input witnesses."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_knowledge import GraphAuthoringProfile
from amphora_contracts_planning import NeedProposal, QuestionProposal
from amphora_contracts_research import ResearchQuestion

from ..context.policy import require
from ..context.snapshot import _constant, _object
from ..proposals.inputs import ProposalInputs
from ..proposals.validator import GraphCandidateValidator
from ..publication.candidate import PublishedCandidate
from ..publication.payload import TraceArtifact
from ..publication.records import encode
from ..publication.review_record import ReviewRecord
from ..research_proposals import ResearchProposalValidator
from .request import MODELS, OwnerRequest
from .selection import HandoffSelection


@dataclass(frozen=True)
class PreparedHandoff:
    request: OwnerRequest
    review: ReviewRecord
    witness: bytes
    manifest: bytes

    @classmethod
    def create(cls, principal, selection, history, review, *, questions=None, knowledge=None):
        selection = HandoffSelection.restore(selection.canonical, principal)
        require(history.projection.reference() == selection.trace() and
                history.interpretation.identity.document()["publication_id"] == selection.document()["interpretation_id"],
                "handoff_origin_binding")
        selected = selection.document()
        arguments = (history.task, history.observation, review)
        if selected["kind"] == "graph":
            require(knowledge is not None, "handoff_graph_context_missing")
            inputs = ProposalInputs.from_publication(*arguments, knowledge, history.interpretation)
            record = GraphCandidateValidator().validate(inputs).proposal()
            require(record is not None, "handoff_candidate_unavailable")
            witness = {"proposal": None, "dependency": None, "knowledge": {
                "profile": inputs.knowledge.profile().model_dump(mode="json"),
                "base": history.task.document().target.base.model_dump(mode="json")
                        if history.task.document().target.base is not None else None}}
        else:
            require(questions is not None, "handoff_question_context_missing")
            candidate = PublishedCandidate.from_publication(*arguments, history.interpretation)
            validated = ResearchProposalValidator().validate(candidate, questions).document()
            items = validated.questions if selected["kind"] == "question" else validated.evidence_needs
            matches = [item for item in items if item.local_id == selected["local_id"]]
            require(len(matches) == 1, "handoff_candidate_unavailable")
            proposal = matches[0]
            record = proposal.question if selected["kind"] == "question" else proposal.need
            dependency = None
            if selected["kind"] == "need":
                draft = next(item for item in candidate.draft().evidence_needs if item.local_id == selected["local_id"])
                if draft.question_local_id is not None:
                    question = next(item.question for item in validated.questions if item.local_id == draft.question_local_id)
                else:
                    question = questions.index()[record.question]
                dependency = {"local_id": draft.question_local_id, "question": question.model_dump(mode="json")}
            witness = {"proposal": proposal.model_dump(mode="json"), "dependency": dependency, "knowledge": None}
        request = OwnerRequest.bind(selection, record)
        raw = encode(witness)
        require(len(raw) <= 1048576, "handoff_witness_limit")
        cls._witness(request, history, raw)
        stored_review = ReviewRecord.from_review(review)
        manifest = cls._manifest(selection, history, request, stored_review, raw)
        return cls(request, stored_review, raw, manifest)

    @staticmethod
    def _manifest(selection, history, request, review, witness):
        return encode({"format": "planning-owner-preparation.v1", "selection_sha256": selection.sha256,
            "task_sha256": history.task.sha256, "observation_sha256": history.projection.document().outcome.observation_sha256,
            "interpretation": history.interpretation.attempt.result.artifact.model_dump(mode="json"),
            "request_sha256": request.sha256, "review_sha256": hashlib.sha256(review.canonical).hexdigest(),
            "witness_sha256": hashlib.sha256(witness).hexdigest()})

    @staticmethod
    def _witness(request, history, raw):
        require(type(raw) is bytes and 0 < len(raw) <= 1048576, "handoff_witness_limit")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_object, parse_constant=_constant)
        require(type(value) is dict and set(value) == {"proposal", "dependency", "knowledge"} and
                encode(value) == raw, "handoff_witness_shape")
        selected, task = request.selection.document(), history.task.document()
        if request.kind == "graph":
            context = value["knowledge"]
            require(value["proposal"] is None and value["dependency"] is None and type(context) is dict and
                    set(context) == {"profile", "base"}, "handoff_graph_witness")
            profile = GraphAuthoringProfile.model_validate_json(json.dumps(context["profile"]))
            base = None if task.target.base is None else task.target.base.model_dump(mode="json")
            record = request.document()
            require(context["base"] == base and profile.graph == record.graph == task.target.graph and
                    profile.vocabulary_reference == record.vocabulary == task.target.vocabulary and
                    profile.policy == record.policy == task.target.policy and record.base == task.target.base,
                    "handoff_graph_witness")
        else:
            require(value["knowledge"] is None, "handoff_research_witness")
            model = QuestionProposal if request.kind == "question" else NeedProposal
            proposal = model.model_validate_json(json.dumps(value["proposal"]))
            record = proposal.question if request.kind == "question" else proposal.need
            require(proposal.local_id == selected["local_id"] and
                    encode(record.model_dump(mode="json")) == request.canonical and
                    proposal.grounding.interpretation_artifacts == (history.interpretation.attempt.result.artifact,),
                    "handoff_research_witness")
            if request.kind == "question":
                require(value["dependency"] is None, "handoff_question_dependency")
            else:
                dependency = value["dependency"]
                require(type(dependency) is dict and set(dependency) == {"local_id", "question"}, "handoff_need_dependency")
                question = ResearchQuestion.model_validate_json(json.dumps(dependency["question"]))
                require(question.reference == record.question, "handoff_need_dependency")
                local = dependency["local_id"]
                if local is None:
                    require(question.reference in task.known_questions, "handoff_need_dependency")
                else:
                    local_selection = HandoffSelection._encode(selected["actor_id"], request.selection.trace(),
                        selected["interpretation_id"], "question", local, selected["owner_id"])
                    expected = "p-" + hashlib.sha256(f"{history.task.sha256}:question:{local}".encode()).hexdigest()
                    require(question.reference.question_id == expected and question.reference.revision == 1,
                            "handoff_need_dependency")
                    return local_selection, question
        return None

    def dependency(self, history):
        return self._witness(self.request, history, self.witness)

    @property
    def sha256(self):
        digest = hashlib.sha256(b"planning-owner-preparation.v1")
        for raw in (self.request.canonical, self.review.canonical, self.witness, self.manifest):
            digest.update(len(raw).to_bytes(8, "big"))
            digest.update(raw)
        return digest.hexdigest()

    @classmethod
    def restore(cls, row, principal, selection, history):
        selection = HandoffSelection.restore(selection.canonical, principal)
        body = bytes(row["body_bytes"])
        require(0 < len(body) <= 262144, "handoff_request_limit")
        record = MODELS[selection.document()["kind"]].model_validate_json(body)
        request = OwnerRequest.bind(selection, record)
        require(request.canonical == body, "handoff_request_canonical")
        review = ReviewRecord.from_bytes(bytes(row["review_bytes"]))
        interpreted = TraceArtifact.restore(history.interpretation.identity, history.projection, history.task, review)
        require(interpreted == history.interpretation.payload.artifact, "handoff_review_binding")
        witness = bytes(row["witness_bytes"])
        cls._witness(request, history, witness)
        manifest = bytes(row["manifest_bytes"])
        require(cls._manifest(selection, history, request, review, witness) == manifest, "handoff_manifest_binding")
        result = cls(request, review, witness, manifest)
        require(result.sha256 == row["payload_sha256"], "stored_handoff_payload")
        return result
