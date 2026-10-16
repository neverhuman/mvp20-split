"""One opt-in synthetic mapping release; no chemistry or execution authority."""
import json
from importlib.metadata import version

from amphora_contracts_population import MaterialMappingManifest,MaterialMappingPage,population_record_schema
from amphora_contracts_tools import ReleaseDescriptor

from .payloads import (MaterialCollection,MapMaterialsRequest,TransformMaterialsRequest,ProposedProcessTransform,
    DeriveProcessRequest,DerivedMaterialBatch,payload_schema,schema_ref)


SCHEMAS={"request":(MapMaterialsRequest,"process-worker.map-materials"),
    "collection":(MaterialCollection,"process-worker.material-collection"),
    "page":(MaterialMappingPage,"population.material-mapping-page"),
    "manifest":(MaterialMappingManifest,"population.material-mapping-manifest"),
    "transform-request":(TransformMaterialsRequest,"process-worker.transform-request"),
    "transform-result":(ProposedProcessTransform,"process-worker.transform-result"),
    "derive-request":(DeriveProcessRequest,"process-worker.derive-request"),
    "derived-batch":(DerivedMaterialBatch,"process-worker.derived-batch")}

PROFILES={"map-materials":("request","manifest"),"transform-materials":("transform-request","transform-result"),
    "derive-process":("derive-request","derived-batch")}


class MappingCapability:
    @property
    def release(self):return version("amphora-process-mapping")

    def descriptor(self,image_sha256):
        request=schema_ref(*SCHEMAS["request"])
        output=population_record_schema("population.material-mapping-manifest")
        assert output==schema_ref(*SCHEMAS["manifest"])
        def port(name,schema):
            return dict(name=name,schema_ref=schema.model_dump(),representation="synthetic-process-mapping-v1",unit="1")
        return ReleaseDescriptor.model_validate_json(json.dumps(dict(schema_version="1",tool=dict(
            schema_version="1",binding=dict(capability_id="process.synthetic-map-materials",release=self.release,
                image_sha256=image_sha256,contract_version="1"),
            purpose="Publish bounded synthetic pairwise, keyed or opted-in Cartesian material mappings.",
            applicability=["synthetic-process-material-v1"],inputs=[port("parameters",request)],
            outputs=[port("result",output)],side_effects="pure",checkpoint_schema=None),
            resources=dict(architectures=["x86_64"],operating_systems=["linux"],cpu_millicores=1000,
                memory_mib=256,gpu_count=0,timeout_seconds=3600,max_parallel_invocations=1,max_batch_size=1),
            egress=dict(mode="deny"),checkpoint=dict(mode="none",readable_schema_sha256=[]),
            reproducibility="deterministic",authority_ceiling="synthetic_only",
            examples=["Map two bounded material collections with exact context and immutable ancestry."],
            anti_examples=["No reaction, conservation, feasibility or lab-control inference."])))

    def schema_bytes(self,record):return payload_schema(*SCHEMAS[record])


class ProcessCapability(MappingCapability):
    def __init__(self,operation="map-materials"):
        if operation not in PROFILES:raise ValueError("unsupported_process_operation")
        self.operation=operation

    @property
    def input_model(self):return SCHEMAS[PROFILES[self.operation][0]][0]

    def descriptor(self,image_sha256):
        descriptor=super().descriptor(image_sha256)
        if self.operation=="map-materials":return descriptor
        value=descriptor.model_dump(mode="json")
        tool=value["tool"]
        tool["binding"]["capability_id"]="process.synthetic-"+self.operation
        tool["purpose"]=("Publish synthetic states with unknown physical properties; no accepted producer claim."
            if self.operation=="transform-materials" else "Assemble material lineage from verified accepted transform execution.")
        tool["applicability"]=["synthetic-process-material-v1"]
        representations=(("synthetic-process-transform-request-v1","synthetic-process-transform-result-v1")
            if self.operation=="transform-materials" else ("synthetic-process-derive-request-v1","synthetic-process-derived-batch-v1"))
        for direction,key,representation in zip(("inputs","outputs"),PROFILES[self.operation],representations,strict=True):
            tool[direction][0].update(schema_ref=schema_ref(*SCHEMAS[key]).model_dump(),representation=representation)
        value["examples"]=["One scoped synthetic state/lineage step with complete retained ancestry."]
        return ReleaseDescriptor.model_validate_json(json.dumps(value))
