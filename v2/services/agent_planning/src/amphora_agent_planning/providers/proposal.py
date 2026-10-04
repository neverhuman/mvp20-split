"""Reviewed output-profile and selected-artifact checks; domain acceptance is separate."""

import json

from amphora_contracts_planning import ReferenceProposal
from pydantic import ValidationError

from ..context import AttemptBinding
from ..context.policy import require


class ProposalPolicy:
    @staticmethod
    def parse(raw: bytes, attempt: AttemptBinding) -> ReferenceProposal:
        def object_pairs(pairs):
            obj = {}
            for key, value in pairs:
                require(key not in obj, "duplicate_output_key")
                obj[key] = value
            return obj

        def nonfinite(_value):
            raise ValueError("nonfinite_output")

        try:
            value = json.loads(raw.decode("utf-8"), object_pairs_hook=object_pairs, parse_constant=nonfinite)
            proposal = ReferenceProposal.model_validate_json(json.dumps(value, allow_nan=False))
        except (UnicodeDecodeError, json.JSONDecodeError, ValidationError, RecursionError) as exc:
            raise ValueError("invalid_output") from exc
        context = attempt.request.document().context
        require(proposal.action in context.allowed_actions, "action_not_allowed")
        if proposal.action == "abstain":
            require(proposal.payload is None, "abstention_payload")
        else:
            require(proposal.payload is not None, "missing_proposal_payload")
            require(proposal.payload.scope == context.scope, "proposal_scope_mismatch")
            require(any(item.artifact == proposal.payload for item in context.entries), "unselected_payload")
        return proposal
