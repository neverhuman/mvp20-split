"""Immutable scenario pins and local consistency, with no owner-existence claim."""

import hashlib
import json
from dataclasses import dataclass

from amphora_contracts_core import Scope

from .wire import FixtureManifest

MAX_BYTES = 262144


class ManifestError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise ManifestError(code)


@dataclass(frozen=True, slots=True)
class ScopeBoundary:
    scope: Scope

    def inspect(self, value):
        """Every nested public scope must match, including Artifact/source subreferences."""
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "scope":
                    require(
                        child == self.scope.model_dump(mode="json"), "manifest_scope"
                    )
                self.inspect(child)
        elif isinstance(value, list):
            for child in value:
                self.inspect(child)


@dataclass(frozen=True, slots=True)
class SpecimenSet:
    specimens: tuple

    def verify(self):
        keys, samples, observations = set(), set(), set()
        for item in self.specimens:
            sample = (item.sample.sample_id, item.sample.revision)
            observation = (item.observation.observation_id, item.observation.revision)
            require(item.key not in keys, "duplicate_specimen")
            require(sample not in samples, "duplicate_sample")
            require(observation not in observations, "duplicate_observation")
            keys.add(item.key)
            samples.add(sample)
            observations.add(observation)
        # Equal candidate refs deliberately do not merge different material states/specimens.


@dataclass(frozen=True, slots=True, init=False)
class ScenarioManifest:
    canonical_bytes: bytes
    sha256: str

    def __init__(self, document):
        require(type(document) is FixtureManifest, "manifest_document")
        # Revalidate copied/model-constructed DTOs and retain no caller-owned containers.
        document = FixtureManifest.model_validate_json(document.model_dump_json())
        payload = document.model_dump(mode="json")
        ScopeBoundary(document.scope).inspect(payload)
        span = document.source.span
        require(
            0 <= span.start < span.end <= span.source.raw.size_bytes,
            "manifest_source_span",
        )
        require(span.end - span.start <= 65536, "manifest_source_window")
        require(
            document.graph.assertion.graph == document.graph.snapshot.graph,
            "manifest_graph",
        )
        SpecimenSet(document.specimens).verify()
        views = [(v.owner, v.view_id) for v in document.views]
        require(len(views) == len(set(views)), "duplicate_view")
        raw = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        require(len(raw) <= MAX_BYTES, "manifest_size")
        object.__setattr__(self, "canonical_bytes", raw)
        object.__setattr__(self, "sha256", hashlib.sha256(raw).hexdigest())

    @classmethod
    def parse(cls, raw):
        require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, "manifest_size")

        def unique(pairs):
            result = {}
            for key, value in pairs:
                require(key not in result, "manifest_duplicate_key")
                result[key] = value
            return result

        def invalid_constant(_value):
            raise ManifestError("manifest_nonfinite")

        try:
            decoded = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=unique,
                parse_constant=invalid_constant,
            )
            return cls(
                FixtureManifest.model_validate_json(
                    json.dumps(decoded, allow_nan=False)
                )
            )
        except (UnicodeError, RecursionError) as error:
            raise ManifestError("manifest_encoding") from error

    def document(self):
        return FixtureManifest.model_validate_json(self.canonical_bytes)
