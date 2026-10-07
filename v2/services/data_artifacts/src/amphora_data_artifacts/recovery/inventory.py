"""Data alone enumerates its catalog and validates the retained immutable bytes."""

import hashlib
import json
import time
from dataclasses import dataclass, field

from amphora_contracts_core import ArtifactRef
from sqlalchemy import text

from ..publication.model import UploadError


@dataclass(frozen=True)
class CatalogEntry:
    reference: ArtifactRef
    storage_key: str

    @classmethod
    def from_row(cls, row):
        reference = ArtifactRef.model_validate({'artifact_id': row['artifact_id'],
            'scope': {'tenant_id': row['tenant_id'], 'project_id': row['project_id']},
            'sha256': row['content_sha256'], 'size_bytes': row['size_bytes'],
            'media_type': row['media_type'], 'schema_ref': row['schema_ref']})
        return cls(reference, row['storage_key'])

    def record(self):
        return {'artifact': self.reference.model_dump(mode='json'), 'storage_key': self.storage_key}

    def verify(self, storage, deadline):
        fingerprint, count = hashlib.sha256(), 0
        try:
            with storage.path(self.storage_key).open('rb') as stream:
                while block := stream.read(1024 * 1024):
                    if time.monotonic() >= deadline:
                        raise TimeoutError('catalog_audit_deadline')
                    count += len(block)
                    if count > self.reference.size_bytes:
                        return 'content_mismatch'
                    fingerprint.update(block)
        except TimeoutError:
            raise
        except FileNotFoundError:
            return 'content_missing'
        except (OSError, UploadError):
            return 'content_unreadable'
        return 'verified' if count == self.reference.size_bytes and fingerprint.hexdigest() == self.reference.sha256 else 'content_mismatch'


@dataclass
class AuditTotals:
    checked: int = 0
    verified: int = 0
    verified_bytes: int = 0
    failures: dict = field(default_factory=dict)
    fingerprint: object = field(default_factory=hashlib.sha256)

    def observe(self, entry, result):
        self.checked += 1
        raw = json.dumps(entry.record(), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()
        self.fingerprint.update(len(raw).to_bytes(8, 'big') + raw)
        if result == 'verified':
            self.verified += 1
            self.verified_bytes += entry.reference.size_bytes
        else:
            self.failures[result] = self.failures.get(result, 0) + 1

    def result(self):
        return {'profile': 'data-catalog-integrity-v1', 'status': 'verified' if not self.failures else 'failed',
                'checked': self.checked, 'verified': self.verified, 'verified_bytes': self.verified_bytes,
                'failures': dict(sorted(self.failures.items())), 'catalog_sha256': self.fingerprint.hexdigest(),
                'authority': 'byte_integrity_only_not_scientific_or_restore_acceptance'}


class CatalogAudit:
    def __init__(self, engine, storage):
        self.engine, self.storage = engine, storage

    def run(self, *, scope=None, seconds=300, maximum_entries=100000, inventory=None):
        if type(seconds) is not int or not 1 <= seconds <= 3600:
            raise ValueError('catalog_audit_seconds')
        if type(maximum_entries) is not int or not 1 <= maximum_entries <= 1000000:
            raise ValueError('catalog_audit_limit')
        deadline, totals = time.monotonic() + seconds, AuditTotals()
        query = ('SELECT tenant_id,project_id,artifact_id,content_sha256,size_bytes,media_type,schema_ref,storage_key '
                 'FROM artifacts.catalog')
        parameters = {}
        if scope is not None:
            query += ' WHERE tenant_id=:tenant AND project_id=:project'
            parameters = {'tenant': scope.tenant_id, 'project': scope.project_id}
        query += ' ORDER BY tenant_id,project_id,artifact_id'
        with self.engine.connect() as connection:
            connection.exec_driver_sql('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            if connection.execute(text('SELECT current_user')).scalar_one() != 'artifact_service':
                raise ValueError('catalog_audit_service_role')
            records = connection.execution_options(stream_results=True).execute(text(query), parameters).mappings()
            for row in records:
                if totals.checked >= maximum_entries or time.monotonic() >= deadline:
                    raise TimeoutError('catalog_audit_incomplete')
                entry = CatalogEntry.from_row(row)
                result = entry.verify(self.storage, deadline)
                totals.observe(entry, result)
                if inventory is not None:
                    inventory.write(json.dumps(entry.record() | {'integrity': result}, sort_keys=True) + '\n')
            pending_query = "SELECT count(*) FROM artifacts.reservations WHERE status='reserved'"
            if scope is not None:
                pending_query += ' AND tenant_id=:tenant AND project_id=:project'
            pending = connection.execute(text(pending_query), parameters).scalar_one()
        # Integrity and unresolved retention are separate facts; neither silently clears a hold.
        return totals.result() | {'pending_reservations': pending}
