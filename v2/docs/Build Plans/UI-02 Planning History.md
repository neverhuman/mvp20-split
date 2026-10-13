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
