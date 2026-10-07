# Runtime Registry identity tests

Owns create-once, deployment-bound credential and allowed-owner regression cases
for registry_access. Uses temporary installations and real current-user Windows
DPAPI; never reads or alters the active installation. Run this folder together
with lifecycle/test_credential_scope.py and tool_catalog/test_credentials.py.
Actual independent owner configurations and Registry permissions need separate
integration evidence; token provisioning alone is not an authorization proof.
