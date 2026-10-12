"""Immutable campaign preparation rows; no issuance or processing-rights grant."""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text

from ..context.policy import require
from ..persistence import family_state
from ..persistence.journal import KEY, PlanningJournal
from .record import CampaignPreparation


@dataclass(frozen=True)
class StoredCampaignPreparation:
    record: CampaignPreparation
    registered_at: datetime


class CampaignPreparationJournal:
    def __init__(self, engine):
        self.engine = engine
        self.requests = PlanningJournal(engine)

    def _request(self, connection, principal, key):
        request = self.requests._request(connection, key, principal)
        require(request is not None, 'request_unknown')
        require(request.document().purpose in {'campaign_proposal', 'supervision'}, 'campaign_preparation_purpose')
        return request

    def _read(self, connection, key, request):
        row = connection.execute(text('SELECT * FROM planning.campaign_preparations WHERE ' + KEY), key).mappings().first()
        if row is None:
            return None
        return self._stored(row, key, request)

    @staticmethod
    def _stored(row, key, request):
        record = CampaignPreparation.from_bytes(request, bytes(row['canonical_bytes']), bytes(row['packet_bytes']))
        document = record.document()
        require(PlanningJournal._key(document.engagement) == key and
                (row['tenant_id'], row['project_id'], row['engagement_id']) == (key['tenant'], key['project'], key['engagement']) and
                (row['request_sha256'], row['manifest_sha256'], row['plan_sha256'], row['packet_sha256']) ==
                (document.request_sha256, record.sha256, document.plan_sha256, document.packet.sha256),
                'stored_campaign_preparation_corrupt')
        return StoredCampaignPreparation(record, row['registered_at'])

    def register(self, principal, plan, packet, *, guard=None):
        reference = plan.request.document().reference
        principal.require('record_attempts', reference.scope)
        require(plan.request.document().actor_id == principal.actor_id, 'request_actor_mismatch')
        record = CampaignPreparation.bind(plan, packet)
        document = record.document()
        key = self.requests._key(reference)
        with self.engine.begin() as connection:
            membership = family_state.lock_request(connection, key)
            require(membership is None, 'campaign_preparation_extraction_family')
            request = self._request(connection, principal, key)
            require(request.canonical == record.packet.request.canonical, 'request_conflict')
            existing = self._read(connection, key, request)
            if existing is not None:
                require(existing.record.canonical == record.canonical and existing.record.packet.canonical == record.packet.canonical,
                        'campaign_preparation_conflict')
                return existing
            consumed = connection.execute(text('SELECT EXISTS (SELECT 1 FROM planning.dispatches WHERE ' + KEY +
                ' UNION ALL SELECT 1 FROM planning.observations WHERE ' + KEY + ')'), key).scalar_one()
            require(not consumed, 'campaign_preparation_after_call')
            if guard is not None:
                guard(connection)
            connection.execute(text('INSERT INTO planning.campaign_preparations '
                '(tenant_id,project_id,engagement_id,request_sha256,manifest_sha256,plan_sha256,packet_sha256,canonical_bytes,packet_bytes) '
                'VALUES (:tenant,:project,:engagement,:request,:manifest,:plan,:packet,:content,:packet_content)'),
                {**key, 'request': document.request_sha256, 'manifest': record.sha256, 'plan': document.plan_sha256,
                 'packet': document.packet.sha256, 'content': record.canonical, 'packet_content': record.packet.canonical})
            return self._read(connection, key, request)

    def read(self, principal, reference):
        principal.require('read_attempts', reference.scope)
        key = self.requests._key(reference)
        with self.engine.connect() as connection:
            request = self._request(connection, principal, key)
            return self._read(connection, key, request)
