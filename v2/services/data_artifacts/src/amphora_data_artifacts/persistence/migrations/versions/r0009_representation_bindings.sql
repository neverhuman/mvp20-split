CREATE TABLE artifacts.encoding_binding_jobs (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 binding_id varchar(128) NOT NULL, actor_id varchar(128) NOT NULL,
 profile_id varchar(128) NOT NULL, version varchar(128) NOT NULL, profile_sha256 varchar(64) NOT NULL,
 source_id varchar(128) NOT NULL, revision_id varchar(128) NOT NULL,
 work_sha256 varchar(64) NOT NULL CHECK(work_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,binding_id),
 UNIQUE(tenant_id,project_id,binding_id,actor_id),
 UNIQUE(tenant_id,project_id,binding_id,work_sha256),
 FOREIGN KEY(tenant_id,project_id,profile_id,version,profile_sha256)
 REFERENCES artifacts.encoding_profiles(tenant_id,project_id,profile_id,version,profile_sha256),
 FOREIGN KEY(tenant_id,project_id,source_id,revision_id) REFERENCES artifacts.source_revisions
);
CREATE TABLE artifacts.encoding_requests (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, encoding_id varchar(128) NOT NULL, binding_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 rights_epoch bytea NOT NULL CHECK(octet_length(rights_epoch) BETWEEN 1 AND 65536),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,actor_id,encoding_id),
 FOREIGN KEY(tenant_id,project_id,binding_id,actor_id)
 REFERENCES artifacts.encoding_binding_jobs(tenant_id,project_id,binding_id,actor_id)
);
CREATE TABLE artifacts.encoding_binding_cursors (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, binding_id varchar(128) NOT NULL,
 attempt bigint NOT NULL DEFAULT 1 CHECK(attempt BETWEEN 1 AND 9007199254740991),
 stage varchar(32) NOT NULL DEFAULT 'prepared' CHECK(stage IN
 ('prepared','begin_prepared','upload_begun','streamed','finalize_prepared','artifact_finalized','published','rejected')),
 token varchar(128) NOT NULL, fence bigint NOT NULL CHECK(fence BETWEEN 1 AND 9007199254740991),
 expires_at timestamptz NOT NULL,
 PRIMARY KEY(tenant_id,project_id,binding_id),
 FOREIGN KEY(tenant_id,project_id,binding_id) REFERENCES artifacts.encoding_binding_jobs
);
CREATE TABLE artifacts.encoding_binding_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, binding_id varchar(128) NOT NULL,
 attempt bigint NOT NULL CHECK(attempt BETWEEN 1 AND 9007199254740991),
 stage varchar(32) NOT NULL CHECK(stage IN
 ('begin_prepared','upload_begun','streamed','finalize_prepared','artifact_finalized','published','rejected')),
 token varchar(128) NOT NULL, fence bigint NOT NULL CHECK(fence BETWEEN 1 AND 9007199254740991),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,binding_id,attempt,stage),
 FOREIGN KEY(tenant_id,project_id,binding_id) REFERENCES artifacts.encoding_binding_jobs
);
CREATE TABLE artifacts.representation_bindings (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, binding_id varchar(128) NOT NULL,
 work_sha256 varchar(64) NOT NULL, artifact_id varchar(128) NOT NULL, artifact_sha256 varchar(64) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,binding_id),
 FOREIGN KEY(tenant_id,project_id,binding_id,work_sha256)
 REFERENCES artifacts.encoding_binding_jobs(tenant_id,project_id,binding_id,work_sha256),
 FOREIGN KEY(tenant_id,project_id,work_sha256) REFERENCES artifacts.encoding_results,
 FOREIGN KEY(tenant_id,project_id,artifact_id,artifact_sha256)
 REFERENCES artifacts.catalog(tenant_id,project_id,artifact_id,content_sha256)
);
GRANT SELECT,INSERT ON artifacts.encoding_binding_jobs,artifacts.encoding_requests,
 artifacts.encoding_binding_cursors,artifacts.encoding_binding_events,artifacts.representation_bindings TO artifact_service;
GRANT UPDATE(attempt,stage,token,fence,expires_at) ON artifacts.encoding_binding_cursors TO artifact_service;
