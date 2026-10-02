"""Configured scoped principals; no caller-supplied actor or action authority."""

import hashlib

from ..authoring.canonical import KnowledgeError


class Credentials:
    def __init__(self, entries):
        self._grants = {}
        for token, principal in entries:
            if (not isinstance(token, str) or not 32 <= len(token) <= 512
                    or any(not 33 <= ord(char) <= 126 for char in token)):
                raise ValueError("invalid_knowledge_credential")
            digest = hashlib.sha256(token.encode()).digest()
            if digest in self._grants:
                raise ValueError("duplicate_knowledge_credential")
            self._grants[digest] = principal
        if not self._grants:
            raise ValueError("knowledge_credentials_required")

    def authenticate(self, authorization):
        if authorization is None or not authorization.startswith("Bearer ") or len(authorization) > 519:
            raise KnowledgeError("unauthorized")
        try:
            key = hashlib.sha256(authorization[7:].encode("ascii")).digest()
        except UnicodeEncodeError as error:
            raise KnowledgeError("unauthorized") from error
        principal = self._grants.get(key)
        if principal is None:
            raise KnowledgeError("unauthorized")
        return principal
