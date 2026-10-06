"""Provider schema projection; local action/reference/semantic validation stays authoritative."""

from amphora_contracts_planning import ExtractionDraft, extraction_draft_schema


def response_format(profile):
    if profile != extraction_draft_schema():
        return {"type": "json_object"}
    schema = ExtractionDraft.model_json_schema(mode="validation")

    def strict(value):
        if isinstance(value, list):
            return [strict(item) for item in value]
        if not isinstance(value, dict):
            return value
        result = {
            key: ({name: strict(child) for name, child in item.items()}
                  if key in {"properties", "$defs"} else strict(item))
            for key, item in value.items() if key not in {"default", "title"}
        }
        if result.get("type") == "object":
            result["additionalProperties"] = False
            result["required"] = list(result.get("properties", {}))
        return result

    return {"type": "json_schema", "name": "amphora_extraction_v1", "strict": True, "schema": strict(schema)}
