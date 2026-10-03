"""Actual Qdrant/profile migration preserves old pins and never aligns by dimensions."""

import json
import os
from datetime import datetime
from pathlib import Path

import pytest
from amphora_contracts_evidence import SourceSpan
from amphora_contracts_representations import EncodeSourceRequest, RetrieveRepresentations
from amphora_data_artifacts.representations.bindings.workflow import BindingWorkflow
from amphora_data_artifacts.representations.fixture import fixture_profile
from amphora_data_artifacts.representations.storage.registry import ProfileRegistry
from amphora_data_artifacts.retrieval.mapping import reference_to_wire
from amphora_data_artifacts.retrieval.proof_records import head
from amphora_data_artifacts.retrieval.qdrant.adapter import QdrantAdapter
from amphora_data_artifacts.retrieval.qdrant.configuration import QdrantConfiguration
from amphora_data_artifacts.retrieval.queries.mapping import policy_to_wire
from amphora_data_artifacts.retrieval.queries.policy import QueryPolicy
from amphora_data_artifacts.retrieval.service import RetrievalService
from amphora_data_artifacts.retrieval.validation import RetrievalError
from sqlalchemy import text

pytestmark = [pytest.mark.postgres, pytest.mark.skipif(os.environ.get("AMPHORA_TEST_QDRANT") != "1",
    reason="Explicit actual Qdrant fixture required")]


def test_profile_migration_atomically_selects_new_generation_and_preserves_old_pins(generation):
    from qdrant_fixture import owned_state

    e=generation
    state=owned_state()
    backend=QdrantAdapter(QdrantConfiguration(state['endpoint'],state['api_key']))
    service=RetrievalService(e.ingestion.reads,backend)
    old=service.advance(e.p,e.request)
    assert old.state=='published'
    old_bytes=old.model_dump_json()
    old_query=RetrieveRepresentations(wire_version='1',retrieval_id='old-query',generation=old.generation.reference,
        query=e.binding.reference,policy=policy_to_wire(QueryPolicy(1)))
    old_result=service.queries.retrieve(e.p,old_query)
    assert old_result.matches[0].score==8.0
    profile=fixture_profile('l2',version='2')
    ref=ProfileRegistry(e.engine).register(e.p,profile)
    encoding=EncodeSourceRequest(wire_version='1',encoding_id='normalized',profile=ref,
        source=SourceSpan(source=e.source.reference,unit='byte',start=0,end=4,sha256=e.source.reference.raw.sha256))
    new_binding=BindingWorkflow(e.ingestion.reads,e.ingestion.env.uploads,e.ingestion.env.storage).encode(e.p,encoding).outcome.binding
    assert new_binding.source==e.binding.source
    assert new_binding.reference!=e.binding.reference and new_binding.vector!=e.binding.vector
    assert new_binding.profile.profile_id==e.binding.profile.profile_id
    assert (e.binding.profile.version,new_binding.profile.version)==('1','2')
    request=e.request.model_copy(update={'generation_id':'g2','profile':ref,'bindings':(new_binding.reference,),
        'expected_head':old.generation.reference})
    service.intents.prepare(e.p,request)
    lease=service.leases.claim(e.p,'corpus','g2')
    service.publication.build_and_verify(e.p,lease)
    with e.engine.connect() as c:
        assert reference_to_wire(head(c,e.p,'corpus'))==old.generation.reference
    new_query=old_query.model_copy(update={'retrieval_id':'new-query','generation':reference_to_wire(lease.attempt.generation),
        'query':new_binding.reference})
    with pytest.raises(RetrievalError,match='generation_unpublished'):
        service.queries.retrieve(e.p,new_query)
    current=service.publication.publish(e.p,lease)
    with e.engine.connect() as c:
        assert reference_to_wire(head(c,e.p,'corpus'))==current.generation.reference
    result=service.queries.retrieve(e.p,new_query)
    assert result.matches[0].score==pytest.approx(1.0,abs=1e-6)
    assert result.matches[0].binding==new_binding
    for request in (old_query.model_copy(update={'retrieval_id':'cross-old','query':new_binding.reference}),
        new_query.model_copy(update={'retrieval_id':'cross-new','query':e.binding.reference})):
        with pytest.raises(RetrievalError,match='query_profile'):
            service.queries.retrieve(e.p,request)
    old_again=service.queries.retrieve(e.p,old_query.model_copy(update={'retrieval_id':'old-after-head'}))
    assert old_again.generation==old.generation.reference and old_again.matches==old_result.matches
    assert service.generation(e.p,'corpus','g1',old.generation.reference.sha256).model_dump_json()==old_bytes
    assert service.queries.read(e.p,'old-query')==old_result
    # Explicit replacement of a projection may select old-profile vectors again; history still pins g2.
    rollback=e.request.model_copy(update={'generation_id':'g3','expected_head':current.generation.reference})
    selected=service.advance(e.p,rollback)
    assert selected.state=='published' and selected.generation.manifest.profile==e.binding.profile
    assert service.queries.retrieve(e.p,new_query.model_copy(update={'retrieval_id':'new-after-rollback'})).matches==result.matches
    with e.engine.connect() as c:
        counts={table:c.execute(text('SELECT count(*) FROM artifacts.'+table+' WHERE tenant_id=:tenant AND project_id=:project'),e.p.bindings).scalar_one()
            for table in ('encoding_profiles','encoding_work','representation_bindings','index_publications','retrieval_queries','retrieval_results')}
    assert counts=={'encoding_profiles':2,'encoding_work':2,'representation_bindings':2,'index_publications':3,
        'retrieval_queries':4,'retrieval_results':4}
    evidence={'timestamp_local':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'old':old.model_dump(mode='json'),
        'new':current.model_dump(mode='json'),'rollback':selected.model_dump(mode='json'),
        'old_query':old_result.model_dump(mode='json'),'new_query':result.model_dump(mode='json'),
        'counts':counts,'old_bytes_unchanged':True,'score_tolerance':1e-6,'claim':'Synthetic profile/projection migration only'}
    (Path(__file__).absolute().parents[4]/'.test-results/profile-migration.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
