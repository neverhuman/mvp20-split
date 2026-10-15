# Campaign resources contract

Version 0.1.0 owns the additive POP-01.05 bounded draft admission boundary.
Architecture owner: [Runtime architecture](../../../Architecture.md).

`CampaignInvocationResources` requires profile `campaign-invocation-cap-v1` and a
strict integer capacity 1..8. `AdmitResourceBoundedDraft` extends the existing
draft admission with required resources. `parse_resource_bounded_draft` accepts
only `graph.admit_draft_bounded`, uses the numeric canonical command profile and
rejects cross-scope Artifact inputs, including collection members.

This package has no database, network, scheduling or scientific behavior. It imports
only public Core, Commands and Graph Runtime contracts. Runtime must persist the
complete immutable request and enforce capacity using its existing unsettled-attempt
reservation ledger under the run lock. Prepared or uncertain completion retains a
reservation. The cap does not terminate disconnected remote processes.

Legacy admission DTOs, families and bytes are unchanged. An older Runtime must not
resume an active bounded run; installation and recovery qualification belong to
Runtime and Deployment. This DTO publication alone does not implement the route.

Replacement requires identical schemas and command bytes, strict rejection of
unknown profiles/fields and invalid capacity, and scoped Artifact validation.
Tests are owned by `tests/`, registered as `campaign-resources` in dev/test_scopes.json.
Dev schema-publication tests pin every predecessor schema separately.
