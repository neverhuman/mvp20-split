CREATE TABLE runtime.supervision_recipes (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 recipe_sha256 varchar(64) NOT NULL CHECK (recipe_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_recipe bytea NOT NULL CHECK (octet_length(canonical_recipe) BETWEEN 1 AND 262144),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,run_id),
 FOREIGN KEY (tenant_id,project_id,run_id)
  REFERENCES runtime.supervision_policies(tenant_id,project_id,run_id)
);
GRANT SELECT,INSERT ON runtime.supervision_recipes TO runtime_service;
