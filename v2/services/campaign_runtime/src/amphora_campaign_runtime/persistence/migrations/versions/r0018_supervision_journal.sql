CREATE TABLE runtime.supervision_requests (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 decision_id varchar(128) NOT NULL, ordinal integer NOT NULL CHECK (ordinal BETWEEN 1 AND 16),
 plan_sha256 varchar(64) NOT NULL, prepared_by varchar(128) NOT NULL, planning_actor varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL, checkpoint_id varchar(128) NOT NULL,
 request_sha256 varchar(64) NOT NULL CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
 frame_sha256 varchar(64) NOT NULL CHECK (frame_sha256 ~ '^[0-9a-f]{64}$'),
 root_request_sha256 varchar(64), parent_request_sha256 varchar(64),
 canonical_frame bytea NOT NULL CHECK (octet_length(canonical_frame) BETWEEN 1 AND 16777216),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,run_id,decision_id,ordinal),
 UNIQUE (tenant_id,project_id,run_id,decision_id,request_sha256),
 UNIQUE (tenant_id,project_id,planning_actor,engagement_id),
 FOREIGN KEY (tenant_id,project_id,run_id,plan_sha256)
  REFERENCES runtime.graph_runs(tenant_id,project_id,run_id,plan_sha256),
 FOREIGN KEY (tenant_id,project_id,run_id,decision_id,root_request_sha256)
  REFERENCES runtime.supervision_requests(tenant_id,project_id,run_id,decision_id,request_sha256),
 FOREIGN KEY (tenant_id,project_id,run_id,decision_id,parent_request_sha256)
  REFERENCES runtime.supervision_requests(tenant_id,project_id,run_id,decision_id,request_sha256),
 CHECK ((ordinal=1 AND root_request_sha256 IS NULL AND parent_request_sha256 IS NULL)
  OR (ordinal>1 AND root_request_sha256 IS NOT NULL AND parent_request_sha256 IS NOT NULL))
);
CREATE TABLE runtime.supervision_outbox (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 decision_id varchar(128) NOT NULL, request_sha256 varchar(64) NOT NULL,
 actor_id varchar(128) NOT NULL, family varchar(128) NOT NULL CHECK (family='planning.supervision.request'),
 command_id varchar(128) NOT NULL, profile varchar(64) NOT NULL CHECK (profile='amphora-command-v2'),
 command_sha256 varchar(64) NOT NULL CHECK (command_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_command bytea NOT NULL CHECK (octet_length(canonical_command) BETWEEN 1 AND 524288),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,actor_id,family,command_id),
 UNIQUE (tenant_id,project_id,run_id,decision_id,request_sha256),
 FOREIGN KEY (tenant_id,project_id,run_id,decision_id,request_sha256)
  REFERENCES runtime.supervision_requests(tenant_id,project_id,run_id,decision_id,request_sha256)
);
GRANT SELECT,INSERT ON runtime.supervision_requests,runtime.supervision_outbox TO runtime_service;
