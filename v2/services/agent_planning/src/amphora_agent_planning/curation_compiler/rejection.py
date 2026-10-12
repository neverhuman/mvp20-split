"""Known model policy violations, distinct from corrupt retained evidence."""

POLICY_CODES = frozenset({
    'decision_future_not_permitted', 'decision_future_identity', 'decision_future_context',
    'decision_future_nodes', 'decision_future_scopes', 'decision_future_depth',
    'decision_future_iterations', 'decision_future_timeout', 'decision_future_side_effect',
    'decision_action_not_permitted', 'decision_tool_applicability',
})


class ProposalRejected(ValueError):
    """Raised only before selecting or dispatching a compiler operation."""
