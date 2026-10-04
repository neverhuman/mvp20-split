"""Bounded SDK upload transitions; journals retain their own state and authority."""

from amphora_tool_protocol import CommandRejected


def drive_upload(journal, client, principal, lease, state):
    store = journal.store

    def guard():
        store.guard(principal, lease)

    def advance(action, data=None):
        return journal.advance(principal, lease, state.position, action, data)

    # One invocation can recover an abandoned upload and finish one successor.
    # It does not spend all eight attempts retrying a failing peer.
    for _ in range(10):
        attempt, artifact = state.attempt, state.payload.artifact
        if attempt.stage in {"finalized", "rejected"}:
            return state
        guard()
        if attempt.stage == "prepared":
            try:
                receipt = client.begin_derived(artifact.content, artifact.declaration,
                    attempt.identity.begin_id, guard=guard, resume=True)
            except CommandRejected as error:
                state = advance("rejected", {"reason": error.reason_code})
            else:
                state = advance("begun", receipt.model_dump(mode="json"))
        elif attempt.stage == "begun":
            # Only this successful CAS authorizes this invocation's single PUT.
            # A crash immediately after CAS is conservatively uncertain.
            state = advance("streaming")
            receipt = client.stream(state.attempt.upload.upload, artifact.body, guard=guard)
            state = advance("streamed", receipt.model_dump(mode="json"))
        elif attempt.stage == "streaming":
            state = advance("abandoned")
        elif attempt.stage == "abandoned":
            state = advance("replacement")
        elif attempt.stage == "streamed":
            state = advance("finalizing")
        elif attempt.stage == "finalizing":
            try:
                receipt = client.finalize(attempt.upload.upload, attempt.identity.finalize_id,
                                               guard=guard, resume=True)
            except CommandRejected as error:
                state = advance("rejected", {"reason": error.reason_code})
            else:
                derivation = client.derivation(receipt.artifact)
                state = advance("finalized", {"receipt": receipt.model_dump(mode="json"),
                                               "derivation": derivation.model_dump(mode="json")})
    raise ValueError("publication_transition_limit")
