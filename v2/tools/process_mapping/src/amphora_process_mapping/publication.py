"""Preflight complete mapping/ancestry before publishing any child artifacts."""
from dataclasses import dataclass

from amphora_contracts_core import ArtifactRef
from amphora_contracts_population import MembershipPageReference,population_record_schema

from .payloads import MaterialCollection,schema_ref
from .process import MaterialMapping,BoundMaterial
from .validation import require,consistent_references


@dataclass(frozen=True)
class MappingPublication:
    mapping: MaterialMapping
    left: ArtifactRef
    right: ArtifactRef
    parents: tuple
    pages: tuple

    @classmethod
    def load(cls,request,session):
        context=request.context
        require(context.generation.scope==session.scope,"mapping_request_scope")
        require(context.generation.run_id==session.attempt.invocation.run_id,"mapping_request_run")
        collection_schema=schema_ref(MaterialCollection,"process-worker.material-collection")
        sources=tuple(session.read(ref) for ref in (request.left,request.right))
        left,right=(source.decode(MaterialCollection,collection_schema,session.scope) for source in sources)
        require(left.context==right.context==context,"mapping_collection_context")
        references=tuple(item.state for item in (*left.items,*right.items))
        consistent_references((request.left,request.right,*references))
        unique={ref.artifact_id:ref for ref in references}
        materials=tuple(session.read(unique[key]) for key in sorted(unique))
        mapping=MaterialMapping.create(context,request.policy,left.items,right.items,materials)
        parents=[request.left,request.right,*unique.values()]
        metadata={}
        if context.generation.predecessor is not None:
            ref=context.generation.predecessor
            metadata[ref.artifact_id]=ref
        for material in materials:
            bound=BoundMaterial.verify(material,context)
            state=bound.record
            for ref in (state.representation,state.conditions,*((state.composition,) if state.composition else ())):
                require(ref.scope==session.scope,"mapping_metadata_scope")
                require(metadata.setdefault(ref.artifact_id,ref)==ref,"mapping_metadata_conflict")
        consistent_references((*parents,*metadata.values()))
        for key in sorted(metadata):session.read(metadata[key])
        parents.extend(metadata.values())
        # Each page explicitly retains all referenced material/metadata sources.
        # Reject incompatible maxima BEFORE the first upload, never truncate.
        pages=mapping.pages()
        session.check_parents(tuple(parents))
        require(len(pages)+len({request.left.artifact_id,request.right.artifact_id})+
            len(session.attempt.invocation.inputs)<=128,"mapping_manifest_parent_bound")
        return cls(mapping,request.left,request.right,tuple(parents),pages)

    def publish(self,session):
        references=[]
        for page in self.pages:
            artifact=session.publish(page,population_record_schema("population.material-mapping-page"),
                self.parents,"page-"+str(page.ordinal))
            references.append(MembershipPageReference(ordinal=page.ordinal,
                members=len(page.pairs)+len(page.excluded),artifact=artifact.reference))
        record=self.mapping.manifest(self.left,self.right,tuple(references))
        return session.publish(record,population_record_schema("population.material-mapping-manifest"),
            (self.left,self.right,*(ref.artifact for ref in references)),"mapping")
