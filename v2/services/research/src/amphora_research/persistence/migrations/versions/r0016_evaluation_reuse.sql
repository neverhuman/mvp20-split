CREATE TABLE research.evaluation_reuse (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 reuse_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 sha256 varchar(64) NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 8388608),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,reuse_id)
);
GRANT SELECT, INSERT ON research.evaluation_reuse TO research_service;
