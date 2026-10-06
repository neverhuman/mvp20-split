import pytest

from amphora_research.evaluation_reuse.errors import ReuseError
from amphora_research.evaluation_reuse.resolution import dependencies

from .fixtures import declaration


def test_dependency_identity_conflicts_and_bounded_source_count():
    source=declaration().representation.source
    assert dependencies(source,source)==(source,)
    with pytest.raises(ReuseError,match='identity_conflict'):
        dependencies(source,source.model_copy(update={'sha256':'e'*64}))
    refs=tuple(source.model_copy(update={'artifact_id':'source-'+str(i)}) for i in range(129))
    assert len(dependencies(refs[:128]))==128
    with pytest.raises(ReuseError,match='source_limit'):dependencies(refs)
