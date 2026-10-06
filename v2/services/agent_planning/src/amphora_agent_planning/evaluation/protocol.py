"""Immutable pre-result protocol identity, bounded input and independent label checks."""

import hashlib
import json
import re
from dataclasses import dataclass

from .records import CorpusRecord, ManifestRecord


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False).encode()


def document(raw, *, limit):
    if len(raw.encode('utf-8') if isinstance(raw, str) else raw) > limit:
        raise ValueError('evaluation_document_limit')

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('evaluation_duplicate_key')
            result[key] = value
        return result

    def invalid(_value):
        raise ValueError('evaluation_nonfinite_number')

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
        # Also rejects exponent overflow; caps nesting before any recursive scorer work.
        pending = [(value, 0)]
        while pending:
            item, depth = pending.pop()
            if depth > 32:
                raise ValueError('evaluation_document_depth')
            if isinstance(item, dict):
                pending.extend((child, depth + 1) for child in item.values())
            elif isinstance(item, list):
                pending.extend((child, depth + 1) for child in item)
        canonical(value)
        return value
    except (RecursionError, UnicodeError) as error:
        raise ValueError('evaluation_document_invalid') from error


def pointer_parts(pointer):
    if not pointer:
        return ()
    if not pointer.startswith('/') or re.search(r'~(?![01])', pointer):
        raise ValueError('evaluation_pointer_invalid')
    parts = tuple(part.replace('~1', '/').replace('~0', '~') for part in pointer[1:].split('/'))
    if len(parts) > 32:
        raise ValueError('evaluation_pointer_depth')
    return parts


@dataclass(frozen=True)
class EvaluationProtocol:
    manifest: ManifestRecord
    corpus: CorpusRecord
    sha256: str

    @classmethod
    def load(cls, manifest_bytes, corpus_bytes):
        manifest = ManifestRecord.model_validate_json(canonical(document(manifest_bytes, limit=1048576)))
        corpus = CorpusRecord.model_validate_json(canonical(document(corpus_bytes, limit=4194304)))
        if hashlib.sha256(corpus_bytes).hexdigest() != manifest.corpus_sha256:
            raise ValueError('evaluation_corpus_digest')
        cases = corpus.cases
        categories = {item.category for item in manifest.categories}
        if len(categories) != len(manifest.categories) or categories != {case.category for case in cases}:
            raise ValueError('evaluation_categories')
        if len({case.case_id for case in cases}) != len(cases):
            raise ValueError('evaluation_duplicate_case')
        data = [canonical(item.model_dump(mode='json')) for item in manifest.allowed_data]
        if len(set(data)) != len(data):
            raise ValueError('evaluation_duplicate_data')
        for case in cases:
            if len({item.assertion_id for item in case.assertions}) != len(case.assertions):
                raise ValueError('evaluation_duplicate_assertion')
            for assertion in case.assertions:
                pointer_parts(assertion.pointer)
                document(assertion.expected_json, limit=8192)
        identity = canonical(manifest.model_dump(mode='json'))
        return cls(manifest, corpus, hashlib.sha256(identity).hexdigest())

    @property
    def planned_observations(self):
        return len(self.corpus.cases) * self.manifest.repetitions

    def model_inputs(self):
        """Only input identities may reach the runner; expected labels remain evaluator-owned."""
        return tuple((case.case_id, case.input_sha256) for case in self.corpus.cases)
