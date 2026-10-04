"""Test-owned semantic review accounting; no automatic entailment or acceptance."""

import hashlib
import json
from dataclasses import dataclass


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


@dataclass(frozen=True)
class CorpusCase:
    case_id: str
    category: str
    split: str
    source: bytes
    oracle: bytes

    @classmethod
    def load(cls, root, row):
        source, oracle = ((root / row[key]).read_bytes() for key in ("source", "oracle"))
        if digest(source) != row["source_sha256"] or digest(oracle) != row["oracle_sha256"]:
            raise ValueError("corpus_digest")
        document = json.loads(oracle)
        if document["case_id"] != row["case_id"] or document["category"] != row["category"]:
            raise ValueError("corpus_binding")
        if row["split"] not in {"calibration", "held_out"}:
            raise ValueError("corpus_split")
        return cls(row["case_id"], row["category"], row["split"], source, oracle)

    def expectations(self):
        return json.loads(self.oracle)


@dataclass(frozen=True)
class Score:
    true_positive: int
    false_positive: int
    false_negative: int
    context_present: int
    context_total: int
    abstained: int
    provider_failed: int
    forbidden: int

    def document(self):
        emitted = self.true_positive + self.false_positive
        expected = self.true_positive + self.false_negative
        return {**vars(self), "precision": None if emitted == 0 else self.true_positive / emitted,
            "recall": None if expected == 0 else self.true_positive / expected}

    @classmethod
    def combine(cls, scores):
        return cls(*(sum(getattr(score, name) for score in scores) for name in cls.__dataclass_fields__))


@dataclass(frozen=True)
class ReviewedResponse:
    response_id: str
    case: CorpusCase
    output: bytes
    review: bytes

    @classmethod
    def bind(cls, case, record):
        if set(record) != {"response_id", "case_id", "source_sha256", "oracle_sha256", "output", "output_sha256", "review"}:
            raise ValueError("review_shape")
        output = canonical(record["output"])
        if record["case_id"] != case.case_id or record["source_sha256"] != digest(case.source) or record["oracle_sha256"] != digest(case.oracle):
            raise ValueError("review_case_binding")
        if record["output_sha256"] != digest(output):
            raise ValueError("review_output_binding")
        if type(record["response_id"]) is not str or not record["response_id"]:
            raise ValueError("review_identity")
        review = record["review"]
        if set(review) != {"claims", "context_present", "forbidden", "disposition", "reviewer", "note"}:
            raise ValueError("review_shape")
        if review["reviewer"] != "coding_agent_synthetic_review" or not review["note"]:
            raise ValueError("review_authority")
        expected = case.expectations()
        claims = review["claims"]
        if type(claims) is not list or len(claims) > 128:
            raise ValueError("review_claim_limit")
        seen = set()
        for claim in claims:
            if set(claim) != {"path", "meaning"} or claim["path"] in seen:
                raise ValueError("review_claim_identity")
            seen.add(claim["path"])
            cls._locate(record["output"], claim["path"])
            match = claim["meaning"]
            if match is not None and (type(match) is not int or not 0 <= match < len(expected["expected_meaning"])):
                raise ValueError("review_unknown_meaning")
        expected_paths = {f"/{group}/{index}" for group in ("assertions", "questions", "answers", "evidence_needs", "diagnostics", "edits")
            for index, _ in enumerate(record["output"].get(group, []))}
        if seen != expected_paths:
            raise ValueError("review_incomplete_output")
        for field, size in (("context_present", len(expected["context_to_preserve"])), ("forbidden", len(expected["hard_rejections"]))):
            indices = review[field]
            if type(indices) is not list or any(type(index) is not int or not 0 <= index < size for index in indices) or len(set(indices)) != len(indices):
                raise ValueError("review_index")
        if review["disposition"] not in {"proposed", "abstained", "provider_failed"}:
            raise ValueError("review_disposition")
        if review["disposition"] != "proposed" and (claims or review["context_present"] or review["forbidden"]):
            raise ValueError("review_empty_disposition")
        if review["disposition"] == "abstained" and record["output"].get("action") != "abstain":
            raise ValueError("review_abstention_binding")
        return cls(record["response_id"], case, output, canonical(review))

    @staticmethod
    def _locate(output, path):
        if type(path) is not str or not path.startswith("/") or len(path) > 256:
            raise ValueError("review_output_path")
        value = output
        try:
            for part in path[1:].split("/"):
                if isinstance(value, list):
                    if not part.isdigit():
                        raise ValueError("review_output_path")
                    value = value[int(part)]
                else:
                    value = value[part]
        except (KeyError, IndexError, TypeError):
            raise ValueError("review_output_path") from None
        return value

    def score(self):
        review = json.loads(self.review)
        meanings = {claim["meaning"] for claim in review["claims"] if claim["meaning"] is not None}
        expected = self.case.expectations()
        return Score(len(meanings), len(review["claims"]) - len(meanings), len(expected["expected_meaning"]) - len(meanings),
            len(review["context_present"]), len(expected["context_to_preserve"]),
            int(review["disposition"] == "abstained"), int(review["disposition"] == "provider_failed"), len(review["forbidden"]))


def report(cases, responses):
    if not cases or not responses:
        raise ValueError("evaluation_empty")
    if len({case.case_id for case in cases}) != len(cases) or len({row.response_id for row in responses}) != len(responses):
        raise ValueError("evaluation_duplicate_identity")
    known = {case.case_id: case for case in cases}
    if any(known.get(row.case.case_id) != row.case for row in responses):
        raise ValueError("evaluation_case_binding")
    if {row.case.case_id for row in responses} != set(known):
        raise ValueError("evaluation_missing_review")
    groups = {}
    for split, category in sorted({(case.split, case.category) for case in cases}):
        rows = [row for row in responses if (row.case.split, row.case.category) == (split, category)]
        score = Score.combine([row.score() for row in rows])
        groups[split + "/" + category] = {"responses": len(rows), "cases": len({row.case.case_id for row in rows}), **score.document()}
    return {"authority": "reviewed_synthetic_fixture_only", "responses": len(responses), "cases": len(cases), "groups": groups}
