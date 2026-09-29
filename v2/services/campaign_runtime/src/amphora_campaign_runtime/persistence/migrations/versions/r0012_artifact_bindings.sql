ALTER TABLE runtime.graph_nodes DROP CONSTRAINT graph_nodes_kind_check;
ALTER TABLE runtime.graph_nodes ADD CONSTRAINT graph_nodes_kind_check
 CHECK (kind IN ('invoke','branch','join','scatter','iterate','finish','await','artifact_project','artifact_materialize'));
CREATE TABLE runtime.binding_intents (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(64) NOT NULL, intent_id varchar(128) NOT NULL CHECK (intent_id LIKE 'binding:%'),
 plan_sha256 varchar(64) NOT NULL, semantic_sha256 varchar(64) NOT NULL,
 node jsonb NOT NULL, inputs jsonb NOT NULL, deadline timestamptz NOT NULL,
 opened_revision bigint NOT NULL, audit_ordinal integer NOT NULL DEFAULT 0 CHECK (audit_ordinal=0),
 status varchar(16) NOT NULL CHECK (status IN ('prepared','committed','aborted')),
 output_bindings jsonb NOT NULL DEFAULT '[]', outputs jsonb, resources jsonb, outcome jsonb,
 lease_token varchar(128), lease_until timestamptz,
 PRIMARY KEY (tenant_id,project_id,intent_id),
 UNIQUE (tenant_id,project_id,run_id,activation_id),
 FOREIGN KEY (tenant_id,project_id,run_id,activation_id) REFERENCES runtime.graph_nodes,
 FOREIGN KEY (tenant_id,project_id,plan_sha256) REFERENCES runtime.graph_plans,
 FOREIGN KEY (tenant_id,project_id,run_id,opened_revision,audit_ordinal)
  REFERENCES runtime.audit_events(tenant_id,project_id,run_id,revision,ordinal) DEFERRABLE INITIALLY DEFERRED,
 CHECK (jsonb_typeof(node)='object' AND jsonb_typeof(inputs)='array' AND jsonb_typeof(output_bindings)='array'),
 CHECK ((status='prepared' AND outcome IS NULL) OR
        (status IN ('committed','aborted') AND outcome IS NOT NULL AND jsonb_typeof(outcome)='object'))
);
CREATE TABLE runtime.binding_reservations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, intent_id varchar(128) NOT NULL,
 output_binding varchar(128) NOT NULL, receipt jsonb NOT NULL CHECK (jsonb_typeof(receipt)='object'),
 PRIMARY KEY (tenant_id,project_id,intent_id,output_binding),
 FOREIGN KEY (tenant_id,project_id,intent_id) REFERENCES runtime.binding_intents
);
CREATE TABLE runtime.binding_closures (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 intent_id varchar(128) NOT NULL, receipt_id varchar(128) NOT NULL,
 revision bigint NOT NULL, audit_ordinal integer NOT NULL DEFAULT 0 CHECK (audit_ordinal=0),
 document jsonb NOT NULL CHECK (jsonb_typeof(document)='object'),
 PRIMARY KEY (tenant_id,project_id,intent_id),
 UNIQUE (tenant_id,project_id,receipt_id),
 FOREIGN KEY (tenant_id,project_id,intent_id) REFERENCES runtime.binding_intents,
 FOREIGN KEY (tenant_id,project_id,run_id,revision,audit_ordinal)
  REFERENCES runtime.audit_events(tenant_id,project_id,run_id,revision,ordinal) DEFERRABLE INITIALLY DEFERRED
);
GRANT SELECT,INSERT ON runtime.binding_intents,runtime.binding_reservations,runtime.binding_closures TO runtime_service;
GRANT UPDATE(status,output_bindings,outputs,resources,outcome,lease_token,lease_until) ON runtime.binding_intents TO runtime_service;
