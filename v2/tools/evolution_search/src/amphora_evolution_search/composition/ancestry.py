"""Pure, explicit retained-publication DAG assessment before dispatch."""
from dataclasses import dataclass

from ..ranking import require
from .work import add


@dataclass(frozen=True)
class Publication:
    """A prospective immutable artifact; parents include admitted input carriers."""
    identity: str
    size_bytes: int
    parents: tuple[str,...]=()

    def __post_init__(self):
        require(type(self.identity) is str and bool(self.identity),"composition_artifact_identity")
        require(type(self.size_bytes) is int and 0<=self.size_bytes<=262144,
            "composition_artifact_bytes")
        require(type(self.parents) is tuple and all(type(p) is str and bool(p) for p in self.parents)
            and len(set(self.parents))==len(self.parents),"composition_artifact_parents")
        require(self.identity not in self.parents and len(self.parents)<=128,
            "composition_direct_ancestry")


@dataclass(frozen=True)
class RetainedFootprint:
    artifacts: int
    bytes: int
    largest_ancestor_count: int


class PublicationLedger:
    """Closed explicit DAG, including external source ancestry, without owner I/O.

    A zero-parent record is an explicitly supplied leaf, never an inferred leaf.
    Caller evidence must establish external closure before constructing the ledger.
    This counts content bytes only, not receipt/DB/storage-provider overhead.
    """
    def __init__(self):
        self._records={}
        self._closures={}

    def include(self,publication):
        require(type(publication) is Publication,"composition_publication_shape")
        previous=self._records.get(publication.identity)
        if previous is not None:
            require(previous==publication,"composition_publication_conflict")
            return
        require(all(parent in self._records for parent in publication.parents),
            "composition_ancestry_incomplete")
        closure=set(publication.parents)
        for parent in publication.parents:
            closure.update(self._closures[parent])
            require(len(closure)<4096,"composition_retained_ancestry")
        require(len(closure)<4096,"composition_retained_ancestry")
        self._records[publication.identity]=publication
        self._closures[publication.identity]=frozenset(closure)

    def retained(self,roots):
        require(type(roots) is tuple and bool(roots) and all(type(root) is str
            and root in self._records for root in roots),"composition_retained_roots")
        included=set(roots)
        for root in roots:included.update(self._closures[root])
        size=0
        for identity in included:size=add(size,self._records[identity].size_bytes)
        return RetainedFootprint(len(included),size,max(len(self._closures[item]) for item in included))
