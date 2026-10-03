CREATE TABLE artifacts.index_generations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 corpus_id varchar(128) NOT NULL, generation_id varchar(128) NOT NULL,
 generation_sha256 varchar(64) NOT NULL CHECK(generation_sha256 ~ '^[0-9a-f]{64}$'),
 actor_id varchar(128) NOT NULL, profile_id varchar(128) NOT NULL,
 version varchar(128) NOT NULL, profile_sha256 varchar(64) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 4194304),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,corpus_id,generation_id),
 UNIQUE(tenant_id,project_id,corpus_id,generation_id,generation_sha256),
 FOREIGN KEY(tenant_id,project_id,profile_id,version,profile_sha256)
 REFERENCES artifacts.encoding_profiles(tenant_id,project_id,profile_id,version,profile_sha256)
);
CREATE TABLE artifacts.index_generation_bindings (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 corpus_id varchar(128) NOT NULL, generation_id varchar(128) NOT NULL,
 ordinal smallint NOT NULL CHECK(ordinal BETWEEN 0 AND 255), binding_id varchar(128) NOT NULL,
 PRIMARY KEY(tenant_id,project_id,corpus_id,generation_id,ordinal),
 UNIQUE(tenant_id,project_id,corpus_id,generation_id,binding_id),
 FOREIGN KEY(tenant_id,project_id,corpus_id,generation_id) REFERENCES artifacts.index_generations,
 FOREIGN KEY(tenant_id,project_id,binding_id) REFERENCES artifacts.representation_bindings
);
CREATE TABLE artifacts.index_generation_cursors (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 corpus_id varchar(128) NOT NULL, generation_id varchar(128) NOT NULL,
 phase varchar(16) NOT NULL CHECK(phase IN ('prepared','building','verified','published','failed','abandoned')),
 sequence bigint NOT NULL CHECK(sequence BETWEEN 1 AND 9007199254740991),
 token varchar(128), fence bigint NOT NULL DEFAULT 0 CHECK(fence BETWEEN 0 AND 9007199254740991),
 expires_at timestamptz,
 CHECK((fence=0 AND token IS NULL AND expires_at IS NULL) OR (fence>0 AND token IS NOT NULL AND expires_at IS NOT NULL)),
 PRIMARY KEY(tenant_id,project_id,corpus_id,generation_id),
 FOREIGN KEY(tenant_id,project_id,corpus_id,generation_id) REFERENCES artifacts.index_generations
);
CREATE TABLE artifacts.index_build_attempts (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 corpus_id varchar(128) NOT NULL, generation_id varchar(128) NOT NULL,
 token varchar(128) NOT NULL, fence bigint NOT NULL CHECK(fence BETWEEN 1 AND 9007199254740991),
 namespace varchar(80) NOT NULL UNIQUE,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,corpus_id,generation_id,fence),
 FOREIGN KEY(tenant_id,project_id,corpus_id,generation_id) REFERENCES artifacts.index_generations
);
CREATE TABLE artifacts.index_generation_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 corpus_id varchar(128) NOT NULL, generation_id varchar(128) NOT NULL,
 sequence bigint NOT NULL CHECK(sequence BETWEEN 1 AND 9007199254740991),
 phase varchar(16) NOT NULL CHECK(phase IN ('prepared','building','verified','published','failed','abandoned')),
 reason varchar(128) NOT NULL, token varchar(128), fence bigint NOT NULL CHECK(fence BETWEEN 0 AND 9007199254740991),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,corpus_id,generation_id,sequence),
 FOREIGN KEY(tenant_id,project_id,corpus_id,generation_id) REFERENCES artifacts.index_generations
);
GRANT SELECT,INSERT ON artifacts.index_generations,artifacts.index_generation_bindings,
 artifacts.index_generation_cursors,artifacts.index_build_attempts,artifacts.index_generation_events TO artifact_service;
GRANT UPDATE(phase,sequence,token,fence,expires_at) ON artifacts.index_generation_cursors TO artifact_service;
