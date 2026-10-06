# Actual fitness owner handoff

- Owner: BP-08.03/B2.03a; verified 2026-10-06 14:15:54.
- Run from root: `AMPHORA_TEST_POSTGRES=1` and `v2/dev/.venv/Scripts/python.exe v2/dev/verify_fitness_handoff.py --output .test-results/<unique-directory>`.

Three fresh wheel closures install Data, Research and an SDK-only controller. Research-owned bootstrap code creates synthetic immutable candidate/material/experiment/observation/interpretation/eligibility/synthesis records through Research domain stores in its own interpreter. This setup is explicit; it does not claim lab intake, canonicalization or evaluator producer provenance. The controller imports no owner implementation or SQL and publishes actual source and declared-identity Artifacts through Data HTTP.

The probe assembles and retries fitness through Research HTTP, restarts Research and checks identical replay/history, then restarts Data with the Research source credential removed. New assembly must fail403 while the separately granted historical read returns original bytes. Evidence retains package/wheel manifests, scoped identity, source count and timestamps. No histories or artifacts are deleted. Data-original configuration remains recorded before the denial variant.

Passing this gate is actual owner handoff evidence only. It does not authorize cache reuse, verify scientific truth, build tool images, or prove a target deployment. B2.03b owns producer-backed reuse; V1 owns independent replacement/closeout.

Evidence: `.test-results/fitness-handoff-20261006a/http/evidence.json`, passed2026-10-06 14:13:04;14source references, scopeb923ba844fbb49d3ac4be5b6347f0e3f, fitnessdigestd622030535c74a8bd5f628d6cd49c745e13080057a5befb87c9c4da4fb0a1e1f. Research0.38/Data0.30/SDK0.2 in three fresh closures.12boundarychecks11.48s.
