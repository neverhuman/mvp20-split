import json

import pytest
from amphora_sequence_statistics.kernel import compute
from pydantic import ValidationError


@pytest.mark.parametrize("sequence,alphabet,length,counts", [
    ("ABACA", "ABCD", 5, [("A", 3), ("B", 1), ("C", 1), ("D", 0)]),
    ("", "ACGT", 0, [("A", 0), ("C", 0), ("G", 0), ("T", 0)]),
    ("aAa0", "0Aa", 4, [("0", 1), ("A", 1), ("a", 2)]),
])
def test_explicit_alphabet_golden(sequence, alphabet, length, counts):
    raw = json.dumps({"sequence": sequence, "alphabet": alphabet}).encode()
    assert json.loads(compute(raw)) == {"schema_version": "1", "length": length,
        "counts": [{"symbol": symbol, "count": count} for symbol, count in counts]}
    assert compute(raw) == compute(raw)


@pytest.mark.parametrize("sequence,alphabet,reason", [
    ("ABX", "ABC", "invalid_sequence_symbol"), ("a", "A", "invalid_sequence_symbol"),
    ("A", "AA", "duplicate_alphabet_symbol"),
])
def test_invalid_symbols_are_explicit_failures(sequence, alphabet, reason):
    with pytest.raises(ValueError, match=reason):
        compute(json.dumps({"sequence": sequence, "alphabet": alphabet}).encode())


@pytest.mark.parametrize("change", [{"alphabet": ""}, {"alphabet": "A B"}, {"sequence": "A!"},
    {"sequence": "A" * 65537}, {"sequence": 12}, {"extra": True}])
def test_malformed_payload_rejected(change):
    with pytest.raises(ValidationError):
        compute(json.dumps({"sequence": "A", "alphabet": "A", **change}).encode())
