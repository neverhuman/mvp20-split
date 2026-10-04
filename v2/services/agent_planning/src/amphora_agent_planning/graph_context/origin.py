"""Accepted change binds a pinned snapshot, without implying scientific truth."""

import hashlib

from amphora_contracts_knowledge import AcceptedGraphChange

from ..context.policy import require
from .records import canonical


def verify_change(pins, supplied):
    pins = pins.validated()
    require(pins.base is not None, "knowledge_change_without_head")
    change = AcceptedGraphChange.model_validate(supplied.model_dump(mode="python", warnings=False))
    content = change.content
    require(change.reference == pins.base.change and
            hashlib.sha256(canonical(content)).hexdigest() == change.reference.sha256, "knowledge_change_digest")
    require(content.resulting_snapshot == pins.base.snapshot and content.position == pins.base.change.position and
            content.policy == pins.policy and content.proposal.graph == pins.graph and
            content.proposal.change_id == change.reference.change_id and content.proposal.policy == pins.policy and
            content.proposal.vocabulary == pins.vocabulary, "knowledge_change_binding")
    return change
