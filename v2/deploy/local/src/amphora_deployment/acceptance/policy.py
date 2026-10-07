"""Closed BP-09 evidence universe. Changes require a new ledger profile."""

PROFILE = "bp09-local-synthetic.v1"
# File names and assertions are reviewed policy, never caller-selected commands.
GATES = {
    "host": ("Selected_Local_Host.json", "passed"),
    "installation": ("Owner_Inventory.json", "passed"),
    "live_context": ("Owner_Context_Campaign.json", "passed"),
    "successor": ("Corrected_Successor.json", "passed"),
    "capacity": ("Managed_Capacity.json", "passed"),
    "browser": ("Gateway_Replacement_Browser.json", "passed"),
    "daemon_recovery": ("Shared_Daemon.json", "passed"),
    "backup": ("Cold_Backup.json", "cold_backup_verified"),
    "restore": ("Restore_Verification.json", "isolated_restore_accepted"),
    "reconstruction": ("Evaluator_Reconstruction.json", "rebuilt_evaluator_cutover_accepted_with_retained_failures"),
    "recovery_faults": ("Recovery_Faults.json", "passed"),
    "recovery_acceptance": ("Recovery_Acceptance.json", "accepted_with_nonblocking_followups"),
}
ASSERTIONS = {
    "live_context": ((('scientific', 'successful_invocations'), 15),
                     (('scientific', 'evaluations'), 6),
                     (('checkpoint', 'winner'), 'model_accepted'),
                     (('restart', 'original_graph_and_admission_unchanged'), True),
                     (('restart', 'additional_model_calls'), 0)),
    "daemon_recovery": ((('one_original_intent_one_container',), True),
                        (('blocked_graph_receipt_completions_exact',), True)),
    "backup": ((('source_stores_restored',), True),
               (('objective',), 'last fully drained backup; measure recovery time without hard limit')),
    "restore": ((('source_preserved',), True), (('provider_calls',), 0),
                (('catalog', 'failures'), {}), (('catalog', 'pending_reservations'), 0)),
    "reconstruction": ((('campaign', 'evaluations'), 6),),
    "recovery_faults": ((('backup', 'original_backup_unchanged'), True),
                        (('fencing', 'late_rejection'), 'stale_attempt')),
    "recovery_acceptance": ((('independent_installations', 'status'), 'passed'),
                            (('independent_installations', 'qualified_evaluator_wheel_closure_unchanged'), True),
                            (('catalog', 'failures'), {}), (('catalog', 'pending_reservations'), 0)),
}
LIMITATIONS = (
    "synthetic_software_evidence_not_scientific_validation",
    "same_host_user_and_retained_owner_dependencies",
    "recovery_time_measured_without_hard_limit",
    "intermittent_worker_failures_unresolved_no_soak_claim",
    "separate_campaign_scopes_not_one_combined_run",
    "hash_integrity_not_evidence_authenticity_or_current_health",
)
