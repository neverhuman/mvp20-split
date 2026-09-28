"""Configured, bounded authenticated runtime lookup; never inside a DB transaction."""

from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from amphora_contracts_artifacts import RuntimeOutcome


class OutcomeUnavailable(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RuntimeOutcomes:
    def __init__(self, owner, endpoint, token, *, timeout=5):
        url = urlsplit(endpoint)
        if (url.username or url.password or url.query or url.fragment or not url.hostname
            or (url.scheme != "https" and not (url.scheme == "http" and url.hostname in {"127.0.0.1", "::1"}))
            or len(token) < 32 or not 0 < timeout <= 30):
            raise ValueError("Invalid runtime endpoint configuration")
        self.owner, self.endpoint, self.token, self.timeout = owner, endpoint, token, timeout
        self.opener = build_opener(ProxyHandler({}), NoRedirect())

    def lookup(self, binding):
        if binding.intent.runtime_owner != self.owner:
            raise OutcomeUnavailable("runtime_owner_unavailable")
        request = Request(self.endpoint, data=binding.model_dump_json().encode(), method="POST",
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json"})
        try:
            with self.opener.open(request, timeout=self.timeout) as response:
                data = response.read(262145)
                if len(data) > 262144:
                    raise OutcomeUnavailable("runtime_response_too_large")
                # Pydantic enforces the closed proof union and all identity fields.
                outcome = RuntimeOutcome.model_validate_json(data)
        except (URLError, OSError, ValueError) as error:
            raise OutcomeUnavailable("runtime_outcome_unavailable") from error
        if outcome.binding != binding:
            raise OutcomeUnavailable("runtime_binding_mismatch")
        return outcome
