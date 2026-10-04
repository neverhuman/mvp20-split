"""Relations belong to a focused policy, not wide DTO constructors."""

from amphora_contracts_core import Scope
from amphora_contracts_planning import EngagementRequest


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


class ContextPolicy:
    @staticmethod
    def validate(request: EngagementRequest, actor_id: str, scope: Scope) -> None:
        manifest = request.context
        require(request.reference.scope == scope == manifest.scope, "scope_mismatch")
        require(request.actor_id == actor_id, "actor_mismatch")
        require(request.purpose != "supervision" or request.runtime_cut is not None, "missing_runtime_cut")
        if request.runtime_cut is not None:
            require(request.runtime_cut.scope == scope, "runtime_scope_mismatch")
        bases = (manifest.objective, manifest.prompt, manifest.policy, manifest.model.configuration)
        included = (*bases, *(entry.artifact for entry in manifest.entries))
        omitted = tuple(item.artifact for item in manifest.omissions)
        require(all(ref.scope == scope for ref in (*included, *omitted)), "artifact_scope_mismatch")
        identities = {}
        for ref in (*included, *omitted):
            previous = identities.setdefault(ref.artifact_id, ref)
            require(previous == ref, "artifact_identity_conflict")
        entry_ids = tuple(entry.artifact.artifact_id for entry in manifest.entries)
        omitted_ids = tuple(item.artifact_id for item in omitted)
        require(len(set(entry_ids)) == len(entry_ids), "duplicate_context_entry")
        require(len(set(omitted_ids)) == len(omitted_ids), "duplicate_omission")
        require(not {ref.artifact_id for ref in included}.intersection(omitted_ids), "included_omission")
        require(len(set(manifest.allowed_actions)) == len(manifest.allowed_actions), "duplicate_action")
        limits = manifest.limits
        per_attempt = limits.max_input_tokens + limits.max_output_tokens
        require(per_attempt <= manifest.model.context_window_tokens, "context_window_exceeded")
        require(per_attempt <= limits.total_tokens, "insufficient_attempt_budget")
