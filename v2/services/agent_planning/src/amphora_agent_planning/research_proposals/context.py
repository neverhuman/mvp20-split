"""Immutable selected question bodies; public reads must establish their origin."""

from dataclasses import dataclass

from amphora_contracts_research import ResearchQuestion

from ..context.policy import require
from ..extraction import ExtractionSnapshot
from ..proposals.context import canonical


@dataclass(frozen=True)
class QuestionContext:
    task_sha256: str
    records: tuple[bytes, ...]

    @classmethod
    def bind(cls, task, records):
        task = ExtractionSnapshot.from_bytes(task.canonical, task.request)
        require(type(records) is tuple and len(records) <= 64, 'research_question_context_limit')
        selected, seen, documents = task.document().known_questions, set(), []
        for supplied in records:
            record = ResearchQuestion.model_validate_json(supplied.model_dump_json(warnings=False))
            require(record.reference in selected, 'research_question_not_selected')
            require(record.reference not in seen, 'research_question_duplicate')
            require(record.applicability.scope == record.reference.scope, 'research_question_context_scope')
            criteria = [criterion.criterion_id for criterion in record.criteria]
            require(len(set(criteria)) == len(criteria), 'research_question_criteria_duplicate')
            previous = record.supersedes
            require((previous is None and record.reference.revision == 1) or
                    (previous is not None and previous.scope == record.reference.scope and
                     previous.question_id == record.reference.question_id and previous.revision + 1 == record.reference.revision),
                    'research_question_predecessor')
            seen.add(record.reference)
            documents.append(canonical(record))
        require(sum(map(len, documents)) <= 4194304, 'research_question_context_limit')
        return cls(task.sha256, tuple(documents))

    def documents(self):
        return tuple(ResearchQuestion.model_validate_json(raw) for raw in self.records)

    def index(self):
        return {record.reference: record for record in self.documents()}
