CREATE TABLE planning.extraction_tasks (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 task_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 task_sha256 char(64) NOT NULL CHECK(task_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,task_id),
 UNIQUE(tenant_id,project_id,engagement_id),
 UNIQUE(tenant_id,project_id,task_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,engagement_id,request_sha256)
 REFERENCES planning.requests(tenant_id,project_id,engagement_id,request_sha256)
);
CREATE TABLE planning.extraction_traces (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 trace_id varchar(128) NOT NULL, task_id varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL, ordinal integer NOT NULL,
 trace_sha256 char(64) NOT NULL CHECK(trace_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 1048576),
 prior_trace_id varchar(128), prior_sha256 char(64),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,trace_id),
 UNIQUE(tenant_id,project_id,trace_id,trace_sha256),
 UNIQUE(tenant_id,project_id,engagement_id,ordinal),
 CHECK((prior_trace_id IS NULL) = (prior_sha256 IS NULL)),
 CHECK(prior_trace_id IS NULL OR prior_trace_id <> trace_id),
 FOREIGN KEY(tenant_id,project_id,task_id,engagement_id)
 REFERENCES planning.extraction_tasks(tenant_id,project_id,task_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal)
 REFERENCES planning.observations(tenant_id,project_id,engagement_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,prior_trace_id,prior_sha256)
 REFERENCES planning.extraction_traces(tenant_id,project_id,trace_id,trace_sha256)
);
GRANT SELECT,INSERT ON planning.extraction_tasks,planning.extraction_traces TO planning_service;
