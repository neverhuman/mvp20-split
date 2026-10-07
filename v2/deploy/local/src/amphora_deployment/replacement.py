"""Declarative replacement order; no process control or private Runtime reads."""

from dataclasses import dataclass

from .profile import require


@dataclass(frozen=True)
class CampaignCut:
    admissions_paused: bool
    active_campaigns: int
    inflight_attempts: int
    pending_retentions: int

    def plan(self):
        require(type(self.admissions_paused) is bool, "cut_paused_shape")
        for value in (self.active_campaigns, self.inflight_attempts, self.pending_retentions):
            require(type(value) is int and 0 <= value <= 2**53 - 1, "cut_count")
        blockers = []
        for condition, reason in ((self.admissions_paused, "pause_admission_first"),
                                  (self.active_campaigns == 0, "wait_for_campaign_terminal"),
                                  (self.inflight_attempts == 0, "wait_for_attempt_drain"),
                                  (self.pending_retentions == 0, "wait_for_retention_confirmation")):
            if not condition:
                blockers.append(reason)
        return {"status": "blocked" if blockers else "order_available", "blockers": blockers,
                "authority": "operator_supplied_counts_not_verified_runtime_evidence", "executes_actions": False,
                "stop_order": [] if blockers else ["keep_admission_paused", "stop_idle_workers", "stop_planning_and_runtime_coordinators",
                    "drain_owner_deliveries_and_projections", "stop_owner_apis", "capture_consistent_database_and_artifact_backup"],
                "start_order": [] if blockers else ["verify_storage_and_owner_schema_versions", "start_owner_apis",
                    "start_owner_delivery_and_projection_consumers", "verify_registry_and_pinned_releases",
                    "start_compatible_workers", "start_planning_and_runtime_coordinators", "verify_health_and_history", "enable_admission_last"]}
