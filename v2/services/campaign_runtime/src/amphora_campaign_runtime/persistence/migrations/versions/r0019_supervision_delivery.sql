CREATE TABLE runtime.supervision_delivery (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 decision_id varchar(128) NOT NULL, request_sha256 varchar(64) NOT NULL,
 status varchar(32) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','leased','recorded','rejected','failed','expired')),
 fence bigint NOT NULL DEFAULT 0 CHECK (fence BETWEEN 0 AND 9007199254740991),
 holder varchar(128), expires_at timestamptz,
 claims integer NOT NULL DEFAULT 0 CHECK (claims BETWEEN 0 AND 16),
 events integer NOT NULL DEFAULT 0 CHECK (events BETWEEN 0 AND 64),
 PRIMARY KEY (tenant_id,project_id,run_id,decision_id,request_sha256),
 FOREIGN KEY (tenant_id,project_id,run_id,decision_id,request_sha256)
  REFERENCES runtime.supervision_outbox(tenant_id,project_id,run_id,decision_id,request_sha256),
 CHECK ((status='leased' AND holder IS NOT NULL AND expires_at IS NOT NULL AND fence>0)
  OR (status<>'leased' AND holder IS NULL AND expires_at IS NULL))
);
CREATE TABLE runtime.supervision_delivery_events (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 decision_id varchar(128) NOT NULL, request_sha256 varchar(64) NOT NULL,
 sequence integer NOT NULL CHECK (sequence BETWEEN 1 AND 64), event_id varchar(128) NOT NULL,
 fence bigint NOT NULL CHECK (fence BETWEEN 0 AND 9007199254740991),
 kind varchar(32) NOT NULL CHECK (kind IN ('claim','unknown','pending','awaiting_readback','recorded','rejected','failed','expired')),
 evidence bytea NOT NULL CHECK (octet_length(evidence) BETWEEN 1 AND 524288),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,run_id,decision_id,request_sha256,sequence),
 UNIQUE (tenant_id,project_id,run_id,decision_id,request_sha256,event_id),
 FOREIGN KEY (tenant_id,project_id,run_id,decision_id,request_sha256)
  REFERENCES runtime.supervision_delivery
);
CREATE TABLE runtime.supervision_responses (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 decision_id varchar(128) NOT NULL, request_sha256 varchar(64) NOT NULL,
 response_id varchar(128) NOT NULL, sequence integer NOT NULL CHECK (sequence BETWEEN 1 AND 64),
 response_sha256 varchar(64) NOT NULL CHECK (response_sha256 ~ '^[0-9a-f]{64}$'),
 canonical_response bytea NOT NULL CHECK (octet_length(canonical_response) BETWEEN 1 AND 262144),
 capture_bytes bytea CHECK (octet_length(capture_bytes) <= 65536), operation_id varchar(128) NOT NULL,
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,response_id),
 UNIQUE (tenant_id,project_id,run_id,decision_id,request_sha256,sequence),
 UNIQUE (tenant_id,project_id,operation_id),
 FOREIGN KEY (tenant_id,project_id,run_id,decision_id,request_sha256)
  REFERENCES runtime.supervision_requests(tenant_id,project_id,run_id,decision_id,request_sha256),
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES runtime.commands(tenant_id,project_id,operation_id)
);
GRANT SELECT,INSERT ON runtime.supervision_delivery,runtime.supervision_delivery_events,runtime.supervision_responses TO runtime_service;
GRANT UPDATE(status,fence,holder,expires_at,claims,events) ON runtime.supervision_delivery TO runtime_service;
