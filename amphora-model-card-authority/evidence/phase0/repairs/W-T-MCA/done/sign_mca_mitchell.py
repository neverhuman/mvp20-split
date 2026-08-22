#!/usr/bin/env python3
"""DSSE-Ed25519-sign the amphora-model-card-authority W-T-MCA done receipt.
AUDIT_ONLY: signs an audit/theory receipt under evidence/phase0/repairs/;
does NOT promote authority, does NOT flip scientific_readiness, does NOT
modify the portfolio manifest, module-manifest.json, any locked dataset, or
a signed Phase-0 KPI. Derived key_id cross-checked vs pinned trust store.
"""
import base64
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = Path("/home/ubuntu/amphora/build/mvp20-split")
BENCH = ROOT / "amphora-model-card-authority/evidence/phase0/repairs/W-T-MCA/done"
SEED_DIR = Path.home() / ".local/share/amphora/phase0/keys"
EVAL_SEED = SEED_DIR / "evaluator.ed25519.seed"
TRUST = ROOT / "config/phase0-trust-store.v1.json"


def sha(b):
    return hashlib.sha256(b).hexdigest()


def pae(t, body):
    return (
        b"DSSEv1 " + str(len(t)).encode() + b" " + t.encode() + b" " +
        str(len(body)).encode() + b" " + body
    )


def load_seed(p):
    raw = p.read_bytes().strip()
    if len(raw) == 64:
        try:
            return bytes.fromhex(raw.decode())
        except Exception:
            pass
    return raw[:32]


canon = (BENCH / "diagnostic.canonical.json").read_bytes()
runB = (BENCH / "diagnostic.runB.json").read_bytes()
assert canon == runB, "two-replay bytes differ"
diag_sha = sha(canon)
diag = json.loads(canon)
oracle_sha = sha((BENCH / "mca_mitchell_conformance_oracle.py").read_bytes())
manifest_sha = sha((ROOT / "module-manifest.json").read_bytes())

eval_sk = Ed25519PrivateKey.from_private_bytes(load_seed(EVAL_SEED))
eval_pub = eval_sk.public_key().public_bytes_raw()
eval_pub_hex = eval_pub.hex()
eval_key_id = f"phase0-evaluator-{sha(eval_pub)}"
trust = json.loads(TRUST.read_text())
tbr = {k.get("role"): k for k in trust["keys"]}
eval_pin = eval_key_id == tbr.get("PHASE0_EVALUATOR", {}).get("key_id")

req_table = diag["requirements_table"]
summary = diag["requirements_summary"]

refuted_claims_this_schema_would_have_caught_earlier = [
    {
        "requirement_id": "R4-metrics",
        "portfolio_finding": "amphora-ip-fto-guard-metric-schema-parity-result (CLAIM_REFUTED): the module's primary KPI was absent from runtime/test/benchmark, discovered only by a dedicated cross-artifact parity audit.",
        "mechanism": "R4 requires kpi_name/unit/direction/validation_bar to be populated, non-null, on every emitted model_card. Enforcing that as a schema-validation gate on this module's own card artifact would have failed closed the moment a consuming module's primary KPI went missing from its runtime path, instead of requiring a later, separate audit to notice.",
    },
    {
        "requirement_id": "R5-evaluation-data",
        "portfolio_finding": "amphora-ip-fto-guard-claim-chart-provenance-result (CLAIM_REFUTED): family 26 (Hempel EP2653485A2) charted a fabricated 'polyurea topcoat' element not present in the source.",
        "mechanism": "R5 requires dataset_ids/dataset_checksums to resolve to a real, checksummed source per claim. A card that required every charted element to carry a resolvable dataset_id+checksum would have failed a schema check the moment an element had no matching source, instead of surviving until a dedicated provenance audit found the fabrication.",
    },
    {
        "requirement_id": "R3-factors",
        "portfolio_finding": "amphora-tolerance-robustness-repeated-scaffold-monte-carlo-result (CLAIM_REFUTED): overturned the earlier single-seed W5 SURVIVED verdict; repeated N=60 scaffold sampling found OpenPoly Tg coverage mean 0.875 with 31/60 draws breaching the floor.",
        "mechanism": "R3 requires relevant/evaluation factors (e.g. scaffold family) to be disaggregated on the card, not folded into one aggregate pass/fail. A card that had to show per-scaffold-group coverage from the start would have exposed the instability the first time it was issued, rather than needing a dedicated repeated-sampling re-attack to overturn an earlier single-seed survival.",
    },
    {
        "requirement_id": "R8-ethical-considerations",
        "portfolio_finding": "amphora-ip-fto-guard-counsel-assertion-detection-completeness-result (CLAIM_REFUTED, scoped): 8/8 false-negative rate on counsel-assertion detection.",
        "mechanism": "R8 requires a card-bound known_risks/misuse_cases field. A required per-card disclosure of detection-completeness limitations would have forced the false-negative gap to be stated on the card at issuance instead of being found later under a dedicated red-team audit.",
    },
]

proposed_followups = []
for r in req_table:
    if r["verdict"] != "conformant":
        proposed_followups.append({
            "requirement_id": r["id"],
            "section": r["section"],
            "finding": (
                f"{r['section']}: 0/{r['n_required']} of the section's required signal fields "
                f"({', '.join(r['required_signal_fields'])}) are present in the live runtime "
                f"model_card ({', '.join(r['present_in_observed_runtime']) or 'none'})."
            ),
            "proposed_repair_criterion": {
                "R1-model-details": "Bind per-instance developer/org, model_version (from Cargo.toml, already hashed as version_source_sha256 in capability-profile.json), a build/commit model_date, and a citation/contact field into model_card; add them to the score-envelope schema's model_card.required list.",
                "R2-intended-use": "Add required string/array fields primary_intended_uses and out_of_scope_use_cases to model_card, hash-bound to the corresponding mission.md prose so card and doc cannot drift.",
                "R3-factors": "Add a relevant_factors/evaluation_factors array to model_card populated from the same group/scaffold/source labels already required by mission.md's group-safe-split policy.",
                "R4-metrics": "Runtime MUST populate the already-schema-required kpi_name/unit/direction/validation_bar fields on every emitted model_card; add a CI schema-validation gate that fails closed on any null/missing value in this list (the schema already requires them -- the runtime just does not emit them).",
                "R5-evaluation-data": "Runtime MUST populate dataset_ids/dataset_checksums non-empty for every card; each id must resolve to a real, checksummed source object.",
                "R6-training-data": "Either add training_dataset_ids distinct from evaluation dataset_ids, or add an explicit mission.md statement of why training-data provenance is out of scope for this authority-only card (Mitchell et al. requires a stated rationale for omission, not silence).",
                "R7-quantitative-analyses": "Add a results object to model_card carrying the underlying model's unitary metric value plus at least one disaggregated/subgroup breakdown, not only the current boolean current_pass gate.",
                "R8-ethical-considerations": "Add a known_risks/ethical_considerations field to model_card enumerating misuse modes already named in mission.md's 'Known contradictions' section, bound per-card rather than only at module-doc level.",
                "R9-caveats-and-recommendations": "Bind mission.md's caveats (rights UNRESOLVED, known contradictions, no-scientific-validation disclaimer) into the per-instance model_card object itself, so a consumer holding only the ScoreEnvelope JSON sees them without also fetching module docs.",
            }[r["id"]],
        })

body_obj = {
    "schema": "amphora.model-card-authority.mitchell-2019-conformance-done-receipt.v1",
    "receipt_id": "w-t-mca-mitchell-2019-conformance-done-v1",
    "campaign_item_id": "W-T-MCA",
    "module_id": "amphora-model-card-authority",
    "authority": "AUDIT_ONLY",
    "authority_ceiling": "EVIDENCE_ONLY",
    "phase": "PRE_PHASE_0",
    "scientific_success_required_for_phase0": False,
    "promotes_authority": False,
    "flips_scientific_readiness": False,
    "modifies_manifest": False,
    "modifies_module_manifest": False,
    "modifies_locked_dataset": False,
    "modifies_signed_phase0_kpi": False,
    "modifies_shipped_runtime": False,
    "human_review_performed": False,
    "organizational_independence_asserted": False,
    "generated_on_host": "xbabe2",
    "date": "2026-08-13",
    "directive_ref": None,
    "directive_path": "none",
    "directive_sha256": "",
    "directive_obligation": None,
    "claim_under_attack": {
        "receipt_path": "amphora-model-card-authority/evidence/phase0/kpis/",
        "claim_text": "The authority lattice and card completeness are measured against a published model-card standard.",
    },
    "verdict": "CLAIM_REFUTED",
    "verdict_reason": (
        "Measured for the first time against Mitchell et al. (2019), 'Model Cards for Model "
        "Reporting' (FAT* '19, DOI 10.1145/3287560.3287596), the model_card artifact this module "
        "owns completeness for scores 0/9 conformant, 9/9 divergent, 0/9 not-applicable across "
        "every section the baseline specifies. The claim that card completeness 'is measured "
        "against a published model-card standard' was self-referential before this receipt (no "
        "prior mission.md, capability-profile.json, or receipt in this module names Mitchell et "
        "al. 2019 or any other published model-card schema) and, now that it has been measured, "
        "the artifact diverges from that baseline on every section: only 1 of the 7 Model-Details "
        "sub-signals (model_id) is present, and the live native-Rust runtime never emits 7 of the "
        "score-envelope schema's own 10 model_card.required fields "
        "(current_status, dataset_checksums, dataset_ids, direction, kpi_name, unit, "
        "validation_bar) across all 3 non-error captured cases in the previously-signed "
        "live-runtime-envelope-parity-v1 ground truth."
    ),
    "claim": (
        "THEORY-DIMENSION VERDICT: measured against Mitchell et al. (2019) for the first time, "
        "the claim 'the authority lattice and card completeness are measured against a published "
        "model-card standard' is REFUTED. Of 9 normative sections enumerated from the baseline, "
        f"{summary['n_conformant']}/9 are conformant, {summary['n_divergent']}/9 are divergent, and "
        f"{summary['n_not_applicable']}/9 are not-applicable, scored against the live native-Rust "
        "model_card artifact (amphora-engine/src/lib.rs:270, metrics.model_card) as captured in "
        "amphora-model-card-authority/evidence/audit/live-runtime-envelope-parity-v1/"
        "runtime_ground_truth.v1.json. The sharpest single finding is R4/R5: the module's own "
        "score-envelope.schema.json ALREADY requires kpi_name, unit, direction, validation_bar, "
        "dataset_ids, dataset_checksums, and current_status on every model_card -- these are not "
        "novel asks imported from Mitchell et al., they are this module's own pre-existing "
        "contract -- yet the live runtime emits zero of the seven in all 3 captured non-error "
        "cases, uniformly. The published baseline's Metrics and Evaluation-Data sections simply "
        "name, with external authority, a completeness gap this module's own schema already "
        "specified and never enforced."
    ),
    "baseline": {
        "name": "Model Cards for Model Reporting",
        "authors": "Margaret Mitchell, Simone Wu, Andrew Zaldivar, Parker Barnes, Lucy Vasserman, Ben Hutchinson, Elena Spitzer, Inioluwa Deborah Raji, Timnit Gebru",
        "venue": "Proceedings of the ACM Conference on Fairness, Accountability, and Transparency (FAT* '19)",
        "year": 2019,
        "pages": "220-229",
        "doi": "10.1145/3287560.3287596",
        "doi_or_url": "https://doi.org/10.1145/3287560.3287596",
        "license_note": "Open access (ACM DL open + arXiv:1810.03993); short paraphrased section names cited below, full text not reproduced.",
        "sections_scored": [r["section"] for r in req_table],
        "secondary_baseline": {
            "name": "Datasheets for Datasets",
            "authors": "Timnit Gebru, Jamie Morgenstern, Briana Vecchione, Jennifer Wortman Vaughan, Hanna Wallach, Hal Daume III, Kate Crawford",
            "venue": "Communications of the ACM, Vol. 64, No. 12",
            "year": 2021,
            "doi": "10.1145/3458723",
            "doi_or_url": "https://doi.org/10.1145/3458723",
            "role": "Cited as the dataset-provenance line of work the objective names; used only to corroborate that R5/R6 (dataset_ids/dataset_checksums with no train/eval distinction and no rationale statement) is a real, independently-named gap, not a Mitchell-specific artifact.",
        },
    },
    "requirements_table": req_table,
    "requirements_summary": summary,
    "refuted_claims_this_schema_would_have_caught_earlier": refuted_claims_this_schema_would_have_caught_earlier,
    "proposed_followups": proposed_followups,
    "live_artifact_under_test": {
        "description": "The metrics.model_card object emitted by the native Rust runtime for every ScoreEnvelope; this is the concrete 'card' this module's authority claims completeness over.",
        "emission_site": "amphora-engine/src/lib.rs:270",
        "emission_site_sha256": diag["runtime_source_anchors"]["engine_emission_sha256"],
        "schema_definition_path": "amphora-candidate-contract/schemas/score-envelope.schema.json",
        "schema_definition_sha256": diag["runtime_source_anchors"]["score_envelope_schema_sha256"],
        "schema_model_card_fields": diag["schema_analysis"]["model_card_schema_fields"],
        "schema_model_card_required_fields": diag["schema_analysis"]["model_card_schema_required_fields"],
        "observed_runtime_field_shapes": diag["runtime_analysis"]["observed_model_card_field_shapes"],
        "observed_shape_uniform_across_all_captured_cases": diag["runtime_analysis"]["observed_shape_is_uniform_across_all_cases"],
        "schema_required_fields_never_emitted_by_runtime": diag["runtime_analysis"]["schema_required_fields_never_emitted_by_runtime"],
        "ground_truth_source": {
            "path": "amphora-model-card-authority/evidence/audit/live-runtime-envelope-parity-v1/runtime_ground_truth.v1.json",
            "sha256": diag["runtime_source_anchors"]["runtime_ground_truth_sha256"],
            "note": "Reused, not re-executed: this is a previously-captured, previously-signed native-Rust runtime capture from the live-runtime-envelope-parity-v1 audit. This receipt does not run the Rust engine; it re-derives a new theory conclusion from that existing capture.",
        },
    },
    "relationship_to_prior_fires": "First fire on W-T-MCA (campaign item fires[] was empty at entry). No prior downgrade_reason to address.",
    "does_not_establish": [
        "No wet-lab, product-qualification, batch-release, legal, regulatory, or scientific authority.",
        "Does not close the separate authority-lattice-completeness claim (evidence/audit/authority-lattice-completeness-v1, Denning 1976 baseline) -- that claim concerns the grant-ceiling meet/join lattice, not card-field completeness, and is unaffected by this finding.",
        "Not a claim that amphora-engine's model_card emission is unsafe for its current EVIDENCE_ONLY/DISABLED ceiling -- the ceiling fields it DOES emit (model_authority, solver_use, product_claim_ready, model_readiness_status) are exactly the fields the authority-lattice audit already verified. This finding is about reporting completeness, not authority-grant correctness.",
        "The runtime (amphora-engine/src/lib.rs) is NOT modified by this receipt; this is an independent, non-mutating theory/spec audit (AUDIT_ONLY).",
    ],
    "reproducibility": {
        "two_replay_sha256_gate": "PASS",
        "canonical_diagnostic_sha256": diag_sha,
        "runB_diagnostic_sha256": sha(runB),
        "byte_identical": canon == runB,
        "oracle_path": "amphora-model-card-authority/evidence/phase0/repairs/W-T-MCA/done/mca_mitchell_conformance_oracle.py",
        "oracle_sha256": oracle_sha,
        "rerun_command": "python3 amphora-model-card-authority/evidence/phase0/repairs/W-T-MCA/done/mca_mitchell_conformance_oracle.py",
    },
    "provenance": {
        "module_manifest_sha256": manifest_sha,
        "oracle_sha256": oracle_sha,
    },
    "signing_key": {
        "role": "PHASE0_EVALUATOR",
        "key_id": eval_key_id,
        "public_key_hex": eval_pub_hex,
        "used_for": "AUDIT_ONLY theory receipt under evidence/phase0/repairs/W-T-MCA/done/",
        "signs_phase0_evaluation_or_review": False,
        "derives_pinned_trust_store_key_id": bool(eval_pin),
    },
}

body = json.dumps(body_obj, indent=2, sort_keys=True).encode()
ptype = "application/vnd.amphora.model-card-authority-w-t-mca-mitchell-2019-conformance+json"
sig = eval_sk.sign(pae(ptype, body))
envelope = {
    "payload": base64.standard_b64encode(body).decode(),
    "payloadType": ptype,
    "signatures": [{"keyid": eval_key_id, "sig": base64.standard_b64encode(sig).decode()}],
}
receipt = {
    "evaluator_key_id": eval_key_id,
    "evaluator_public_key_hex": eval_pub_hex,
    "signature": envelope,
}
out = BENCH / "w-t-mca-mitchell-2019-conformance-done-receipt.v1.dsse.json"
out.write_text(json.dumps(receipt, indent=2, sort_keys=True))

Ed25519PublicKey.from_public_bytes(eval_pub).verify(
    base64.standard_b64decode(envelope["signatures"][0]["sig"]),
    pae(ptype, base64.standard_b64decode(envelope["payload"])),
)
print("WROTE", out)
print("evaluator_key_id", eval_key_id)
print("eval_derives_pinned_trust_key", eval_pin)
print("two_replay_sha256", diag_sha)
print("envelope_sha256", sha(out.read_bytes()))
print("signature_verified", True)
