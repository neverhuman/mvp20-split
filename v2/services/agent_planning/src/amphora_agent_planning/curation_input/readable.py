"""Version-two data projection; source packet and immutable schema pins stay intact."""
import base64
import binascii
import hashlib
import json
from copy import deepcopy

from ..context.policy import require
from ..context.snapshot import _constant, _object


def readable_context(context):
    value = deepcopy(context)
    for row in value['slices']:
        if row['lane'] == 'artifact' and row['payload'].get('body_base64') is not None:
            readable_artifact(row)
            continue
        if row['lane'] != 'runtime_schema' or row['payload'].get('status') != 'available':
            continue
        payload = row['payload']
        record = payload['record']
        require(record['reference'] == payload['reference'], 'curation_readable_schema_reference')
        encoded = record.get('schema_bytes_base64')
        require(type(encoded) is str and 0 < len(encoded) <= 1398104, 'curation_readable_schema_size')
        try:
            raw = base64.b64decode(encoded, validate=True)
            require(0 < len(raw) <= 1048576, 'curation_readable_schema_size')
            require(hashlib.sha256(raw).hexdigest() == record['reference']['sha256'], 'curation_readable_schema_digest')
            document = json.loads(raw.decode('utf-8'), object_pairs_hook=_object, parse_constant=_constant)
            require(type(document) in (dict, bool), 'curation_readable_schema_document')
        except (binascii.Error, UnicodeError, json.JSONDecodeError, RecursionError) as error:
            raise ValueError('curation_readable_schema_encoding') from error
        record.pop('schema_bytes_base64')
        record['schema_document'] = document
    return value


def readable_artifact(row):
    payload = row['payload']
    ref = payload['artifact']
    require(ref == row['identity'] and payload['status'] == 'available', 'curation_readable_artifact_reference')
    require(ref['media_type'] in {'text/plain', 'application/json'}, 'curation_readable_artifact_media')
    encoded = payload['body_base64']
    require(type(encoded) is str and len(encoded) <= 5592408, 'curation_readable_artifact_size')
    try:
        raw = base64.b64decode(encoded, validate=True)
        require(len(raw) == ref['size_bytes'] and len(raw) <= 4194304, 'curation_readable_artifact_size')
        require(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'curation_readable_artifact_digest')
        text = raw.decode('utf-8')
        if ref['media_type'] == 'application/json':
            json.loads(text, object_pairs_hook=_object, parse_constant=_constant)
    except (binascii.Error, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ValueError('curation_readable_artifact_encoding') from error
    payload.pop('body_base64')
    payload['body_text'] = text
