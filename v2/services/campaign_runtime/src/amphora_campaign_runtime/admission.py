"""Pure invocation binding checks; not authorization, dispatch or scientific review."""

from dataclasses import dataclass

from amphora_contracts_tools import Completion, Invocation, Succeeded, ToolDescriptor

from .graph import Issue


@dataclass(frozen=True)
class InvocationPolicy:
    """Own the dependency/applicability boundary before persistence exists."""

    @staticmethod
    def issues(invocation: Invocation, descriptor: ToolDescriptor) -> tuple[Issue, ...]:
        errors = []

        def add(code: str) -> None:
            errors.append(Issue(code, "invocation", code.replace("_", " ")))

        if invocation.tool != descriptor.binding:
            add("tool_binding_mismatch")
        ports = {p.name: p for p in descriptor.inputs}
        if len(ports) != len(descriptor.inputs) or len({p.name for p in descriptor.outputs}) != len(
            descriptor.outputs
        ):
            add("duplicate_descriptor_port")
        received = [p.port for p in invocation.inputs]
        if len(received) != len(set(received)):
            add("duplicate_input")
        if any(p.required and p.name not in received for p in descriptor.inputs):
            add("missing_required_input")
        for item in invocation.inputs:
            if item.port not in ports:
                add("unknown_input")
            elif item.artifact.schema_ref != ports[item.port].schema_ref:
                add("input_schema_mismatch")
            if item.artifact.scope != invocation.scope:
                add("cross_scope_artifact")
        if invocation.checkpoint is not None:
            if invocation.checkpoint.scope != invocation.scope:
                add("cross_scope_checkpoint")
            if invocation.checkpoint.schema_ref != descriptor.checkpoint_schema:
                add("checkpoint_schema_mismatch")
        return tuple(errors)

    @staticmethod
    def completion_issues(
        completion: Completion, invocation: Invocation, descriptor: ToolDescriptor
    ) -> tuple[Issue, ...]:
        """Only compares supplied bindings; live fences/grants are BP-02 obligations."""
        errors = list(InvocationPolicy.issues(invocation, descriptor))
        if (completion.invocation_id, completion.attempt_id, completion.fence) != (
            invocation.invocation_id,
            invocation.attempt_id,
            invocation.fence,
        ):
            errors.append(Issue("attempt_mismatch", "completion", "Result belongs to a different attempt."))
        if isinstance(completion.outcome, Succeeded):
            # Reuse the same binding rules against output port requirements.
            output_descriptor = descriptor.model_copy(update={"inputs": descriptor.outputs})
            proposed = invocation.model_copy(
                update={"inputs": completion.outcome.outputs, "checkpoint": completion.outcome.checkpoint}
            )
            errors.extend(InvocationPolicy.issues(proposed, output_descriptor))
        return tuple(errors)
