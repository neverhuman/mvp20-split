"""Atomic complete selected-tool rounds; uncertainty cannot allocate new identity."""

from amphora_contracts_core import Identifier
from pydantic import TypeAdapter
from sqlalchemy import text

from ..context.policy import require
from .records import CompilerRound
from .store import KEY


class CompilerRounds:
    def __init__(self, operations):
        self.operations = operations

    def read(self, connection, key, check_id):
        TypeAdapter(Identifier).validate_python(check_id, strict=True)
        params = key | {'check': check_id}
        row = connection.execute(text('SELECT * FROM planning.compiler_rounds WHERE ' + KEY + ' AND check_id=:check'),
                                 params).mappings().first()
        if row is None:
            return None
        expected = self.operations.batch(check_id)
        actual = connection.execute(text('SELECT effect_id FROM planning.compiler_effects WHERE ' + KEY +
            ' AND check_id=:check LIMIT 65'), params).scalars().all()
        require(1 <= len(expected) <= 64 and row['expected_count'] == len(expected) and
                set(actual) == {effect.effect_id for effect, _ in expected}, 'compiler_round_coverage')
        states = tuple(self.operations.read(connection, key, effect.effect_id) for effect, _ in expected)
        require(all(item is not None for item in states), 'compiler_round_incomplete')
        return CompilerRound(check_id, row['ordinal'], row['registered_at'], states)

    def prepare(self, connection, key, check_id):
        existing = self.read(connection, key, check_id)
        if existing is not None:
            return existing
        rows = connection.execute(text('SELECT check_id,ordinal FROM planning.compiler_rounds WHERE ' + KEY +
            ' ORDER BY ordinal LIMIT 17'), key).mappings().all()
        require(len(rows) < 16, 'compiler_round_limit')
        require([row['ordinal'] for row in rows] == list(range(1, len(rows) + 1)), 'compiler_round_order')
        if rows:
            previous = self.read(connection, key, rows[-1]['check_id'])
            require(previous is not None and previous.terminal, 'compiler_round_unresolved')
        expected = self.operations.batch(check_id)
        require(1 <= len(expected) <= 64, 'compiler_round_tools')
        connection.execute(text('INSERT INTO planning.compiler_rounds '
            '(tenant_id,project_id,selection_id,check_id,ordinal,expected_count) '
            'VALUES (:tenant,:project,:selection,:check,:ordinal,:count)'),
            key | {'check': check_id, 'ordinal': len(rows) + 1, 'count': len(expected)})
        for effect, request in expected:
            self.operations.insert(connection, key, effect, request)
        return self.read(connection, key, check_id)
