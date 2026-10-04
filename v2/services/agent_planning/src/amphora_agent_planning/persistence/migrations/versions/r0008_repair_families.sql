CREATE TABLE planning.repair_families (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL, task_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL, policy_sha256 char(64) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 4096),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,task_id,engagement_id)
 REFERENCES planning.extraction_tasks(tenant_id,project_id,task_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,engagement_id,request_sha256)
 REFERENCES planning.requests(tenant_id,project_id,engagement_id,request_sha256),
 FOREIGN KEY(tenant_id,project_id,engagement_id)
 REFERENCES planning.budget_policies(tenant_id,project_id,engagement_id)
);
CREATE TABLE planning.repair_members (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL, task_id varchar(128) NOT NULL,
 root_engagement_id varchar(128) NOT NULL,
 parent_trace_id varchar(128), parent_sha256 char(64),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 4096),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id),
 CHECK((parent_trace_id IS NULL) = (parent_sha256 IS NULL)),
 CHECK((engagement_id = root_engagement_id) = (parent_trace_id IS NULL)),
 FOREIGN KEY(tenant_id,project_id,root_engagement_id)
 REFERENCES planning.repair_families(tenant_id,project_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,task_id,engagement_id)
 REFERENCES planning.extraction_tasks(tenant_id,project_id,task_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,parent_trace_id,parent_sha256)
 REFERENCES planning.extraction_traces(tenant_id,project_id,trace_id,trace_sha256)
);
CREATE INDEX repair_members_family ON planning.repair_members(tenant_id,project_id,root_engagement_id);
GRANT SELECT,INSERT ON planning.repair_families,planning.repair_members TO planning_service;
