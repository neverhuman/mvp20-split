# Local owner installation inventory

Owner BP-09.02/B1.01. This module owns immutable wheel/lock/interpreter identities
and reviewed native Windows owner command recipes. It is not an installer,
credential store, supervisor, gateway, migration runner or readiness authority.

OwnerInstallation verifies the retained independent-install manifest, exact wheel
bytes, matching owner release, source lock and interpreter binary. Other primary
owner packages in a closure reject. InstallationInventory requires all six owners,
an exact profile hash and source commit, canonicalizes their identities and reports
readiness/scientific eligibility as not assessed. No credentials appear in records.

Recipes define owner schema/role names and separate migration/serving entry points.
SERVING_HOSTS additionally permits the independent gateway; it has no database role or migration command. OWNERS and InstallationInventory still require exactly six SQL owners. The gateway receives only launcher and operator proxy credentials.
Planning serves through supervision_api and explicitly binds127.0.0.1; the other
five owner CLIs enforce loopback themselves. Migrator URLs remain environment-only
and are never startup arguments. Later lifecycle code must supply only the proper
owner credential to each distinct command. Module paths cannot come from a manifest.

Tests belong under deploy/local/tests/install. Actual owner builds, preserved hash
checks and isolated imports supplement unit fixtures. A source commit alone cannot
prove a clean build; wheel and lock hashes bind actual installed content. Full
external wheel/ABI closure and service/runtime readiness are separate checks.

Verified 2026-10-06 21:53:59: six actual owner installations,79localwheels, exact source-lock/interpreter hashes.56profile/install regressions4.51s and21final install/import checks15.08s passed. Coverage details/remaining branches are in [inventory evidence](../../../../../docs/Audits/Evidence/BP-09-Deployment/Owner_Inventory.json). No service, migration or data-store change performed.
