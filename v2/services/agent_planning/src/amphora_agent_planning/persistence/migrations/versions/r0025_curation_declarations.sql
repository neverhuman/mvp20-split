CREATE TABLE planning.curation_declarations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, curation_id varchar(128) NOT NULL,
 origin_sha256 char(64) NOT NULL CHECK(origin_sha256 ~ '^[0-9a-f]{64}$'),
 origin_bytes bytea NOT NULL CHECK(octet_length(origin_bytes) BETWEEN 1 AND 8388608),
 PRIMARY KEY(tenant_id,project_id,curation_id),
 FOREIGN KEY(tenant_id,project_id,curation_id) REFERENCES planning.curation_requests(tenant_id,project_id,curation_id)
);
CREATE TABLE planning.curation_declaration_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, curation_id varchar(128) NOT NULL,
 position integer NOT NULL CHECK(position BETWEEN 1 AND 64),
 event_sha256 char(64) NOT NULL CHECK(event_sha256 ~ '^[0-9a-f]{64}$'),
 event_bytes bytea NOT NULL CHECK(octet_length(event_bytes) BETWEEN 1 AND 262144),
 PRIMARY KEY(tenant_id,project_id,curation_id,position),
 FOREIGN KEY(tenant_id,project_id,curation_id) REFERENCES planning.curation_declarations(tenant_id,project_id,curation_id)
);
GRANT SELECT,INSERT ON planning.curation_declarations,planning.curation_declaration_events TO planning_service;
