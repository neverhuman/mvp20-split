from amphora_contracts_core import SchemaRef
from sqlalchemy import text

from ..assessment.reader import AssessmentDataReader
from .profiles import CandidateProfile, CandidateProfiles, CandidateRegistrationError
from .registration import CandidateRegistrar


def configured(ledger, config, keys, secret):
    keys(config, ("data", "profiles"))
    keys(config["data"], ("endpoint", "token_env"))
    endpoint, token = config["data"]["endpoint"], secret(config["data"]["token_env"])
    if not isinstance(config["profiles"], list):
        raise CandidateRegistrationError("candidate_profiles_invalid")
    profiles = []
    for item in config["profiles"]:
        keys(item, ("schema", "kind", "semantic_profile"))
        profiles.append(
            CandidateProfile(
                SchemaRef.model_validate(item["schema"]),
                item["kind"],
                SchemaRef.model_validate(item["semantic_profile"]),
            )
        )
    selected = CandidateProfiles(profiles)
    # Validate transport configuration before admitting service traffic.
    from amphora_contracts_core import Scope

    AssessmentDataReader(
        endpoint, token, Scope(tenant_id="configuration", project_id="validation")
    )
    with ledger.engine.connect() as connection:
        connection.execute(
            text("SELECT record_sha256 FROM research.candidate_registrations LIMIT 1")
        )
    return CandidateRegistrar(
        ledger, selected, lambda scope: AssessmentDataReader(endpoint, token, scope)
    )
