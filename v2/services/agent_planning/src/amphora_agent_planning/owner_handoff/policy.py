"""Conservative submission eligibility survives later transient observations."""

import json


class SubmissionPolicy:
    @staticmethod
    def block(state):
        if state.position >= 63:
            return "event_limit"
        for event, _ in state.events:
            value = json.loads(event.canonical)
            if value["action"] == "blocked" and value["data"] in {"request_rejected", "identity_conflict"}:
                return value["data"]
        return None
