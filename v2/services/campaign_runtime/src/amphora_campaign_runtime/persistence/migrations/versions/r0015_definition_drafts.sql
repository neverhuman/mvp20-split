CREATE TABLE runtime.definition_heads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, draft_id varchar(128) NOT NULL,
 head_revision bigint NOT NULL CHECK (head_revision BETWEEN 1 AND 9007199254740991),
 PRIMARY KEY (tenant_id,project_id,draft_id)
);
CREATE TABLE runtime.definition_revisions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, draft_id varchar(128) NOT NULL,
 revision bigint NOT NULL CHECK (revision BETWEEN 1 AND 9007199254740991),
 parent_revision bigint,
 content_sha256 varchar(64) NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
 record jsonb NOT NULL CHECK (jsonb_typeof(record)='object' AND octet_length(record::text)<=1048576),
 operation_id varchar(128) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,draft_id,revision),
 UNIQUE (tenant_id,project_id,operation_id),
 CHECK ((revision=1 AND parent_revision IS NULL) OR (revision>1 AND parent_revision IS NOT NULL AND parent_revision=revision-1)),
 FOREIGN KEY (tenant_id,project_id,draft_id) REFERENCES runtime.definition_heads DEFERRABLE INITIALLY DEFERRED,
 FOREIGN KEY (tenant_id,project_id,draft_id,parent_revision)
  REFERENCES runtime.definition_revisions(tenant_id,project_id,draft_id,revision) DEFERRABLE INITIALLY DEFERRED,
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES runtime.commands(tenant_id,project_id,operation_id)
);
ALTER TABLE runtime.definition_heads ADD FOREIGN KEY (tenant_id,project_id,draft_id,head_revision)
 REFERENCES runtime.definition_revisions(tenant_id,project_id,draft_id,revision) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE runtime.definition_audit (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, draft_id varchar(128) NOT NULL,
 revision bigint NOT NULL, operation_id varchar(128) NOT NULL,
 kind varchar(64) NOT NULL CHECK (kind='draft_saved'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,operation_id),
 FOREIGN KEY (tenant_id,project_id,draft_id,revision) REFERENCES runtime.definition_revisions,
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES runtime.commands(tenant_id,project_id,operation_id)
);
GRANT SELECT,INSERT ON runtime.definition_heads TO runtime_service;
GRANT UPDATE (head_revision) ON runtime.definition_heads TO runtime_service;
GRANT SELECT,INSERT ON runtime.definition_revisions,runtime.definition_audit TO runtime_service;
