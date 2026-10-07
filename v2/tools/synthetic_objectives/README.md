# Synthetic numeric objectives

- Owner: original BP-08.02 boundary; release0.3.0 is the BP-08.05 correction-identity fixture, qualified for synthetic correction and offline images. Prior0.2 Registry/replacement acceptance remains historical evidence below.
- Design: [Search](../../docs/Architecture/Campaigns/Search.md); standalone evaluator, separate from the search owner.

This tool declares two required Artifact inputs: parameters (public EvaluationRequest) and policy (the exact synthetic policy). It emits EvaluationObservation. The fixed synthetic-quadratic-v1 problem accepts 1..32 finite dimensionless genes in [-1e6,1e6]. It computes cost=sum(x_i^2) and/or distance=sum((x_i-1)^2), preserving requested objective order. The profile has no hard constraints, so violation is exactly zero; this is a declared synthetic problem, not a fallback for missing constraints. Output quality is always synthetic.

The request must pin this exact evaluator release/image, a proposed candidate with its ev- identity, unique supported objective names/units, no extra context and the exact synthetic policy Artifact metadata. The policy command emits canonical bytes; schema --kind policy emits the required schema. Data must publish/retain the actual policy Artifact before use. The kernel checks the actual named policy input reference and bytes against the request and known profile; it does not fetch hidden references or assert permission. Observation provenance retains that policy reference and the canonical request digest. No scientific measurement or external evidence is invented.

Responsibilities: kernel.py owns applicability, fixed formulas and result mapping; metadata.py owns exact public input/output/policy schemas and descriptor; adapter.py owns configured image binding and safe failures; __main__.py exposes compute/describe/policy/schema/worker. Compute and describe require --image-sha256; compute also requires --policy-file and is an offline arithmetic check, not proof that the declared Artifact exists or is authorized. Worker uses the explicit multi_input_worker companion and public Tool Protocol SDK clients with local configuration; Runtime owns claims/leases/acceptance, Data owns bytes. Input/output cap262144 bytes. Diagnostics never echo payloads.

No search-owner imports, population selection, graph iteration, database, model call, laboratory integration, molecular representation, synthesis assessment or scientific promotion belongs here. Each invocation is pure; descriptor egress deny, authority synthetic_only, worker checkpoint mode none. The offline-wheel Dockerfile produces a verified Linux/amd64 image; local Windows-hosted Linux/TLS deployment is qualified by BP-09.03; other target profiles remain unverified. Tests belong under tests/kernel and tests/cli. Rebuild acceptance preserves exact formulas, scope/policy/evaluator binding, objective order, provenance and safe rejection; publish a new immutable profile/release if those semantics change.

Verified 2026-10-06 11:20:45:144 evaluator/multi-input/legacy-SDK/boundary checks20.18s. Kernel and metadata100% measured coverage; aggregate parent coverage78% because CLI/offline subprocess paths and configured worker helper are not attributed/exercised here. Arithmetic [1,-2] gives cost5/distance9; policy identity, content, evaluator, units and applicability mismatches reject. Actual Runtime/Data HTTP, image arithmetic and Registry/replacement checks subsequently passed; process coverage is not inferred from those scenarios.

Release0.2.0 adds the existing Registry-required synthetic-tests applicability marker; formulas and payload schemas are unchanged. Requalification and actual-owner replacement passed in BP-08.02/V1. Prior0.1.0 images/descriptors remain immutable historical evidence.

Release0.3.0 creates a distinct immutable evaluator identity for the successor
correction proof. Arithmetic, policy bytes and payload schemas are unchanged;
this does not claim a scientific correction or numerical improvement. New
search specifications/evaluations/selection must pin0.3 explicitly. Original0.2
checkpoints and ranks stay immutable and cannot resume or provide fitness under
the new identity. The old independent0.2 installation is preserved separately.

[Replacement evidence](../../docs/Audits/Evidence/BP-08-Search/Registry_Replacement.json) verifies matching image/installed local wheel closures, registered/active descriptors, explicit real policy Artifacts, six evaluations per campaign and independent replacement. [Image qualification](../../docs/Audits/Evidence/BP-08-Search/Eligibility_Requalification.json) retains the fixed-box arithmetic golden and schema hashes.

Verified 2026-10-06 19:54:31: Release0.3 acceptance passed actual isolated corrected-successor workers, old history preservation after fresh Runtime, and offline Linuxamd64 image/goldens/schema/nonroot/isolation with exact installed wheel closure. See [correction](../../docs/Audits/Evidence/BP-08-Search/Corrected_Successor.json) and [images](../../docs/Audits/Evidence/BP-08-Search/Recovery_Images.json). Registry0.2 qualification remains historical; no automatic0.3Registry activation or target-host deployment is claimed.

BP-09.03 target-host evidence: [integrated campaign](../../docs/Audits/Evidence/BP-09-Deployment/Owner_Context_Campaign.json) and [closeout](../../docs/Audits/BP-09.03_Integrated_Demo_Closeout.md). Actual retained15/6/3/15 synthetic execution is software evidence only; earlier BP-08 qualification limits remain historical.
