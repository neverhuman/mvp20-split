import hashlib
import json
from pathlib import Path

import pytest
from amphora_contracts_candidate_spaces import SequenceDesign, SequenceMoveRequest
from amphora_sequence_space import (
    OPERATOR,
    PROFILE,
    SequenceDesignError,
    SequenceSpace,
    canonical,
)


def payload():
    data = json.loads(Path(__file__).with_name("request.json").read_bytes())
    data["source"]["profile"] = PROFILE.model_dump(mode="json")
    data["operator"] = OPERATOR.model_dump(mode="json")
    return data


@pytest.mark.parametrize(
    "position,base,expected",
    [(0, "T", "TCGT"), (1, "G", "AGGT"), (3, "A", "ACGA"), (1, "C", "ACGT")],
)
def test_exact_substitution_and_noop(position, base, expected):
    data = payload()
    data["move"].update(position=position, base=base)
    request = SequenceMoveRequest.model_validate_json(json.dumps(data))
    result = SequenceSpace(request.source).apply(request)
    assert result.result.sequence == expected and request.source.sequence == "ACGT"
    assert (
        result.result.scope == request.source.scope
        and result.result.alphabet == "DNA-ACGT-v1"
    )
    assert result.source_sha256 == hashlib.sha256(canonical(request.source)).hexdigest()


@pytest.mark.parametrize("which", ["operator", "source", "position"])
def test_pinned_move_and_bounds(which):
    data = payload()
    space = SequenceSpace(
        SequenceMoveRequest.model_validate_json(json.dumps(data)).source
    )
    if which == "operator":
        data["operator"]["sha256"] = "f" * 64
    elif which == "source":
        data["source"]["sequence"] = "AAAA"
    else:
        data["move"]["position"] = 4
    with pytest.raises(SequenceDesignError):
        space.apply(SequenceMoveRequest.model_validate_json(json.dumps(data)))


def test_foreign_profile_rejects_even_with_dna_shape():
    data = payload()["source"]
    data["profile"]["schema_id"] = "synthetic-polymer-space"
    with pytest.raises(SequenceDesignError, match="profile"):
        SequenceSpace(SequenceDesign.model_validate_json(json.dumps(data)))
