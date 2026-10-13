# Planning peer reader credentials

UI-01.08j/M3; Deployment0.20.1. Owns the optional create-once current-user DPAPI
sidecar `planning-readers.dpapi`, bound to the original deployment identity with
distinct entropy. Original credentials never change. Two distinct references:
PLANNING_KNOWLEDGE_TOKEN reaches only Planning/Knowledge; PLANNING_RESEARCH_TOKEN
reaches only Planning/Research. Explicit manifest selection is required; legacy
manifests do not load this sidecar. Values enter selected child environments only.

Provisioning requires ready stores/readable original identity under the existing
operation lease. Existing corrupt, foreign or wrong-membership sidecars fail closed;
never regenerate or rotate them. Results disclose names/status only.

Credentials alone grant no action. Independently reviewed peer configurations must
grant only scoped read_graph/read_declarations required by curation. This module
owns no peer tables, model key, provider calls or campaign admission. Actual peer
qualification and serving delivery are separate gates. Rotation is not implemented.

Tests: deploy/local/tests/curation_access; actual Windows DPAPI, original-vault
preservation, identity/membership/corruption, least-privilege environment selection
and legacy absence. Architecture: System service isolation and local deployment.
