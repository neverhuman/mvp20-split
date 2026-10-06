import json

from amphora_contracts_core import Scope
from amphora_contracts_fitness import FitnessProfile
from sqlalchemy import text

from ..assessment.reader import AssessmentDataReader
from .operations import FitnessOperations
from .profile import ConfiguredFitness


def configured(ledger, config, keys, secret):
    keys(config, ("profiles", "data"))
    keys(config["data"], ("endpoint", "token_env"))
    endpoint, token = config["data"]["endpoint"], secret(config["data"]["token_env"])
    profiles = tuple(ConfiguredFitness(FitnessProfile.model_validate_json(json.dumps(value))) for value in config["profiles"])
    AssessmentDataReader(endpoint, token, Scope(tenant_id="configuration", project_id="validation"))
    with ledger.engine.connect() as connection:
        connection.execute(text("SELECT sha256 FROM research.fitness_projections LIMIT 1"))
    return FitnessOperations(ledger, profiles, lambda scope: AssessmentDataReader(endpoint, token, scope))
