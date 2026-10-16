"""Author an explicit finite slice/evaluation loop from an unchanged method body."""
import json

from amphora_contracts_campaigns import ExecutableCampaignV4,IterateV4
from amphora_contracts_population_steps import population_step_schema

from ..population_workers.capabilities import PopulationCapability
from ..ranking import require


def output(node):return {"kind":"output","node_id":node,"port":"result"}


class PrimaryBatchLoop:
    """Pure authoring helper; compiler/admission and frozen-spec checks stay external.

    Initial request must start at zero for complete-cohort evaluation. Its source
    and spec/budget relationship require verification by the enclosing composer.
    No placeholder slice, hidden scheduler, owner I/O or evaluation pruning.
    """
    def __init__(self,method_definition,*,max_population,batch_size,max_parallel,image_sha256):
        self.method=ExecutableCampaignV4.model_validate_json(method_definition.model_dump_json())
        require(type(max_population) is int and 1<=max_population<=1000,"composition_population_limit")
        require(type(batch_size) is int and 1<=batch_size<=32,"composition_batch_size")
        require(type(max_parallel) is int and 1<=max_parallel<=8,"composition_batch_parallel")
        body=self.method.body
        require(len(body.inputs)==1 and body.inputs[0].name=="candidate"
            and body.inputs[0].value_type.kind=="artifact"
            and body.inputs[0].value_type.schema_ref==population_step_schema("population-step.candidate-context")
            and len(body.outputs)==1 and body.outputs[0].name=="result",
            "composition_primary_method_ports")
        require(not any(node.kind in {"scatter","iterate","await"} for node in body.nodes),
            "composition_primary_method_scope")
        self.maximum,self.batch,self.parallel=max_population,batch_size,max_parallel
        self.release=PopulationCapability("slice").descriptor(image_sha256)

    @property
    def request_shape(self):
        port=self.release.tool.inputs[0]
        return dict(kind="artifact",schema_ref=port.schema_ref.model_dump(mode="json"),
            representation=port.representation,unit=port.unit,media_type="application/json")

    @property
    def prepared_shape(self):
        return dict(kind="artifact",schema_ref=population_step_schema("population-step.prepared").model_dump(mode="json"),
            representation=self.release.tool.outputs[0].representation,unit="1",media_type="application/json")

    def build(self,initial,*,prepared,node_id="batches"):
        boolean=dict(kind="scalar",scalar="boolean",unit="1")
        integer=dict(kind="scalar",scalar="integer",unit="1")
        candidate=self.method.body.inputs[0].value_type.model_dump(mode="json")
        result=self.method.body.outputs[0].value_type.model_dump(mode="json")
        limits=dict(max_items=32,max_artifacts=33,max_bytes=262144,timeout_seconds=120)
        nodes=[dict(kind="invoke",node_id="slice",tool=self.release.tool.binding.model_dump(mode="json"),
            inputs=[dict(port="parameters",source=dict(kind="input",name="request"))],
            timeout_seconds=3600,checkpoint=None)]
        def project(name,path,mode,shape):
            nodes.append(dict(kind="artifact_project",node_id=name,source=output("slice"),path=[path],mode=mode,
                output=dict(name="result",value_type=shape),limits=limits))
        project("contexts","members","references",dict(kind="collection",item=candidate,
            max_items=32,missing_slots=False))
        nodes.append(dict(kind="scatter",node_id="evaluate",collection=output("contexts"),
            item_input="candidate",captures=[],max_members=32,max_parallel=self.parallel,
            body=self.method.body.model_dump(mode="json"),result_port="result",
            output=dict(name="result",value_type=dict(kind="collection",item=result,
                max_items=32,missing_slots=True)),
            policy=dict(kind="partial",minimum=0,close="all_terminal",deadline_seconds=None)))
        project("next_index","next_index","values",integer)
        project("complete","complete","values",boolean)
        nodes.append(dict(kind="artifact_materialize",node_id="next_request",fields=[
            dict(name="schema_version",mode="inline",source=dict(kind="string",value="1")),
            dict(name="prepared",mode="references",source=dict(kind="input",name="prepared")),
            dict(name="start_index",mode="inline",source=output("next_index")),
            dict(name="limit",mode="inline",source=dict(kind="integer",value=self.batch,unit="1"))],
            output=dict(name="result",value_type=self.request_shape),limits=limits))
        nodes.append(dict(kind="finish",node_id="finish",outputs=[
            dict(port="request",source=output("next_request")),dict(port="complete",source=output("complete"))]))
        ports=[dict(name="request",value_type=self.request_shape),dict(name="complete",value_type=boolean)]
        body=dict(inputs=[*ports,dict(name="prepared",value_type=self.prepared_shape)],outputs=ports,nodes=nodes,edges=[dict(source=a["node_id"],target=b["node_id"],route="next")
            for a,b in zip(nodes,nodes[1:])])
        loop=dict(kind="iterate",node_id=node_id,state=[dict(name="request",value_type=self.request_shape,
            initial=initial,feedback_port="request"),dict(name="complete",value_type=boolean,
            initial=dict(kind="boolean",value=False),feedback_port="complete")],
            captures=[dict(port="prepared",source=prepared)],body=body,
            until=dict(kind="compare",left=dict(source=dict(kind="result",name="complete"),path=[],value_type=boolean),
                operator="eq",right=dict(kind="boolean",value=True)),
            max_iterations=(self.maximum+self.batch-1)//self.batch,on_limit="blocked")
        return IterateV4.model_validate_json(json.dumps(loop))
