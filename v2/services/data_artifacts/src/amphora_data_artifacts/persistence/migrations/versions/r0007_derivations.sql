CREATE TABLE artifacts.derived_uploads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, upload_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL,
 family varchar(128) NOT NULL CHECK(family='artifacts.begin_derived_upload'), command_id varchar(128) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,upload_id),
 UNIQUE(tenant_id,project_id,actor_id,family,command_id),
 FOREIGN KEY(tenant_id,project_id,upload_id) REFERENCES artifacts.uploads,
 FOREIGN KEY(tenant_id,project_id,actor_id,family,command_id) REFERENCES artifacts.commands
);
CREATE TABLE artifacts.derivations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, artifact_id varchar(128) NOT NULL,
 upload_id varchar(128) NOT NULL,
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 262144),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,artifact_id), UNIQUE(tenant_id,project_id,upload_id),
 FOREIGN KEY(tenant_id,project_id,artifact_id) REFERENCES artifacts.catalog,
 FOREIGN KEY(tenant_id,project_id,upload_id) REFERENCES artifacts.derived_uploads
);
CREATE TABLE artifacts.derivation_inputs (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 artifact_id varchar(128) NOT NULL, input_artifact_id varchar(128) NOT NULL,
 ordinal integer NOT NULL CHECK(ordinal BETWEEN 0 AND 127),
 CHECK(artifact_id<>input_artifact_id),
 PRIMARY KEY(tenant_id,project_id,artifact_id,input_artifact_id),
 UNIQUE(tenant_id,project_id,artifact_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,artifact_id) REFERENCES artifacts.derivations,
 FOREIGN KEY(tenant_id,project_id,input_artifact_id) REFERENCES artifacts.catalog
);
GRANT SELECT,INSERT ON artifacts.derived_uploads,artifacts.derivations,artifacts.derivation_inputs TO artifact_service;
