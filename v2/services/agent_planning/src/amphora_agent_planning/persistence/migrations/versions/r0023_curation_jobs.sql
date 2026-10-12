CREATE TABLE planning.curation_progress (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 curation_id varchar(128) NOT NULL, revision bigint NOT NULL CHECK(revision BETWEEN 1 AND 9007199254740991),
 view_bytes bytea NOT NULL CHECK(octet_length(view_bytes) BETWEEN 1 AND 262144),
 view_sha256 char(64) NOT NULL CHECK(view_sha256 ~ '^[0-9a-f]{64}$'),
 PRIMARY KEY(tenant_id,project_id,curation_id,revision),
 FOREIGN KEY(tenant_id,project_id,curation_id) REFERENCES planning.curation_requests(tenant_id,project_id,curation_id)
);
CREATE TABLE planning.curation_leases (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 curation_id varchar(128) NOT NULL, worker_id varchar(128) NOT NULL,
 fence char(32) NOT NULL CHECK(fence ~ '^[0-9a-f]{32}$'), lease_until timestamptz NOT NULL,
 PRIMARY KEY(tenant_id,project_id,curation_id),
 FOREIGN KEY(tenant_id,project_id,curation_id) REFERENCES planning.curation_requests(tenant_id,project_id,curation_id)
);
GRANT SELECT,INSERT ON planning.curation_progress TO planning_service;
GRANT SELECT,INSERT,UPDATE ON planning.curation_leases TO planning_service;
