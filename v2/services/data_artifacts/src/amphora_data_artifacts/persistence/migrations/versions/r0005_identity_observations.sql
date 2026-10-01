ALTER TABLE artifacts.conversion_traces
 ADD UNIQUE(tenant_id,project_id,trace_id,trace_sha256);
CREATE TABLE artifacts.identity_observation_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 observation_id varchar(128) NOT NULL, trace_id varchar(128) NOT NULL, trace_sha256 varchar(64) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16384),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,observation_id),
 FOREIGN KEY(tenant_id,project_id,trace_id,trace_sha256)
 REFERENCES artifacts.conversion_traces(tenant_id,project_id,trace_id,trace_sha256)
);
CREATE TABLE artifacts.identity_observation_results (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, observation_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16384),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,observation_id),
 FOREIGN KEY(tenant_id,project_id,observation_id) REFERENCES artifacts.identity_observation_intents
);
GRANT SELECT,INSERT ON artifacts.identity_observation_intents,artifacts.identity_observation_results TO artifact_service;
