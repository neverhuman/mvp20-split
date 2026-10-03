"""Publish/check deterministic Draft 2020-12 input and output schema artifacts."""

import argparse
import hashlib
import json
from pathlib import Path

import amphora_contracts_artifacts as artifact_contracts
import amphora_contracts_evidence as evidence_contracts
import amphora_contracts_graph_runtime as graph_runtime_contracts
import amphora_contracts_knowledge as knowledge_contracts
import amphora_contracts_research as research_contracts
import amphora_contracts_runtime as runtime_contracts
import amphora_contracts_solver_fixture as solver_fixture_contracts
import amphora_contracts_tools as tool_contracts
from amphora_contracts_campaigns import (
    ActivationPath,
    ArtifactMaterializeV4,
    ArtifactProjectV4,
    BindingPrimitiveDescriptor,
    CampaignDefinition,
    ExecutableCampaign,
    ExecutableCampaignV3,
    ExecutableCampaignV4,
    ExecutionPlan,
    ExecutionPlanV3,
    ExecutionPlanV4,
    PlanLock,
    PlanLockV3,
    PlanLockV4,
)
from amphora_contracts_commands import CommandIdentity
from amphora_contracts_core import ArtifactRef, Finding, SchemaRef, Scope
from amphora_contracts_tools import Completion, Invocation, ToolBinding, ToolDescriptor

ROOT = Path(__file__).absolute().parents[1]
MODELS = {
    "core.scope": Scope,
    "core.schema-ref": SchemaRef,
    "core.artifact-ref": ArtifactRef,
    "core.finding": Finding,
    "tools.binding": ToolBinding,
    "tools.descriptor": ToolDescriptor,
    "tools.invocation": Invocation,
    "tools.completion": Completion,
    "campaigns.definition": CampaignDefinition,
}
MODELS_V2 = {
    "campaigns.definition": ExecutableCampaign,
    "campaigns.execution-plan": ExecutionPlan,
    "campaigns.plan-lock": PlanLock,
    "campaigns.activation-path": ActivationPath,
    "graph-runtime.run-page": graph_runtime_contracts.GraphRunPageV2,
}
MODELS_V3 = {
    "graph-runtime.run-page": graph_runtime_contracts.GraphRunPageV3,
    "campaigns.definition": ExecutableCampaignV3,
    "campaigns.execution-plan": ExecutionPlanV3,
    "campaigns.plan-lock": PlanLockV3,
}
MODELS_V4 = {
    "campaigns.definition": ExecutableCampaignV4,
    "campaigns.execution-plan": ExecutionPlanV4,
    "campaigns.plan-lock": PlanLockV4,
    "campaigns.artifact-project": ArtifactProjectV4,
    "campaigns.artifact-materialize": ArtifactMaterializeV4,
    "campaigns.binding-primitive": BindingPrimitiveDescriptor,
}

for name, model in {
    "vocabulary": knowledge_contracts.DomainVocabulary,
    "proposal": knowledge_contracts.GraphChangeProposal,
    "proposal-status": knowledge_contracts.GraphProposalStatus,
    "authoring-profile": knowledge_contracts.GraphAuthoringProfile,
    "rebuild-request": knowledge_contracts.GraphRebuildRequest,
    "rebuild-status": knowledge_contracts.GraphRebuildStatus,
    "reasoning-rule-set": knowledge_contracts.ReasoningRuleSet,
    "reasoning-request": knowledge_contracts.ReasoningRequest,
    "reasoning-result": knowledge_contracts.ReasoningResult,
    "reasoning-status": knowledge_contracts.ReasoningStatus,
    "correct-reasoning-receipt": knowledge_contracts.CorrectReasoningReceipt,
    "select-reasoning-receipt": knowledge_contracts.SelectReasoningReceipt,
    "reasoning-publication-request": knowledge_contracts.ReasoningPublicationRequest,
    "reasoning-publication-status": knowledge_contracts.ReasoningPublicationStatus,
    "accepted-change": knowledge_contracts.AcceptedGraphChange,
    "change-decision": knowledge_contracts.GraphChangeDecision,
    "snapshot": knowledge_contracts.DomainGraphSnapshot,
    "head": knowledge_contracts.DomainHead,
    "entity": knowledge_contracts.DomainEntity,
    "assertion": knowledge_contracts.DomainAssertion,
    "question-link": knowledge_contracts.QuestionEvidenceLink,
    "grounding": knowledge_contracts.ClaimGrounding,
}.items():
    MODELS["knowledge." + name] = model

for name, model in {
    "source-revision": evidence_contracts.SourceRevision,
    "prepared-document": evidence_contracts.PreparedDocument,
    "prepared-source": evidence_contracts.PreparedSource,
    "observe-source-identity": evidence_contracts.ObserveSourceIdentity,
    "source-identity-observation": evidence_contracts.SourceIdentityObservation,
    "source-identity-status": evidence_contracts.SourceIdentityStatus,
    "source-rights-revision": evidence_contracts.SourceRightsRevision,
    "retain-prepared-source": evidence_contracts.RetainPreparedSource,
    "prepared-lab-record": evidence_contracts.PreparedLabRecord,
    "source-span": evidence_contracts.SourceSpan,
    "conversion-trace": evidence_contracts.ConversionTrace,
    "conversion-trace-ref": evidence_contracts.ConversionTraceRef,
}.items():
    MODELS["evidence." + name] = model

for name, model in {
    "material-state-revision": research_contracts.MaterialStateRevision,
    "experiment-definition": research_contracts.ExperimentDefinition,
    "observation-revision": research_contracts.ObservationRevision,
    "synthesis-profile": research_contracts.SynthesisProfile,
    "synthesis-assessment": research_contracts.SynthesisAssessment,
    "eligibility-profile": research_contracts.EligibilityProfile,
    "eligibility-assessment": research_contracts.EligibilityAssessment,
    "synthetic-evidence": research_contracts.SyntheticEvidenceRecord,
    "assessment-profile": research_contracts.EvidenceAssessmentProfile,
    "assessment-request": research_contracts.EvidenceAssessmentRequest,
    "assessment": research_contracts.EvidenceAssessment,
    "assessment-status": research_contracts.EvidenceAssessmentStatus,
    "correct-assessment-receipt": research_contracts.CorrectAssessmentReceipt,
    "select-assessment-receipt": research_contracts.SelectAssessmentReceipt,
    "assessment-publication-request": research_contracts.AssessmentPublicationRequest,
    "assessment-publication-status": research_contracts.AssessmentPublicationStatus,
    "candidate-revision": research_contracts.CandidateRevision,
    "resolve-identity": research_contracts.ResolveIdentity,
    "identity-resolution": research_contracts.IdentityResolution,
    "sample-identity": research_contracts.SampleIdentity,
    "question": research_contracts.ResearchQuestion,
    "evidence-need": research_contracts.EvidenceNeed,
}.items():
    MODELS["research." + name] = model

MODELS["commands.identity"] = CommandIdentity
for name, model in {
    "draft-save": graph_runtime_contracts.SaveDraft,
    "draft-command-receipt": graph_runtime_contracts.DraftCommandReceipt,
    "draft-validate": graph_runtime_contracts.ValidateDraft,
    "draft-revision": graph_runtime_contracts.DraftRevision,
    "draft-page": graph_runtime_contracts.DraftPage,
    "draft-validation": graph_runtime_contracts.DraftValidation,
    "draft-admission": graph_runtime_contracts.AdmitDraft,
    "definition-universe": graph_runtime_contracts.DefinitionUniverse,
    "definition-schema": graph_runtime_contracts.DefinitionSchema,
    "successor-proposal": graph_runtime_contracts.SuccessorProposal,
    "carry-sources": graph_runtime_contracts.CarrySources,
    "successor-lineage": graph_runtime_contracts.SuccessorLineage,
    "snapshot-page": graph_runtime_contracts.GraphSnapshotPage,
    "scope-page": graph_runtime_contracts.GraphScopePage,
    "topology-page": graph_runtime_contracts.GraphTopologyPage,
    "view-catalog": graph_runtime_contracts.GraphViewCatalog,
    "node-detail": graph_runtime_contracts.GraphNodeDetail,
    "value-page": graph_runtime_contracts.GraphValuePage,
    "invalidation-page": graph_runtime_contracts.GraphInvalidationPage,
}.items():
    MODELS["graph-runtime." + name] = model
for name, model in {
    "config": solver_fixture_contracts.SolverConfig,
    "proposal-batch": solver_fixture_contracts.ProposalBatch,
    "state": solver_fixture_contracts.SolverState,
    "selection": solver_fixture_contracts.Selection,
    "score-request": solver_fixture_contracts.ScoreRequest,
    "score-result": solver_fixture_contracts.ScoreResult,
    "retain-input": solver_fixture_contracts.RetainInput,
}.items():
    MODELS["solver-fixture." + name] = model
for name, model in {
    "admit-run": graph_runtime_contracts.AdmitGraphRun,
    "advance": graph_runtime_contracts.AdvanceGraph,
    "run-page": graph_runtime_contracts.GraphRunPage,
    "domain-receipt": graph_runtime_contracts.DomainReceipt,
    "receipt-chain-ref": graph_runtime_contracts.ReceiptChainRef,
    "receipt-revision-ref": graph_runtime_contracts.ReceiptRevisionRef,
    "receipt-correction": graph_runtime_contracts.ReceiptCorrection,
    "receipt-correction-view": graph_runtime_contracts.ReceiptCorrectionView,
    "wait-expectation": graph_runtime_contracts.WaitExpectation,
    "submit-receipt": graph_runtime_contracts.SubmitDomainReceipt,
    "wait-closure": graph_runtime_contracts.WaitClosure,
    "wait-observation": graph_runtime_contracts.WaitObservation,
}.items():
    MODELS["graph-runtime." + name] = model
for name, model in {
    "release-descriptor": tool_contracts.ReleaseDescriptor,
    "lock-entry": tool_contracts.LockEntry,
    "eligibility": tool_contracts.EligibilityResult,
    "eligibility-decision": tool_contracts.EligibilityDecision,
    "register-release": tool_contracts.RegisterRelease,
    "registration-receipt": tool_contracts.ReleaseRegistrationReceipt,
    "change-release": tool_contracts.ChangeRelease,
    "register-deployment": tool_contracts.RegisterDeployment,
    "change-deployment": tool_contracts.ChangeDeployment,
    "replica-heartbeat": tool_contracts.ReplicaHeartbeat,
    "resolve-release": tool_contracts.ResolveRelease,
    "release-snapshot": tool_contracts.ReleaseSnapshot,
    "deployment-snapshot": tool_contracts.DeploymentSnapshot,
    "heartbeat-snapshot": tool_contracts.HeartbeatSnapshot,
    "registry-receipt": tool_contracts.RegistryReceipt,
    "release-page": tool_contracts.ReleasePage,
}.items():
    MODELS["tools." + name] = model
for name, model in {
    "admit-fixture": runtime_contracts.AdmitFixtureRun,
    "claim": runtime_contracts.ClaimInvocation,
    "renew": runtime_contracts.RenewAttempt,
    "complete": runtime_contracts.CompleteInvocation,
    "cancel": runtime_contracts.CancelRun,
    "revoke-worker": runtime_contracts.RevokeWorker,
    "receipt": runtime_contracts.CommandReceipt,
    "claim-response": runtime_contracts.ClaimResponse,
    "run-snapshot": runtime_contracts.RunSnapshot,
    "notification": runtime_contracts.RuntimeNotification,
    "delivery-acknowledgement": runtime_contracts.DeliveryAcknowledgement,
    "audit-page": runtime_contracts.AuditPage,
    "delivery-page": runtime_contracts.DeliveryPage,
    "completion-record": runtime_contracts.CompletionRecord,
}.items():
    MODELS["runtime." + name] = model
for name, model in {
    "begin-upload": artifact_contracts.BeginUpload,
    "begin-derived-upload": artifact_contracts.BeginDerivedUpload,
    "derivation-declaration": artifact_contracts.DerivationDeclaration,
    "derived-upload-receipt": artifact_contracts.DerivedUploadReceipt,
    "derived-upload-observation": artifact_contracts.DerivedUploadObservation,
    "derivation-receipt": artifact_contracts.DerivationReceipt,
    "finalize": artifact_contracts.FinalizeArtifact,
    "reserve": artifact_contracts.ReserveArtifact,
    "runtime-outcome": artifact_contracts.RuntimeOutcome,
    "confirm": artifact_contracts.ConfirmRetention,
    "reconcile": artifact_contracts.ReconcileReservation,
    "reservation-receipt": artifact_contracts.ReservationReceipt,
    "upload-receipt": artifact_contracts.UploadReceipt,
    "upload-content-receipt": artifact_contracts.UploadContentReceipt,
    "finalized-receipt": artifact_contracts.FinalizedReceipt,
    "publication-observation": artifact_contracts.PublicationObservation,
}.items():
    MODELS["artifacts." + name] = model



def encoded(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")


def artifacts(version="1") -> dict[str, bytes]:
    models = {"1": MODELS, "2": MODELS_V2, "3": MODELS_V3, "4": MODELS_V4}[version]
    result = {}
    for name, model in sorted(models.items()):
        for mode in ("validation", "serialization"):
            schema = model.model_json_schema(mode=mode)
            schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
            schema["$id"] = f"urn:amphora:{name}:{version}:{mode}"
            result[f"{name}.{mode}.json"] = encoded(schema)
    manifest = {
        "profile": "amphora-schema-publication-v1",
        "wire_version": version,
        "schemas": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(result.items())},
    }
    result["manifest.json"] = encoded(manifest)
    return result


def publish(directory: Path, check: bool = False, version="1") -> list[str]:
    expected = artifacts(version)
    if check:
        actual = {p.name: p.read_bytes() for p in directory.glob("*.json")}
        return sorted(k for k in actual.keys() | expected.keys() if actual.get(k) != expected.get(k))
    directory.mkdir(parents=True, exist_ok=True)
    for name, data in expected.items():
        (directory / name).write_bytes(data)
    return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    differences = [f"v{version}/{name}" for version in ("1", "2", "3", "4")
        for name in publish(ROOT / "contracts" / "schemas" / ("v" + version), args.check, version)]
    if differences:
        raise SystemExit("Schema publication differs: " + ", ".join(differences))
    print("Schema publication verified" if args.check else f"Published {2 * (len(MODELS) + len(MODELS_V2) + len(MODELS_V3) + len(MODELS_V4))} schemas and versioned manifests")
