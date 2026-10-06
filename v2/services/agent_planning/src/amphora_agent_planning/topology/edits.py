"""Single authorized graph edits; no Runtime compiler import or hidden rewrites."""
from amphora_contracts_campaigns import ExecutableCampaignV4
from pydantic import ValidationError
from .values import TopologyRejected, encoded, require


def local_scope(definition, address):
    body=definition['body']
    for name in address.scope_path:
        found=next((n for n in body['nodes'] if n['node_id']==name),None)
        require(found is not None and found['kind'] in {'iterate','scatter'},'topology_scope_unknown')
        body=found['body']
    node=next((n for n in body['nodes'] if n['node_id']==address.node_id),None)
    require(node is not None and node['kind']=='invoke','topology_target_not_invocation')
    return body,node


def port_shape(port):
    return port.schema_ref,port.representation,port.unit,port.required


def swap(state, body, node, edit):
    require(node['tool']==edit.expected_tool.model_dump(mode='json'),'topology_old_tool')
    original=next((lock for lock in state.plan().document.lock.tools if lock.tool==edit.expected_tool),None)
    require(original is not None,'topology_original_lock')
    old,new=state.release(original,active=False),state.release(edit.replacement)
    require(old.tool.binding.capability_id==new.tool.binding.capability_id and old.tool.binding!=new.tool.binding,'topology_evaluator_identity')
    for direction in ('inputs','outputs'):
        require({p.name:port_shape(p) for p in getattr(old.tool,direction)}=={p.name:port_shape(p) for p in getattr(new.tool,direction)},'topology_port_mismatch')
    require(old.tool.checkpoint_schema==new.tool.checkpoint_schema and old.checkpoint==new.checkpoint,'topology_checkpoint_mismatch')
    require(node['timeout_seconds']<=new.resources.timeout_seconds,'topology_timeout')
    require(all(getattr(new.resources,key)<=getattr(old.resources,key) for key in ('cpu_millicores','memory_mib','gpu_count')),'topology_resource_increase')
    node['tool']=new.tool.binding.model_dump(mode='json')


def insert(state, body, node, edit):
    require(not any(n['node_id']==edit.node_id for n in body['nodes']),'topology_insert_duplicate')
    original=next((lock for lock in state.plan().document.lock.tools if lock.tool.model_dump(mode='json')==node['tool']),None)
    require(original is not None,'topology_original_lock')
    target=state.release(original,active=False)
    transform=state.release(edit.transform)
    require(len(transform.tool.inputs)==len(transform.tool.outputs)==1,'topology_transform_unary')
    incoming,outgoing=transform.tool.inputs[0],transform.tool.outputs[0]
    require(incoming.name==edit.transform_input and outgoing.name==edit.transform_output,'topology_transform_port')
    require(incoming.required and outgoing.required and transform.tool.checkpoint_schema is None and transform.checkpoint.mode=='none','topology_transform_state')
    expected=next((p for p in target.tool.inputs if p.name==edit.target_input),None)
    require(expected is not None,'topology_input_unknown')
    # Requiredness belongs to a port; transformed values must retain schema/representation/unit.
    require(port_shape(incoming)[:3]==port_shape(outgoing)[:3]==port_shape(expected)[:3],'topology_port_mismatch')
    bindings=[b for b in node['inputs'] if b['port']==edit.target_input]
    require(len(bindings)==1 and bindings[0]['source']==edit.expected_source.model_dump(mode='json'),'topology_source_changed')
    require(edit.timeout_seconds<=transform.resources.timeout_seconds,'topology_timeout')
    edges=[edge for edge in body['edges'] if edge['target']==node['node_id']]
    require(len(edges)<=1,'topology_insert_control_join')
    for edge in edges:edge['target']=edit.node_id
    body['edges'].append({'source':edit.node_id,'target':node['node_id'],'route':'next'})
    addition={'kind':'invoke','node_id':edit.node_id,'tool':transform.tool.binding.model_dump(mode='json'),
              'inputs':[{'port':edit.transform_input,'source':bindings[0]['source']}],
              'checkpoint':None,'timeout_seconds':edit.timeout_seconds}
    bindings[0]['source']={'kind':'output','node_id':edit.node_id,'port':edit.transform_output}
    body['nodes'].insert(body['nodes'].index(node),addition)


def apply(state, edit, revision):
    definition=state.plan().document.definition.model_dump(mode='json')
    require(revision==definition['revision']+1,'topology_successor_revision')
    body,node=local_scope(definition,edit.target)
    (swap if edit.kind=='evaluator_swap' else insert)(state,body,node,edit)
    definition['revision']=revision
    try:
        result=ExecutableCampaignV4.model_validate_json(encoded(definition))
    except ValidationError as error:
        raise TopologyRejected('topology_result_shape') from error
    require(len(result.model_dump_json().encode())<=1048576,'topology_document_size')
    return result
