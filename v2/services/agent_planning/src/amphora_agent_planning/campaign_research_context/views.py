"""One exact named-page observation, including unavailable state and continuation."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_research_views import research_view_schema

from ..campaign_research_access.reader import PEER_CODES
from ..context.policy import require
from ..research_view_access import ViewPage, ViewSelection
from ..research_view_access.query import canonical


@dataclass(frozen=True)
class CampaignViewContext:
    selection: ViewSelection
    canonical: bytes

    @classmethod
    def bind(cls, request, result):
        selection = ViewSelection.bind(result.selection.document(), result.selection.request)
        require(selection.request == request, 'campaign_research_view_request')
        require((result.page is None) != (result.failure is None), 'campaign_research_view_shape')
        page = None
        if result.page is not None:
            require(result.page.selection == selection, 'campaign_research_view_selection')
            page = ViewPage.bind(selection, result.page.document())
        else:
            require(result.failure in PEER_CODES | {'research_view_invalid'}, 'campaign_research_view_reason')
        value = {'view': selection.view, 'request': selection.document().model_dump(mode='json'),
            'selection_sha256': selection.sha256, 'result_schema': research_view_schema(selection.view).model_dump(mode='json'),
            'status': 'available' if page is not None else 'unavailable', 'reason': result.failure,
            'page': None if page is None else json.loads(page.canonical)}
        return cls(selection, canonical(value))

    @property
    def identity(self):
        # Same scoped page selection across requests can be compared without global request invalidation.
        return canonical({'view': self.selection.view, 'request': self.selection.document().model_dump(mode='json')})

    @property
    def observation_sha256(self):
        value = json.loads(self.canonical)
        return hashlib.sha256(canonical({key: value[key] for key in ('result_schema', 'status', 'reason', 'page')})).hexdigest()
