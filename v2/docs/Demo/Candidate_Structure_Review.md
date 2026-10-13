# Review a supplied chemical structure

- Status: Studio0.36 inspector qualified on actual local/LAN owners; held-example invitation and drain qualified.
- Reviewed: 2026-10-13 18:16:04 America/Chicago.
- Purpose: inspect an actual supplied-structure result without claiming molecular optimization.

The main demo remains at `http://127.0.0.1:57013` and
`https://192.168.1.70:57013` when its wrappers are running. Selected frozen serving
`v2/.test-results/curation-demo-serving-20261013h` contains Studio0.36. The prior f
directory remains unchanged. Results now includes **Candidate structures**.
The old Hansen/Arrhenius runs have no chemical structures; their empty state is correct.

A separate example runs the chemical tool on supplied `OCCOCCO`, retains its output,
registers the exact candidate in Research, and opens the same production Studio.
The result is **C4H10O3**, with a2D connectivity drawing, explicit unranked status,
missing property/synthesis evidence, and its exact producing execution record.
It is a finite molecule example, not the outcome of a polymer optimization campaign.

From the repository root in PowerShell, use a fresh output directory:

```powershell
$env:AMPHORA_TEST_POSTGRES = '1'
v2/dev/.venv/Scripts/python.exe -X utf8 v2/dev/verify_chemical_handoff.py `
  --output v2/.test-results/ui02-candidate-demo-session-20261013a `
  --installations v2/.test-results/ui02-chemical-handoff-20261013e `
  --registry-installation v2/.test-results/ui02-registry-installation-20261013a `
  --studio v2/.test-results/curation-demo-serving-20261013h/public `
  --gateway-installation v2/.test-results/successor-gateway-installation-20261012a/owner `
  --hold-seconds 86400
```

After `http/studio/ready.json` appears beneath that output, open
`http/studio/Open supplied structure.url`. The short-lived single-use invitation
creates the browser session at localhost port57014. Select **derive_structure**
under Results and evidence. Expand derivation/provenance or inspect the producing
execution step. Touch `http/studio/INVITE` to mint a fresh invitation; never publish
its ticket. Touch `http/studio/STOP` to drain the example and finish its remaining
qualification checks. All owner credentials stay in process environment.

The held example is localhost only and uses a separate fixture scope. It creates
one supplied-structure campaign, makes no model request, and does not alter the
main demo's campaign or Knowledge graph. Source/test/module changes must wait until
all serving/test workflows are stopped, per the repository's execution discipline.
