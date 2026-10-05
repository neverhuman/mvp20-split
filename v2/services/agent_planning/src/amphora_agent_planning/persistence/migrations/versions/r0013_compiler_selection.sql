CREATE TABLE planning.compiler_selections (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, selection_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 ordinal integer NOT NULL CHECK(ordinal BETWEEN 1 AND 16),
 selection_sha256 char(64) NOT NULL CHECK(selection_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 131072),
 registered_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,selection_id),
 UNIQUE(tenant_id,project_id,actor_id,engagement_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,engagement_id,ordinal) REFERENCES planning.attempts,
 FOREIGN KEY(tenant_id,project_id,engagement_id,request_sha256)
 REFERENCES planning.requests(tenant_id,project_id,engagement_id,request_sha256)
);
CREATE TABLE planning.compiler_control (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, selection_id varchar(128) NOT NULL,
 holder varchar(128), fence bigint NOT NULL DEFAULT 0 CHECK(fence BETWEEN 0 AND 9007199254740991),
 expires_at timestamptz,
 CHECK((holder IS NULL) = (expires_at IS NULL)),
 PRIMARY KEY(tenant_id,project_id,selection_id),
 FOREIGN KEY(tenant_id,project_id,selection_id) REFERENCES planning.compiler_selections
);
GRANT SELECT,INSERT ON planning.compiler_selections,planning.compiler_control TO planning_service;
GRANT UPDATE(holder,fence,expires_at) ON planning.compiler_control TO planning_service;
