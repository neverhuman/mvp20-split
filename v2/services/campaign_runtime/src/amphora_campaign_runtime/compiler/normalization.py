"""Canonical authored semantics; ordered members and predicate operands stay ordered."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_campaigns import (
    ExecutableCampaign,
    ExecutableCampaignV3,
    ExecutableCampaignV4,
    ExecutionPlan,
    ExecutionPlanV3,
    ExecutionPlanV4,
    PlanDocument,
    PlanDocumentV3,
    PlanDocumentV4,
    parse_executable_campaign,
)

from .catalog import binding_key, canonical


def _scope(body):
    for key in ("inputs", "outputs"):
        body[key].sort(key=lambda port: port["name"])
    body["nodes"].sort(key=lambda node: node["node_id"])
    body["edges"].sort(key=lambda edge: (edge["source"], edge["target"], edge["route"]))
    for node in body["nodes"]:
        for key in ("inputs", "outputs", "captures"):
            if key in node:
                node[key].sort(key=lambda binding: binding["port"])
        if "state" in node:
            node["state"].sort(key=lambda slot: slot["name"])
        if "fields" in node:
            node["fields"].sort(key=lambda field: field["name"])
        if "body" in node:
            _scope(node["body"])


def normalize(definition):
    record = definition.model_dump(mode="json")
    record["context"].sort(key=lambda pin: (pin["kind"], pin["identity"], pin["revision"], pin["sha256"]))
    _scope(record["body"])
    return parse_executable_campaign(canonical(record))


@dataclass(frozen=True)
class CompiledNode:
    node_id: str
    inputs: tuple
    outputs: tuple

    def record(self):
        return {"node_id": self.node_id, "inputs": [port.record() for port in self.inputs],
                "outputs": [port.record() for port in self.outputs]}


@dataclass(frozen=True)
class CompiledScope:
    path: tuple
    order: tuple
    nodes: tuple
    inputs: tuple
    outputs: tuple

    def record(self):
        return {"path": self.path, "order": self.order, "nodes": [node.record() for node in self.nodes]}


@dataclass(frozen=True)
class CompiledCampaign:
    definition: ExecutableCampaign | ExecutableCampaignV3 | ExecutableCampaignV4
    tools: tuple
    schemas: tuple
    scopes: tuple

    def seal(self):
        definition = self.definition.model_dump(mode="json")
        version = self.definition.schema_version
        profile, document_type, plan_type = {"2": ("v1", PlanDocument, ExecutionPlan),
            "3": ("v2", PlanDocumentV3, ExecutionPlanV3), "4": ("v3", PlanDocumentV4, ExecutionPlanV4)}[version]
        digest = hashlib.sha256(canonical({"profile": "amphora-executable-definition-v" + version, "definition": definition})).hexdigest()
        lock = {"schema_version": version, "compiler_profile": "amphora-deterministic-compiler-" + profile,
                "definition_sha256": digest,
                "tools": [tool.lock.model_dump(mode="json") for tool in sorted(self.tools, key=lambda item: binding_key(item.lock.tool))],
                "schemas": [schema.record() for schema in sorted(self.schemas, key=lambda item: (item.name, item.version, item.digest))],
                "context": definition["context"]}
        document = document_type.model_validate_json(canonical({"profile": "amphora-execution-plan-" + profile, "definition": definition,
                                                               "lock": lock, "scopes": [scope.record() for scope in sorted(self.scopes, key=lambda item: item.path)]}))
        digest = hashlib.sha256(canonical(document.model_dump(mode="json"))).hexdigest()
        return plan_type(schema_version=version, sha256=digest, document=document)
