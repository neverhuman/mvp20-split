CREATE TABLE planning.curation_preparation_links (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 curation_id varchar(128) NOT NULL, engagement_id varchar(128) NOT NULL,
 request_sha256 char(64) NOT NULL CHECK(request_sha256 ~ '^[0-9a-f]{64}$'),
 manifest_sha256 char(64) NOT NULL CHECK(manifest_sha256 ~ '^[0-9a-f]{64}$'),
 envelope_sha256 char(64) NOT NULL CHECK(envelope_sha256 ~ '^[0-9a-f]{64}$'),
 progress_revision bigint NOT NULL,
 PRIMARY KEY(tenant_id,project_id,curation_id),
 UNIQUE(tenant_id,project_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,curation_id) REFERENCES planning.curation_requests(tenant_id,project_id,curation_id),
 FOREIGN KEY(tenant_id,project_id,engagement_id) REFERENCES planning.campaign_preparations(tenant_id,project_id,engagement_id),
 FOREIGN KEY(tenant_id,project_id,engagement_id,request_sha256) REFERENCES planning.requests(tenant_id,project_id,engagement_id,request_sha256),
 FOREIGN KEY(tenant_id,project_id,curation_id,progress_revision) REFERENCES planning.curation_progress(tenant_id,project_id,curation_id,revision)
);
GRANT SELECT,INSERT ON planning.curation_preparation_links TO planning_service;
