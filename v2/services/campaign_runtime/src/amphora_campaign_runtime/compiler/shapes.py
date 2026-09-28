"""Domain value shapes own compatibility, bounds and explicit wire projection."""

from dataclasses import dataclass

from .errors import require


@dataclass(frozen=True)
class SchemaIdentity:
    name: str
    version: str
    digest: str

    @classmethod
    def from_wire(cls, value):
        return cls(value.schema_id, value.version, value.sha256)

    def record(self):
        return {"schema_id": self.name, "version": self.version, "sha256": self.digest}


@dataclass(frozen=True)
class ScalarShape:
    name: str
    unit: str = "1"

    def record(self):
        return {"kind": "scalar", "scalar": self.name, "unit": self.unit}

    def accepts(self, other):
        return isinstance(other, ScalarShape) and self.unit == other.unit and (
            self.name == other.name or self.name == "number" and other.name == "integer")


@dataclass(frozen=True)
class ArtifactShape:
    schema: SchemaIdentity
    representation: str
    unit: str
    media_type: str = "application/json"

    @classmethod
    def from_port(cls, port):
        return cls(SchemaIdentity.from_wire(port.schema_ref), port.representation, port.unit)

    def record(self):
        return {"kind": "artifact", "schema_ref": self.schema.record(), "representation": self.representation,
                "unit": self.unit, "media_type": self.media_type}

    def accepts(self, other):
        return self == other


@dataclass(frozen=True)
class CollectionShape:
    item: ScalarShape | ArtifactShape
    maximum: int
    missing: bool

    def record(self):
        return {"kind": "collection", "item": self.item.record(), "max_items": self.maximum, "missing_slots": self.missing}

    def accepts(self, other):
        return isinstance(other, CollectionShape) and self.item.accepts(other.item) and other.maximum <= self.maximum and (
            self.missing or not other.missing)


def from_wire(value, location):
    if value.kind == "scalar":
        require(value.scalar in {"integer", "number"} or value.unit == "1", "nonnumeric_unit", location)
        return ScalarShape(value.scalar, value.unit)
    if value.kind == "artifact":
        return ArtifactShape(SchemaIdentity.from_wire(value.schema_ref), value.representation, value.unit, value.media_type)
    return CollectionShape(from_wire(value.item, location), value.max_items, value.missing_slots)


@dataclass(frozen=True)
class TypedPort:
    name: str
    shape: ScalarShape | ArtifactShape | CollectionShape

    def record(self):
        return {"name": self.name, "value_type": self.shape.record()}


def ports(values, location):
    require(len({value.name for value in values}) == len(values), "duplicate_port", location)
    return tuple(TypedPort(value.name, from_wire(value.value_type, location + "." + value.name))
                 for value in sorted(values, key=lambda item: item.name))
