from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .constants import (
    DOMAIN_IDS,
    MAX_EVIDENCE_SOURCES_PER_PROMPT,
    MIN_RELEVANT_SOURCES,
    MIN_SOURCES_PER_DOMAIN,
    PROMPT_LIMIT_BYTES,
)
from .schemas import canonical_json


DOI_PREFIX_RE = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", re.IGNORECASE)
ARXIV_PREFIX_RE = re.compile(r"^(?:https?://arxiv\.org/(?:abs|pdf)/|arxiv:\s*)", re.IGNORECASE)
ARXIV_VERSION_RE = re.compile(r"v\d+$", re.IGNORECASE)


def normalized_doi(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = DOI_PREFIX_RE.sub("", value.strip()).casefold().rstrip("./")
    return normalized if normalized.startswith("10.") and "/" in normalized else None


def normalized_arxiv_id(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = ARXIV_PREFIX_RE.sub("", value.strip()).casefold()
    normalized = normalized.removesuffix(".pdf").strip("/ ")
    normalized = ARXIV_VERSION_RE.sub("", normalized)
    return normalized or None


def normalized_title(value: Any) -> str:
    title = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return " ".join(re.findall(r"[a-z0-9]+", title))


def source_identity(record: dict[str, Any]) -> tuple[str, str]:
    """Canonical identity in the mandated DOI, arXiv, title priority order."""

    doi = normalized_doi(record.get("doi") or record.get("DOI"))
    if doi:
        return "doi", doi
    arxiv = normalized_arxiv_id(
        record.get("arxiv_id") or record.get("arxiv") or record.get("eprint")
    )
    if arxiv:
        return "arxiv", arxiv
    title = normalized_title(record.get("title"))
    if not title:
        raise ValueError("research source has no DOI, arXiv ID, or title")
    return "title", title


def deduplicate_sources(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deduplicate sources canonically while merging domain and claim coverage."""

    merged: list[dict[str, Any]] = []
    doi_index: dict[str, int] = {}
    arxiv_index: dict[str, int] = {}
    title_index: dict[str, list[int]] = {}
    for record in records:
        if not isinstance(record, dict):
            continue
        try:
            source_identity(record)
        except ValueError:
            continue
        doi = normalized_doi(record.get("doi") or record.get("DOI"))
        arxiv = normalized_arxiv_id(
            record.get("arxiv_id") or record.get("arxiv") or record.get("eprint")
        )
        title = normalized_title(record.get("title"))
        match: int | None = doi_index.get(doi) if doi else None
        if match is None and arxiv:
            match = arxiv_index.get(arxiv)
        if match is None and title:
            for candidate_index in title_index.get(title, []):
                candidate = merged[candidate_index]
                candidate_doi = normalized_doi(candidate.get("doi") or candidate.get("DOI"))
                candidate_arxiv = normalized_arxiv_id(
                    candidate.get("arxiv_id")
                    or candidate.get("arxiv")
                    or candidate.get("eprint")
                )
                if doi and candidate_doi and doi != candidate_doi:
                    continue
                if arxiv and candidate_arxiv and arxiv != candidate_arxiv:
                    continue
                match = candidate_index
                break
        if match is None:
            current = dict(record)
            merged.append(current)
            match = len(merged) - 1
        else:
            current = merged[match]
        domains = set(_domains(current)) | set(_domains(record))
        if domains:
            current["domains"] = sorted(domains)
        for list_field in ("claims", "citation_ids"):
            combined = list(current.get(list_field) or []) + list(record.get(list_field) or [])
            if combined:
                current[list_field] = list(dict.fromkeys(map(str, combined)))
        current["relevant"] = bool(current.get("relevant", True) or record.get("relevant", True))
        if doi and not normalized_doi(current.get("doi") or current.get("DOI")):
            current["doi"] = doi
        if arxiv and not normalized_arxiv_id(
            current.get("arxiv_id") or current.get("arxiv") or current.get("eprint")
        ):
            current["arxiv_id"] = arxiv
        identity = source_identity(current)
        current["canonical_identity"] = {"kind": identity[0], "value": identity[1]}
        current_doi = normalized_doi(current.get("doi") or current.get("DOI"))
        current_arxiv = normalized_arxiv_id(
            current.get("arxiv_id") or current.get("arxiv") or current.get("eprint")
        )
        current_title = normalized_title(current.get("title"))
        if current_doi:
            doi_index[current_doi] = match
        if current_arxiv:
            arxiv_index[current_arxiv] = match
        if current_title and match not in title_index.setdefault(current_title, []):
            title_index[current_title].append(match)
    return merged


def _domains(record: dict[str, Any]) -> list[str]:
    raw = record.get(
        "domains",
        record.get("domain", record.get("aspect_id", record.get("aspect", []))),
    )
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if item in DOMAIN_IDS]


def validate_evidence_coverage(records: Iterable[dict[str, Any]]) -> list[str]:
    relevant = [record for record in records if record.get("relevant", True)]
    errors: list[str] = []
    if len(relevant) < MIN_RELEVANT_SOURCES:
        errors.append(
            f"relevant source count {len(relevant)} is below {MIN_RELEVANT_SOURCES}"
        )
    counts: Counter[str] = Counter()
    for record in relevant:
        counts.update(_domains(record))
    for domain in sorted(DOMAIN_IDS):
        if counts[domain] < MIN_SOURCES_PER_DOMAIN:
            errors.append(
                f"{domain} has {counts[domain]} relevant sources; needs {MIN_SOURCES_PER_DOMAIN}"
            )
    return errors


def citation_registry(records: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    registry: dict[str, dict[str, Any]] = {}
    for source_index, record in enumerate(records, start=1):
        source_id = str(record.get("source_id") or f"source-{source_index:04d}")
        claims = record.get("claims")
        if not isinstance(claims, list) or not claims:
            claims = [record.get("abstract") or record.get("title")]
        for claim_index, claim in enumerate(claims, start=1):
            if not str(claim or "").strip():
                continue
            citation_id = f"{source_id}.claim-{claim_index:02d}"
            registry[citation_id] = {
                "citation_id": citation_id,
                "source_id": source_id,
                "claim": str(claim),
                "title": record.get("title"),
                "doi": normalized_doi(record.get("doi") or record.get("DOI")),
                "arxiv_id": normalized_arxiv_id(
                    record.get("arxiv_id") or record.get("arxiv")
                ),
                "domains": _domains(record),
            }
    return registry


def build_claim_pack(
    records: Iterable[dict[str, Any]],
    domain: str,
    *,
    limit: int = MAX_EVIDENCE_SOURCES_PER_PROMPT,
    max_bytes: int = PROMPT_LIMIT_BYTES,
) -> list[dict[str, Any]]:
    if domain not in DOMAIN_IDS:
        raise ValueError(f"unknown domain: {domain}")
    if limit > MAX_EVIDENCE_SOURCES_PER_PROMPT:
        raise ValueError("claim pack may contain at most ten sources")
    selected = [
        record
        for record in records
        if record.get("relevant", True) and domain in _domains(record)
    ][:limit]
    pack: list[dict[str, Any]] = []
    for record in selected:
        claims = list(
            record.get("claims")
            or [record.get("abstract") or record.get("title")]
        )[:4]
        candidate = {
            "source_id": record.get("source_id"),
            "title": record.get("title"),
            "doi": normalized_doi(record.get("doi") or record.get("DOI")),
            "arxiv_id": normalized_arxiv_id(
                record.get("arxiv_id") or record.get("arxiv")
            ),
            "claims": claims,
            "citation_ids": [
                f"{record.get('source_id')}.claim-{index:02d}"
                for index in range(1, len(claims) + 1)
            ],
        }
        if len(canonical_json(pack + [candidate])) > max_bytes:
            break
        pack.append(candidate)
    return pack


def import_v1_memory(v1_run_root: Path, destination: Path) -> dict[str, Any]:
    """Import ideas as unverified seeds and invalid artifacts as negative memory."""

    destination.mkdir(parents=True, exist_ok=True)
    concepts: list[dict[str, Any]] = []
    negatives: list[dict[str, Any]] = []
    database = v1_run_root / "campaign.sqlite3"
    if database.exists():
        import sqlite3

        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        try:
            for row in connection.execute(
                "SELECT concept_id,domain,payload_json,valid,rejection_reason FROM concepts"
            ):
                item = {
                    "v1_concept_id": row["concept_id"],
                    "domain": row["domain"],
                    "payload": json.loads(row["payload_json"]),
                    "v2_status": "unverified_idea_seed",
                }
                (concepts if row["valid"] else negatives).append(item)
            for row in connection.execute(
                "SELECT memory_id,domain,payload_json FROM memory_items WHERE kind='failure'"
            ):
                negatives.append(
                    {
                        "v1_memory_id": row["memory_id"],
                        "domain": row["domain"],
                        "payload": json.loads(row["payload_json"]),
                        "v2_status": "negative_memory",
                    }
                )
            for row in connection.execute(
                "SELECT job_id,attempt,error,output_sha256 FROM attempts "
                "WHERE success=0 OR error IS NOT NULL"
            ):
                negatives.append(
                    {
                        "v1_job_id": row["job_id"],
                        "attempt": row["attempt"],
                        "error": row["error"],
                        "output_sha256": row["output_sha256"],
                        "v2_status": "invalid_output_negative_memory",
                    }
                )
        finally:
            connection.close()
    (destination / "idea_seeds.json").write_text(
        json.dumps(concepts, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (destination / "negative_memory.json").write_text(
        json.dumps(negatives, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {
        "idea_seeds": len(concepts),
        "negative_items": len(negatives),
        "features_counted": 0,
    }
