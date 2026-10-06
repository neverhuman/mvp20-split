# Supervision effective fields

Owner: BP-07.04/B2.02a; architecture: Campaign Runtime graph-runner acceptance. Pure selection implemented; SQL winners and conversion integration remain B2.02c/d.

`ScalarSelection.bind(seed, concrete_path, changes)` returns an immutable canonical private `runtime-supervision-scalar-selection.v1` object. Each `FieldChange` names a permitted inline materialization field, exact prior scalar digest and strict graph-runtime `ScalarValue`. Reconstruction validates the pinned policy/plan and scalar-bearing seed, concrete occurrence, names, prior values, types, units and bounds. Closed legacy seeds cannot authorize scalar changes. Decimal-string values are preserved exactly; there is no float coercion, unit conversion or scientific validity claim.

`resolve(original_fields)` checks all original supervised scalar fields before overlaying selected changes. Other fields and the stored graph stay unchanged. This is the common pure operation intended for conversion opening and source-cut revalidation; those production call sites are not connected yet. Original unchanged values may be outside adjustment bounds. A selection is not a SQL winner, request grant, published Artifact or issued tool input.

No IO, SQL, network, provider, clock or cross-owner private dependency. Public transport must use an explicit new profile; this private record does not reinterpret old CampaignAdjustmentDraft. Replacement tests must reject corrupted canonical records, old seeds, wrong occurrences, duplicate/unknown fields, stale prior/current values and invalid type/unit/bounds, while preserving exact scalar bytes and unrelated fields.


select_fields(seed, CheckpointDraft) is the explicit public-to-private proposal mapper. It checks exact seed/cut and one concrete occurrence before invoking ScalarSelection. It cannot accept an old CampaignDraft or grant SQL winner authority. Request/response provenance is established separately through the response journal.
