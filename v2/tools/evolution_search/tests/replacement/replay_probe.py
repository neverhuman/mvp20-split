"""Run with an installed public package; shared saved bytes survive replacement."""

import hashlib
import json
from pathlib import Path

from amphora_contracts_search import SearchCheckpoint, SearchSpec
from amphora_evolution_search import (
    CheckpointSnapshot,
    InitialPopulation,
    OriginalSearch,
)
from jsonschema import Draft202012Validator


def verify(specification, retained, output):
    original = OriginalSearch(SearchSpec.model_validate_json(Path(specification).read_bytes()))
    expected = InitialPopulation.generate(original).checkpoint()
    path = Path(retained)
    if not path.exists():
        path.write_bytes(expected.encode())
    raw = path.read_bytes()
    assert expected.encode() == raw
    loaded = CheckpointSnapshot.decode(original, raw)
    assert loaded.encode() == raw
    Draft202012Validator(SearchCheckpoint.model_json_schema()).validate(json.loads(raw))
    resumed = original.resume_random(loaded.record.rng)
    next_value, after = resumed.draw()
    # A fresh stream consumes all retained draws before the next draw.
    fresh = original.initial_random()
    for _ in range(loaded.record.rng.counter):
        _, fresh = fresh.draw()
    independently_advanced, fresh_after = fresh.draw()
    assert next_value.hex() == independently_advanced.hex() and after == fresh_after
    result = {
        "checkpoint_sha256": hashlib.sha256(raw).hexdigest(),
        "specification_sha256": original.digest,
        "pending": [p.model_dump(mode="json") for p in loaded.record.pending],
        "attempts": len(loaded.record.attempts),
        "next_draw_hex": next_value.hex(), "next_counter": after.counter,
    }
    Path(output).write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
