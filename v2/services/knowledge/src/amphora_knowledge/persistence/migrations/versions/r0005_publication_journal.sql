CREATE TABLE knowledge.publication_payloads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 publication_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 20971520),
 sha256 char(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,graph_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,publication_id) REFERENCES knowledge.reasoning_publications
);
CREATE TABLE knowledge.publication_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 publication_id varchar(128) NOT NULL,
 position smallint NOT NULL CHECK(position BETWEEN 1 AND 48),
 ordinal smallint NOT NULL CHECK(ordinal BETWEEN 1 AND 8),
 action varchar(16) NOT NULL CHECK(action IN ('prepared','begun','streaming','streamed','abandoned','finalizing')),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 sha256 char(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 fence bigint NOT NULL CHECK(fence > 0), holder varchar(128) NOT NULL,
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,graph_id,publication_id,position),
 FOREIGN KEY(tenant_id,project_id,graph_id,publication_id) REFERENCES knowledge.publication_payloads
);
GRANT SELECT, INSERT ON knowledge.publication_payloads,knowledge.publication_events TO knowledge_service;
