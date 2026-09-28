"""Publish/check deterministic Draft 2020-12 input and output schema artifacts."""

import argparse
import hashlib
import json
from pathlib import Path

import amphora_contracts_artifacts as artifact_contracts
import amphora_contracts_runtime as runtime_contracts
import amphora_contracts_tools as tool_contracts
from amphora_contracts_campaigns import CampaignDefinition
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

MODELS["commands.identity"] = CommandIdentity
for name, model in {
    "release-descriptor": tool_contracts.ReleaseDescriptor,
    "lock-entry": tool_contracts.LockEntry,
    "eligibility": tool_contracts.EligibilityResult,
    "eligibility-decision": tool_contracts.EligibilityDecision,
    "register-release": tool_contracts.RegisterRelease,
    "registration-receipt": tool_contracts.ReleaseRegistrationReceipt,
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
    "finalize": artifact_contracts.FinalizeArtifact,
    "reserve": artifact_contracts.ReserveArtifact,
    "runtime-outcome": artifact_contracts.RuntimeOutcome,
    "confirm": artifact_contracts.ConfirmRetention,
    "reconcile": artifact_contracts.ReconcileReservation,
    "reservation-receipt": artifact_contracts.ReservationReceipt,
    "upload-receipt": artifact_contracts.UploadReceipt,
    "upload-content-receipt": artifact_contracts.UploadContentReceipt,
    "finalized-receipt": artifact_contracts.FinalizedReceipt,
}.items():
    MODELS["artifacts." + name] = model



def encoded(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")


def artifacts() -> dict[str, bytes]:
    result = {}
    for name, model in sorted(MODELS.items()):
        for mode in ("validation", "serialization"):
            schema = model.model_json_schema(mode=mode)
            schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
            schema["$id"] = f"urn:amphora:{name}:1:{mode}"
            result[f"{name}.{mode}.json"] = encoded(schema)
    manifest = {
        "profile": "amphora-schema-publication-v1",
        "wire_version": "1",
        "schemas": {name: hashlib.sha256(data).hexdigest() for name, data in sorted(result.items())},
    }
    result["manifest.json"] = encoded(manifest)
    return result


def publish(directory: Path, check: bool = False) -> list[str]:
    expected = artifacts()
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
    differences = publish(ROOT / "contracts" / "schemas" / "v1", args.check)
    if differences:
        raise SystemExit("Schema publication differs: " + ", ".join(differences))
    print("Schema publication verified" if args.check else f"Published {len(MODELS) * 2} schemas and digest manifest")
