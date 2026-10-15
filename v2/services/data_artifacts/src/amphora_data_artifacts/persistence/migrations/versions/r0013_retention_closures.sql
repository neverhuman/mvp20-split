CREATE TABLE artifacts.retention_closures (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 reservation_id varchar(128) NOT NULL,
 profile varchar(64) NOT NULL CHECK(profile='derived-closure-retention-v1'),
 artifact_count integer NOT NULL CHECK(artifact_count BETWEEN 1 AND 4096),
 members_sha256 varchar(64) NOT NULL CHECK(members_sha256 ~ '^[0-9a-f]{64}$'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,reservation_id),
 FOREIGN KEY(tenant_id,project_id,reservation_id) REFERENCES artifacts.reservations
);
CREATE TABLE artifacts.retention_closure_members (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 reservation_id varchar(128) NOT NULL, ordinal integer NOT NULL CHECK(ordinal BETWEEN 0 AND 4095),
 artifact_id varchar(128) NOT NULL, content_sha256 varchar(64) NOT NULL,
 PRIMARY KEY(tenant_id,project_id,reservation_id,artifact_id),
 UNIQUE(tenant_id,project_id,reservation_id,ordinal),
 FOREIGN KEY(tenant_id,project_id,reservation_id) REFERENCES artifacts.retention_closures,
 FOREIGN KEY(tenant_id,project_id,artifact_id,content_sha256) REFERENCES artifacts.catalog(tenant_id,project_id,artifact_id,content_sha256)
);
GRANT SELECT,INSERT ON artifacts.retention_closures,artifacts.retention_closure_members TO artifact_service;
CREATE VIEW artifacts.artifact_protection AS
 SELECT tenant_id,project_id,artifact_id,content_sha256,reservation_id,status
 FROM artifacts.reservations WHERE status IN ('reserved','confirmed')
 UNION
 SELECT m.tenant_id,m.project_id,m.artifact_id,m.content_sha256,m.reservation_id,r.status
 FROM artifacts.retention_closure_members m
 JOIN artifacts.reservations r USING(tenant_id,project_id,reservation_id)
 WHERE r.status IN ('reserved','confirmed');
GRANT SELECT ON artifacts.artifact_protection TO artifact_service;
