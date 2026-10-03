"""Explicit synthetic context matrix; Data owns all consumed evidence bytes."""
import json

from amphora_contracts_research import (
    EligibilityInputProfile,
    ExperimentDefinition,
    LabIntakeRequest,
    LabReturnProfile,
    MaterialStateRevision,
    ReportedObservation,
    ScientificAssessmentRequest,
    SyntheticEligibilityReport,
    SyntheticLabReport,
    synthetic_lab_report_schema,
    synthetic_scientific_report_schema,
)
from amphora_research.experiments.store import ExperimentStore
from amphora_research.material_state.store import MaterialStateStore
from amphora_research.observations.interpretation.profiles import InterpretationProfile
from amphora_research.observations.quality.policy import ObservationUsePolicy, UseRequirements
from amphora_research.observations.reports import ConfiguredLabReturn
from amphora_research.scientific_api.boundary import ConfiguredScientificInput

from ..material_state.storage_fixtures import in_scope
from ..scientific_api.test_resolution import EXAMPLES
from .actual_fixtures import InterpretationPeers


def wire(value):
    return value.model_dump(mode="json")


def numeric(value, unit="mg/L"):
    return {"kind":"numeric","quantity":{"value":value,"unit":unit},"uncertainty":None}


class MatrixPeers(InterpretationPeers):
    def matrix(self):
        template = wire(self.plan)
        method = template["protocol"]["method"]
        context = self.raw("matrix protocol and applicability")
        template["reference"]["experiment_id"] = "context-matrix"
        template["protocol"].update(source=wire(context),applicability=wire(context))
        specimens = []
        for basis in ("observed","proposed"):
            state = wire(self.state)
            state["reference"]["material_state_id"] = "state-"+basis
            process_source = self.raw(basis+" processing record")
            state["preparation"] = [{"event_id":name,"context":{"method":method,
                "conditions":[{"name":"temperature","quantity":{"value":temperature,"unit":"K"}}],
                "duration":{"value":duration,"unit":unit},"atmosphere":"nitrogen"},
                "attribution":{"basis":basis,"actor":"fixture","equipment":["fixture-reactor"],"source":wire(process_source)}}
                for name,temperature,duration,unit in (("heat","298.15","2.00","min"),("quench","280.00","30.0","s"))]
            state["features"] = [{"name":"morphology",
                "value":{"kind":"categorical","label":"amorphous"} if basis == "observed" else {"kind":"missing","reason":"not_measured"},
                "evidence":{"basis":"measured" if basis == "observed" else "unknown",
                    "method":method if basis == "observed" else None,
                    "source":wire(self.raw("measured morphology")) if basis == "observed" else None}}]
            state = MaterialStateRevision.model_validate_json(json.dumps(state))
            MaterialStateStore(self.identities.engine).publish(self.scope,"fixture",state)
            sample = self.plan.samples[0].sample.model_copy(update={
                "reference":self.plan.samples[0].sample.reference.model_copy(update={"sample_id":"sample-"+basis}),
                "material_state":state.reference,"identity_evidence":self.raw(basis+" sample identity")})
            self.identities.publish(self.scope,sample)
            specimens.append({"sample":wire(sample),"state":wire(state)})
        template["samples"] = specimens
        # Independently specified values and claims; no production matching helper.
        cases = (
            ("matched-observed",0,"mg/L",numeric("1.25")),
            ("matched-proposed",1,"mg/L",numeric("2.00")),
            ("wrong-state",1,"mg/L",numeric("3.00")),
            ("wrong-sample",0,"mg/L",numeric("4.00")),
            ("convertible",0,"g/L",numeric("1250")),
            ("inverse-unconfigured",0,"mg/L",numeric("1.25","g/L")),
            ("replicate-high",0,"mg/L",numeric("9.0")),
            ("replicate-low",0,"mg/L",numeric("1.0")),
            ("below-detection",0,"mg/L",{"kind":"censored","lower":None,
                "upper":{"quantity":{"value":"0.01","unit":"mg/L"},"inclusive":False}}),
            ("missing-value",1,"mg/L",{"kind":"missing","reason":"not_measured"}),
            ("not-returned",1,"mg/L",None),
        )
        template["expectations"] = [{"expectation_id":name,"sample":specimens[index]["sample"]["reference"],
            "readout":{"criterion_id":"concentration","kind":"numeric","unit":unit,"x_unit":None},
            "replicate":{"replicate_id":name,"role":"sample"}} for name,index,unit,_ in cases]
        self.plan = ExperimentDefinition.model_validate_json(json.dumps(template))
        ExperimentStore(self.identities.engine).publish(self.scope,"fixture",self.plan)
        rows = []
        for name,index,_,value in cases:
            if value is None:
                continue
            specimen = specimens[1 if name == "wrong-sample" else index]
            state = specimens[0] if name == "wrong-state" else specimen
            row = {"reference":{"scope":wire(self.scope),"observation_id":name,"revision":1},"supersedes":None,
                "binding":{"target":{"experiment":wire(self.plan.reference),"expectation_id":name,"replicate_id":name},
                    "specimen":{"sample":specimen["sample"]["reference"],"material_state":state["state"]["reference"]},
                    "measurement":{"method":method,"context":wire(context)},"role":"sample"},
                "value":value,"quality":{"controls":"failed" if name == "matched-observed" else "unknown" if index else "passed",
                    "flags":["questionable","low_accuracy"] if name == "matched-observed" else ["replicate_disagreement"] if name.startswith("replicate-") else []}}
            rows.append(ReportedObservation.model_validate_json(json.dumps(row)))
        self.rows = tuple(rows)
        profile = ConfiguredLabReturn(LabReturnProfile(wire_version="1",authority="synthetic",profile_id="matrix-lab",version="1",
            experiment=self.plan.reference,adapter=self.plan.protocol.method,publishers=("fixture",)))
        request = self.return_report(profile,self.rows,"matrix-return")
        catalog = self.interpretation_profiles()[0].policy
        explore = InterpretationProfile(self.scope,ObservationUsePolicy("matrix.explore","1","explore",UseRequirements(False,False,False,()),catalog))
        strict = InterpretationProfile(self.scope,ObservationUsePolicy("matrix.strict","1","strict-action",UseRequirements(True,True,True,()),catalog))
        return profile,request,explore,strict

    def return_report(self, profile, rows, identifier):
        raw = self.raw(identifier)
        report = SyntheticLabReport(wire_version="1",authority="synthetic",issuer="fixture",adapter=profile.document.adapter,
            raw_report=raw,observations=rows)
        source = self.report(report,synthetic_lab_report_schema(),(raw,self.plan.protocol.source))
        return LabIntakeRequest(wire_version="1",intake_id=identifier,profile=profile.reference,report=source)

    def eligibility(self, lab_request):
        document = wire(in_scope(EligibilityInputProfile.model_validate_json((EXAMPLES/"eligibility-input-profile.json").read_bytes()),self.scope))
        specimen = self.plan.samples[0]
        context = document["policy"]["context"]
        context["subject"] = {"candidate":wire(specimen.sample.candidate),"sample":wire(specimen.sample.reference),
            "material_state":wire(specimen.state.reference)}
        context["conditions"] = wire(self.plan.protocol.applicability)
        document["policy"]["requirements"][0]["kind"] = "measurement"
        profile = ConfiguredScientificInput(EligibilityInputProfile.model_validate_json(json.dumps(document)))
        report = wire(in_scope(SyntheticEligibilityReport.model_validate_json((EXAMPLES/"synthetic-eligibility-report.json").read_bytes()),self.scope))
        raw = self.raw("explicit synthetic eligibility claim")
        report["raw_report"] = wire(raw)
        report["claims"][0]["context"] = context
        report["claims"][0]["origin"].update(source=wire(lab_request.report),observation=wire(self.rows[0].reference),kind="measurement")
        source = self.report(SyntheticEligibilityReport.model_validate_json(json.dumps(report)),synthetic_scientific_report_schema("eligibility"),
            (raw,lab_request.report,self.plan.protocol.applicability))
        return profile,ScientificAssessmentRequest(wire_version="1",decision_id="matrix-eligibility",profile=profile.reference,reports=(source,))
