"""Original Runtime command and exact receipt/readback history, without transport."""

from dataclasses import dataclass

from amphora_contracts_supervision import SupervisionCommandReceipt, SupervisionResponse
from sqlalchemy import text

from ..context.policy import require
from ..supervision_client.observations import RecordingObservation
from .leases import KEY, LIVE, key, lock


@dataclass(frozen=True)
class CaptureExchange:
    command: object | None
    observation: RecordingObservation | None
    position: int


class CaptureResponseJournal:
    def __init__(self, captures):
        self.captures = captures
        self.engine = captures.engine

    @staticmethod
    def _command(principal, state):
        reference = None
        if state.payload is not None:
            require(state.attempt.stage == 'finalized', 'capture_not_finalized')
            reference = state.attempt.result.artifact
        return state.identity.command(principal, state.origin, reference)

    def _read(self, conn, principal, params, state):
        command_row = conn.execute(text('SELECT * FROM planning.capture_response_commands WHERE ' + KEY), params).mappings().one_or_none()
        position = conn.execute(text('SELECT response_position FROM planning.capture_publication_control WHERE ' + KEY), params).scalar_one()
        rows = conn.execute(text('SELECT * FROM planning.capture_response_observations WHERE ' + KEY +
            ' ORDER BY position'), params).mappings().all()
        require(len(rows) == position, 'stored_capture_response_position')
        if command_row is None:
            require(not rows, 'stored_capture_response_command_missing')
            return CaptureExchange(None, None, 0)
        command = self._command(principal, state)
        require(command.sha256 == command_row['command_sha256'] and command.canonical_bytes == bytes(command_row['canonical_bytes']),
            'stored_capture_response_command')
        observation = None
        for index, row in enumerate(rows, 1):
            require(row['position'] == index, 'stored_capture_response_position')
            receipt = SupervisionCommandReceipt.model_validate_json(bytes(row['receipt_bytes']))
            raw = None if row['readback_bytes'] is None else bytes(row['readback_bytes'])
            readback = None if raw is None else SupervisionResponse.model_validate_json(raw)
            observation = RecordingObservation.observe(command, receipt, readback=readback, previous=observation)
            require(observation.canonical == bytes(row['receipt_bytes']) and observation.readback_canonical == raw,
                'stored_capture_response_observation')
        return CaptureExchange(command, observation, position)

    def read(self, principal, publication_id):
        principal.require('read_attempts', principal.scope)
        params = key(principal, publication_id)
        with self.engine.begin() as conn:
            lock(conn, params)
            state = self.captures._read(conn, principal, params)
            require(state is not None, 'capture_unknown')
            return self._read(conn, principal, params, state)

    def prepare(self, principal, lease):
        with self.engine.begin() as conn:
            lock(conn, key(principal, lease.publication_id))
            params = self.captures._lease(conn, principal, lease)
            state = self.captures._read(conn, principal, params)
            previous = self._read(conn, principal, params, state)
            if previous.command is not None:
                return previous
            command = self._command(principal, state)
            conn.execute(text('INSERT INTO planning.capture_response_commands '
                '(tenant_id,project_id,publication_id,command_sha256,canonical_bytes) '
                'VALUES (:tenant,:project,:publication,:digest,:body)'),
                {**params, 'digest': command.sha256, 'body': command.canonical_bytes})
            self.captures._lease(conn, principal, lease)
            return self._read(conn, principal, params, state)

    def record(self, principal, lease, expected_position, observation):
        require(type(expected_position) is int and 0 <= expected_position < 64, 'capture_response_limit')
        with self.engine.begin() as conn:
            lock(conn, key(principal, lease.publication_id))
            params = self.captures._lease(conn, principal, lease)
            state = self.captures._read(conn, principal, params)
            previous = self._read(conn, principal, params, state)
            require(previous.command is not None, 'capture_response_command_missing')
            readback = None if observation.readback_canonical is None else SupervisionResponse.model_validate_json(observation.readback_canonical)
            checked = RecordingObservation.observe(previous.command, observation.document(), readback=readback, previous=previous.observation)
            require(checked == observation, 'capture_response_observation')
            if previous.observation == checked:
                return previous
            require(previous.position == expected_position, 'capture_response_position_conflict')
            conn.execute(text('INSERT INTO planning.capture_response_observations '
                '(tenant_id,project_id,publication_id,position,receipt_bytes,readback_bytes) '
                'VALUES (:tenant,:project,:publication,:next,:receipt,:readback)'),
                {**params, 'next': expected_position + 1, 'receipt': checked.canonical, 'readback': checked.readback_canonical})
            result = conn.execute(text('UPDATE planning.capture_publication_control SET response_position=:next WHERE ' + LIVE +
                ' AND response_position=:previous'), {**params, 'next': expected_position + 1, 'previous': expected_position})
            require(result.rowcount == 1, 'capture_lease_or_position_lost')
            return self._read(conn, principal, params, state)
