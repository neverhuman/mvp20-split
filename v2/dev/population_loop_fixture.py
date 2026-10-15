"""Actual repeated population body; adapted from Runtime numeric_search fixture syntax."""
import copy


def decorate_population_loop(definition):
    body=definition["body"]
    nodes=list(body["nodes"][:-1])
    start=next(index for index,node in enumerate(nodes) if node["node_id"]=="successor_request")
    selected_shape=copy.deepcopy(body["outputs"][0]["value_type"])
    wave=copy.deepcopy(nodes[start:])
    wave[0]["inputs"][0]["source"]={"kind":"input","name":"state"}
    captures=("execution_plan","method_plan","successor_method_scope_path")
    inputs=[{"name":"state","value_type":selected_shape},
        *(copy.deepcopy(port) for port in body["inputs"] if port["name"] in captures)]
    wave.append({"kind":"finish","node_id":"wave_finish","outputs":[{"port":"state",
        "source":{"kind":"output","node_id":"successor_select","port":"result"}}]})
    child={"inputs":inputs,"outputs":[{"name":"state","value_type":selected_shape}],"nodes":wave,
        "edges":[{"source":a["node_id"],"target":b["node_id"],"route":"next"} for a,b in zip(wave,wave[1:])]}
    loop={"kind":"iterate","node_id":"generations","state":[{"name":"state","value_type":selected_shape,
        "initial":{"kind":"output","node_id":"select","port":"result"},"feedback_port":"state"}],
        "captures":[{"port":name,"source":{"kind":"input","name":name}} for name in captures],
        "body":child,"until":{"kind":"compare","left":{"source":{"kind":"result","name":"state"},
            "path":["stopped"],"value_type":{"kind":"scalar","scalar":"boolean","unit":"1"}},
            "operator":"eq","right":{"kind":"boolean","value":True}},"max_iterations":2,"on_limit":"blocked"}
    nodes=[*nodes[:start],loop,{"kind":"finish","node_id":"finish","outputs":[{"port":"result",
        "source":{"kind":"output","node_id":"generations","port":"state"}}]}]
    body["nodes"]=nodes
    body["edges"]=[{"source":a["node_id"],"target":b["node_id"],"route":"next"} for a,b in zip(nodes,nodes[1:])]
