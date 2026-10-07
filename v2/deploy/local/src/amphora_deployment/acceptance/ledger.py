"""Read-only verification of a reviewed, versioned evidence set."""

import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path

from .policy import ASSERTIONS, GATES, LIMITATIONS, PROFILE

MAX_DOCUMENT = 8 * 1024 * 1024


class EvidenceError(ValueError):
    """Fixed rejection reason; never includes input paths or document payloads."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("duplicate_key")
        result[key] = value
    return result


def _constant(_value):
    raise EvidenceError("nonfinite_json")


def _float(value):
    result = float(value)
    if not math.isfinite(result):
        raise EvidenceError("nonfinite_json")
    return result


def _decode(raw):
    if len(raw) > MAX_DOCUMENT:
        raise EvidenceError("document_too_large")
    try:
        value = json.loads(raw, object_pairs_hook=_object, parse_constant=_constant, parse_float=_float)
    except EvidenceError:
        raise
    except (UnicodeError, ValueError, RecursionError):
        raise EvidenceError("invalid_json") from None
    if not isinstance(value, dict):
        raise EvidenceError("object_required")
    return value


def _read(path):
    try:
        if path.is_symlink() or path.is_junction():
            raise EvidenceError("linked_evidence")
        with path.open('rb') as stream:
            return stream.read(MAX_DOCUMENT + 1)
    except OSError:
        raise EvidenceError("evidence_unavailable") from None


@dataclass(frozen=True)
class EvidencePin:
    gate: str
    sha256: str

    def verify(self, directory):
        filename, status = GATES[self.gate]
        raw = _read(directory / filename)
        if hashlib.sha256(raw).hexdigest() != self.sha256:
            raise EvidenceError("evidence_hash_mismatch")
        record = _decode(raw)
        if record.get('status') != status:
            raise EvidenceError("required_gate_failed")
        for path, expected in ASSERTIONS.get(self.gate, ()):
            value = record
            for key in path:
                if not isinstance(value, dict) or key not in value:
                    raise EvidenceError("required_assertion_missing")
                value = value[key]
            if type(value) is not type(expected) or value != expected:
                raise EvidenceError("required_assertion_failed")


@dataclass(frozen=True)
class AcceptanceLedger:
    baseline: str
    host: str
    pins: tuple[EvidencePin, ...]

    @classmethod
    def from_bytes(cls, raw):
        value = _decode(raw)
        if set(value) != {'format', 'profile', 'baseline', 'host', 'evidence', 'limitations'}:
            raise EvidenceError("invalid_ledger_fields")
        if value['format'] != 'deployment-acceptance.v1' or value['profile'] != PROFILE:
            raise EvidenceError("unsupported_ledger")
        baseline, host = value['baseline'], value['host']
        if not isinstance(baseline, str) or not re.fullmatch('[0-9a-f]{40}', baseline):
            raise EvidenceError("invalid_baseline")
        if not isinstance(host, str) or not re.fullmatch('[A-Za-z0-9_.-]{1,128}', host):
            raise EvidenceError("invalid_host")
        evidence = value['evidence']
        if not isinstance(evidence, dict) or set(evidence) != set(GATES):
            raise EvidenceError("required_gate_set_mismatch")
        if value['limitations'] != list(LIMITATIONS):
            raise EvidenceError("required_limitations_mismatch")
        pins = []
        for gate in sorted(GATES):
            digest = evidence[gate]
            if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                raise EvidenceError("invalid_evidence_hash")
            pins.append(EvidencePin(gate, digest))
        return cls(baseline, host, tuple(pins))

    def verify(self, directory: Path):
        if directory.is_symlink() or directory.is_junction():
            raise EvidenceError("linked_evidence")
        results = []
        for pin in self.pins:
            try:
                pin.verify(directory)
                results.append({'gate': pin.gate, 'status': 'verified'})
            except EvidenceError as error:
                results.append({'gate': pin.gate, 'status': 'rejected', 'reason': str(error)})
        return {
            'format': 'deployment-acceptance-report.v1',
            'status': 'verified' if all(row['status'] == 'verified' for row in results) else 'rejected',
            'profile': PROFILE, 'baseline': self.baseline, 'declared_host': self.host,
            'gates': results, 'limitations': list(LIMITATIONS),
            'services_started': False, 'provider_calls': 0,
        }
