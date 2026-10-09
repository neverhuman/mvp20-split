# Contract Packages

- [Campaign launch](campaign_launch/README.md): bounded Deployment launch request,
  profile and receipt contracts; exact existing Runtime admission remains authoritative.

Independent Python packages expose public imports, versioned wire schemas and language-neutral fixtures. This directory is navigation, not a shared business-service module.

[Representation contracts](representations/README.md) expose complete encoding profiles, source-specific binding requests, vector Artifact documents and publication status. Data owns interpretation, provenance, rights and storage; these DTOs grant none of those authorities.

- [Core](core/README.md): immutable identity, scope, schema and artifact references.
- [Tools](tools/README.md): tool identity, ports, descriptor and invocation/completion protocol.
- [Campaigns](campaigns/README.md): separate validation-only wire-v1 and executable wire-v2 graph boundaries.
- [Synthetic solver fixture](solver_fixture/README.md): bounded payloads for source-derived orchestration fixtures; no algorithms or scientific authority.
- `fixtures/v1/wire_cases.json`: shared positive/negative interchange fixtures.
- `schemas/v1/manifest.json`: generated schema artifact digests; regenerate with `dev/export_schemas.py`.

Each package owns a manifest and lockfile. Consumers import the package's public root, not `models` internals. Release packaging uses normal declared wheel dependencies; local uv path sources are only development resolution. Scientific applicability, permission, durable acceptance and execution are outside these DTOs. See [Contract Architecture](../docs/Architecture/System/Contract_Architecture.md).

BP-02 adds independently packaged [command encoding](commands/README.md), [runtime wire contracts](runtime/README.md) and [artifact wire contracts](artifacts/README.md). The generated manifest owns current schema counts and hashes. No live persistence authority is implied by schema validity.

BP-03.01 adds separate tool release descriptor, immutable lock, registration payload/receipt and independent eligibility-observation roots. Existing invocation/completion/descriptor roots stay unchanged. Canonical metadata and transport examples are split into `fixtures/v1/tool_releases.json` and `tool_release_messages.json`; registry-owned policy and persistence remain outside this package.

`schemas/v2/manifest.json` owns the new executable definition, plan/lock and activation-path schema digests. `dev/export_schemas.py` publishes/checks both bundles without rewriting wire-v1 identities.

BP-04.02 adds [graph-runtime commands/observations](graph_runtime/README.md) as a separate package. It does not add campaign dependencies to the pinned worker contract/SDK closure. Its distinct graph-runtime namespace publishes additive wire-v1 roots; existing campaign and worker schema bytes remain unchanged.

BP-06.01 adds [acquisition evidence contracts](evidence/README.md): source revisions, exact byte spans and conversion traces. DTO validity does not imply rights, provenance verification or scientific acceptance; owner implementation remains in progress.

[Research identity contracts](research/README.md) distinguish candidate, sample, material-state references and versioned questions/evidence needs. They provide no scientific acceptance or owner state.

[Knowledge contracts](knowledge/README.md) expose scoped typed graph edits, grounding/Research links and structural-only decisions/snapshots. They grant no scientific or persistence authority; the owner implementation remains BP-06.02 work.

[Search/checkpoint contracts](search/README.md): finite numeric specification,portablecheckpoint and scoped evaluation request/observation roots. Eight additive schemas preserve556predecessor bytes; domain acceptance belongs to the search tool.
