ALTER TABLE artifacts.uploads ADD COLUMN actor_id varchar(128);
ALTER TABLE artifacts.uploads ADD COLUMN generation bigint NOT NULL DEFAULT 0 CHECK (generation>=0);
ALTER TABLE artifacts.uploads ADD COLUMN selected_attempt varchar(128);
CREATE TABLE artifacts.capacity (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 charged_bytes bigint NOT NULL DEFAULT 0 CHECK (charged_bytes>=0),
 active_streams integer NOT NULL DEFAULT 0 CHECK (active_streams>=0),
 upload_count integer NOT NULL DEFAULT 0 CHECK (upload_count>=0),
 PRIMARY KEY (tenant_id,project_id)
);
-- Legacy catalog/uploads are not implicitly authorized or assigned an actor.
-- Charge existing retained bytes conservatively; new uploads use configured limits.
INSERT INTO artifacts.capacity (tenant_id,project_id,charged_bytes,upload_count)
 SELECT tenant_id,project_id,sum(charge),sum(n)::integer FROM (
 SELECT tenant_id,project_id,size_bytes AS charge,0 AS n FROM artifacts.catalog
 UNION ALL SELECT tenant_id,project_id,bytes_received AS charge,1 AS n FROM artifacts.uploads
 ) legacy GROUP BY tenant_id,project_id;
CREATE TABLE artifacts.upload_attempts (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 upload_id varchar(128) NOT NULL, attempt_id varchar(128) NOT NULL,
 generation bigint NOT NULL CHECK (generation>0),
 storage_key varchar(64) NOT NULL UNIQUE CHECK (storage_key ~ '^[0-9a-f]{32}$'),
 allocated_bytes bigint NOT NULL CHECK (allocated_bytes>=0),
 actual_bytes bigint CHECK (actual_bytes>=0 AND actual_bytes<=allocated_bytes),
 status varchar(16) NOT NULL DEFAULT 'streaming' CHECK (status IN ('streaming','streamed','failed','stale')),
 expires_at timestamptz NOT NULL,
 PRIMARY KEY (tenant_id,project_id,upload_id,attempt_id),
 UNIQUE (tenant_id,project_id,upload_id,generation),
 FOREIGN KEY (tenant_id,project_id,upload_id) REFERENCES artifacts.uploads,
 CHECK (status<>'streamed' OR actual_bytes=allocated_bytes)
);
ALTER TABLE artifacts.uploads ADD CONSTRAINT selected_upload_attempt_fk
 FOREIGN KEY (tenant_id,project_id,upload_id,selected_attempt) REFERENCES artifacts.upload_attempts;
GRANT SELECT,INSERT ON artifacts.capacity,artifacts.upload_attempts TO artifact_service;
GRANT UPDATE(charged_bytes,active_streams,upload_count) ON artifacts.capacity TO artifact_service;
GRANT UPDATE(generation,selected_attempt) ON artifacts.uploads TO artifact_service;
GRANT UPDATE(actual_bytes,status) ON artifacts.upload_attempts TO artifact_service;
