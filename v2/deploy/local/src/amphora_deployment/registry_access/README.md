# Runtime Registry credential

BP-09.03/B1.4c; Deployment0.11. Owns one optional create-once current-user DPAPI
sidecar, `runtime-registry.dpapi`, bound to deployment identity and a distinct
entropy label. The only reference is `RUNTIME_REGISTRY_TOKEN`; only Runtime and
Registry can receive it through lifecycle bindings. Operator, worker, Planning,
Data and gateway credentials remain separate. Original vault bytes never change.

Provisioning holds the deployment operation lease, requires ready stores and a
readable original vault, creates only when absent, then verifies exact reference
membership. Existing corrupt/foreign/extra-entry files fail closed, never rotate
or regenerate. Results expose names/status only. Values enter only explicitly
selected child environments; no plaintext files, arguments or logs.

This module grants no Registry action by itself. A new immutable owner configuration
must declare the scoped Runtime peer principal and read/resolve permissions; it
must not grant register/activate/deploy merely to admit a graph. Existing manifests
without this reference never load the sidecar and preserve their behavior.

Owned tests: deploy/local/tests/registry_access. They exercise actual Windows DPAPI,
repeatability, original-vault preservation, identity/membership/corruption denial,
and lifecycle owner selection. Independent installation and actual peer qualification
are separate gates. Credential rotation/revocation is not implemented here.
