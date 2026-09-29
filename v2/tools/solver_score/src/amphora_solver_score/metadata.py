"""Public payload bytes and descriptor finalized with a separately built image identity."""

import hashlib
import json
from importlib.resources import files

from amphora_contracts_core import SchemaRef
from amphora_contracts_tools import ReleaseDescriptor


def schema_bytes(kind):
    if kind not in {"input", "output"}:
        raise ValueError("unknown_payload_schema")
    return files(__package__).joinpath("schemas", kind + ".json").read_bytes()


def schema_ref(kind):
    return SchemaRef(schema_id="synthetic.solver." + {"input": "scorerequest", "output": "scoreresult"}[kind], version="1",
                     sha256=hashlib.sha256(schema_bytes(kind)).hexdigest())


def descriptor(image_sha256):
    raw = json.loads(files(__package__).joinpath("descriptor.template.json").read_bytes())
    raw["tool"]["binding"]["image_sha256"] = image_sha256
    raw["tool"]["inputs"][0]["schema_ref"] = schema_ref("input").model_dump()
    raw["tool"]["outputs"][0]["schema_ref"] = schema_ref("output").model_dump()
    return ReleaseDescriptor.model_validate_json(json.dumps(raw))
