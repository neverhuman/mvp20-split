CREATE TABLE planning.topology_proposals (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, proposal_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL,
 record_sha256 char(64) NOT NULL CHECK(record_sha256 ~ '^[0-9a-f]{64}$'),
 record_bytes bytea NOT NULL CHECK(octet_length(record_bytes) BETWEEN 1 AND 8388608),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,proposal_id)
);
GRANT SELECT,INSERT ON planning.topology_proposals TO planning_service;
