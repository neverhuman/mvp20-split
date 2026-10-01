"""Reviewed local fixture parsers: no fetching, instructions, or scientific interpretation."""

import re

from amphora_contracts_evidence import (
    ConversionWarning,
    FieldOrigin,
    PreparedDocument,
    PreparedLabRecord,
    prepared_schema,
)

from .flat_json import parse_fields
from .preparation import PreparedAcquisition, source_span
from .provenance import ProvenanceError, SourceDocument

LAB_FIELDS = ("candidate_id", "candidate_revision", "sample_id", "sample_revision", "method", "context", "value", "unit")


def prepare_document(source: SourceDocument) -> PreparedAcquisition:
    try:
        content = source.content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ProvenanceError("invalid_utf8") from error
    output = PreparedDocument(wire_version="1", text=content).model_dump_json().encode("utf-8")
    fields = (FieldOrigin(target_path="/text", origin="converted",
                          spans=(source_span(source, 0, len(source.content)),), step_indices=(0,)),)
    warnings = () if content else (ConversionWarning(code="empty_document", target_path="/text"),)
    return PreparedAcquisition(source, "utf8-document", output, fields, warnings,
                               "unresolved" if warnings else "normalized", prepared_schema("document"))


def prepare_lab(source: SourceDocument) -> PreparedAcquisition:
    located = parse_fields(source.content, frozenset(LAB_FIELDS))
    values = {key: None if key not in located else located[key].value for key in LAB_FIELDS}
    fields, warnings = [], []
    for key, value in values.items():
        spans = () if key not in located else (source_span(source, located[key].start, located[key].end),)
        fields.append(FieldOrigin(target_path="/" + key, origin="missing" if value is None else "converted",
                                  spans=spans, step_indices=(0,)))
        if value is None or not value.strip():
            warnings.append(ConversionWarning(code="missing_context", target_path="/" + key))
    for key in ("candidate_revision", "sample_revision"):
        value = values[key]
        if value is not None and (not re.fullmatch(r"[1-9][0-9]{0,15}", value)
                                  or int(value) > 9007199254740991):
            warnings.append(ConversionWarning(code="invalid_revision", target_path="/" + key))
    for key in ("candidate_id", "sample_id"):
        if values[key] is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", values[key]):
            warnings.append(ConversionWarning(code="invalid_identity", target_path="/" + key))
    # Preserve the original measurement text; censoring, units and interpretation belong to Research.
    if values["value"] is not None and not re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", values["value"]):
        warnings.append(ConversionWarning(code="uninterpreted_measurement", target_path="/value"))
    output = PreparedLabRecord(wire_version="1", **values).model_dump_json().encode("utf-8")
    warnings.append(ConversionWarning(code="identity_reconciliation_required", target_path=None))
    return PreparedAcquisition(source, "synthetic-lab-json", output, tuple(fields), tuple(warnings), "quarantined",
                               prepared_schema("lab"))
