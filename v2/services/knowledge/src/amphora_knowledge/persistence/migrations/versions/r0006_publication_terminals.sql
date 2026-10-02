CREATE TABLE knowledge.publication_terminals (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 publication_id varchar(128) NOT NULL, position smallint,
 outcome varchar(16) NOT NULL CHECK(outcome IN ('published','failed')),
 policy varchar(128) NOT NULL CHECK(policy = 'knowledge.synthetic_entailment.v1'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 524288),
 sha256 char(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 rejection_bytes bytea CHECK(octet_length(rejection_bytes) BETWEEN 1 AND 262144),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 CHECK(outcome <> 'published' OR (position IS NOT NULL AND rejection_bytes IS NULL)),
 PRIMARY KEY(tenant_id,project_id,graph_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,publication_id) REFERENCES knowledge.reasoning_publications,
 FOREIGN KEY(tenant_id,project_id,graph_id,publication_id,position) REFERENCES knowledge.publication_events
);
GRANT SELECT, INSERT ON knowledge.publication_terminals TO knowledge_service;
