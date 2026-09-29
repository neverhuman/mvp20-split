ALTER TABLE runtime.graph_nodes DROP CONSTRAINT graph_nodes_kind_check;
ALTER TABLE runtime.graph_nodes ADD CONSTRAINT graph_nodes_kind_check
 CHECK (kind IN ('invoke','branch','join','scatter','iterate','finish','await'));
CREATE TABLE runtime.graph_waits (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(64) NOT NULL,
 wait_revision bigint NOT NULL CHECK (wait_revision BETWEEN 1 AND 9007199254740991),
 expectation_sha256 varchar(64) NOT NULL CHECK (expectation_sha256 ~ '^[0-9a-f]{64}$'),
 expectation jsonb NOT NULL CHECK (jsonb_typeof(expectation)='object'),
 deadline timestamptz NOT NULL,
 opened_revision bigint NOT NULL CHECK (opened_revision BETWEEN 1 AND 9007199254740991),
 audit_ordinal integer NOT NULL DEFAULT 0 CHECK (audit_ordinal=0),
 PRIMARY KEY (tenant_id,project_id,run_id,activation_id),
 UNIQUE (tenant_id,project_id,run_id,activation_id,wait_revision,expectation_sha256),
 FOREIGN KEY (tenant_id,project_id,run_id,activation_id) REFERENCES runtime.graph_nodes,
 FOREIGN KEY (tenant_id,project_id,run_id,opened_revision,audit_ordinal)
  REFERENCES runtime.audit_events(tenant_id,project_id,run_id,revision,ordinal) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE runtime.graph_wait_receipts (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 issuer_id varchar(128) NOT NULL, receipt_id varchar(128) NOT NULL,
 receipt_sha256 varchar(64) NOT NULL CHECK (receipt_sha256 ~ '^[0-9a-f]{64}$'),
 document jsonb NOT NULL CHECK (jsonb_typeof(document)='object'),
 PRIMARY KEY (tenant_id,project_id,issuer_id,receipt_id),
 UNIQUE (tenant_id,project_id,receipt_sha256)
);
CREATE TABLE runtime.graph_wait_closures (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(64) NOT NULL, wait_revision bigint NOT NULL, expectation_sha256 varchar(64) NOT NULL,
 closure_revision bigint NOT NULL CHECK (closure_revision BETWEEN 1 AND 9007199254740991),
 audit_ordinal integer NOT NULL DEFAULT 0 CHECK (audit_ordinal=0),
 receipt_sha256 varchar(64),
 document jsonb NOT NULL CHECK (jsonb_typeof(document)='object'),
 PRIMARY KEY (tenant_id,project_id,run_id,activation_id),
 FOREIGN KEY (tenant_id,project_id,run_id,activation_id,wait_revision,expectation_sha256)
  REFERENCES runtime.graph_waits(tenant_id,project_id,run_id,activation_id,wait_revision,expectation_sha256),
 FOREIGN KEY (tenant_id,project_id,receipt_sha256)
  REFERENCES runtime.graph_wait_receipts(tenant_id,project_id,receipt_sha256),
 FOREIGN KEY (tenant_id,project_id,run_id,closure_revision,audit_ordinal)
  REFERENCES runtime.audit_events(tenant_id,project_id,run_id,revision,ordinal) DEFERRABLE INITIALLY DEFERRED
);
CREATE TABLE runtime.wait_retention_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 intent_id varchar(128) NOT NULL CHECK (intent_id LIKE 'wait:%'),
 run_id varchar(128) NOT NULL, activation_id varchar(64) NOT NULL,
 wait_revision bigint NOT NULL, expectation_sha256 varchar(64) NOT NULL,
 operation_id varchar(128) NOT NULL,
 semantic_sha256 varchar(64) NOT NULL CHECK (semantic_sha256 ~ '^[0-9a-f]{64}$'),
 output_bindings jsonb NOT NULL CHECK (jsonb_typeof(output_bindings)='array'),
 receipt_sha256 varchar(64) NOT NULL,
 status varchar(16) NOT NULL CHECK (status IN ('prepared','committed','aborted')),
 outcome jsonb,
 PRIMARY KEY (tenant_id,project_id,intent_id),
 UNIQUE (tenant_id,project_id,operation_id),
 FOREIGN KEY (tenant_id,project_id,run_id,activation_id,wait_revision,expectation_sha256)
  REFERENCES runtime.graph_waits(tenant_id,project_id,run_id,activation_id,wait_revision,expectation_sha256),
 FOREIGN KEY (tenant_id,project_id,receipt_sha256)
  REFERENCES runtime.graph_wait_receipts(tenant_id,project_id,receipt_sha256),
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES runtime.commands(tenant_id,project_id,operation_id),
 CHECK ((status='prepared' AND outcome IS NULL) OR
        (status IN ('committed','aborted') AND jsonb_typeof(outcome)='object' AND outcome IS NOT NULL))
);
CREATE TABLE runtime.wait_intent_reservations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, intent_id varchar(128) NOT NULL,
 output_binding varchar(128) NOT NULL, receipt jsonb NOT NULL CHECK (jsonb_typeof(receipt)='object'),
 PRIMARY KEY (tenant_id,project_id,intent_id,output_binding),
 FOREIGN KEY (tenant_id,project_id,intent_id) REFERENCES runtime.wait_retention_intents
);
GRANT SELECT,INSERT ON runtime.graph_waits,runtime.graph_wait_receipts,runtime.graph_wait_closures,
 runtime.wait_retention_intents,runtime.wait_intent_reservations TO runtime_service;
GRANT UPDATE(status,outcome) ON runtime.wait_retention_intents TO runtime_service;
