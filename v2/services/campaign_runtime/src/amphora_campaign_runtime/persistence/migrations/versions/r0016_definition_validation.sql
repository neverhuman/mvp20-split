CREATE TABLE runtime.definition_universes (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 universe_sha256 varchar(64) NOT NULL CHECK (universe_sha256 ~ '^[0-9a-f]{64}$'),
 material jsonb NOT NULL CHECK (jsonb_typeof(material)='object' AND octet_length(material::text)<=50331648),
 PRIMARY KEY (tenant_id,project_id,universe_sha256)
);
ALTER TABLE runtime.definition_revisions ADD UNIQUE (tenant_id,project_id,draft_id,revision,content_sha256);
CREATE TABLE runtime.definition_validations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 validation_id varchar(128) NOT NULL, draft_id varchar(128) NOT NULL, revision bigint NOT NULL,
 content_sha256 varchar(64) NOT NULL, universe_sha256 varchar(64) NOT NULL,
 record jsonb NOT NULL CHECK (jsonb_typeof(record)='object' AND octet_length(record::text)<=65536),
 operation_id varchar(128) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,validation_id),
 UNIQUE (tenant_id,project_id,operation_id),
 FOREIGN KEY (tenant_id,project_id,draft_id,revision,content_sha256)
  REFERENCES runtime.definition_revisions(tenant_id,project_id,draft_id,revision,content_sha256),
 FOREIGN KEY (tenant_id,project_id,universe_sha256) REFERENCES runtime.definition_universes,
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES runtime.commands(tenant_id,project_id,operation_id)
);
GRANT SELECT,INSERT ON runtime.definition_universes,runtime.definition_validations TO runtime_service;
