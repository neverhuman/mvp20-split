CREATE TABLE artifacts.source_rights_revisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, rights_id varchar(128) NOT NULL,
 revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 16384),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,rights_id,revision)
);
CREATE TABLE artifacts.source_rights_heads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, rights_id varchar(128) NOT NULL,
 revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,rights_id),
 FOREIGN KEY(tenant_id,project_id,rights_id,revision) REFERENCES artifacts.source_rights_revisions
);
CREATE INDEX source_raw_rights_lookup ON artifacts.source_revisions(tenant_id,project_id,raw_artifact_id);
CREATE INDEX trace_output_rights_lookup ON artifacts.conversion_traces(tenant_id,project_id,output_artifact_id);
GRANT SELECT,INSERT ON artifacts.source_rights_revisions,artifacts.source_rights_heads TO artifact_service;
GRANT UPDATE(revision) ON artifacts.source_rights_heads TO artifact_service;
