CREATE TABLE artifacts.source_revisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 source_id varchar(128) NOT NULL, revision_id varchar(128) NOT NULL,
 issuer_id varchar(128) NOT NULL, delivery_id varchar(128) NOT NULL,
 raw_artifact_id varchar(128) NOT NULL, raw_sha256 varchar(64) NOT NULL,
 prior_revision_id varchar(128), canonical_bytes bytea NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,source_id,revision_id),
 UNIQUE(tenant_id,project_id,issuer_id,delivery_id),
 CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 CHECK(prior_revision_id IS NULL OR prior_revision_id<>revision_id),
 FOREIGN KEY(tenant_id,project_id,source_id,prior_revision_id) REFERENCES artifacts.source_revisions,
 FOREIGN KEY(tenant_id,project_id,raw_artifact_id,raw_sha256)
 REFERENCES artifacts.catalog(tenant_id,project_id,artifact_id,content_sha256)
);
CREATE TABLE artifacts.source_heads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 source_id varchar(128) NOT NULL, revision_id varchar(128) NOT NULL,
 PRIMARY KEY(tenant_id,project_id,source_id),
 FOREIGN KEY(tenant_id,project_id,source_id,revision_id) REFERENCES artifacts.source_revisions
);
CREATE TABLE artifacts.conversion_traces (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, trace_id varchar(128) NOT NULL,
 source_id varchar(128) NOT NULL, source_revision_id varchar(128) NOT NULL,
 output_artifact_id varchar(128) NOT NULL, output_sha256 varchar(64) NOT NULL,
 trace_sha256 varchar(64) NOT NULL CHECK(trace_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,trace_id),
 FOREIGN KEY(tenant_id,project_id,source_id,source_revision_id) REFERENCES artifacts.source_revisions,
 FOREIGN KEY(tenant_id,project_id,output_artifact_id,output_sha256)
 REFERENCES artifacts.catalog(tenant_id,project_id,artifact_id,content_sha256)
);
GRANT SELECT, INSERT ON artifacts.source_revisions,artifacts.source_heads,artifacts.conversion_traces TO artifact_service;
GRANT UPDATE(revision_id) ON artifacts.source_heads TO artifact_service;
