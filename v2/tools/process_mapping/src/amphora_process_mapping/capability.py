"""One opt-in synthetic mapping release; no chemistry or execution authority."""
import json
from importlib.metadata import version

from amphora_contracts_population import MaterialMappingManifest,MaterialMappingPage,population_record_schema
from amphora_contracts_tools import ReleaseDescriptor

from .payloads import MaterialCollection,MapMaterialsRequest,payload_schema,schema_ref


SCHEMAS={"request":(MapMaterialsRequest,"process-worker.map-materials"),
    "collection":(MaterialCollection,"process-worker.material-collection"),
    "page":(MaterialMappingPage,"population.material-mapping-page"),
    "manifest":(MaterialMappingManifest,"population.material-mapping-manifest")}


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
