CREATE TABLE artifacts.encoding_profiles (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 profile_id varchar(128) NOT NULL, version varchar(128) NOT NULL,
 profile_sha256 varchar(64) NOT NULL CHECK(profile_sha256 ~ '^[0-9a-f]{64}$'),
 actor_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,profile_id,version),
 UNIQUE(tenant_id,project_id,profile_id,version,profile_sha256)
);
CREATE TABLE artifacts.encoding_work (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 work_sha256 varchar(64) NOT NULL CHECK(work_sha256 ~ '^[0-9a-f]{64}$'),
 profile_id varchar(128) NOT NULL, version varchar(128) NOT NULL,
 profile_sha256 varchar(64) NOT NULL,
 input_sha256 varchar(64) NOT NULL CHECK(input_sha256 ~ '^[0-9a-f]{64}$'),
 context_sha256 varchar(64) CHECK(context_sha256 ~ '^[0-9a-f]{64}$'),
 actor_id varchar(128) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,work_sha256),
 FOREIGN KEY(tenant_id,project_id,profile_id,version,profile_sha256)
 REFERENCES artifacts.encoding_profiles(tenant_id,project_id,profile_id,version,profile_sha256)
);
CREATE TABLE artifacts.encoding_leases (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 work_sha256 varchar(64) NOT NULL,
 actor_id varchar(128) NOT NULL, token varchar(128) NOT NULL,
 fence bigint NOT NULL CHECK(fence BETWEEN 1 AND 9007199254740991),
 expires_at timestamptz NOT NULL,
 PRIMARY KEY(tenant_id,project_id,work_sha256),
 FOREIGN KEY(tenant_id,project_id,work_sha256) REFERENCES artifacts.encoding_work
);
CREATE TABLE artifacts.encoding_results (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 work_sha256 varchar(64) NOT NULL,
 actor_id varchar(128) NOT NULL, token varchar(128) NOT NULL,
 fence bigint NOT NULL CHECK(fence BETWEEN 1 AND 9007199254740991),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 65536),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,work_sha256),
 FOREIGN KEY(tenant_id,project_id,work_sha256) REFERENCES artifacts.encoding_work
);
GRANT SELECT,INSERT ON artifacts.encoding_profiles,artifacts.encoding_work,
 artifacts.encoding_leases,artifacts.encoding_results TO artifact_service;
GRANT UPDATE(actor_id,token,fence,expires_at) ON artifacts.encoding_leases TO artifact_service;
