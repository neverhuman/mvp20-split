CREATE TABLE planning.evaluation_suites (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, suite_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL,
 protocol_sha256 char(64) NOT NULL CHECK(protocol_sha256 ~ '^[0-9a-f]{64}$'),
 batch_sha256 char(64) NOT NULL CHECK(batch_sha256 ~ '^[0-9a-f]{64}$'),
 manifest_bytes bytea NOT NULL CHECK(octet_length(manifest_bytes) BETWEEN 1 AND 1048576),
 corpus_bytes bytea NOT NULL CHECK(octet_length(corpus_bytes) BETWEEN 1 AND 4194304),
 input_bytes bytea NOT NULL CHECK(octet_length(input_bytes) BETWEEN 1 AND 16777216),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,suite_id)
);
GRANT SELECT,INSERT ON planning.evaluation_suites TO planning_service;
