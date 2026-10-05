# Supervisor public contracts

Version0.1.0. Runtime owns decision authority; Planning owns context/provider attempts and accounting. This independent package composes existing public Core, Graph Runtime and Planning records without a reverse dependency from Graph Runtime to Planning. No provider SDK, persistence, domain algorithm, credential or endpoint belongs here.

SupervisionSnapshot transports original cut, bounded concrete targets, selected node views/state/output hashes and separate footprint/read-set digests. SupervisionRequest groups Runtime decision/checkpoint/policy identity, that snapshot, original Planning request/digest, absolute Unix-millisecond deadline and bounded lineage. DTO validation does not verify hashes, stored membership, current scope/grants, admitted policy or budgets. Runtime supervision_requests owns projection and cross-record binding; the accepting owner must rederive current state.

Planning decision_scope remains its reviewed declaration digest. It is not either Runtime snapshot digest. Request identity is the scoped Planning engagement; provider attempt ordinal remains separate. Initial lineage has ordinal1 with null parent/root; successors have both digests and ordinal2..16. Cross-record consistency and actual ancestry are separate domain/storage checks. No model may supply accepted execution state through these records.

Tests live under tests/. Strict scalar/tuple/extra-field boundaries, negative wire fixtures and schema preservation are required. Existing profiles remain unchanged. This initial request slice has no response/receipt/command parser or HTTP host; those remain BP-07.04/B1.02b/B1.04. Independent combined public-boundary acceptance is B1.02c.


B1.02a verification:62 scoped request/wire/Runtime-scope/publication cases pass;520 schema files include10 additive files for five supervisor roots and preserve all510 predecessor files. Hash pins and literal original Planning0.69 request bytes live under tests/fixtures. DTO shape alone intentionally accepts a syntactically valid but false digest; Runtime binding tests prove rejection against the original owned footprint/request.
