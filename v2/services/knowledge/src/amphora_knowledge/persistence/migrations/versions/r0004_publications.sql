CREATE TABLE knowledge.reasoning_publications (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 publication_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 request_id varchar(128) NOT NULL,
 result_sha256 char(64) NOT NULL CHECK(result_sha256 ~ '^[0-9a-f]{64}$'),
 publisher_actor varchar(128) NOT NULL, issuer_id varchar(128) NOT NULL,
 schema_sha256 char(64) NOT NULL CHECK(schema_sha256 ~ '^[0-9a-f]{64}$'),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,graph_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,request_id) REFERENCES knowledge.reasoning_decisions
);
CREATE TABLE knowledge.publication_leases (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, graph_id varchar(128) NOT NULL,
 publication_id varchar(128) NOT NULL,
 fence bigint NOT NULL DEFAULT 0 CHECK(fence >= 0),
 holder varchar(128), expires_at timestamptz,
 CHECK((holder IS NULL) = (expires_at IS NULL)),
 PRIMARY KEY(tenant_id,project_id,graph_id,publication_id),
 FOREIGN KEY(tenant_id,project_id,graph_id,publication_id) REFERENCES knowledge.reasoning_publications
);
GRANT SELECT, INSERT ON knowledge.reasoning_publications,knowledge.publication_leases TO knowledge_service;
GRANT UPDATE(fence,holder,expires_at) ON knowledge.publication_leases TO knowledge_service;
