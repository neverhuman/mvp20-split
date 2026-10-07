"""Offline, bounded deployment evidence verification; no execution authority."""

from .ledger import AcceptanceLedger, EvidenceError

__all__ = ["AcceptanceLedger", "EvidenceError"]
