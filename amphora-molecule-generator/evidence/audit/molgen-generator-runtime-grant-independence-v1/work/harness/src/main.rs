// W1 adversarial probe: amphora-molecule-generator "roadmap-diagnostic
// quarantine" claim (docs/mission.md "Honest current state" +
// evidence/phase0/kpis/molecule-generator-roadmap-diagnostic-quarantine-kpi.v1.json).
//
// The claim: "Runtime is a pure roadmap-diagnostic quarantine: never invokes
// RDKit, never emits a proposal, always returns INSUFFICIENT_INPUT ...
// proposal_count=0." The Phase-0 KPI receipt scopes this narrowly to
// generator_result(candidate, context), which IS a hardcoded, input-independent
// stub. But the same crate also ships a live, wired-to-the-CLI generation path:
// amphora_molecule_capabilities::generate_authorized ->
// amphora_engine::EnginePool::generate_compounds -> amphora-cli compound
// campaigns (amphora-cli/src/compound.rs::run_campaign_from_v1) -- a REAL
// production path that DOES invoke the pinned RDKit FFI and DOES emit
// GeneratedMoleculeProposalV1 records, gated only by a Phase-0
// EngineEvidenceContextV3 runtime grant (VerifiedAuditModuleInputV1).
//
// This harness attacks that boundary directly:
//   TEST A (real deployed root, no forgery): construct a real EnginePool
//   against the ACTUAL mvp20-split repo root and call generate_compounds with
//   a real, well-formed generation request. Confirms, by execution (not
//   static reading), that the currently deployed engine has zero runtime
//   grant files anywhere and therefore fails closed right now.
//
//   TEST B (positive control on the runtime-grant verifier): build a fully
//   well-formed VerifiedAuditModuleInputV1 for GENERATOR_ID in-memory
//   (synthetic corpus/dataset/rights, all clearly example.invalid / TEST-ONLY,
//   exactly the pattern amphora-core's own unit tests use) with a REAL
//   epoxy-amine ring-opening reaction SMARTS, and drive it through the SAME
//   EngineEvidenceContextV3::verify() + generate_authorized() production
//   functions used by the CLI.
//     B1 (defect planted): sign the fixture with only 2 distinct identities
//     (reusing one scratch key for two of the three required roles) --
//     mirroring exactly the number of Phase-0 keys this cron / the whole
//     portfolio's config/phase0-trust-store.v1.json actually holds today.
//     Expect: rejected with Independence error, generate_authorized never
//     reached.
//     B2 (control): byte-identical fixture, but signed with 3 genuinely
//     distinct scratch identities. Expect: verify() succeeds and
//     generate_authorized() returns a non-empty, real RDKit-derived proposal
//     -- proving the checker actually discriminates the planted defect
//     rather than rejecting everything.

use std::collections::BTreeMap;
use std::fs;

use amphora_core::{
    AuditInputBindingKindV1, DecisionUse, EngineEvidenceContextV3, EvaluationReceiptV1,
    EvidenceTier, IndependentReviewReceiptV1, MoleculeEvidenceError, PromotionPolicyV1,
    PromotionRuleV1, RightsRecordV1, SignedModelArtifactV1, TrustStore, VerifiedAuditModuleInputV1,
    ENGINE_EVIDENCE_CONTEXT_V3_SCHEMA, EVALUATION_RECEIPT_SCHEMA,
    INDEPENDENT_REVIEW_RECEIPT_SCHEMA, PROMOTION_POLICY_SCHEMA, SIGNED_MODEL_ARTIFACT_SCHEMA,
    VERIFIED_AUDIT_MODULE_INPUT_SCHEMA,
};
use amphora_core::{stable_hash, CampaignGenerationRequestV1};
use amphora_engine::EnginePool;
use amphora_molecule_capabilities::{generate_authorized, ReactionGrammarV1, GENERATOR_ID};
use ed25519_dalek::SigningKey;
use serde_json::{json, Value};
use sha2::{Digest, Sha256};

const REPO_ROOT: &str = "/home/ubuntu/amphora/build/mvp20-split";

fn raw_sha256(bytes: &[u8]) -> String {
    let mut digest = Sha256::new();
    digest.update(bytes);
    format!("{:x}", digest.finalize())
}

fn key(seed: u8) -> SigningKey {
    SigningKey::from_bytes(&[seed; 32])
}

/// Build a fully well-formed GENERATOR_ID runtime-grant fixture. `signers`
/// gives the (model, evaluation, review) SigningKeys -- pass the same key
/// twice to plant an identity-collapse defect.
fn build_grant(
    signers: (&SigningKey, &SigningKey, &SigningKey),
    registry_manifest_sha256: &str,
    review_key_id: &str,
) -> (VerifiedAuditModuleInputV1, PromotionPolicyV1, String) {
    let (model_key, evaluation_key, review_key) = signers;

    let grammar_unsigned = ReactionGrammarV1 {
        grammar_id: "epoxy-amine-ring-opening-addition-v1".into(),
        reaction_family: "epoxy-amine-addition".into(),
        reaction_smarts: "[C:1]1[O:2][C:3]1.[#7X3;H1,H2:4]>>[O:2][C:1][C:3][N:4]".into(),
        source_reaction_ids: vec!["epoxide-amine-ring-opening-march-2007-16-13".into()],
        source_dataset_ids: vec!["scratch-test-fixture-w1-not-real".into()],
        applicability_constraints: BTreeMap::from([("reactant_count".into(), json!(2))]),
        grammar_sha256: String::new(),
    };
    let grammar_sha256 = stable_hash(&serde_json::to_value(&grammar_unsigned).unwrap());
    let grammar = ReactionGrammarV1 {
        grammar_sha256: grammar_sha256.clone(),
        ..grammar_unsigned
    };

    let corpus = json!({"schema": "scratch-corpus.v1", "grammars": [grammar]});
    let dataset = json!({"schema": "scratch-dataset.v1", "note": "W1 harness scratch fixture, not a real dataset"});
    let split = json!({"schema": "scratch-split.v1", "note": "no-fitting audit module, closed-form"});
    let benchmark_lock = json!({"schema": "scratch-benchmark-lock.v1", "note": "audit-only closed-form"});
    let raw_data_hashes: BTreeMap<String, String> =
        BTreeMap::from([("scratch-raw.v1".into(), stable_hash(&json!("scratch-raw-bytes")))]);
    let rights = vec![RightsRecordV1 {
        source_id: "w1-scratch-test-fixture".into(),
        license: "TEST-ONLY-NOT-A-REAL-LICENSE".into(),
        status: "ACCEPTED".into(),
        source_url: "https://example.invalid/w1-scratch-fixture".into(),
        restrictions: vec!["harness fixture only, never used outside this test".into()],
        eligible_for_derivatives: true,
    }];
    let claim_locks: BTreeMap<String, bool> = [
        "audit_only",
        "generated_molecules_unmade_unvalidated",
        "no_optimizer_authority",
        "not_a_synthesis_recommendation",
    ]
    .iter()
    .map(|k| (k.to_string(), true))
    .collect();

    let corpus_sha256 = stable_hash(&corpus);
    let dataset_sha256 = stable_hash(&dataset);
    let split_sha256 = stable_hash(&split);
    let benchmark_lock_sha256 = stable_hash(&benchmark_lock);
    let raw_data_manifest_sha256 = stable_hash(&serde_json::to_value(&raw_data_hashes).unwrap());
    let rights_manifest_sha256 = stable_hash(&serde_json::to_value(&rights).unwrap());
    let claim_locks_sha256 = stable_hash(&serde_json::to_value(&claim_locks).unwrap());
    let applicability_domain = json!({
        "allowed_roles": ["hardener"],
        "coating_domain_only": true,
        "note": "W1 scratch fixture applicability domain"
    });

    let artifact = json!({
        "module_id": GENERATOR_ID,
        "reaction_grammars": [grammar],
        "applicability_domain": applicability_domain,
        "parent_hashes": {
            "corpus": corpus_sha256,
            "dataset": dataset_sha256,
            "split": split_sha256,
            "benchmark_lock": benchmark_lock_sha256,
            "raw_data_manifest": raw_data_manifest_sha256,
            "rights_manifest": rights_manifest_sha256,
            "claim_locks": claim_locks_sha256,
        }
    });
    let mut module_artifact = SignedModelArtifactV1 {
        schema: SIGNED_MODEL_ARTIFACT_SCHEMA.into(),
        module_id: GENERATOR_ID.into(),
        artifact_sha256: stable_hash(&artifact),
        artifact,
        signature: None,
    };
    module_artifact.sign("w1-model-signer", model_key).unwrap();
    let module_artifact_sha256 = stable_hash(&serde_json::to_value(&module_artifact).unwrap());

    let promotion_policy_id = "w1-scratch-audit-only-policy";
    // promotion_policy references the evaluation receipt hash, which we do not
    // know yet; build policy AFTER the evaluation receipt is signed, below.

    let mut evaluation_receipt = EvaluationReceiptV1 {
        schema: EVALUATION_RECEIPT_SCHEMA.into(),
        receipt_id: "w1-scratch-evaluation".into(),
        module_id: GENERATOR_ID.into(),
        registry_manifest_hash: registry_manifest_sha256.into(),
        registry_owned_identity: true,
        artifact_hashes: BTreeMap::from([
            ("module_artifact".into(), module_artifact_sha256.clone()),
            ("corpus".into(), corpus_sha256.clone()),
            ("dataset".into(), dataset_sha256.clone()),
            ("split".into(), split_sha256.clone()),
            ("benchmark_lock".into(), benchmark_lock_sha256.clone()),
            ("raw_data_manifest".into(), raw_data_manifest_sha256.clone()),
            ("rights_manifest".into(), rights_manifest_sha256.clone()),
            ("claim_locks".into(), claim_locks_sha256.clone()),
        ]),
        benchmark_lock_hash: benchmark_lock_sha256.clone(),
        metrics: BTreeMap::from([("generation_smoke_test".into(), json!(true))]),
        confidence_intervals: BTreeMap::new(),
        evidence_tier: EvidenceTier::SyntheticDiagnostic,
        decision_use_ceiling: DecisionUse::AuditOnly,
        passed: true,
        claim_locks: claim_locks.clone(),
        applicability_limits: vec!["W1 scratch harness fixture only".into()],
        signature: None,
    };
    evaluation_receipt
        .sign("w1-evaluation-signer", evaluation_key)
        .unwrap();
    let evaluation_receipt_sha256 = stable_hash(&serde_json::to_value(&evaluation_receipt).unwrap());

    let mut review_receipt = IndependentReviewReceiptV1 {
        schema: INDEPENDENT_REVIEW_RECEIPT_SCHEMA.into(),
        receipt_id: "w1-scratch-review".into(),
        module_id: GENERATOR_ID.into(),
        registry_manifest_hash: registry_manifest_sha256.into(),
        evaluation_receipt_sha256: evaluation_receipt_sha256.clone(),
        model_artifact_sha256: module_artifact_sha256.clone(),
        benchmark_lock_sha256: benchmark_lock_sha256.clone(),
        reviewer_id: "w1-scratch-reviewer".into(),
        reviewer_independent: true,
        independent_transfer_passed: true,
        primary_improvement_confirmed: true,
        verifier_reversed_primary: false,
        claim_locks: claim_locks.clone(),
        applicability_limits: vec!["W1 scratch harness fixture only".into()],
        signature: None,
    };
    review_receipt.sign(review_key_id, review_key).unwrap();

    let promotion_policy = PromotionPolicyV1 {
        schema: PROMOTION_POLICY_SCHEMA.into(),
        policy_id: promotion_policy_id.into(),
        registry_manifest_hash: registry_manifest_sha256.into(),
        default_use: DecisionUse::AuditOnly,
        rules: vec![PromotionRuleV1 {
            module_id: GENERATOR_ID.into(),
            receipt_hash: evaluation_receipt_sha256,
            maximum_use: DecisionUse::AuditOnly,
        }],
    };
    let promotion_policy_sha256 = stable_hash(&serde_json::to_value(&promotion_policy).unwrap());

    let input = VerifiedAuditModuleInputV1 {
        schema: VERIFIED_AUDIT_MODULE_INPUT_SCHEMA.into(),
        module_id: GENERATOR_ID.into(),
        module_artifact_sha256,
        corpus_sha256,
        dataset_sha256,
        split_sha256,
        benchmark_lock_sha256,
        raw_data_manifest_sha256,
        rights_manifest_sha256,
        claim_locks_sha256,
        promotion_policy_sha256: promotion_policy_sha256.clone(),
        required_toolkit_version: amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION.into(),
        applicability_domain,
        claim_locks,
        module_artifact,
        corpus,
        dataset,
        split,
        benchmark_lock,
        raw_data_hashes,
        rights,
        evaluation_receipt,
        independent_review_receipt: review_receipt,
    };

    (input, promotion_policy, promotion_policy_sha256)
}

fn run_case(
    label: &str,
    signers: (&SigningKey, &SigningKey, &SigningKey),
    review_key_id: &str,
) -> Value {
    let manifest_bytes = fs::read(format!("{REPO_ROOT}/module-manifest.json")).unwrap();
    let registry_manifest_sha256 = raw_sha256(&manifest_bytes);

    let (grant, promotion_policy, promotion_policy_sha256) =
        build_grant(signers, &registry_manifest_sha256, review_key_id);

    let context = EngineEvidenceContextV3 {
        schema: ENGINE_EVIDENCE_CONTEXT_V3_SCHEMA.into(),
        registry_manifest_sha256: registry_manifest_sha256.clone(),
        promotion_policy_sha256,
        promotion_policy,
        molecule_models: BTreeMap::new(),
        phase0_runtime_grants: BTreeMap::from([(GENERATOR_ID.to_string(), grant)]),
    };

    let mut trust_store = TrustStore::default();
    for (id, k) in [
        ("w1-model-signer", signers.0),
        ("w1-evaluation-signer", signers.1),
        (review_key_id, signers.2),
    ] {
        // duplicate key_id insert would error; only insert each id once
        let _ = trust_store.insert(id, k.verifying_key().to_bytes());
    }

    let verify_result = context.verify(
        &trust_store,
        &registry_manifest_sha256,
        amphora_rdkit_ffi::REQUIRED_RDKIT_VERSION,
    );

    match verify_result {
        Err(error) => json!({
            "case": label,
            "verify_ok": false,
            "verify_error": format!("{error}"),
            "is_independence_error": matches!(error, MoleculeEvidenceError::Independence),
            "generation_attempted": false,
        }),
        Ok(validated) => {
            let request_id = format!("w1-{label}-generation-request");
            let parent_structures = vec!["C1CO1".to_string(), "NCCN".to_string()];
            let requested_role = "hardener";
            let reaction_family = "epoxy-amine-addition";
            let deterministic_seed: u64 = 20260816;

            let parent_facts = parent_structures
                .iter()
                .map(|s| amphora_rdkit_ffi::molecule_facts(s))
                .collect::<Result<Vec<_>, _>>();
            let parent_facts = match parent_facts {
                Ok(f) => f,
                Err(e) => {
                    return json!({
                        "case": label,
                        "verify_ok": true,
                        "generation_attempted": true,
                        "generation_error": format!("parent molecule_facts failed: {e}"),
                    })
                }
            };
            let request_value = json!({
                "request_id": request_id,
                "parent_structures": parent_structures,
                "requested_role": requested_role,
                "reaction_family": reaction_family,
                "deterministic_seed": deterministic_seed,
            });
            let parent_facts_value = serde_json::to_value(&parent_facts).unwrap();

            let authorization = validated.authorize_runtime_grant(
                GENERATOR_ID,
                &request_id,
                &stable_hash(&request_value),
                AuditInputBindingKindV1::MoleculeFacts,
                &stable_hash(&parent_facts_value),
            );
            let Some(authorization) = authorization else {
                return json!({
                    "case": label,
                    "verify_ok": true,
                    "generation_attempted": true,
                    "generation_error": "authorize_runtime_grant returned None",
                });
            };

            let result = generate_authorized(
                &request_id,
                &parent_structures,
                requested_role,
                reaction_family,
                deterministic_seed,
                &authorization,
            );
            match result {
                Ok(proposals) => json!({
                    "case": label,
                    "verify_ok": true,
                    "generation_attempted": true,
                    "generation_succeeded": true,
                    "proposal_count": proposals.len(),
                    "rdkit_invoked": true,
                    "sample_product_smiles": proposals.first().map(|p| p.product_structure.clone()),
                    "sample_reactive_amine_hydrogen_count": proposals.first().map(|p| p.molecule_facts.reactive_amine_hydrogen_count),
                }),
                Err(error) => json!({
                    "case": label,
                    "verify_ok": true,
                    "generation_attempted": true,
                    "generation_succeeded": false,
                    "generation_error": format!("{error}"),
                }),
            }
        }
    }
}

fn test_a_real_deployed_root() -> Value {
    let evidence_marker = format!("{REPO_ROOT}/.amphora/evidence/engine-evidence-context.v1.json");
    let marker_exists = std::path::Path::new(&evidence_marker).exists();

    let engine = EnginePool::new(REPO_ROOT, 1);
    let engine = match engine {
        Ok(e) => e,
        Err(error) => {
            return json!({
                "test": "A_real_deployed_root",
                "engine_pool_constructed": false,
                "error": format!("{error}"),
            })
        }
    };
    let request = CampaignGenerationRequestV1 {
        request_id: "w1-real-root-probe".into(),
        parent_structures: vec!["C1CO1".into(), "NCCN".into()],
        requested_role: "hardener".into(),
        reaction_family: "epoxy-amine-addition".into(),
    };
    let result = engine.generate_compounds(&request, 20260816);
    json!({
        "test": "A_real_deployed_root",
        "engine_pool_constructed": true,
        "evidence_context_marker_file_exists": marker_exists,
        "generate_compounds_ok": result.is_ok(),
        "generate_compounds_error": result.err().map(|e| format!("{e}")),
    })
}

fn main() {
    let a = test_a_real_deployed_root();

    let k_model = key(101);
    let k_eval = key(102);
    let k_review_distinct = key(103);

    // B1: label-identity gap -- same underlying key (k_eval) signs both the
    // evaluation_receipt (key_id "w1-evaluation-signer") and the
    // independent_review_receipt, but registered/asserted under a DIFFERENT
    // key_id label ("w1-review-signer"). Only 2 real distinct private keys
    // are in play, matching what this cron actually holds (evaluator +
    // internal-reviewer). Independence is checked purely on the 3 returned
    // key_id strings.
    let b1_two_keys_distinct_labels = run_case(
        "B1_two_real_keys_but_three_distinct_labels",
        (&k_model, &k_eval, &k_eval),
        "w1-review-signer",
    );

    // B2: control -- 3 genuinely distinct underlying keys, 3 distinct labels.
    let b2_three_keys_three_labels = run_case(
        "B2_three_real_keys_three_labels_control",
        (&k_model, &k_eval, &k_review_distinct),
        "w1-review-signer",
    );

    // C: honest same-label negative control -- same underlying key AND the
    // same key_id label reused for both evaluation and review. This is the
    // textbook "same signer" case the Independence check exists to catch.
    let c_same_key_same_label_must_fail = run_case(
        "C_same_key_same_label_negative_control",
        (&k_model, &k_eval, &k_eval),
        "w1-evaluation-signer",
    );

    let report = json!({
        "test_a_real_deployed_root_fails_closed": a,
        "test_b1_two_real_keys_but_three_distinct_labels_SUCCEEDS": b1_two_keys_distinct_labels,
        "test_b2_three_real_keys_three_labels_control_SUCCEEDS": b2_three_keys_three_labels,
        "test_c_same_key_same_label_negative_control_MUST_FAIL": c_same_key_same_label_must_fail,
    });
    println!("{}", serde_json::to_string_pretty(&report).unwrap());
}
