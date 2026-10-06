"""Reviewed encoding/scope validation; no operator or scientific inference."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_candidate_spaces import (
    NumericDesign,
    PolymerDesign,
    ProposedDesignChange,
    SequenceDesign,
)
from amphora_contracts_core import SchemaRef

MODELS = {
    "candidate-space.numeric": NumericDesign,
    "candidate-space.polymer": PolymerDesign,
    "candidate-space.sequence": SequenceDesign,
    "candidate-space.change": ProposedDesignChange,
}


class CandidateRegistrationError(ValueError):
    pass


def schema_reference(name):
    model = MODELS.get(name)
    if model is None:
        raise CandidateRegistrationError("candidate_schema_unsupported")
    schema = model.model_json_schema(mode="validation")
    schema.update(
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"urn:amphora:{name}:1:validation",
        }
    )
    raw = (
        json.dumps(
            schema,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()
    return SchemaRef(
        schema_id=name, version="1", sha256=hashlib.sha256(raw).hexdigest()
    )


@dataclass(frozen=True)
class CandidateProfile:
    schema: SchemaRef
    kind: str
    semantic_profile: SchemaRef

    def __post_init__(self):
        if self.kind not in {
            "numeric",
            "polymer",
            "sequence",
        } or self.schema != schema_reference(self.schema.schema_id):
            raise CandidateRegistrationError("candidate_profile_invalid")
        if self.schema.schema_id not in {
            "candidate-space.change",
            "candidate-space." + self.kind,
        }:
            raise CandidateRegistrationError("candidate_profile_kind_mismatch")

    def decode(self, body, scope):
        def unique(pairs):
            values = {}
            for key, value in pairs:
                if key in values:
                    raise CandidateRegistrationError("candidate_duplicate_json_key")
                values[key] = value
            return values

        try:
            if type(body) is not bytes or len(body) > 262144:
                raise CandidateRegistrationError("candidate_representation_limit")
            data = json.loads(body.decode("utf-8"), object_pairs_hook=unique)
            record = MODELS[self.schema.schema_id].model_validate_json(
                json.dumps(data, allow_nan=False)
            )
            design = (
                record.result if isinstance(record, ProposedDesignChange) else record
            )
            if (
                design.scope != scope
                or design.kind != self.kind
                or design.profile != self.semantic_profile
            ):
                raise CandidateRegistrationError(
                    "candidate_representation_binding_mismatch"
                )
            return design
        except CandidateRegistrationError:
            raise
        except (ValueError, TypeError, RecursionError) as error:
            raise CandidateRegistrationError(
                "candidate_representation_invalid"
            ) from error


class CandidateProfiles:
    def __init__(self, profiles):
        self.profiles = tuple(profiles)
        keys = [
            (profile.schema, profile.kind, profile.semantic_profile)
            for profile in self.profiles
        ]
        if not 1 <= len(keys) <= 64 or len(set(keys)) != len(keys):
            raise CandidateRegistrationError("candidate_profiles_invalid")

    def admit(self, reference):
        if reference.media_type != "application/json" or reference.size_bytes > 262144:
            raise CandidateRegistrationError("candidate_representation_limit")
        matches = [
            profile
            for profile in self.profiles
            if profile.schema == reference.schema_ref
        ]
        if not matches:
            raise CandidateRegistrationError("candidate_schema_unconfigured")
        return matches

    def validate(self, reference, body):
        matches = self.admit(reference)
        if (
            type(body) is not bytes
            or len(body) != reference.size_bytes
            or hashlib.sha256(body).hexdigest() != reference.sha256
        ):
            raise CandidateRegistrationError("candidate_representation_integrity")
        for profile in matches:
            try:
                return profile.decode(body, reference.scope)
            except CandidateRegistrationError as error:
                if str(error) != "candidate_representation_binding_mismatch":
                    raise
        raise CandidateRegistrationError("candidate_representation_binding_mismatch")
