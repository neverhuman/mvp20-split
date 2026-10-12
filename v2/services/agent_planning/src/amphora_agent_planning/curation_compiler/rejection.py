"""Known model policy violations, distinct from corrupt retained evidence."""

POLICY_CODES = frozenset({
    'decision_future_not_permitted', 'decision_future_identity', 'decision_future_context',
    'decision_future_nodes', 'decision_future_scopes', 'decision_future_depth',
    'decision_future_iterations', 'decision_future_timeout', 'decision_future_side_effect',
    'decision_action_not_permitted', 'decision_tool_applicability',
    'campaign_authored_scope_limit', 'campaign_authored_node_limit', 'campaign_authored_duplicate_node',
    'campaign_producer_unknown', 'campaign_tool_not_reviewed', 'campaign_tool_not_consumed_or_ambiguous',
    'campaign_tool_lifecycle', 'campaign_tool_duplicate_input', 'campaign_tool_input_ports',
    'campaign_tool_timeout', 'campaign_tool_checkpoint', 'campaign_tool_checkpoint_schema',
    'campaign_tool_literal_representation', 'campaign_tool_input_unconsumed',
    'campaign_tool_runtime_unavailable', 'campaign_tool_reviewed_lock',
    'campaign_evidence_context_missing', 'campaign_evidence_need_question',
    'campaign_evidence_duplicate_need', 'campaign_evidence_duplicate_assessment',
    'campaign_evidence_assessment_pin', 'campaign_evidence_assessment_question',
    'campaign_evidence_reference_unselected',
})


class ProposalRejected(ValueError):
    """Raised only before selecting or dispatching a compiler operation."""
