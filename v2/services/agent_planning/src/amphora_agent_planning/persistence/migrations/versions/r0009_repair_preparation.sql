CREATE TABLE planning.repair_preparations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 engagement_id varchar(128) NOT NULL, root_engagement_id varchar(128) NOT NULL,
 task_id varchar(128) NOT NULL,
 task_sha256 char(64) NOT NULL CHECK(task_sha256 ~ '^[0-9a-f]{64}$'),
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 parent_trace_id varchar(128) NOT NULL, parent_sha256 char(64) NOT NULL,
 manifest_sha256 char(64) NOT NULL CHECK(manifest_sha256 ~ '^[0-9a-f]{64}$'),
 packet_sha256 char(64) NOT NULL CHECK(packet_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,engagement_id)
 REFERENCES planning.repair_members(tenant_id,project_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,root_engagement_id)
 REFERENCES planning.repair_families(tenant_id,project_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,task_id,engagement_id)
 REFERENCES planning.extraction_tasks(tenant_id,project_id,task_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,engagement_id,request_sha256)
 REFERENCES planning.requests(tenant_id,project_id,engagement_id,request_sha256),
 FOREIGN KEY(tenant_id,project_id,parent_trace_id,parent_sha256)
 REFERENCES planning.extraction_traces(tenant_id,project_id,trace_id,trace_sha256)
);
GRANT SELECT,INSERT ON planning.repair_preparations TO planning_service;
