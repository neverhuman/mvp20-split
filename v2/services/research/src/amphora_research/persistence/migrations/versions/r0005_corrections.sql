CREATE TABLE research.receipt_corrections (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 issuer_id varchar(128) NOT NULL, chain_id varchar(128) NOT NULL,
 ordinal bigint NOT NULL CHECK(ordinal BETWEEN 1 AND 9007199254740991),
 change_id varchar(128) NOT NULL,
 request_bytes bytea NOT NULL CHECK(octet_length(request_bytes) BETWEEN 1 AND 2097152),
 record_bytes bytea NOT NULL CHECK(octet_length(record_bytes) BETWEEN 1 AND 2097152),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,issuer_id,chain_id,ordinal),
 UNIQUE(tenant_id,project_id,issuer_id,change_id)
);
GRANT SELECT,INSERT ON research.receipt_corrections TO research_service;
