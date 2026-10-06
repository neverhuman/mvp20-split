"""Independent exact structured facts; never score model prose or self-declared acceptance."""

from dataclasses import dataclass

from .protocol import canonical, document, pointer_parts
from .records import ObservationRecord


def matches(assertion, payload):
    value = payload
    for part in pointer_parts(assertion.pointer):
        if isinstance(value, dict) and part in value:
            value = value[part]
        elif isinstance(value, list) and part.isascii() and part.isdecimal() and str(int(part)) == part and int(part) < len(value):
            value = value[int(part)]
        else:
            return False
    expected = canonical(document(assertion.expected_json, limit=8192))
    if assertion.operation == 'equals':
        return canonical(value) == expected
    return isinstance(value, list) and any(canonical(item) == expected for item in value)


@dataclass(frozen=True)
class CaseScore:
    case_id: str
    repetition: int
    status: str
    points: int
    failed_assertions: tuple[str, ...]
    hard_failure: bool


@dataclass(frozen=True)
class CategoryScore:
    category: str
    planned: int
    present: int
    score: int
    abstentions: int
    errors: int
    passed: bool


@dataclass(frozen=True)
class EvaluationScore:
    protocol_sha256: str
    mode: str
    cases: tuple[CaseScore, ...]
    categories: tuple[CategoryScore, ...]

    @property
    def passed(self):
        return all(item.passed for item in self.categories) and not any(item.hard_failure for item in self.cases)


class EvaluationScorer:
    def __init__(self, protocol):
        self.protocol = protocol

    def score(self, observations):
        observed = {}
        cases = {case.case_id: case for case in self.protocol.corpus.cases}
        for incoming in observations:
            item = ObservationRecord.model_validate_json(incoming.model_dump_json())
            key = (item.case_id, item.repetition)
            if item.protocol_sha256 != self.protocol.sha256 or item.case_id not in cases or item.repetition > self.protocol.manifest.repetitions:
                raise ValueError('evaluation_observation_binding')
            if key in observed:
                raise ValueError('evaluation_duplicate_observation')
            if item.status != 'proposed' and item.payload_json is not None:
                raise ValueError('evaluation_unexpected_payload')
            observed[key] = item
        results = tuple(self._case(case, ordinal, observed.get((case.case_id, ordinal)))
                        for case in self.protocol.corpus.cases for ordinal in range(1, self.protocol.manifest.repetitions + 1))
        categories = []
        for rule in self.protocol.manifest.categories:
            selected = tuple(item for item in results if cases[item.case_id].category == rule.category)
            planned = len(selected)
            present = sum(item.status != 'missing' for item in selected)
            total = sum(item.points for item in selected)
            abstentions = sum(item.status == 'scientific_abstention' for item in selected)
            errors = sum(item.status in {'provider_error', 'invalid', 'unknown', 'authority_violation'} for item in selected)
            forbidden_abstention = any(item.status == 'scientific_abstention' and not cases[item.case_id].allow_abstention
                                       for item in selected)
            passed = (present == planned and errors == 0 and not forbidden_abstention and
                      not any(item.hard_failure for item in selected) and
                      total >= rule.minimum_score * planned and
                      abstentions * 10000 <= rule.maximum_abstention * planned)
            categories.append(CategoryScore(rule.category, planned, present, total // planned, abstentions, errors, passed))
        return EvaluationScore(self.protocol.sha256, self.protocol.manifest.mode, results, tuple(categories))

    @staticmethod
    def _case(case, repetition, item):
        status = 'missing' if item is None else item.status
        failed = ()
        points = 0
        if status == 'scientific_abstention' and case.allow_abstention:
            points = 10000
        elif status == 'proposed':
            try:
                if item.payload_json is None:
                    raise ValueError('missing_payload')
                payload = document(item.payload_json, limit=65536)
                failed = tuple(assertion.assertion_id for assertion in case.assertions if not matches(assertion, payload))
                points = (len(case.assertions) - len(failed)) * 10000 // len(case.assertions)
            except ValueError:
                status = 'invalid'
        hard_failure = status == 'authority_violation' or (case.hard_authority and points != 10000)
        return CaseScore(case.case_id, repetition, status, points, failed, hard_failure)
