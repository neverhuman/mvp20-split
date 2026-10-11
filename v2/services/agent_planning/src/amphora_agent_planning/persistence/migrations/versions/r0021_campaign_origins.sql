CREATE TABLE planning.campaign_origins (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 draft_id varchar(128) NOT NULL, revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 content_sha256 char(64) NOT NULL CHECK(content_sha256 ~ '^[0-9a-f]{64}$'),
 selection_id varchar(128) NOT NULL, effect_id varchar(128) NOT NULL,
 pointer_sha256 char(64) NOT NULL CHECK(pointer_sha256 ~ '^[0-9a-f]{64}$'),
 pointer_bytes bytea NOT NULL CHECK(octet_length(pointer_bytes) BETWEEN 1 AND 8192),
 recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,draft_id,revision),
 UNIQUE(tenant_id,project_id,selection_id,effect_id),
 FOREIGN KEY(tenant_id,project_id,selection_id,effect_id) REFERENCES planning.compiler_effects
);
GRANT SELECT,INSERT ON planning.campaign_origins TO planning_service;
