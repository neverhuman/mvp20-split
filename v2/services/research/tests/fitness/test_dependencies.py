import pytest
from amphora_research.fitness.policy import FitnessError
from amphora_research.fitness.resolution import artifact_dependencies
from ..material_state.test_context import artifact


def test_dependency_deduplication_rejects_conflicting_identities_and_bounds_reads():
    source = artifact()
    assert artifact_dependencies(source,(source,)) == (source,)
    with pytest.raises(FitnessError,match='identity_conflict'):
        artifact_dependencies(source,source.model_copy(update={'sha256':'e'*64}))
    sources = tuple(artifact('source-'+str(i)) for i in range(129))
    assert len(artifact_dependencies(sources[:128])) == 128
    with pytest.raises(FitnessError,match='source_limit'):
        artifact_dependencies(sources)
