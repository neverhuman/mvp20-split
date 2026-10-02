"""Finite ground implications with explicit polarity and immutable provenance."""

from dataclasses import dataclass
from typing import Literal


class ReasoningError(ValueError):
    """Invalid kernel input; never an accepted domain decision."""


def name(value):
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ReasoningError("invalid_reasoning_name")


@dataclass(frozen=True, order=True)
class Atom:
    subject: str
    predicate: str
    object: str

    def __post_init__(self):
        for value in (self.subject, self.predicate, self.object):
            name(value)


@dataclass(frozen=True, order=True)
class Fact:
    atom: Atom
    polarity: Literal["affirmed", "negated"] = "affirmed"

    def __post_init__(self):
        if type(self.atom) is not Atom or self.polarity not in ("affirmed", "negated"):
            raise ReasoningError("invalid_fact")

    def opposite(self):
        return Fact(self.atom, "negated" if self.polarity == "affirmed" else "affirmed")


@dataclass(frozen=True, order=True)
class Seed:
    fact: Fact
    origin: str

    def __post_init__(self):
        name(self.origin)
        if type(self.fact) is not Fact:
            raise ReasoningError("invalid_seed")


@dataclass(frozen=True)
class Rule:
    rule_id: str
    premises: tuple[Fact, ...]
    conclusion: Fact

    def __post_init__(self):
        name(self.rule_id)
        if (type(self.premises) is not tuple or not 1 <= len(self.premises) <= 16
                or any(type(p) is not Fact for p in self.premises)
                or type(self.conclusion) is not Fact or len(set(self.premises)) != len(self.premises)):
            raise ReasoningError("invalid_ground_rule")
        object.__setattr__(self, "premises", tuple(sorted(self.premises)))


@dataclass(frozen=True)
class Program:
    version: str
    rules: tuple[Rule, ...]

    def __post_init__(self):
        name(self.version)
        if (type(self.rules) is not tuple or len(self.rules) > 256
                or any(type(rule) is not Rule for rule in self.rules)):
            raise ReasoningError("invalid_program")
        if len({rule.rule_id for rule in self.rules}) != len(self.rules):
            raise ReasoningError("duplicate_rule_identity")
        object.__setattr__(self, "rules", tuple(sorted(self.rules, key=lambda rule: rule.rule_id)))


@dataclass(frozen=True)
class Limits:
    depth: int = 32
    work: int = 100_000
    facts: int = 8192

    def __post_init__(self):
        for value, ceiling in ((self.depth, 64), (self.work, 1_000_000), (self.facts, 8192)):
            if type(value) is not int or not 1 <= value <= ceiling:
                raise ReasoningError("invalid_reasoning_limit")


@dataclass(frozen=True)
class Proof:
    fact: Fact
    depth: int
    rule_id: str | None
    premises: tuple[Fact, ...]
    origins: tuple[str, ...]


@dataclass(frozen=True)
class Conclusion:
    status: Literal["supported", "contradicted", "unknown"]
    positive: bool
    negative: bool
    conflict: bool


@dataclass(frozen=True)
class Closure:
    program: Program
    proofs: tuple[Proof, ...]
    complete: bool
    stop_code: str | None
    work: int

    def assess(self, fact):
        present = {proof.fact for proof in self.proofs}
        positive, negative = fact in present, fact.opposite() in present
        status = "unknown"
        if self.complete and positive != negative:
            status = "supported" if positive else "contradicted"
        return Conclusion(status, positive, negative, positive and negative)

    def origins(self, fact):
        """Return original input identities, never treat derivations as new evidence."""
        indexed = {proof.fact: proof for proof in self.proofs}
        pending, visited, origins = [fact], set(), set()
        while pending:
            current = pending.pop()
            if current in visited or current not in indexed:
                continue
            visited.add(current)
            proof = indexed[current]
            origins.update(proof.origins)
            pending.extend(proof.premises)
        return tuple(sorted(origins))
