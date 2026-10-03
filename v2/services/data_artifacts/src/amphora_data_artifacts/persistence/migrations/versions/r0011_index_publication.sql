CREATE TABLE artifacts.index_verifications (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 corpus_id varchar(128) NOT NULL, generation_id varchar(128) NOT NULL,
 fence bigint NOT NULL, canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,corpus_id,generation_id),
 FOREIGN KEY(tenant_id,project_id,corpus_id,generation_id,fence) REFERENCES artifacts.index_build_attempts
);
CREATE TABLE artifacts.index_publications (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 corpus_id varchar(128) NOT NULL, generation_id varchar(128) NOT NULL,
 generation_sha256 varchar(64) NOT NULL, canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,corpus_id,generation_id),
 UNIQUE(tenant_id,project_id,corpus_id,generation_id,generation_sha256),
 FOREIGN KEY(tenant_id,project_id,corpus_id,generation_id) REFERENCES artifacts.index_verifications,
 FOREIGN KEY(tenant_id,project_id,corpus_id,generation_id,generation_sha256)
 REFERENCES artifacts.index_generations(tenant_id,project_id,corpus_id,generation_id,generation_sha256)
);
CREATE TABLE artifacts.index_heads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 corpus_id varchar(128) NOT NULL, generation_id varchar(128) NOT NULL,
 generation_sha256 varchar(64) NOT NULL,
 PRIMARY KEY(tenant_id,project_id,corpus_id),
 FOREIGN KEY(tenant_id,project_id,corpus_id,generation_id,generation_sha256)
 REFERENCES artifacts.index_publications(tenant_id,project_id,corpus_id,generation_id,generation_sha256)
);
GRANT SELECT,INSERT ON artifacts.index_verifications,artifacts.index_publications,artifacts.index_heads TO artifact_service;
GRANT UPDATE(generation_id,generation_sha256) ON artifacts.index_heads TO artifact_service;
