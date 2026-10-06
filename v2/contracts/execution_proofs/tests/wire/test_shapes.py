import json
import pytest
from amphora_contracts_execution_proofs import AcceptedToolExecution
from pydantic import ValidationError


def test_historical_proof_requires_complete_records_and_cannot_be_a_grant():
    for data in ({'wire_version':'1','authority':'accepted_execution','worker_id':'fixture'},
                 {'wire_version':'1','authority':'reuse_permitted','worker_id':'fixture','invocation':{},'completion':{}}):
        with pytest.raises(ValidationError):
            AcceptedToolExecution.model_validate_json(json.dumps(data))
