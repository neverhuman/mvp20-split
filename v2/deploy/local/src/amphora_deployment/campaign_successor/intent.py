"""Exact successor identity; never downgraded to a fresh launch."""
import json

from amphora_contracts_campaign_successor_launch import parse_successor_launch
from amphora_contracts_graph_runtime import PredecessorCut

from ..campaign_launch.intent import LaunchError, LaunchIntent


class SuccessorIntent(LaunchIntent):
    @classmethod
    def parse(cls, raw: bytes):
        try:
            return cls(*parse_successor_launch(raw))
        except ValueError:
            raise LaunchError('launch_request_invalid') from None

    @property
    def key(self):
        return (*super().key, 'campaign.launch_successor')

    @property
    def predecessor(self):
        return PredecessorCut.model_validate_json(json.dumps(
            json.loads(self.admission.canonical_bytes)['payload']['predecessor']))

    @property
    def admission_route(self):
        return '/v1/graph-runs/draft-successors'
