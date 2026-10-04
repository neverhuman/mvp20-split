"""Byte identity and quote geometry are not scientific entailment or source rights."""

import hashlib
from dataclasses import dataclass

from amphora_contracts_planning import ExtractionDraft, ExtractionSource, SourceQuotation

from ..context.policy import require

MAX_SOURCE_BYTES = 4194304


@dataclass(frozen=True)
class SourceText:
    canonical_binding: bytes
    content: bytes

    @classmethod
    def bind(cls, descriptor, content):
        source = ExtractionSource.model_validate_json(descriptor.model_dump_json(warnings=False))
        require(type(content) is bytes and 0 < len(content) <= MAX_SOURCE_BYTES, "extraction_source_size")
        require(source.source.raw.media_type == "text/plain", "extraction_source_format")
        require(len(content) == source.source.raw.size_bytes and
                hashlib.sha256(content).hexdigest() == source.source.raw.sha256, "extraction_source_digest")
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("extraction_source_utf8") from exc
        return cls(source.model_dump_json().encode("utf-8"), content)

    def descriptor(self):
        return ExtractionSource.model_validate_json(self.canonical_binding)

    def verify_quote(self, supplied):
        require(type(supplied.text) is str, "quotation_text_type")
        try:
            encoded = supplied.text.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ValueError("quotation_utf8") from exc
        quote = SourceQuotation.model_validate_json(supplied.model_dump_json(warnings=False))
        span = quote.span
        require(span.source == self.descriptor().source, "quotation_source_mismatch")
        require(0 <= span.start < span.end <= len(self.content), "quotation_bounds")
        selected = self.content[span.start:span.end]
        require(hashlib.sha256(selected).hexdigest() == span.sha256, "quotation_digest")
        require(encoded == selected, "quotation_bytes")


@dataclass(frozen=True)
class SourceBundle:
    sources: tuple[SourceText, ...]

    @classmethod
    def bind(cls, snapshot, supplied):
        require(type(supplied) is tuple and len(supplied) <= 16, "extraction_source_set")
        sources = tuple(SourceText.bind(row.descriptor(), row.content) for row in supplied)
        required = snapshot.document().sources
        require(len(sources) == len(required), "extraction_source_set")
        require(sum(len(row.content) for row in sources) <= MAX_SOURCE_BYTES, "extraction_source_total")
        ordered = []
        for descriptor in required:
            matches = [row for row in sources if row.descriptor() == descriptor]
            require(len(matches) == 1, "extraction_source_set")
            ordered.append(matches[0])
        return cls(tuple(ordered))

    def verify_attribution(self, attribution):
        for quotation in attribution.quotations:
            source = next((row for row in self.sources if row.descriptor().source == quotation.span.source), None)
            require(source is not None, "quotation_source_unselected")
            source.verify_quote(quotation)

    def verify_draft_quotes(self, supplied):
        draft = ExtractionDraft.model_validate_json(supplied.model_dump_json(warnings=False))
        for group in (draft.entities, draft.assertions, draft.questions, draft.answers, draft.evidence_needs):
            for item in group:
                self.verify_attribution(item.attribution)
        return draft
