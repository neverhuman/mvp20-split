"""Conservative graph expansion and queue bounds from public wire-v4 syntax."""
from dataclasses import dataclass
import hashlib
import json

from amphora_contracts_campaigns import ExecutableCampaignV4,ExecutionPlanV4
from amphora_contracts_graph_runtime import GraphLimits
from amphora_contracts_runtime import AttemptBudget
from amphora_contracts_tools import ToolBinding

from ..ranking import require


SAFE_COUNT=9007199254740991
MAX_SCOPE_DEPTH=16


def add(left,right):
    require(type(left) is int and type(right) is int and 0<=right<=SAFE_COUNT
        and 0<=left<=SAFE_COUNT-right,"composition_count_overflow")
    return left+right


def multiply(left,right):
    require(type(left) is int and type(right) is int and 0<=left<=SAFE_COUNT and 0<=right<=SAFE_COUNT
        and (not right or left<=SAFE_COUNT//right),"composition_count_overflow")
    return left*right


@dataclass(frozen=True)
class BindingBudgets:
    materializations: int=0
    projections: int=0
    declared_bytes: int=0
    declared_artifacts: int=0

    def __post_init__(self):
        for count in (self.materializations,self.projections,self.declared_bytes,self.declared_artifacts):
            require(type(count) is int and 0<=count<=SAFE_COUNT,"composition_binding_count")

    def include(self,other,factor):
        return BindingBudgets(*(add(a,multiply(b,factor)) for a,b in zip(
            (self.materializations,self.projections,self.declared_bytes,self.declared_artifacts),
            (other.materializations,other.projections,other.declared_bytes,other.declared_artifacts),strict=True)))


@dataclass(frozen=True)
class ScopeWork:
    activations: int
    scopes: int
    calls: tuple[tuple[ToolBinding,int],...]
    queued_upper: int
    bindings: BindingBudgets

    def __post_init__(self):
        for count in (self.activations,self.scopes,self.queued_upper):
            require(type(count) is int and 0<=count<=SAFE_COUNT,"composition_work_count")
        require(type(self.calls) is tuple and type(self.bindings) is BindingBudgets,"composition_work_shape")
        require(all(type(item) is tuple and len(item)==2 and isinstance(item[0],ToolBinding)
            and type(item[1]) is int and 0<=item[1]<=SAFE_COUNT for item in self.calls),"composition_tool_counts")
        require(len({binding for binding,_ in self.calls})==len(self.calls),"composition_tool_duplicate")
        require(self.scopes>=1 and self.queued_upper<=self.invocations,"composition_scope_counts")

    @property
    def invocations(self):
        total=0
        for _,count in self.calls:total=add(total,count)
        return total


class ScopeTally:
    def __init__(self):
        self.activations=0;self.scopes=1;self.calls={};self.queued=0;self.bindings=BindingBudgets()

    def include(self,child,total_factor,parallel_factor):
        self.activations=add(self.activations,multiply(child.activations,total_factor))
        self.scopes=add(self.scopes,multiply(child.scopes,total_factor))
        self.queued=add(self.queued,multiply(child.queued_upper,parallel_factor))
        self.bindings=self.bindings.include(child.bindings,total_factor)
        for binding,count in child.calls:
            self.calls[binding]=add(self.calls.get(binding,0),multiply(count,total_factor))

    def result(self):
        ordered=tuple(sorted(self.calls.items(),key=lambda item:item[0].model_dump_json()))
        return ScopeWork(self.activations,self.scopes,ordered,self.queued,self.bindings)


def scope_work(body,depth):
    require(depth<=MAX_SCOPE_DEPTH,"composition_scope_depth")
    tally=ScopeTally()
    for node in body.nodes:
        tally.activations=add(tally.activations,1)
        if node.kind=="invoke":
            tally.calls[node.tool]=add(tally.calls.get(node.tool,0),1)
            tally.queued=add(tally.queued,1)
        elif node.kind in {"artifact_project","artifact_materialize"}:
            budgets=BindingBudgets(int(node.kind=="artifact_materialize"),int(node.kind=="artifact_project"),
                node.limits.max_bytes,node.limits.max_artifacts)
            tally.bindings=tally.bindings.include(budgets,1)
        elif node.kind=="scatter":
            child=scope_work(node.body,depth+1)
            tally.include(child,node.max_members,min(node.max_members,node.max_parallel))
        elif node.kind=="iterate":
            child=scope_work(node.body,depth+1)
            tally.include(child,node.max_iterations,1)
        else:
            require(node.kind in {"branch","join","finish"},"composition_node_not_supported")
    return tally.result()


@dataclass(frozen=True)
class GraphWorkBounds:
    definition_sha256: str
    work: ScopeWork
    plan_sha256: str|None=None

    @classmethod
    def from_definition(cls,definition):
        definition=ExecutableCampaignV4.model_validate_json(definition.model_dump_json())
        value=definition.model_dump(mode="json")
        raw=json.dumps(dict(profile="amphora-executable-definition-v4",definition=value),
            sort_keys=True,separators=(",",":"),ensure_ascii=True,allow_nan=False).encode()
        require(len(raw)<=262144,"composition_definition_bytes")
        return cls(hashlib.sha256(raw).hexdigest(),scope_work(definition.body,1))

    @classmethod
    def from_plan(cls,plan,expected_plan_sha256):
        plan=ExecutionPlanV4.model_validate_json(plan.model_dump_json())
        raw=json.dumps(plan.document.model_dump(mode="json"),sort_keys=True,separators=(",",":"),
            ensure_ascii=True,allow_nan=False).encode()
        require(plan.sha256==expected_plan_sha256==hashlib.sha256(raw).hexdigest(),"composition_plan_identity")
        bounds=cls.from_definition(plan.document.definition)
        require(plan.document.lock.definition_sha256==bounds.definition_sha256,"composition_definition_identity")
        return cls(bounds.definition_sha256,bounds.work,plan.sha256)

    def check_admission_budget(self,limits,budget,*,queue_limit=256):
        limits=GraphLimits.model_validate_json(limits.model_dump_json())
        budget=AttemptBudget.model_validate_json(budget.model_dump_json())
        require(type(queue_limit) is int and 1<=queue_limit<=256,"composition_queue_limit")
        require(self.work.activations<=limits.max_activations,"composition_activation_budget")
        require(self.work.queued_upper<=queue_limit,"composition_queue_budget")
        attempts=multiply(self.work.invocations,budget.max_attempts_per_activation)
        require(attempts<=budget.limit,"composition_attempt_budget")
        return attempts
