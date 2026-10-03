CREATE TABLE artifacts.retrieval_queries (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, retrieval_id varchar(128) NOT NULL,
 corpus_id varchar(128) NOT NULL, generation_id varchar(128) NOT NULL,
 generation_sha256 varchar(64) NOT NULL, query_binding_id varchar(128) NOT NULL,
 query_sha256 varchar(64) NOT NULL CHECK(query_sha256 ~ '^[0-9a-f]{64}$'),
 request_bytes bytea NOT NULL CHECK(octet_length(request_bytes) BETWEEN 1 AND 4194304),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,actor_id,retrieval_id),
 UNIQUE(tenant_id,project_id,actor_id,retrieval_id,query_sha256),
 FOREIGN KEY(tenant_id,project_id,corpus_id,generation_id,generation_sha256)
 REFERENCES artifacts.index_publications(tenant_id,project_id,corpus_id,generation_id,generation_sha256),
 FOREIGN KEY(tenant_id,project_id,query_binding_id) REFERENCES artifacts.representation_bindings
);
CREATE TABLE artifacts.retrieval_results (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 actor_id varchar(128) NOT NULL, retrieval_id varchar(128) NOT NULL,
 query_sha256 varchar(64) NOT NULL, result_sha256 varchar(64) NOT NULL CHECK(result_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_bytes bytea NOT NULL CHECK(octet_length(canonical_bytes) BETWEEN 1 AND 4194304),
 access_bytes bytea NOT NULL CHECK(octet_length(access_bytes) BETWEEN 1 AND 4194304),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY(tenant_id,project_id,actor_id,retrieval_id),
 FOREIGN KEY(tenant_id,project_id,actor_id,retrieval_id,query_sha256)
 REFERENCES artifacts.retrieval_queries(tenant_id,project_id,actor_id,retrieval_id,query_sha256)
);
GRANT SELECT,INSERT ON artifacts.retrieval_queries,artifacts.retrieval_results TO artifact_service;
