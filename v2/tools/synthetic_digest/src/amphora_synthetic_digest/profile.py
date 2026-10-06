import hashlib
import json

from amphora_contracts_core import SchemaRef


def pin(name, rules):
    raw = json.dumps({'profile': name, 'version': '1', 'rules': rules},
                     sort_keys=True, separators=(',', ':')).encode('utf-8')
    return SchemaRef(schema_id=name, version='1', sha256=hashlib.sha256(raw).hexdigest())


METHOD = pin('synthetic-digest-score', 'unsigned integer from first six hex digits of declared canonical SHA256; no science')
APPLICABILITY = pin('synthetic-cache-qualification', 'engineering oracle only; purpose synthetic-cache-qualification; no physical interpretation')
UNCERTAINTY = pin('synthetic-digest-exact', 'exact deterministic integer for declared digest; no measurement uncertainty claim')
