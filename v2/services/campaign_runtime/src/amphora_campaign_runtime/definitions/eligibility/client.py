"""Server-only, bounded public Registry calls outside Runtime transactions."""

import json
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from amphora_contracts_commands import CommandIdentity
from amphora_contracts_tools import (
    RegistryReceipt,
    ResolveRelease,
    parse_registry_command,
)

from .observations import EligibilityObservation, EligibilityUnavailable


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class RegistryEligibility:
    def __init__(self, endpoint, token, actor_id, *, maximum_age_seconds=5):
        parsed = urlsplit(endpoint)
        if (not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in {"", "/"} or parsed.scheme != "https"
                and not (parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "::1"})):
            raise ValueError("Explicit Registry origin required")
        if (not isinstance(token, str) or len(token) < 32 or type(maximum_age_seconds) is not int
                or not 1 <= maximum_age_seconds <= 60):
            raise ValueError("Configured Registry credential and bounded observation age required")
        # Validate actor bounds using the public identity, without registering anything.
        CommandIdentity(actor_id=actor_id, command_family="registry.resolve", command_id="configuration",
                        scope={"tenant_id": "configuration", "project_id": "configuration"})
        self.endpoint, self.token, self.actor_id = endpoint.rstrip("/"), token, actor_id
        self.maximum_age_seconds = maximum_age_seconds

    def observe(self, verified):
        deadline = time.monotonic() + 10
        reviewed = {tool.lock.descriptor_sha256: tool for tool in verified.universe.releases}
        observations = []
        for lock in verified.entry.plan.document.lock.tools:
            tool = reviewed[lock.descriptor_sha256]
            identity = CommandIdentity(actor_id=self.actor_id, scope=verified.draft.content.definition.scope,
                command_family="registry.resolve", command_id=uuid.uuid4().hex)
            # Existing Registry admits only synthetic fixtures. This is an explicit fixed profile,
            # never a claim that arbitrary scientific context has been assessed.
            need = ResolveRelease(release=lock, context="synthetic-tests",
                                  inputs=tool.descriptor.tool.inputs, outputs=tool.descriptor.tool.outputs)
            command = parse_registry_command("registry.resolve", json.dumps({
                "identity": identity.model_dump(mode="json"), "payload": need.model_dump(mode="json")}))
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EligibilityUnavailable("draft_registry_timeout")
            receipt = self._resolve(command, remaining)
            if time.monotonic() > deadline:
                raise EligibilityUnavailable("draft_registry_timeout")
            observations.append(EligibilityObservation.bind(command, receipt, tool, self.maximum_age_seconds))
        return tuple(observations)

    def _resolve(self, command, timeout):
        request = Request(self.endpoint + "/v1/registry/resolve", data=command.canonical_bytes,
            headers={"Authorization": "Bearer " + self.token, "Content-Type": "application/json", "Accept": "application/json"},
            method="POST")
        try:
            with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=timeout) as response:
                body = response.read(262145)
                if response.status != 200 or len(body) > 262144:
                    raise EligibilityUnavailable("draft_registry_response_invalid")
            return RegistryReceipt.model_validate_json(body)
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as error:
            raise EligibilityUnavailable("draft_registry_unavailable") from error
