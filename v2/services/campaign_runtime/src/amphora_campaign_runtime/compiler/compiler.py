"""Pure bounded semantic compilation. The caller supplies verified public resolver inputs."""

from .catalog import binding_key
from .errors import require
from .normalization import CompiledCampaign, CompiledNode, CompiledScope, normalize
from .resolution import SchemaUsage, SourceResolver
from .shapes import ArtifactShape, CollectionShape, TypedPort, from_wire, ports
from .topology import ScopeTopology


def collection_policy(policy, shape, maximum, location):
    require(isinstance(shape, CollectionShape), "collection_output_required", location)
    require(shape.maximum >= maximum, "collection_output_bound", location)
    if policy.kind == "partial":
        require(policy.minimum <= maximum, "partial_minimum_bound", location)
        require(shape.missing, "partial_missing_slots_required", location)
        require((policy.close == "deadline") == (policy.deadline_seconds is not None), "partial_deadline_policy", location)


class _Compilation:
    def __init__(self, definition, tools, schemas):
        self.definition, self.tools = definition, tools
        self.usage, self.used_tools, self.scopes = SchemaUsage(schemas), {}, []
        self.node_count, self.scope_count = 0, 0

    def typed_ports(self, values, location):
        result = ports(values, location)
        for port in result:
            self.usage.check(port.shape, location + "." + port.name)
        return result

    def scope(self, body, path=()):
        location = "/".join(path) or "root"
        self.node_count += len(body.nodes)
        self.scope_count += 1
        require(len(path) <= 16 and self.node_count <= 4096 and self.scope_count <= 1024, "graph_complexity_limit", location)
        topology = ScopeTopology(body, location)
        inputs, outputs = self.typed_ports(body.inputs, location), self.typed_ports(body.outputs, location)
        interfaces = {}
        resolver = SourceResolver(self.definition.scope, inputs, interfaces, topology, self.usage)
        for key in topology.order:
            node = topology.nodes[key]
            here = location + "." + key
            node_inputs, node_outputs = (), ()
            if node.kind == "invoke":
                tool = self.tools.require(node.tool, here)
                self.used_tools[binding_key(node.tool)] = tool
                for identity in tool.schemas():
                    self.usage.catalog.require(identity, here)
                    self.usage.identities.add(identity)
                require(node.timeout_seconds <= tool.descriptor.resources.timeout_seconds, "tool_timeout_bound", here)
                node_inputs, node_outputs = tool.ports("inputs"), tool.ports("outputs")
                resolver.bindings(node.inputs, node_inputs, key, here,
                                  optional=tuple(port.name for port in tool.descriptor.tool.inputs if not port.required))
                if node.checkpoint is not None:
                    require(tool.lock.checkpoint_schema is not None, "checkpoint_not_supported", here)
                    checkpoint = resolver.resolve(node.checkpoint, key, here)
                    require(isinstance(checkpoint, ArtifactShape) and checkpoint.schema.record() == tool.lock.checkpoint_schema.model_dump(mode="json"),
                            "checkpoint_schema_mismatch", here)
            elif node.kind == "branch":
                resolver.predicate(node.predicate, key, here)
            elif node.kind == "await":
                subject = resolver.resolve(node.subject, key, here)
                require(isinstance(subject, ArtifactShape), "await_artifact_subject_required", here)
                node_inputs = (TypedPort("subject", subject),)
                node_outputs = self.typed_ports((node.output,), here)
                require(isinstance(node_outputs[0].shape, ArtifactShape), "await_artifact_output_required", here)
            elif node.kind == "join":
                node_outputs = self.typed_ports((node.output,), here)
                shape = node_outputs[0].shape
                collection_policy(node.policy, shape, len(node.members), here)
                require(len({member.member_id for member in node.members}) == len(node.members), "duplicate_join_member", here)
                require(shape.missing or all(member.required for member in node.members), "optional_missing_slots_required", here)
                for member in node.members:
                    actual = resolver.resolve(member.source, key, here, member=True)
                    require(shape.item.accepts(actual), "join_member_type_mismatch", here)
            elif node.kind in {"iterate", "scatter"}:
                child = self.scope(node.body, path + (key,))
                node_inputs = child.inputs
                expected = {port.name: port.shape for port in child.inputs}
                supplied = {binding.port for binding in node.captures}
                if node.kind == "scatter":
                    collection = resolver.resolve(node.collection, key, here)
                    require(isinstance(collection, CollectionShape), "scatter_collection_required", here)
                    require(not collection.missing, "scatter_missing_slots_unsupported", here)
                    require(collection.maximum <= node.max_members, "scatter_membership_bound", here)
                    require(node.item_input in expected and expected[node.item_input].accepts(collection.item), "scatter_item_type_mismatch", here)
                    require(node.item_input not in supplied, "duplicate_capture", here)
                    supplied.add(node.item_input)
                    child_outputs = {port.name: port.shape for port in child.outputs}
                    require(node.result_port in child_outputs, "unknown_scatter_result", here)
                    node_outputs = self.typed_ports((node.output,), here)
                    shape = node_outputs[0].shape
                    collection_policy(node.policy, shape, node.max_members, here)
                    require(shape.item.accepts(child_outputs[node.result_port]), "scatter_result_type_mismatch", here)
                else:
                    require(len({slot.name for slot in node.state}) == len(node.state), "duplicate_loop_state", here)
                    results = {port.name: port.shape for port in child.outputs}
                    for slot in node.state:
                        shape = self.usage.check(from_wire(slot.value_type, here), here)
                        require(slot.name not in supplied, "duplicate_capture", here)
                        supplied.add(slot.name)
                        require(slot.name in expected and expected[slot.name] == shape, "loop_state_input_mismatch", here)
                        require(shape.accepts(resolver.resolve(slot.initial, key, here)), "loop_initial_type_mismatch", here)
                        require(slot.feedback_port in results and shape.accepts(results[slot.feedback_port]), "loop_feedback_type_mismatch", here)
                    resolver.predicate(node.until, key, here, results=results)
                    node_outputs = child.outputs
                require(supplied == set(expected), "scope_input_bindings", here)
                capture_ports = tuple(port for port in child.inputs if port.name in {binding.port for binding in node.captures})
                resolver.bindings(node.captures, capture_ports, key, here)
            else:
                node_inputs = node_outputs = outputs
                resolver.bindings(node.outputs, outputs, key, here)
            interfaces[key] = CompiledNode(key, node_inputs, node_outputs)
        compiled = CompiledScope(path, topology.order, tuple(interfaces[key] for key in sorted(interfaces)), inputs, outputs)
        self.scopes.append(compiled)
        return compiled

    def compile(self):
        pins = self.definition.context
        require(len({(pin.kind, pin.identity) for pin in pins}) == len(pins), "duplicate_context_pin", "context")
        self.scope(self.definition.body)
        require(len(self.used_tools) <= 256 and len(self.usage.identities) <= 512, "plan_lock_limit", "lock")
        return CompiledCampaign(normalize(self.definition), tuple(self.used_tools.values()),
                                tuple(self.usage.identities), tuple(self.scopes)).seal()


def compile_campaign(definition, tools, schemas):
    """Return the matching immutable wire-v2/v3 plan or a bounded error; no writes/I/O."""
    return _Compilation(definition, tools, schemas).compile()
