"""Successor receipt projection over the shared, unchanged launch lifecycle."""
from amphora_contracts_campaign_successor_launch import SuccessorLaunchReceipt
from ..campaign_launch.state import LaunchState


class SuccessorState(LaunchState):
    receipt_model = SuccessorLaunchReceipt

    def receipt(self):
        return SuccessorLaunchReceipt(**self.receipt_fields(),
            profile_kind='campaign-successor-launch.v1', predecessor=self.intent.predecessor)
