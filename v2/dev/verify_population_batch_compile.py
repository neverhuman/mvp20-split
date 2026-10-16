"""Exchange public packets between Search export and isolated Runtime compilation.

No owner services, databases, containers, admission or provider calls. Export may
use Search; compile imports Runtime only, never Search implementation.
"""
import argparse
import hashlib
import json
from pathlib import Path


def export(folder):
    from amphora_contracts_campaigns import ExecutableCampaignV4
    from amphora_evolution_search.composition.batching import PrimaryBatchLoop
    from amphora_evolution_search.population_workers.capabilities import PopulationCapability
    folder.mkdir(parents=True,exist_ok=False)
    root=Path(__file__).absolute().parents[1]
    method=json.loads((root/"tools/evolution_search/tests/population_workers/primary-method-definition.json").read_bytes())
    capabilities=[PopulationCapability(operation) for operation in ("seed","slice","evaluate-squares")]
    releases=[capability.descriptor("f"*64).model_dump(mode="json") for capability in capabilities]
    method["body"]["nodes"][0]["tool"]=releases[2]["tool"]["binding"]
    method=ExecutableCampaignV4.model_validate_json(json.dumps(method))
    schemas={}
    for capability,release in zip(capabilities,releases):
        for direction,ports in (("input","inputs"),("output","outputs")):
            reference=release["tool"][ports][0]["schema_ref"]
            schemas[reference["sha256"]]=dict(schema_ref=reference,body=capability.schema_bytes(direction).decode())
    graphs=[]
    for batch in (1,8,32):
        author=PrimaryBatchLoop(method,max_population=32,batch_size=batch,max_parallel=4,image_sha256="f"*64)
        loop=author.build(dict(kind="input",name="request"),prepared=dict(kind="input",name="prepared"))
        graph=method.model_dump(mode="json")
        graph["body"]=dict(inputs=[dict(name="request",value_type=author.request_shape),dict(name="prepared",value_type=author.prepared_shape)],
            outputs=[dict(name="result",value_type=author.request_shape)],
            nodes=[loop.model_dump(mode="json"),dict(kind="finish",node_id="finish",outputs=[dict(port="result",
                source=dict(kind="output",node_id="batches",port="request"))])],
            edges=[dict(source="batches",target="finish",route="next")])
        graphs.append(dict(batch=batch,definition=graph))
    packet=dict(releases=releases,schemas=list(schemas.values()),graphs=graphs)
    (folder/"packet.json").write_text(json.dumps(packet),encoding="utf-8")
    print("Exported3 bounded batch graphs and public release/schema packets")


def compile_packet(folder):
    from amphora_contracts_campaigns import ExecutableCampaignV4
    from amphora_contracts_core import SchemaRef
    from amphora_contracts_tools import LockEntry,ReleaseDescriptor
    from amphora_campaign_runtime.compiler import (ResolvedTool,ToolCatalog,PinnedSchema,
        SchemaIdentity,SchemaCatalog,compile_campaign)
    packet=json.loads((folder/"packet.json").read_bytes())
    tools=[]
    for raw in packet["releases"]:
        descriptor=ReleaseDescriptor.model_validate_json(json.dumps(raw))
        content=json.dumps(dict(profile="amphora-tool-release-v1",descriptor=raw),sort_keys=True,
            separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
        lock=dict(schema_version="1",tool=raw["tool"]["binding"],descriptor_sha256=hashlib.sha256(content).hexdigest(),
            input_schemas=[dict(port=port["name"],schema_ref=port["schema_ref"]) for port in raw["tool"]["inputs"]],
            output_schemas=[dict(port=port["name"],schema_ref=port["schema_ref"]) for port in raw["tool"]["outputs"]],
            checkpoint_schema=None)
        tools.append(ResolvedTool(descriptor,LockEntry.model_validate_json(json.dumps(lock))))
    schemas=SchemaCatalog([PinnedSchema(SchemaIdentity.from_wire(SchemaRef.model_validate_json(json.dumps(item["schema_ref"]))),
        item["body"].encode()) for item in packet["schemas"]])
    evidence=[]
    for graph in packet["graphs"]:
        plan=compile_campaign(ExecutableCampaignV4.model_validate_json(json.dumps(graph["definition"])),ToolCatalog(tools),schemas)
        evidence.append(dict(batch=graph["batch"],plan_sha256=plan.sha256))
    (folder/"compiled.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
    print("Runtime compiled3 bounded batch graphs; no execution/admission claimed")


def author(folder):
    from amphora_contracts_campaigns import ExecutableCampaignV4
    from amphora_evolution_search.composition.batching import PrimaryBatchLoop
    packet=json.loads((folder/"batch-author-input.json").read_bytes())
    builder=PrimaryBatchLoop(ExecutableCampaignV4.model_validate_json(json.dumps(packet["method"])),
        max_population=packet["max_population"],batch_size=packet["batch_size"],
        max_parallel=packet["max_parallel"],image_sha256=packet["image_sha256"])
    loop=builder.build(packet["initial"],prepared=packet["prepared"])
    (folder/"batch-author-output.json").write_text(json.dumps(dict(loop=loop.model_dump(mode="json"),
        request_shape=builder.request_shape)),encoding="utf-8")
    print("Authored explicit slice loop from the supplied method graph")


def assess(folder):
    from dataclasses import asdict
    from amphora_contracts_campaigns import ExecutionPlanV4
    from amphora_contracts_population import PopulationSpecification
    from amphora_contracts_graph_runtime import GraphLimits
    from amphora_contracts_runtime import AttemptBudget
    from amphora_evolution_search.composition import GraphWorkBounds
    from amphora_evolution_search.composition.publications import NumericPublicationProfile
    from amphora_evolution_search.composition.validation_io import SeedValidationIoProfile
    packet=json.loads((folder/"batch-preflight-input.json").read_bytes())
    plan=ExecutionPlanV4.model_validate_json(json.dumps(packet["plan"]))
    specification=PopulationSpecification.model_validate_json(json.dumps(packet["specification"]))
    work=GraphWorkBounds.from_plan(plan,packet["expected_plan_sha256"])
    attempts=work.check_admission_budget(GraphLimits(max_activations=specification.budget.max_activations),
        AttemptBudget(limit=256))
    publications=NumericPublicationProfile(specification,"f"*64).assess(work.work,3)
    io=SeedValidationIoProfile(specification,"f"*64).assess(work.work,3)
    evidence=dict(plan_sha256=work.plan_sha256,definition_sha256=work.definition_sha256,
        activations=work.work.activations,queued_upper=work.work.queued_upper,attempts_upper=attempts,
        publications=asdict(publications),external_ancestry="Controlled fixture only; production inspection awaits POP-01.08",
        worker_validation_io=asdict(io),worker_response_body_bytes_upper=io.response_body_bytes,
        scope="Structural/publication assessment; not full E2.3 preflight or owner admission")
    (folder/"batch-preflight-output.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
    print("Verified plan packet identity and structural/publication/worker-I/O bounds")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=("export","compile","author","assess"))
    parser.add_argument("folder",type=Path)
    arguments=parser.parse_args()
    {"export":export,"compile":compile_packet,"author":author,"assess":assess}[arguments.mode](arguments.folder)
