import copy

from amphora_agent_planning.publication.candidate import PublishedCandidate
from amphora_agent_planning.research_proposals import QuestionContext, ResearchProposalValidator
from amphora_contracts_research import ResearchQuestion

from ..proposals.support import Case, encode


class ResearchCase(Case):
    def __init__(self):
        super().__init__()
        self.method = {'schema_id': 'fixture.assay', 'version': '1', 'sha256': 'c' * 64}
        self.draft.update(entities=[], assertions=[], edits=[], action='request_evidence')
        self.request['context']['allowed_actions'].append('request_evidence')
        self.draft['questions'] = [{'local_id': 'q', 'objective': 'Does A correlate with B?',
            'applicability': self.context, 'criteria': [{'criterion_id': 'association', 'description': 'Observed association'}],
            'attribution': copy.deepcopy(self.attribution)}]
        self.draft['answers'] = [{'local_id': 'a', 'question_local_id': 'q', 'question': None,
            'answer': 'A does not cause B.', 'validation_method': self.method, 'context': self.context,
            'attribution': copy.deepcopy(self.attribution)}]
        self.draft['evidence_needs'] = [{'local_id': 'n', 'question_local_id': 'q', 'question': None,
            'criterion_ids': ['association'], 'method': self.method, 'required_context': self.context,
            'attribution': copy.deepcopy(self.attribution)}]
        self.known = []

    def known_question(self):
        record = ResearchQuestion.model_validate_json(encode({'wire_version': '1',
            'reference': {'scope': self.scope.model_dump(mode='json'), 'question_id': 'known', 'revision': 1},
            'objective': 'Existing selected question', 'applicability': self.context,
            'criteria': [{'criterion_id': 'association', 'description': 'Declared criterion'}], 'supersedes': None}))
        self.task['known_questions'].append(record.reference.model_dump(mode='json'))
        self.known.append(record)
        return record

    def bindings(self):
        bound = self.bind()
        candidate = PublishedCandidate.from_publication(bound.task, bound.observation, bound.review, bound.publication)
        return candidate, QuestionContext.bind(bound.task, tuple(self.known))

    def validate(self):
        return ResearchProposalValidator().validate(*self.bindings()).document()
