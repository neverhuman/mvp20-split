# UI-02 planning and implementation history

## 2026-10-13 11:29:12 ? Approved chemical boundary and P1.1

Owner approved UI-02.01: supplied connected finite molecules/fully specified
oligomers, formula and inert PNG; independently packaged tool and opt-in Research
profile. No paid calls or chemical-property recommendation authority. Container
hosting is deferred per owner; it does not interrupt UI-02 priority.

Local79358/session13h and LAN90134/LAN13f drained through their STOP files, both
exit0 before source changes. Frozen Studio0.34.4 serving13f remains the restart
baseline. Five abandoned NAS-read shells were closed earlier; demo processes
were retained until this explicit implementation drain.

Added contracts/chemical_structure0.1.0 with request/result, safe failure union,
exact candidate/scope/source binding, molecular graph, method/environment identity,
formula/isotope/charge policy and bounded PNG. Published four schema files and
finite-smiles semantic profile; all668 predecessor fingerprints preserved.
Owned wire/publication12tests pass. Full schema suite24pass/1fail identified only
an older aggregate-count assertion; corrected its scope, both affected tests pass.
Production dependency boundary check passes. P1.1 complete100%; P1=25%, overall6.25%, Build8.33%, Verification0%. Next P1.2 isolated tool.
Development sync also reconciled existing Planning0.142/Deployment0.20.2 editable
versions; immutable installed serving directories are unchanged.

## 2026-10-13 11:37:38 ? P1.2 independent chemistry tool

Pinned RDKit2025.9.6 with locked numpy2.5.4/Pillow12.3.0. Separate profile,
parsed molecule, display bundle and request derivation objects. Exact original
request SHA-256, duplicate-key rejection, strict scope, unsupported feature checks,
explicit/isotopic hydrogen, charge/stereo preservation,800x600 inert bounded PNG.
No source-level formula/depiction generation in Research/Runtime/Studio.

Independent .test-results/ui02-chemical-independent-20261013a passes32 copied
kernel tests; installed schemas equal publication, two fresh CLI processes return
identical retained bytes. Service and sibling tool imports absent. Supplied ethylene
glycol formula C2H6O2 and PNG visually inspected; finite oligomer C4H10O3 golden
also passes. Dependency boundary check passes. Earlier test harness oversized-case
ID exceeded Windows path bounds; named case IDs repaired, all tests pass.
All668 predecessor schema bytes remain unchanged; chemical semantic profiles now
have explicit LF Git attributes to preserve digest identity across Windows clones.
P1.2=100%; P1=50%; overall12.5%, Build16.67%, Verification0%. P1.3 next; Linux
worker/Registry/Runtime/Data/Research acceptance remains P1.4, not claimed here.

## 2026-10-13 11:43:38 ? P1.3 opt-in Research registration

Research0.41.0 adds ChemicalCandidateProfile, enabled only by an explicit
finite_molecule/schema/profile configuration. No RDKit or tool imports. Exact
candidate/revision binding now passes from registrar into profile validation;
old synthetic behavior remains. Validates successful derived bundle, graph topology,
charge and bounded PNG header/hash/dimensions; does not claim chemical interpretation
or producer authentication. Existing DTOs/routes/research_0016 tables unchanged.

75 PostgreSQL/registration/identity checks pass, including chemical host startup,
malformed bundle/identity/scope/profile failures, fresh access on retries and
immutable historical reads after denial. Existing synthetic race/rollback/routes
remain covered. Two schema compatibility checks and dependency guard pass. First
invocation lacked dev pytest configuration; rerun with explicit -c passed.
P1.3=100%, P1=75%, overall18.75%, Build25%, Verification0%. P1.4 actual independently
installed registered graph/retention/Research handoff next. No new model calls.

## 2026-10-13 11:53:07 ? Actual integration exposes Registry gate

Six independent installations completed (Runtime/Data/Research/chemical/Registry/
SDK controller). Actual Registry accepted chemical descriptor registration, then
rejected activation_profile_denied. Initial harness dereferenced absent release;
corrected fresh-scope rerun retained the denial explicitly. Both probes closed owned
processes; no chemical campaign admitted or model calls. Exact receipts committed
under docs/Audits/Evidence/UI-02-Chemical/Registry_Activation.json.

Code confirms both activation and separate scientific selection are synthetic-only;
the original inventory missed this prerequisite. UI-02.02 proposes a scoped exact-pin
structural profile shared by activation/selection, default legacy behavior/digests
and immutable receipt replay unchanged. No Registry change, workaround or synthetic
relabelling performed. P1.4=0%, P1=75%, overall18.75% unchanged pending decision.

2026-10-13 11:55:57: prior frozen Studio0.34.4 demo restored, local31118/session13i and LAN47144/LAN13g. Both ready; app.js HTTP200 and exact21fa5c5d6f790ffd902f0074290a651c5bebcd5173cf136ba105ac43514db5f2 match. No UI-02 cutover or new model calls. Final normalized-LF tool installation passes32 copied tests.
