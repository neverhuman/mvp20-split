"""Verify supplied public plan bytes against owner digests and frozen method body."""
import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_campaigns import ExecutableCampaignV4, ExecutionPlanV4
from amphora_contracts_core import SchemaRef
from amphora_contracts_population_steps import population_step_schema

from ..ranking import require


def plan_bytes(value):
    # Retained public compiler profile: same JSON digest recipe as Runtime's
    # compiler/catalog.py and normalization.py; adapted here without owner imports.
    return json.dumps(value,sort_keys=True,separators=(",", ":"),ensure_ascii=True,allow_nan=False).encode()


def payload_schema(model, name):
    schema=model.model_json_schema(mode="validation")
    schema.update({"$schema":"https://json-schema.org/draft/2020-12/schema", "$id":f"urn:amphora:{name}:1:validation"})
    raw=(json.dumps(schema,sort_keys=True,separators=(",", ":"),ensure_ascii=False,allow_nan=False)+"\n").encode()
    return SchemaRef(schema_id=name,version="1",sha256=hashlib.sha256(raw).hexdigest())


def read_plan(reference, artifacts):
    plan=artifacts.read(reference).decode(ExecutionPlanV4,payload_schema(ExecutionPlanV4,reference.schema_ref.schema_id),artifacts.scope)
    require(hashlib.sha256(plan_bytes(plan.document.model_dump(mode="json"))).hexdigest()==plan.sha256,"population_plan_digest")
    definition=plan.document.definition
    require(definition.scope==artifacts.scope,"population_plan_scope")
    digest=hashlib.sha256(plan_bytes({"profile":"amphora-executable-definition-v4", "definition":definition.model_dump(mode="json")})).hexdigest()
    require(digest==plan.document.lock.definition_sha256,"population_plan_definition_digest")
    return plan


@dataclass(frozen=True)
class PrimaryMethodPlan:
    execution: ExecutionPlanV4
    method: ExecutionPlanV4
    scope_path: tuple[str, ...]
    methods: tuple

    @classmethod
    def load(cls, request, original, artifacts):
        execution=read_plan(request.execution_plan,artifacts)
        method=read_plan(request.method_plan,artifacts)
        frozen=original.record.method_graph
        definition=artifacts.read(frozen.definition).decode(ExecutableCampaignV4,
            payload_schema(ExecutableCampaignV4,frozen.definition.schema_ref.schema_id),artifacts.scope)
        require(method.sha256==frozen.plan_sha256 and method.document.definition==definition,"population_method_plan_pin")
        body=execution.document.definition.body
        for part in request.method_scope_path:
            matches=tuple(node for node in body.nodes if node.node_id==part and node.kind in {"scatter","iterate"})
            require(len(matches)==1,"population_method_scope_path")
            body=matches[0].body
        require(body==definition.body,"population_method_embedding")
        require(not any(node.kind in {"scatter","iterate"} for node in body.nodes),"population_primary_nested_occurrences")
        invokes={node.node_id:node for node in body.nodes if node.kind=="invoke"}
        require(all(len(binding.node_path)==1 for binding in frozen.methods),"population_primary_method_path")
        require(len(invokes)==len(frozen.methods) and set(invokes)=={binding.node_path[0] for binding in frozen.methods},"population_primary_method_coverage")
        require(len(body.inputs)==1 and body.inputs[0].name=="candidate" and body.inputs[0].value_type.kind=="artifact"
            and body.inputs[0].value_type.schema_ref==population_step_schema("population-step.candidate-context"),
            "population_primary_context_port")
        for binding in frozen.methods:
            node=invokes[binding.node_path[0]]
            require(node.tool==binding.tool and node.checkpoint is None and len(node.inputs)==1
                and node.inputs[0].port=="parameters" and node.inputs[0].source.kind=="input"
                and node.inputs[0].source.name=="candidate"
                and binding.input_schema==population_step_schema("population-step.candidate-context"),
                "population_primary_method_binding")
        return cls(execution,method,request.method_scope_path,frozen.methods)

    def binding(self, node):
        if tuple(occurrence.node_id for occurrence in node.path.occurrences)!=self.scope_path:
            return None
        matches=tuple(binding for binding in self.methods if binding.node_path[0]==node.path.node_id)
        if not matches:return None
        require(len(matches)==1 and node.kind=="invoke","population_primary_method_identity")
        address=hashlib.sha256(plan_bytes({"profile":"amphora-activation-address-v1","plan_sha256":self.execution.sha256,
            "path":node.path.model_dump(mode="json")})).hexdigest()
        require(address==node.activation_id,"population_primary_activation_address")
        return matches[0]
