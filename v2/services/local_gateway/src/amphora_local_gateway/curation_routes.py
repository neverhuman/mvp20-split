"""Exact approved Planning curation/capability routes; no generic command lane."""
from dataclasses import dataclass
import re
from urllib.parse import unquote, urlsplit

from .configuration import require

IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z')
ERRORS = frozenset({'curation_not_recorded', 'curation_receipt_not_recorded',
    'curation_command_conflict', 'curation_receipt_conflict', 'curation_history_inconsistent',
    'invalid_curation_request', 'capability_request_not_recorded', 'capability_history_inconsistent',
    'invalid_capability_request', 'capability_request_not_found', 'fulfillment_command_conflict',
    'fulfillment_history_inconsistent', 'invalid_fulfillment_request', 'planning_access_denied'})


@dataclass(frozen=True)
class CurationRoute:
    method: str

    @classmethod
    def parse(cls, target):
        parsed = urlsplit(target)
        parts = parsed.path.split('/')
        family = parts[2] if len(parts) > 2 else ''
        if not family.startswith(('campaign-curations', 'capability-requests')):
            return None
        require(not parsed.query, 'gateway_curation_route')
        method = None
        if family == 'campaign-curations':
            if len(parts) == 3:
                method = 'POST'
            elif len(parts) == 5 and parts[3:] == ['receipts', 'query']:
                method = 'POST'
            elif len(parts) == 4 and IDENTIFIER.fullmatch(unquote(parts[3])):
                method = 'GET'
        elif family == 'capability-requests' and len(parts) in (4, 5) and IDENTIFIER.fullmatch(unquote(parts[3])):
            if len(parts) == 4:
                method = 'GET'
            elif parts[4] == 'fulfillments':
                method = 'POST'
        require(method is not None, 'gateway_curation_route')
        return cls(method)

    def check(self, method, body):
        require(method == self.method and len(body) <= 262144
            and (method != 'GET' or not body), 'gateway_curation_request_bound')
