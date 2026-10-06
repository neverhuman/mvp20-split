import json

from amphora_contracts_core import Scope
from amphora_contracts_evaluation_reuse import ReuseProfile
from sqlalchemy import text

from ..assessment.reader import AssessmentDataReader
from .operations import ReuseOperations
from .producer import ProducerReader
from .profile import ConfiguredReuse


def configured(ledger, config, keys, secret):
    keys(config,('profiles','data','runtime'))
    peers = []
    scope = Scope(tenant_id='configuration',project_id='validation')
    for name, reader in (('data',AssessmentDataReader),('runtime',ProducerReader)):
        keys(config[name],('endpoint','token_env'))
        endpoint,token = config[name]['endpoint'],secret(config[name]['token_env'])
        reader(endpoint,token,scope)
        peers.append((endpoint,token))
    profiles = tuple(ConfiguredReuse(ReuseProfile.model_validate_json(json.dumps(value))) for value in config['profiles'])
    with ledger.engine.connect() as connection:
        connection.execute(text('SELECT sha256 FROM research.evaluation_reuse LIMIT 1'))
    return ReuseOperations(ledger,profiles,
        lambda scope:AssessmentDataReader(*peers[0],scope),lambda scope:ProducerReader(*peers[1],scope))
