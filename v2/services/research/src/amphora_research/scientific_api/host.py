"""Optional science composition; environment-referenced credentials and no startup migrations."""
import json

from amphora_contracts_core import Scope
from amphora_contracts_research import EligibilityInputProfile, LabReturnProfile, SynthesisInputProfile
from amphora_tool_protocol import HttpTransport
from sqlalchemy import text

from ..assessment.reader import AssessmentDataReader
from ..observations.reports import ConfiguredLabReturn
from .boundary import IDENTIFIER, ConfiguredScientificInput, require
from .operations import ScientificOperations
from .profiles import ReviewedProfiles
from .publications import ScientificPublications


def configured_operations(engine, config, keys, secret):
    keys(config,("lab_profiles","eligibility_profiles","synthesis_profiles","data","publication","consumer_publishers"))
    keys(config["data"],("endpoint","token_env"))
    keys(config["publication"],("actor_id","token_env"))
    configured = []
    for field,model,wrapper in (("lab_profiles",LabReturnProfile,ConfiguredLabReturn),
        ("eligibility_profiles",EligibilityInputProfile,ConfiguredScientificInput),
        ("synthesis_profiles",SynthesisInputProfile,ConfiguredScientificInput)):
        values = config[field]
        require(isinstance(values,list) and len(values) <= 32,"invalid_scientific_profiles")
        configured.extend(wrapper(model.model_validate_json(json.dumps(raw))) for raw in values)
    require(len(configured) <= 32,"invalid_scientific_profiles")
    registry = ReviewedProfiles(configured)
    publishers = config["consumer_publishers"]
    require(isinstance(publishers,list) and len(publishers) <= 32,"invalid_consumer_publishers")
    for publisher in publishers:
        IDENTIFIER.validate_python(publisher,strict=True)
    require(len(set(publishers)) == len(publishers),"duplicate_consumer_publisher")
    publisher = IDENTIFIER.validate_python(config["publication"]["actor_id"],strict=True)
    endpoint,read_token = config["data"]["endpoint"],secret(config["data"]["token_env"])
    publish_token = secret(config["publication"]["token_env"])
    def reader(scope):
        return AssessmentDataReader(endpoint,read_token,scope)
    def transport():
        return HttpTransport(endpoint,publish_token)
    # Validate even a history-only configuration with no active profiles; no peer I/O.
    reader(Scope(tenant_id="configuration",project_id="validation"))
    transport()
    with engine.connect() as connection:
        for table in ("lab_intents","lab_terminals","material_state_revisions","experiment_revisions","observation_revisions",
            "scientific_decisions","decision_sources","decision_observations","decision_consumers",
            "science_publication_headers","science_publication_events","science_publication_leases",
            "scientific_input_intents","scientific_input_outcomes"):
            connection.execute(text(f"SELECT 1 FROM research.{table} LIMIT 1"))
    publications = ScientificPublications(engine,reader,transport,publisher,publishers)
    return ScientificOperations(engine,registry,reader,publications)
