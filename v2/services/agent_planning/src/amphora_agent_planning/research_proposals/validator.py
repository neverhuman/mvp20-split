"""Distinct attributed proposals with local dependency resolution and no writes."""

import hashlib
from collections import Counter
from dataclasses import dataclass

from amphora_contracts_planning import AnswerProposal, NeedProposal, QuestionProposal, ResearchProposalSet
from amphora_contracts_research import EvidenceNeed, EvidenceNeedRef, ResearchQuestion, ResearchQuestionRef

from ..context.policy import require
from ..proposals.context import canonical
from ..proposals.result import Findings
from .context import QuestionContext


@dataclass(frozen=True)
class ResearchProposals:
    canonical: bytes

    def document(self):
        return ResearchProposalSet.model_validate_json(self.canonical)


class ResearchProposalValidator:
    def validate(self, candidate, questions):
        require(questions.task_sha256 == candidate.task.sha256, 'research_context_task_binding')
        questions = QuestionContext.bind(candidate.task, questions.documents(), questions.unavailable())
        return _Validation(candidate, questions).run()


class _Validation:
    def __init__(self, candidate, questions):
        self.candidate, self.task, self.draft = candidate, candidate.task.document(), candidate.draft()
        self.known = questions.index()
        self.selected = tuple(entry.artifact for entry in candidate.task.request.document().context.entries)
        self.findings = Findings()
        for finding in questions.findings(candidate.task):
            self.findings.add(finding.location, finding.code, withhold=False)
        self.questions, self.answers, self.needs, self.local_questions = [], [], [], {}

    def identity(self, kind, local_id):
        return 'p-' + hashlib.sha256(f'{self.candidate.task.sha256}:{kind}:{local_id}'.encode()).hexdigest()

    def context(self, reference):
        require(reference is not None, 'required_context_missing')
        require(reference in self.selected, 'context_not_selected')
        return reference

    def attributed(self, item, path):
        return dict(local_id=item.local_id, source_path=path, model_attribution=item.attribution,
                    grounding=self.candidate.grounding((item.attribution,)))

    def question(self, item, path):
        attribution = self.attributed(item, path)
        require(bool(item.objective.strip()), 'empty_question_objective')
        criteria = [criterion.criterion_id for criterion in item.criteria]
        require(len(set(criteria)) == len(criteria), 'duplicate_question_criterion')
        identifier = self.identity('question', item.local_id)
        require(not any(ref.question_id == identifier for ref in self.task.known_questions), 'proposed_question_exists')
        record = ResearchQuestion(wire_version='1', reference=ResearchQuestionRef(scope=self.task.scope,
            question_id=identifier, revision=1), objective=item.objective, applicability=self.context(item.applicability),
            criteria=item.criteria, supersedes=None)
        self.local_questions[item.local_id] = record
        return QuestionProposal(**attribution, question=record)

    def target(self, item):
        require((item.question_local_id is None) != (item.question is None), 'question_target_ambiguous')
        if item.question_local_id is not None:
            require(item.question_local_id in self.local_questions, 'question_candidate_unresolved')
            return self.local_questions[item.question_local_id]
        require(item.question in self.task.known_questions, 'question_reference_not_selected')
        require(item.question in self.known, 'question_reference_unavailable')
        return self.known[item.question]

    def answer(self, item, path):
        attribution = self.attributed(item, path)
        require(bool(item.answer.strip()), 'empty_answer_text')
        target = self.target(item)
        require(item.validation_method is not None, 'answer_method_missing')
        return AnswerProposal(**attribution, question=target.reference, answer=item.answer,
                              validation_method=item.validation_method, context=self.context(item.context))

    def need(self, item, path):
        attribution = self.attributed(item, path)
        target = self.target(item)
        criteria = item.criterion_ids
        require(len(set(criteria)) == len(criteria), 'duplicate_need_criterion')
        require(set(criteria) <= {criterion.criterion_id for criterion in target.criteria}, 'unknown_need_criterion')
        require(item.method is not None, 'need_method_missing')
        identifier = self.identity('need', item.local_id)
        require(not any(ref.need_id == identifier for ref in self.task.known_needs), 'proposed_need_exists')
        record = EvidenceNeed(wire_version='1', reference=EvidenceNeedRef(scope=self.task.scope, need_id=identifier, revision=1),
            question=target.reference, criterion_ids=criteria, method=item.method,
            required_context=self.context(item.required_context), supersedes=None)
        return NeedProposal(**attribution, need=record)

    def group(self, name, output, build):
        items = getattr(self.draft, name)
        counts = Counter(item.local_id for item in items)
        for index, item in enumerate(items):
            path = f'/{name}/{index}'
            if counts[item.local_id] > 1:
                self.findings.add(path, 'duplicate_candidate_identity')
                continue
            result = self.findings.check(path, lambda item=item, path=path: build(item, path))
            if result is not None:
                output.append(result)

    def document(self):
        any_proposal = bool(self.questions or self.answers or self.needs)
        outcome = 'abstained' if self.draft.action == 'abstain' else (
            'partial' if any_proposal and self.findings.withheld else 'proposed' if any_proposal else 'unresolved')
        return ResearchProposalSet(wire_version='1', authority='proposal_only', validation='quotation_and_structure_only',
            task_sha256=self.candidate.task.sha256, candidate_sha256=hashlib.sha256(self.candidate.candidate_bytes).hexdigest(),
            interpretation=self.candidate.interpretation(), outcome=outcome, questions=tuple(self.questions),
            answers=tuple(self.answers), evidence_needs=tuple(self.needs), findings=tuple(self.findings.records),
            withheld=tuple(sorted(self.findings.withheld)))

    def run(self):
        for diagnostic in self.draft.diagnostics:
            self.findings.add(diagnostic.target_path, 'model_reported_' + diagnostic.kind, withhold=False)
        if self.draft.action != 'abstain':
            self.group('questions', self.questions, self.question)
            self.group('answers', self.answers, self.answer)
            self.group('evidence_needs', self.needs, self.need)
        raw = canonical(self.document())
        if len(raw) > 262144:
            for item in (*self.questions, *self.answers, *self.needs):
                self.findings.add(item.source_path, 'research_proposal_size')
            self.questions.clear()
            self.answers.clear()
            self.needs.clear()
            raw = canonical(self.document())
        require(len(raw) <= 262144, 'research_findings_size')
        return ResearchProposals(raw)
