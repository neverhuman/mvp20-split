"""Immutable public byte profiles and safe bounded topology failures."""
import hashlib
import json


class TopologyRejected(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise TopologyRejected(code)


def encoded(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def reconstruct(model, supplied):
    require(type(supplied) is model, 'topology_record_type')
    raw=supplied.model_dump_json(warnings=False)
    require(len(raw.encode())<=1048576,'topology_document_size')
    return model.model_validate_json(raw)
