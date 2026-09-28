"""Case-sensitive symbol counts; explicit alphabet is part of the input."""

from collections import Counter
from dataclasses import dataclass

from .payloads import SequenceInput, SequenceOutput, SymbolCount


@dataclass(frozen=True, slots=True)
class Alphabet:
    symbols: str

    def __post_init__(self):
        if len(set(self.symbols)) != len(self.symbols):
            raise ValueError("duplicate_alphabet_symbol")

    def count(self, sequence):
        counts = Counter(sequence)
        if counts.keys() - set(self.symbols):
            raise ValueError("invalid_sequence_symbol")
        return tuple((symbol, counts[symbol]) for symbol in self.symbols)


def compute(payload: bytes) -> bytes:
    request = SequenceInput.model_validate_json(payload)
    counts = Alphabet(request.alphabet).count(request.sequence)
    result = SequenceOutput(length=len(request.sequence),
        counts=tuple(SymbolCount(symbol=symbol, count=count) for symbol, count in counts))
    return result.model_dump_json().encode()
