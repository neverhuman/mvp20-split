# Selected local demonstration operations

Status: BP-09.05 accepted; instructions executed against the retained local profile. This is the same-host Windows/DPAPI profile, loopback access, one user
and one campaign. Read the [package boundary](README.md) before changing releases.
It is a retained engineering demonstration, not a general installer or production
service. Docker Desktop must already be available. No credential values belong in
shell arguments, logs, manifests, Git or these instructions.

## Install and select the retained profile

Run PowerShell in `Z:\mvp20-split`, with `$env:PYTHONUTF8='1'`. The dev interpreter is
`v2/dev/.venv/Scripts/python.exe`. Restore targets require the same Windows user,
retained protected installation and pinned store/tool images. Source setup is
documented by the [installation](src/amphora_deployment/installation/README.md)
and [persistence](src/amphora_deployment/persistence/README.md) boundaries. Do not
run fresh provisioning or migrations over the retained demonstration.

Build/install a new isolated Deployment closure into a new output directory:

```powershell
@'
import sys
from pathlib import Path
sys.path.insert(0, str(Path('v2/dev').absolute()))
from install_owner_peer import install
install(Path('.test-results/acceptance-owner').absolute(), 'amphora-deployment',
        ['amphora_campaign_runtime', 'amphora_data_artifacts', 'sqlalchemy', 'pydantic'])
'@ | v2/dev/.venv/Scripts/python.exe -
```

Use a fresh suffix if that output exists; preserve previous results. This builds
the reviewed package and records exact wheels; it does not start services or
install owner dependencies for another machine. Six serving owner installations,
gateway and Studio assets are retained under `.test-results`; losing those is a
different recovery scope. Never infer wheel equivalence from a version string.

## Inspect and stop

The supervisor control CLI uses protected local credentials internally:

```powershell
& $deploymentPython -m amphora_deployment.lifecycle status --root $installationRoot
& $deploymentPython -m amphora_deployment.lifecycle readiness --root $installationRoot
```

For a managed campaign, quiesce each configured scientific worker and native worker
using `quiesce --scientific-worker NAME` / `quiesce --worker NAME` with the same
root. Wait for no active work, then drain owners with `drain --owner NAME`.
The [lifecycle contract](src/amphora_deployment/lifecycle/README.md) owns ordering;
normal shutdown rejects outstanding work. Finish with `shutdown --root ...`.
Do not substitute force-stop for a successful drain. The smoke command below owns
its services, runs sequentially and drains them in its cleanup path; do not run it
alongside another controller using the same ports/root.

Diagnose from scoped controller status, readiness, fixed transport-stage counters,
owner exit codes and retained run/attempt IDs. Use targeted container inspection
only for the exact journal-owned container. The selected tool profile suppresses
raw container logs. Worker exits2/3 seen during reconstructed campaigns remain
unresolved; a successful retry is not a repair. Preserve failed histories, never
reset databases or broadly kill processes. A refused controller lease means
another owner may still be active, not permission to delete its journal.

## Backup and isolated restore

The accepted recovery target is **the last fully drained backup; measure time
without a hard limit**. Exact backup manifest/owner pins are in
[Cold Backup](../../docs/Audits/Evidence/BP-09-Deployment/Cold_Backup.json) and
[Restore Verification](../../docs/Audits/Evidence/BP-09-Deployment/Restore_Verification.json).
Capture requires all source owners/workers drained, stopped and leases released;
the capture helper stops only the selected two stores and restores their original
running state. Include every historical artifact root, not only the active root.

`v2/dev/capture_local_backup.py --help` lists explicit source, artifact roots,
configuration, retained readbacks, new backup output and evidence arguments.
For a new target use `v2/dev/restore_local_backup.py` with `--backup`,
`--trusted-evidence`, `--expected-owners`, `--target` and `--output`.
Target/output must be new and separate from source. The accepted backup is physical
`local-v2/backup-20261007e`; expected pins are
`.test-results/local-restore-expected-20261007a.json`; trusted evidence is
`.test-results/local-cold-backup-20261007e.json`. Do not allocate another restore
merely to inspect the already accepted target. The backup has protected data;
retain it locally. No source/volume deletion or new shared Docker outage is needed.

Store readiness is not restored-owner acceptance. Check catalog references through
the Data owner's public audit CLI and original/corrected/blocked history through
the public APIs. The recorded10.563seconds is infrastructure recovery only; do
not report it as end-to-end RTO. Corrupt/missing backup bytes and mismatched schema
pins must reject before target resources are created.

## Reproducible retained-history smoke

With the frozen `Acceptance_Ledger.json`, use the independently installed package
above. This starts fresh owner processes against the existing isolated restore,
checks original history, inspects original/corrected browser views at1440/390 and
checks the blocked history. It performs no worker or model calls. The shared
stores must already be running; this is not another daemon interruption drill.

```powershell
$deploymentPython = (Join-Path $PWD '.test-results/acceptance-owner/environment/Scripts/python.exe')
$installationRoot = 'C:/Users/alb_p/AppData/Local/Packages/PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0/LocalCache/Local/Amphora/local-v2/restore-20261007b'
v2/dev/.venv/Scripts/python.exe v2/dev/verify_acceptance_smoke.py `
  --python $deploymentPython `
  --ledger 'v2/docs/Audits/Evidence/BP-09-Deployment/Acceptance_Ledger.json' `
  --evidence-directory 'v2/docs/Audits/Evidence/BP-09-Deployment' `
  --root $installationRoot `
  --configuration '.test-results/local-restore-materials-20261007b' `
  --retained '.test-results/local-integrated-live-20261007b' `
  --public '.test-results/studio-local-successor-20261007b/public' `
  --successor '.test-results/local-corrected-successor-20261007b' `
  --failure-configuration '.test-results/local-restored-failure-config-20261007b' `
  --failure-retained '.test-results/local-controller-fault-20261007b' `
  --output '.test-results/acceptance-smoke'
```

Use a new output suffix for each run. Exit0 plus the written evidence report is
required; retain failure output. The ledger verifies reviewed bytes and selected
assertions; it does not authenticate historical claims or prove current health.
Actual smoke supplies a separate current-health observation.

## Next-campaign replacement

Pin descriptor, public schemas, exact image digest, policy artifact and worker
recipe for the new tool. Qualify it independently from its module README and
acceptance fixtures. Keep original releases/images/history. Quiesce admissions
and verify zero active campaigns, inflight attempts and pending retentions using
`python -m amphora_deployment replacement-order --admissions-paused
--active-campaigns 0 --inflight-attempts 0 --pending-retentions 0`; these declared
counts must come from actual owner observations. This command only reports the
order, not authorization or execution. Apply new bindings to a future campaign,
then verify its exact image/release and retained predecessor history. Never repin
an active campaign or reinterpret old result bytes. See the rebuilt evaluator
[boundary](../../tools/synthetic_objectives_rebuilt/README.md).
