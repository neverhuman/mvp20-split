"""Own representation parser and source-byte-bound receipt; no external authority."""
import hashlib
import json

from amphora_contracts_candidate_spaces import SequenceDesign
from amphora_contracts_candidate_canonicalization import CanonicalCandidate

from .equivalence import SequenceCanonical
from .profile import canonical


def unique(pairs):
    result = {}
    for name,value in pairs:
        if name in result:
            raise ValueError("duplicate_design_key")
        result[name] = value
    return result


def canonicalize(payload):
    if type(payload) is not bytes or len(payload) > 262144:
        raise ValueError("invalid_canonicalization_payload")
    def invalid(_):
        raise ValueError("nonfinite_design_value")
    value = json.loads(payload.decode("utf-8"),object_pairs_hook=unique,parse_constant=invalid)
    record = SequenceDesign.model_validate_json(json.dumps(value,allow_nan=False))
    normalized = SequenceCanonical(record)
    receipt = CanonicalCandidate(wire_version="1",authority="synthetic_encoding",scope=record.scope,kind="sequence",
        semantic_profile=record.profile,equivalence_profile=normalized.policy,
        source_sha256=hashlib.sha256(payload).hexdigest(),canonical_sha256=normalized.sha256)
    return canonical(receipt)
