# Bounded metadata GET transport

Owner: Planning, BP-07.03/B1.02b. This module owns HTTP framing and resource limits for compiled Registry/Runtime/Data metadata reads. Public Tools, Graph Runtime and Representations DTOs are direct dependencies. No peer implementation, database or command writer belongs here. Existing Research/Knowledge POST readers retain their own unchanged profiles.

`MetadataTransport(owner, endpoint, token).read(path, window)` allows only Registry release inventory/exact digest and Runtime definition universe/exact schema and Data retained retrieval query routes. Query keys, duplicates, identifiers, versions and digests are validated before I/O; arbitrary paths, authorities, fragments and control characters reject. Origin is configured authenticated127.0.0.1 HTTP with explicit port. No proxy, redirect, retry, model-selected host or automatic continuation exists.

`MetadataWindow` binds one owner, at most30 seconds and16MiB aggregate response bytes. Registry permits8 calls; Data permits32 calls; Runtime permits257 (one universe plus at most256 selected schemas). Each response is bounded4MiB. A socket shutdown timer bounds slow headers/body; parsing and subsequent identity checks must finish before deadline. Limits are metadata ceilings, not model token budgets or permission to process source Artifacts.

Responses use strict JSON parsing, rejecting duplicate keys, nonfinite values, malformed UTF-8 and invalid public DTOs. Safe metadata errors distinguish denial, missing identity, unavailable peer, media/protocol and budget exhaustion without returning peer bodies or credentials. A transport success proves shape only; the owning registry_access or Runtime metadata reader must bind scope, identities, hashes and scientific/compilation authority.

Tests live under tests/metadata_reads, with loopback HTTP, trickling-body deadlines, closed routes, response/aggregate/call bounds and explicit failure outcomes. Replacement retains exact GET/auth behavior and resource gates. Current Registry client proof does not complete Runtime semantic binding or actual-owner integration; those remain subsequent gates. Defensive closed-socket timer cleanup and alternate empty-read paths are reported coverage gaps.

BP-07.03/B1.02c.ii adds only Data GET /v1/retrieval/queries/{id}, with no query parameters or query creation. Data ownership does not widen Registry/Runtime target catalogs or budgets. Retrieval read history and processing-content access remain separate.

BP-08.04 topology qualification adds one closed Runtime metadata target: GET `/v3/graph-runs/{identifier}?limit=1`, returning GraphRunPageV3. The exact page limit is mandatory; duplicate/unknown query keys and other limits reject. Existing read-only timed/byte/JSON/authentication boundaries apply. No tool SDK path restrictions or existing owner grants are widened. Topology uses a five-second window; this client remains localhost-only.
