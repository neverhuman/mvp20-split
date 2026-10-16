"""Restricted closed public-schema JSON byte upper bounds, without fabricated DTOs."""
import json

from ..ranking import require
from .work import add,multiply


def literal_bytes(value):
    return len(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),
        allow_nan=False).encode("utf-8"))


def bounded_json_bytes(schema):
    """Bound all declared fields, including optional/default fields.

    Only this closed bounded subset is supported. In particular, unrestricted
    numbers/strings, maps, external references and recursive schemas reject.
    A bound does not validate payloads or replace the public DTO validator.
    """
    definitions=schema.get("$defs",{})

    def visit(node,trail=()):
        require(type(node) is dict and len(trail)<32,"composition_json_schema")
        require(not any(key in node for key in ("allOf","not","if","then","else",
            "patternProperties","unevaluatedProperties","prefixItems")),"composition_json_unsupported")
        if "$ref" in node:
            reference=node["$ref"]
            require(type(reference) is str and reference.startswith("#/$defs/")
                and reference not in trail,"composition_json_reference")
            name=reference[len("#/$defs/"):]
            require(name in definitions and "/" not in name,"composition_json_reference")
            return visit(definitions[name],(*trail,reference))
        if "const" in node:return literal_bytes(node["const"])
        if "enum" in node:
            require(type(node["enum"]) is list and bool(node["enum"]),"composition_json_enum")
            return max(literal_bytes(value) for value in node["enum"])
        alternatives=node.get("anyOf",node.get("oneOf"))
        if alternatives is not None:
            require(type(alternatives) is list and bool(alternatives),"composition_json_union")
            return max(visit(item,(*trail,"union")) for item in alternatives)
        kind=node.get("type")
        if kind=="null":return 4
        if kind=="boolean":return 5
        if kind=="string":
            maximum=node.get("maxLength")
            if maximum is None and node.get("pattern")=="^[0-9a-f]{64}$":maximum=64
            require(type(maximum) is int and maximum>=0,"composition_json_string")
            # JSON escapes take at most six bytes per Unicode code point;
            # UTF-8 uses at most four. Quotes are charged separately.
            return add(2,multiply(6,maximum))
        if kind=="integer":
            lower,upper=node.get("minimum"),node.get("maximum")
            require(type(lower) is int and type(upper) is int and lower<=upper,
                "composition_json_integer")
            return max(len(str(lower)),len(str(upper)))
        if kind=="array":
            maximum=node.get("maxItems")
            require(type(maximum) is int and maximum>=0 and "items" in node,
                "composition_json_array")
            item=visit(node["items"],(*trail,"array"))
            return add(2,add(multiply(maximum,item),max(0,maximum-1)))
        if kind=="object":
            require(node.get("additionalProperties") is False and type(node.get("properties")) is dict,
                "composition_json_object")
            fields=node["properties"];size=2
            for name,value in fields.items():
                size=add(size,add(literal_bytes(name)+1,visit(value,(*trail,"object"))))
            return add(size,max(0,len(fields)-1))
        raise ValueError("composition_json_unsupported")

    return visit(schema)
