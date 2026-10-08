"""Executable dependency graph: separate scientific methods for each candidate."""

CAMPAIGN_ID='polymer-screening-mvp'

def definition(scope,releases,context_type=None,context_pin=None):
    def shape(stage,direction):
        p=releases[stage]['tool'][direction][0]
        return {'kind':'artifact','media_type':'application/json',**{k:p[k] for k in ('schema_ref','representation','unit')}}
    inputs=[];outputs=[];nodes=[];bindings=[];edges=[]
    if context_type:
        port={'name':'campaign_context','value_type':context_type}
        inputs.append(port);outputs.append(port)
        bindings.append({'port':'campaign_context','source':{'kind':'input','name':'campaign_context'}})
    for candidate in ('candidate_a','candidate_b'):
        for stage in ('hansen_solvency','arrhenius_viscosity'):
            name=candidate+'_'+stage
            inputs.append({'name':name,'value_type':shape(stage,'inputs')})
            outputs.append({'name':name,'value_type':shape(stage,'outputs')})
            nodes.append({'kind':'invoke','node_id':name,'tool':releases[stage]['tool']['binding'],
                'inputs':[{'port':'parameters','source':{'kind':'input','name':name}}], 'timeout_seconds':60})
            bindings.append({'port':name,'source':{'kind':'output','node_id':name,'port':'result'}})
            edges.append({'source':name,'target':'retain_scientific_observations','route':'next'})
    nodes.append({'kind':'finish','node_id':'retain_scientific_observations','outputs':bindings})
    return {'schema_version':'4','profile':'deterministic-v3','campaign_id':CAMPAIGN_ID,'revision':2 if context_type else 1,'scope':scope,'context':[context_pin] if context_pin else [],
        'body':{'inputs':inputs,'outputs':outputs,'nodes':nodes,'edges':edges}}
