"""Public Research identity client; no Research implementation or database access."""

import http.client
import json
import re
from urllib.parse import urlsplit

from amphora_contracts_evidence import PreparedLabRecord
from amphora_contracts_research import (
    CandidateRevisionRef,
    IdentityResolution,
    ResolveIdentity,
    SampleRevisionRef,
)


class ResearchLookupError(ValueError):
    """Safe code; an unavailable peer must not be recast as an unknown identity."""


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ResearchLookupError("research_protocol_error")
        result[key] = value
    return result


def _constant(_value):
    raise ResearchLookupError("research_protocol_error")


def lab_identity_query(prepared) -> ResolveIdentity | None:
    """Malformed/missing identifiers stay unresolved without making a peer request."""
    if prepared.converter_id != "synthetic-lab-json":
        raise ResearchLookupError("lab_profile_required")
    record = PreparedLabRecord.model_validate_json(prepared.content)
    for value in (record.candidate_id, record.sample_id):
        if value is None or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", value):
            return None
    for value in (record.candidate_revision, record.sample_revision):
        if value is None or not re.fullmatch(r"[1-9][0-9]{0,15}", value) or int(value) > 9007199254740991:
            return None
    scope = prepared.source.reference.scope
    return ResolveIdentity(wire_version="1", scope=scope,
        candidate=CandidateRevisionRef(scope=scope, candidate_id=record.candidate_id, revision=int(record.candidate_revision)),
        sample=SampleRevisionRef(scope=scope, sample_id=record.sample_id, revision=int(record.sample_revision)))


class ResearchClient:
    def __init__(self, endpoint: str, token: str, timeout: float = 5):
        parsed = urlsplit(endpoint)
        if (parsed.scheme != "http" or parsed.hostname != "127.0.0.1" or parsed.username is not None
                or parsed.password is not None or parsed.path not in ("", "/") or parsed.query or parsed.fragment
                or parsed.port is None or not 1 <= parsed.port <= 65535):
            raise ValueError("explicit_loopback_research_endpoint_required")
        if not isinstance(token, str) or not 32 <= len(token) <= 512 or any(not 33 <= ord(char) <= 126 for char in token):
            raise ValueError("invalid_research_credential")
        if type(timeout) not in (int, float) or not 0 < timeout <= 30:
            raise ValueError("invalid_research_timeout")
        self._host, self._port, self._token, self._timeout = parsed.hostname, parsed.port, token, timeout

    def resolve(self, query: ResolveIdentity) -> IdentityResolution:
        if query.scope != query.candidate.scope or query.scope != query.sample.scope:
            raise ResearchLookupError("request_scope_mismatch")
        connection = http.client.HTTPConnection(self._host, self._port, timeout=self._timeout)
        try:
            connection.request("POST", "/v1/identities/resolve", body=query.model_dump_json().encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": "Bearer " + self._token})
            response = connection.getresponse()
            if response.status in (401, 403):
                raise ResearchLookupError("research_access_denied")
            if response.status != 200:
                raise ResearchLookupError("research_unavailable")
            if response.getheader("Content-Type", "").split(";", 1)[0].strip().lower() != "application/json":
                raise ResearchLookupError("research_protocol_error")
            raw = response.read(16385)
            if len(raw) > 16384:
                raise ResearchLookupError("research_response_limit")
        except (OSError, http.client.HTTPException) as error:
            raise ResearchLookupError("research_unavailable") from error
        finally:
            connection.close()
        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique, parse_constant=_constant)
            result = IdentityResolution.model_validate_json(json.dumps(value))
        except (ValueError, RecursionError) as error:
            raise ResearchLookupError("research_protocol_error") from error
        if (result.scope != query.scope or result.candidate != query.candidate or result.sample != query.sample
                or (result.disposition == "matched") != (result.reason == "exact_identity_only")):
            raise ResearchLookupError("research_binding_mismatch")
        return result
