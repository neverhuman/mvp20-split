"""Typed conversion interfaces; value validation/publication belong to execution."""

from collections.abc import Mapping

from .errors import require
from .shapes import ArtifactShape, CollectionShape, ScalarShape, TypedPort


class BindingCompiler:
    def __init__(self, resolver, usage):
        self.resolver, self.usage = resolver, usage

    def project(self, node, output, location):
        source = self.resolver.resolve(node.source, node.node_id, location)
        require(isinstance(source, ArtifactShape) and source.media_type == "application/json",
                "binding_json_artifact_required", location)
        schema = self.usage.catalog.require(source.schema, location)
        target = schema.binding_target(node.path, location)
        require(not isinstance(output, ArtifactShape), "binding_project_graph_value_required", location)
        if isinstance(output, ScalarShape):
            require(node.mode == "values", "binding_project_mode", location)
            require(output == schema.project(node.path, source.unit, location), "binding_projection_type", location)
        else:
            require(isinstance(output, CollectionShape) and not output.missing, "binding_project_collection_required", location)
            require(target.get("type") == "array" and "maxItems" in target,
                    "binding_bounded_array_required", location)
            require(target["maxItems"] <= output.maximum <= node.limits.max_items, "binding_member_bound", location)
            if node.mode == "values":
                require(isinstance(output.item, ScalarShape), "binding_scalar_items_required", location)
                # A zero-bound array still declares its item shape; inspect the schema rather than indexing data.
                item = schema._resolve(target.get("items", True), location)
                require(item.get("type") == output.item.name, "binding_projection_type", location)
                unit = item.get("x-amphora-unit", source.unit if output.item.name in {"integer", "number"} else "1")
                require(unit == output.item.unit, "binding_projection_unit", location)
            else:
                require(isinstance(output.item, ArtifactShape) and output.item.media_type == "application/json",
                        "binding_artifact_items_required", location)
                require(output.maximum <= node.limits.max_artifacts, "binding_artifact_bound", location)
                if node.mode == "references":
                    item = schema._resolve(target.get("items", True), location)
                    require(item.get("type") == "object" and {"artifact_id", "scope", "sha256", "schema_ref",
                        "media_type", "size_bytes"} <= set(item.get("required", ())), "binding_reference_manifest_required", location)
                else:
                    require(source.unit == output.item.unit, "binding_projection_unit", location)
                    # Full item content is validated against the pinned output schema before publication.
                    self.usage.catalog.require(output.item.schema, location)
        return (TypedPort("source", source),)

    def materialize(self, node, output, location):
        require(isinstance(output, ArtifactShape) and output.media_type == "application/json",
                "binding_json_artifact_required", location)
        schema = self.usage.catalog.require(output.schema, location)
        target = schema.binding_target((), location)
        names = [field.name for field in node.fields]
        require(len(set(names)) == len(names), "duplicate_materialize_field", location)
        require(target.get("type") == "object", "binding_object_output_required", location)
        require(set(target.get("required", ())) <= set(names) <= set(target.get("properties", {})),
                "binding_materialize_fields", location)
        ports = []
        for field in node.fields:
            value = self.resolver.resolve(field.source, node.node_id, location + "." + field.name)
            if isinstance(value, CollectionShape):
                require(value.maximum <= node.limits.max_items, "binding_member_bound", location)
                if isinstance(value.item, ArtifactShape):
                    require(value.maximum <= node.limits.max_artifacts, "binding_artifact_bound", location)
            if field.mode == "references":
                item = value.item if isinstance(value, CollectionShape) else value
                require(isinstance(item, ArtifactShape), "binding_reference_source_required", location)
            if isinstance(value, ScalarShape):
                require(schema.project((field.name,), output.unit, location).accepts(value), "binding_materialize_type", location)
            else:
                target_field = schema.binding_target((field.name,), location)
                if isinstance(value, CollectionShape):
                    require(target_field.get("type") == "array", "binding_materialize_type", location)
                    require(value.maximum <= target_field.get("maxItems", 10000), "binding_materialize_bound", location)
                    item_schema = target_field.get("items", True)
                    options = item_schema.get("anyOf", ()) if isinstance(item_schema, Mapping) else ()
                    if value.missing:
                        require(any(self._missing(schema._resolve(option, location)) for option in options),
                                "binding_materialize_missing_schema", location)
                    options = options or (item_schema,)
                    require(any(self._compatible(schema._resolve(option, location), value.item, field.mode, output.unit, location)
                                for option in options), "binding_materialize_type", location)
                else:
                    require(self._compatible(target_field, value, field.mode, output.unit, location),
                            "binding_materialize_type", location)
            ports.append(TypedPort(field.name, value))
        return tuple(sorted(ports, key=lambda port: port.name))

    @staticmethod
    def _missing(schema):
        return (schema.get("type") == "object"
            and schema.get("properties", {}).get("kind", {}).get("const") == "missing"
            and {"kind", "member_id", "reason_code"} <= set(schema.get("required", ())))

    def _compatible(self, target, value, mode, parent_unit, location):
        if isinstance(value, ScalarShape):
            return (target.get("type") == value.name or target.get("type") == "number" and value.name == "integer") and (
                target.get("x-amphora-unit", parent_unit if value.name in {"number", "integer"} else "1") == value.unit)
        if mode == "references":
            return target.get("type") == "object" and {"artifact_id", "scope", "sha256", "schema_ref",
                "media_type", "size_bytes"} <= set(target.get("properties", ()))
        require(value.media_type == "application/json", "binding_json_artifact_required", location)
        source = self.usage.catalog.require(value.schema, location).binding_target((), location)
        return target.get("type") == source.get("type") and target.get("x-amphora-unit", parent_unit) == value.unit
