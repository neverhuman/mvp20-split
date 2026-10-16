"""Conservative byte-aware page counts for reviewed population row envelopes."""
from dataclasses import dataclass

from ..ranking import require
from .work import add,multiply


@dataclass(frozen=True)
class PageEnvelope:
    """Caller-established canonical row/header maxima, including ordinal digits.

    Header includes the empty array brackets. Commas are charged separately.
    This does not establish that actual DTO bytes satisfy the supplied maxima.
    """
    row_bytes: int
    header_bytes: int

    def __post_init__(self):
        require(type(self.row_bytes) is int and 1<=self.row_bytes<=8192,
            "composition_row_bytes")
        require(type(self.header_bytes) is int and 2<=self.header_bytes<=131072,
            "composition_page_header")
        require(self.header_bytes+self.row_bytes<=131072,"composition_page_row_fit")

    def bound(self,rows):
        require(type(rows) is int and rows>=0,"composition_page_rows")
        # Each row uses at most row_bytes, plus all but the first comma.
        per_page=min(64,(131072-self.header_bytes+1)//(self.row_bytes+1))
        count=add(rows,per_page-1)//per_page if rows else 0
        require(count<=512,"composition_page_count")
        size=add(multiply(rows,self.row_bytes),multiply(count,self.header_bytes))
        size=add(size,rows-count)
        return PageFootprint(count,size)


@dataclass(frozen=True)
class PageFootprint:
    pages: int=0
    bytes: int=0

    def __post_init__(self):
        require(type(self.pages) is int and 0<=self.pages<=512,"composition_page_count")
        require(type(self.bytes) is int and 0<=self.bytes<=67108864,
            "composition_page_closure_bytes")
        require((self.pages==0)==(self.bytes==0) and self.bytes<=self.pages*131072,
            "composition_page_footprint")

    def include(self,other):
        require(type(other) is PageFootprint,"composition_page_footprint")
        return PageFootprint(add(self.pages,other.pages),add(self.bytes,other.bytes))
