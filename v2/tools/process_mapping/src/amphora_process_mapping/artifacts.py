"""Public-SDK attempt fencing and complete direct ancestry.

Adapted from v2 Search PopulationArtifacts, retaining owner-local validation and
publication identities. No Search implementation dependency or retention grants.
"""
import hashlib
import uuid

from amphora_contracts_artifacts import ContentDescriptor,DerivationDeclaration,TransformationDescriptor

from .validation import PopulationArtifact,canonical,require


class ProcessArtifacts:
    def __init__(self,client,attempt,release,image_sha256):
        self.client,self.attempt=client,attempt
        self.release,self.image_sha256=release,image_sha256
        self.published={}
        self.read_bytes=0

    @property
    def scope(self):return self.client.identity.scope

    def read(self,reference):
        require(reference.scope==self.scope and reference.size_bytes<=262144,"process_source_bound")
        require(self.read_bytes+reference.size_bytes<=67108864,"process_read_budget")
        self.attempt.refresh()
        content=self.client.read(reference)
        self.attempt.check()
        require(type(content) is bytes and len(content)==reference.size_bytes
            and hashlib.sha256(content).hexdigest()==reference.sha256,"process_source_digest")
        self.read_bytes+=len(content)
        return PopulationArtifact(reference,content)

    def check_parents(self,parents):
        references={}
        for ref in (*(binding.artifact for binding in self.attempt.invocation.inputs),*parents):
            require(ref.scope==self.scope,"process_parent_scope")
            require(references.setdefault(ref.artifact_id,ref)==ref,"process_parent_conflict")
        require(1<=len(references)<=128,"process_parent_bound")
        return tuple(references[key] for key in sorted(references))

    def derivation(self,reference):
        require(reference.scope==self.scope,"process_derivation_scope")
        self.attempt.refresh()
        result=self.client.derivation(reference)
        self.attempt.check()
        return result

    def publish(self,record,schema,parents,label):
        raw=canonical(record)
        require(len(raw)<=262144,"process_output_bound")
        parents=self.check_parents(parents)
        content=ContentDescriptor(sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw),
            media_type="application/json",schema_ref=schema)
        declaration=DerivationDeclaration(transformation=TransformationDescriptor(
            transformation_id=self.attempt.invocation.tool.capability_id,version=self.release,
            sha256=self.image_sha256),inputs=parents)
        identity=(content.model_dump_json(),declaration.model_dump_json())
        if label in self.published:
            old,artifact=self.published[label]
            require(old==identity,"process_publication_label_conflict")
            self.attempt.check()
            return artifact
        require(len(self.published)<128,"process_publication_bound")
        key=uuid.uuid5(uuid.NAMESPACE_URL,"amphora.process/publication-v1:"+
            self.attempt.invocation.attempt_id+":"+label).hex
        self.attempt.refresh()
        upload=self.client.begin_derived(content,declaration,"begin-"+key,guard=self.attempt.check).upload
        self.attempt.refresh()
        self.client.stream(upload,raw,guard=self.attempt.check)
        self.attempt.refresh()
        result=self.client.finalize(upload,"finalize-"+key,guard=self.attempt.check)
        self.attempt.check()
        artifact=PopulationArtifact(result.artifact,raw)
        self.published[label]=identity,artifact
        return artifact
