CREATE TABLE runtime.supervision_call_reservations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 decision_id varchar(128) NOT NULL, request_sha256 varchar(64) NOT NULL,
 max_attempts integer NOT NULL CHECK (max_attempts BETWEEN 1 AND 16),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,run_id,request_sha256),
 FOREIGN KEY (tenant_id,project_id,run_id)
  REFERENCES runtime.supervision_recipes(tenant_id,project_id,run_id),
 FOREIGN KEY (tenant_id,project_id,run_id,decision_id,request_sha256)
  REFERENCES runtime.supervision_requests(tenant_id,project_id,run_id,decision_id,request_sha256)
);
GRANT SELECT,INSERT ON runtime.supervision_call_reservations TO runtime_service;
