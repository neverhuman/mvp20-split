"""Research-owned fixtures; Data owns bytes through its isolated public HTTP service."""
import hashlib
import json
import os
from dataclasses import replace

from amphora_contracts_core import ArtifactRef
from amphora_contracts_research import (
    LabIntakeRequest,
    LabReturnProfile,
    ObservationQuality,
    ReportedObservation,
    ScientificAssessmentRequest,
    SyntheticEligibilityReport,
    SyntheticLabReport,
    SyntheticSynthesisReport,
    synthetic_lab_report_schema,
    synthetic_lab_report_schema_document,
    synthetic_scientific_report_schema,
    synthetic_scientific_report_schema_document,
)
from amphora_research.experiments.store import ExperimentStore
from amphora_research.experiments.wire import from_wire, reference_to_wire, to_wire
from amphora_research.observations.reports import ConfiguredLabReturn
from amphora_research.scientific_api.boundary import ConfiguredScientificInput
from amphora_research.scientific_publication.artifact import ScientificArtifact

from ..assessment.live_peers import Owner, owned_script
from ..assessment.test_actual_resolution import publish
from ..material_state.storage_fixtures import in_scope, publish_specimen
from .test_resolution import EXAMPLES, resolution_case


class ScientificPeers:
    def __init__(self, ledger, directory, interpreter):
        identities,self.scope = ledger
        self.identities,self.directory,self.interpreter = identities,directory,interpreter
        url = identities.engine.url
        self.environment = dict(os.environ,DATA_DB=url.set(username="artifact_service").render_as_string(hide_password=False),
            RESEARCH_DB=url.render_as_string(hide_password=False),DATA_TOKEN="d"*32,READ_TOKEN="r"*32,
            PUBLISH_TOKEN="p"*32,RESEARCH_TOKEN="s"*32,RESEARCH_READ_TOKEN="h"*32,OTHER_TOKEN="o"*32,
            PEER_MIGRATION=url.set(username="artifact_migrator").render_as_string(hide_password=False))
        owned_script(interpreter,"import os; from amphora_data_artifacts.persistence.migrate import upgrade; upgrade(os.environ['PEER_MIGRATION'])",self.environment)
        self.raw_schema = {"schema_id":"fixture.bytes","version":"1","sha256":hashlib.sha256(b'{"type":"string","contentEncoding":"base64"}').hexdigest()}
        schemas = [{"media_type":"application/octet-stream",**self.raw_schema}]
        def add(name, body, schema):
            path = name+".json"
            (directory/path).write_bytes(body)
            schemas.append({"media_type":"application/json",**schema,"schema_path":path})
        for kind in ("eligibility","synthesis"):
            add(kind+"-input",synthetic_scientific_report_schema_document(kind),synthetic_scientific_report_schema(kind).model_dump(mode="json"))
        add("lab-input",synthetic_lab_report_schema_document(),synthetic_lab_report_schema().model_dump(mode="json"))
        for kind in ("lab-intake","eligibility","synthesis"):
            body = ScientificArtifact.schema_document(kind)
            add(kind+"-output",body,{"schema_id":"research."+kind+".payload","version":"1","sha256":hashlib.sha256(body).hexdigest()})
        (directory/"bytes").mkdir()
        scope = self.scope.model_dump(mode="json")
        config = {"database_url_env":"DATA_DB","storage_root":str(directory/"bytes"),"profiles":schemas,
            "principals":[{"token_env":"DATA_TOKEN","actor_id":"fixture","scope":scope,"actions":["read","source_history","upload","finalize"]},
                {"token_env":"READ_TOKEN","actor_id":"reader","scope":scope,"actions":["read","source_history"]},
                {"token_env":"PUBLISH_TOKEN","actor_id":"publisher","scope":scope,"actions":["read","source_history","upload","finalize"]}]}
        self.data_config = directory/"data.json"
        self.data_config.write_text(json.dumps(config),encoding="utf-8")
        self.state,self.plan,self.observation = publish_specimen(identities,self.scope)
        self.data = Owner("amphora_data_artifacts",self.data_config,self.environment,"d"*32,interpreter)

    def raw(self, name):
        return ArtifactRef.model_validate_json(json.dumps(publish(self.data,self.scope.model_dump(mode="json"),
            ("Synthetic fixture: "+name).encode(),self.raw_schema)))

    def report(self, document, schema, inputs):
        adapter = document.adapter
        method = {"transformation_id":adapter.schema_id,"version":adapter.version,"sha256":adapter.sha256}
        result = publish(self.data,self.scope.model_dump(mode="json"),document.model_dump_json().encode(),schema.model_dump(mode="json"),
            inputs=[ref.model_dump(mode="json") for ref in inputs],method=method)
        return ArtifactRef.model_validate_json(json.dumps(result))

    def lab(self):
        context,raw = self.raw("protocol"),self.raw("lab raw")
        plan = from_wire(self.plan)
        plan = replace(plan,protocol=replace(plan.protocol,applicability=context,source=context),
            expectations=plan.expectations+(replace(plan.expectations[0],expectation_id="second",
                replicate=replace(plan.expectations[0].replicate,replicate_id="replicate-2")),))
        self.plan = to_wire(plan)
        ExperimentStore(self.identities.engine).publish(self.scope,"fixture",self.plan)
        profile = ConfiguredLabReturn(LabReturnProfile(wire_version="1",authority="synthetic",profile_id="lab",version="1",
            experiment=reference_to_wire(plan.identity.reference),adapter=plan.protocol.method,publishers=("fixture",)))
        observation = self.observation
        binding = observation.binding.model_copy(update={"measurement":observation.binding.measurement.model_copy(update={"context":context})})
        first = ReportedObservation(reference=observation.reference,supersedes=None,binding=binding,value=observation.value,
            quality=ObservationQuality(controls="failed",flags=("questionable","low_accuracy")))
        report = SyntheticLabReport(wire_version="1",authority="synthetic",issuer="fixture",adapter=profile.document.adapter,raw_report=raw,observations=(first,))
        artifact = self.report(report,synthetic_lab_report_schema(),(raw,context))
        request = LabIntakeRequest(wire_version="1",intake_id="actual-lab",profile=profile.reference,report=artifact)
        return profile,request

    def decision(self, kind):
        template,_ = resolution_case(kind)
        model = SyntheticEligibilityReport if kind == "eligibility" else SyntheticSynthesisReport
        document = in_scope(template.configured.document,self.scope)
        report = in_scope(model.model_validate_json((EXAMPLES/("synthetic-"+kind+"-report.json")).read_bytes()),self.scope)
        references = {}
        def replace_refs(value):
            if isinstance(value,dict):
                if "artifact_id" in value:
                    name = value["artifact_id"]
                    if name not in references:
                        references[name] = self.raw(kind+" "+name)
                    return references[name].model_dump(mode="json")
                return {key:replace_refs(item) for key,item in value.items()}
            if isinstance(value,list):
                return [replace_refs(item) for item in value]
            return value
        configured = ConfiguredScientificInput(type(document).model_validate_json(json.dumps(replace_refs(document.model_dump(mode="json")))))
        report = model.model_validate_json(json.dumps(replace_refs(report.model_dump(mode="json"))))
        source = self.report(report,synthetic_scientific_report_schema(kind),tuple(references.values()))
        request = ScientificAssessmentRequest(wire_version="1",decision_id="actual-"+kind,profile=configured.reference,reports=(source,))
        return configured,request

    def consumer(self, inputs):
        return publish(self.data,self.scope.model_dump(mode="json"),b"Synthetic explicit consumer: "+json.dumps(inputs).encode(),self.raw_schema,
            inputs=inputs,method={"transformation_id":"fixture.consumer","version":"1","sha256":"a"*64})
