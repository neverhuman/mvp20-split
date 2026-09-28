CREATE TABLE artifacts.commands (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, family varchar(128) NOT NULL, command_id varchar(128) NOT NULL,
 operation_id varchar(128) NOT NULL, profile varchar(64) NOT NULL,
 request_sha256 varchar(64) NOT NULL CHECK (request_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK (octet_length(canonical_bytes)<=262144),
 status varchar(16) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','accepted','rejected')),
 receipt jsonb, terminal_at timestamptz,
 PRIMARY KEY (tenant_id,project_id,actor_id,family,command_id), UNIQUE (tenant_id,project_id,operation_id),
 CHECK ((status='pending' AND receipt IS NULL AND terminal_at IS NULL) OR
        (status<>'pending' AND receipt IS NOT NULL AND terminal_at IS NOT NULL))
);
CREATE TABLE artifacts.uploads (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, upload_id varchar(128) NOT NULL,
 expected_descriptor jsonb NOT NULL CHECK (jsonb_typeof(expected_descriptor)='object'),
 storage_key varchar(128) NOT NULL CHECK (storage_key ~ '^[a-zA-Z0-9_-]+$'),
 bytes_received bigint NOT NULL DEFAULT 0 CHECK (bytes_received BETWEEN 0 AND 9007199254740991),
 status varchar(16) NOT NULL DEFAULT 'provisional' CHECK (status IN ('provisional','finalized','abandoned')),
 PRIMARY KEY (tenant_id,project_id,upload_id), UNIQUE (storage_key)
);
CREATE TABLE artifacts.catalog (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, artifact_id varchar(128) NOT NULL,
 content_sha256 varchar(64) NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
 size_bytes bigint NOT NULL CHECK (size_bytes BETWEEN 0 AND 9007199254740991),
 media_type varchar(128) NOT NULL, schema_ref jsonb NOT NULL CHECK (jsonb_typeof(schema_ref)='object'),
 storage_key varchar(128) NOT NULL CHECK (storage_key ~ '^[a-zA-Z0-9_-]+$'),
 PRIMARY KEY (tenant_id,project_id,artifact_id), UNIQUE (storage_key),
 UNIQUE (tenant_id,project_id,artifact_id,content_sha256)
);
CREATE TABLE artifacts.reservations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, reservation_id varchar(128) NOT NULL,
 artifact_id varchar(128) NOT NULL, content_sha256 varchar(64) NOT NULL,
 runtime_owner varchar(128) NOT NULL, intent_id varchar(128) NOT NULL, output_binding varchar(128) NOT NULL,
 semantic_sha256 varchar(64) NOT NULL CHECK (semantic_sha256 ~ '^[0-9a-f]{64}$'),
 status varchar(16) NOT NULL DEFAULT 'reserved' CHECK (status IN ('reserved','confirmed','released')),
 outcome_proof jsonb,
 PRIMARY KEY (tenant_id,project_id,reservation_id),
 UNIQUE (tenant_id,project_id,runtime_owner,intent_id,output_binding),
 FOREIGN KEY (tenant_id,project_id,artifact_id,content_sha256)
 REFERENCES artifacts.catalog(tenant_id,project_id,artifact_id,content_sha256),
 CHECK ((status='reserved' AND outcome_proof IS NULL) OR (status<>'reserved' AND outcome_proof IS NOT NULL))
);
CREATE TABLE artifacts.audit_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 event_id varchar(128) NOT NULL, operation_id varchar(128) NOT NULL, ordinal integer NOT NULL CHECK (ordinal>=0),
 payload jsonb NOT NULL,
 PRIMARY KEY (tenant_id,project_id,event_id), UNIQUE (tenant_id,project_id,operation_id,ordinal),
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES artifacts.commands(tenant_id,project_id,operation_id)
);
CREATE TABLE artifacts.outbox (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, operation_id varchar(128) NOT NULL,
 event_id varchar(128) NOT NULL, target varchar(128) NOT NULL, payload jsonb NOT NULL,
 status varchar(16) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','leased','acknowledged')),
 delivery_attempts integer NOT NULL DEFAULT 0 CHECK (delivery_attempts>=0), lease_expires_at timestamptz,
 PRIMARY KEY (tenant_id,project_id,operation_id),
 FOREIGN KEY (tenant_id,project_id,event_id) REFERENCES artifacts.audit_events
);
GRANT SELECT,INSERT ON artifacts.commands,artifacts.uploads,artifacts.catalog,artifacts.reservations,
 artifacts.audit_events,artifacts.outbox TO artifact_service;
GRANT UPDATE(status,receipt,terminal_at) ON artifacts.commands TO artifact_service;
GRANT UPDATE(status,bytes_received) ON artifacts.uploads TO artifact_service;
GRANT UPDATE(status,outcome_proof) ON artifacts.reservations TO artifact_service;
GRANT UPDATE(status,delivery_attempts,lease_expires_at) ON artifacts.outbox TO artifact_service;
