"""Owner-local scientific declarations with real Data evidence for every consumed dependency."""
import json

from amphora_contracts_research import (
    LabIntakeRequest,
    ObservationQuality,
    ReportedObservation,
    SyntheticLabReport,
    synthetic_lab_report_schema,
)
from amphora_research.observations.interpretation.profiles import InterpretationProfile
from amphora_research.observations.normalization.catalog import ConversionCatalog, ConversionRule
from amphora_research.observations.quality.policy import ObservationUsePolicy, UseRequirements
from amphora_research.observations.quantities import DecimalValue

from ..assessment.live_peers import Owner
from ..scientific_api.peer_fixtures import ScientificPeers


class InterpretationPeers(ScientificPeers):
    def bind_real_sample_evidence(self):
        proof = self.raw("sample identity proof")
        prior = self.plan.samples[0].sample
        sample = prior.model_copy(update={"reference":prior.reference.model_copy(update={"revision":2}),
            "supersedes":prior.reference,"identity_evidence":proof})
        self.identities.publish(self.scope,sample)
        self.plan = self.plan.model_copy(update={"samples":(self.plan.samples[0].model_copy(update={"sample":sample}),),
            "expectations":tuple(item.model_copy(update={"sample":sample.reference}) for item in self.plan.expectations)})
        binding = self.observation.binding
        self.observation = self.observation.model_copy(update={"binding":binding.model_copy(update={
            "specimen":binding.specimen.model_copy(update={"sample":sample.reference})})})
        return proof

    def interpretation_profiles(self):
        catalog = ConversionCatalog("fixture.concentration","1",(
            ConversionRule("concentration","mg/L","g/L",DecimalValue("0.001")),))
        return (InterpretationProfile(self.scope,catalog),
            InterpretationProfile(self.scope,ObservationUsePolicy("fixture.explore","1","explore",UseRequirements(False,False,False,()))),
            InterpretationProfile(self.scope,ObservationUsePolicy("fixture.strict","1","strict-action",UseRequirements(True,True,True,()))))

    def corrected_lab(self, profile, original):
        raw = self.raw("corrected laboratory raw evidence")
        value = original.value.model_copy(update={"quantity":original.value.quantity.model_copy(update={"value":"1.30"})})
        observation = ReportedObservation(reference=original.reference.model_copy(update={"revision":2}),supersedes=original.reference,
            binding=original.binding,value=value,quality=ObservationQuality(controls="passed",flags=("questionable",)))
        report = SyntheticLabReport(wire_version="1",authority="synthetic",issuer="fixture",adapter=profile.document.adapter,
            raw_report=raw,observations=(observation,))
        source = self.report(report,synthetic_lab_report_schema(),tuple(dict.fromkeys((raw,self.plan.protocol.source,self.plan.protocol.applicability))))
        return LabIntakeRequest(wire_version="1",intake_id="corrected-lab",profile=profile.reference,report=source)

    def restart_data(self, *, allow_reads=True):
        port = int(self.data.endpoint.rsplit(":",1)[1])
        self.data.stop()
        config = json.loads(self.data_config.read_text())
        for principal in config["principals"]:
            if principal["token_env"] == "READ_TOKEN":
                principal["actions"] = ["read","source_history"] if allow_reads else ["source_history"]
        self.data_config.write_text(json.dumps(config))
        self.data = Owner("amphora_data_artifacts",self.data_config,self.environment,"d"*32,self.interpreter,port=port)
