CREATE TABLE planning.supervision_requests (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL, decision_id varchar(128) NOT NULL,
 ordinal integer NOT NULL CHECK (ordinal BETWEEN 1 AND 16),
 planning_request_sha256 char(64) NOT NULL CHECK (planning_request_sha256 ~ '^[0-9a-f]{64}$'),
 request_sha256 char(64) NOT NULL CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_request bytea NOT NULL CHECK (octet_length(canonical_request) BETWEEN 1 AND 262144),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,engagement_id),
 UNIQUE (tenant_id,project_id,run_id,decision_id,ordinal),
 FOREIGN KEY (tenant_id,project_id,engagement_id,planning_request_sha256)
  REFERENCES planning.requests(tenant_id,project_id,engagement_id,request_sha256)
);
CREATE TABLE planning.supervision_commands (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 family varchar(128) NOT NULL CHECK (family='planning.supervision.request'), command_id varchar(128) NOT NULL,
 operation_id varchar(128) NOT NULL, profile varchar(64) NOT NULL CHECK (profile='amphora-command-v2'),
 command_sha256 char(64) NOT NULL CHECK (command_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_command bytea NOT NULL CHECK (octet_length(canonical_command) BETWEEN 1 AND 262144),
 canonical_receipt bytea NOT NULL CHECK (octet_length(canonical_receipt) BETWEEN 1 AND 16384),
 committed_engagement_id varchar(128), recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,actor_id,family,command_id),
 UNIQUE (tenant_id,project_id,operation_id),
 FOREIGN KEY (tenant_id,project_id,committed_engagement_id) REFERENCES planning.supervision_requests
);
GRANT SELECT,INSERT ON planning.supervision_requests,planning.supervision_commands TO planning_service;
