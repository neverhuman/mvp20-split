ALTER TABLE runtime.runs ADD COLUMN execution_mode varchar(16) NOT NULL DEFAULT 'fixture'
 CHECK (execution_mode IN ('fixture','graph'));
ALTER TABLE runtime.activations ADD COLUMN dispatch_order bigint NOT NULL DEFAULT 0
 CHECK (dispatch_order BETWEEN 0 AND 9007199254740991);
CREATE TABLE runtime.graph_plans (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 plan_sha256 varchar(64) NOT NULL CHECK (plan_sha256 ~ '^[0-9a-f]{64}$'),
 document jsonb NOT NULL CHECK (jsonb_typeof(document)='object'),
 tool_descriptors jsonb NOT NULL CHECK (jsonb_typeof(tool_descriptors)='array'),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 PRIMARY KEY (tenant_id,project_id,plan_sha256)
);
CREATE TABLE runtime.graph_runs (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 plan_sha256 varchar(64) NOT NULL, inputs jsonb NOT NULL CHECK (jsonb_typeof(inputs)='array'),
 max_activations integer NOT NULL CHECK (max_activations BETWEEN 1 AND 100000),
 deadline timestamptz NOT NULL,
 frontier_revision bigint NOT NULL DEFAULT 0 CHECK (frontier_revision BETWEEN 0 AND 9007199254740991),
 next_dispatch_order bigint NOT NULL DEFAULT 0 CHECK (next_dispatch_order BETWEEN 0 AND 9007199254740991),
 outputs jsonb, stop_reason varchar(128),
 PRIMARY KEY (tenant_id,project_id,run_id),
 FOREIGN KEY (tenant_id,project_id,run_id) REFERENCES runtime.runs,
 FOREIGN KEY (tenant_id,project_id,plan_sha256) REFERENCES runtime.graph_plans,
 CHECK (outputs IS NULL OR jsonb_typeof(outputs)='array')
);
CREATE TABLE runtime.graph_scopes (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 scope_key varchar(64) NOT NULL CHECK (scope_key ~ '^[0-9a-f]{64}$'),
 definition_path jsonb NOT NULL CHECK (jsonb_typeof(definition_path)='array'),
 occurrences jsonb NOT NULL CHECK (jsonb_typeof(occurrences)='array'),
 status varchar(16) NOT NULL CHECK (status IN ('active','completed','failed','skipped','blocked')),
 inputs jsonb NOT NULL CHECK (jsonb_typeof(inputs)='array'), outputs jsonb,
 parent_activation_id varchar(64),
 PRIMARY KEY (tenant_id,project_id,run_id,scope_key),
 FOREIGN KEY (tenant_id,project_id,run_id) REFERENCES runtime.graph_runs,
 CHECK (outputs IS NULL OR jsonb_typeof(outputs)='array')
);
CREATE TABLE runtime.graph_nodes (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 activation_id varchar(64) NOT NULL CHECK (activation_id ~ '^[0-9a-f]{64}$'),
 scope_key varchar(64) NOT NULL, node_id varchar(128) NOT NULL,
 path jsonb NOT NULL CHECK (jsonb_typeof(path)='object'),
 kind varchar(16) NOT NULL CHECK (kind IN ('invoke','branch','join','scatter','iterate','finish')),
 priority jsonb NOT NULL CHECK (jsonb_typeof(priority)='array'),
 status varchar(16) NOT NULL CHECK (status IN ('waiting','ready','issued','succeeded','skipped','failed','blocked')),
 state jsonb NOT NULL DEFAULT '{}' CHECK (jsonb_typeof(state)='object'),
 outputs jsonb, reason_code varchar(128),
 PRIMARY KEY (tenant_id,project_id,run_id,activation_id),
 UNIQUE (tenant_id,project_id,run_id,scope_key,node_id),
 FOREIGN KEY (tenant_id,project_id,run_id,scope_key) REFERENCES runtime.graph_scopes,
 CHECK (outputs IS NULL OR jsonb_typeof(outputs)='array')
);
CREATE INDEX graph_nodes_frontier ON runtime.graph_nodes (tenant_id,project_id,run_id,status);
GRANT SELECT,INSERT ON runtime.graph_plans,runtime.graph_runs,runtime.graph_scopes,runtime.graph_nodes TO runtime_service;
GRANT UPDATE(frontier_revision,next_dispatch_order,outputs,stop_reason) ON runtime.graph_runs TO runtime_service;
GRANT UPDATE(status,outputs) ON runtime.graph_scopes TO runtime_service;
GRANT UPDATE(status,state,outputs,reason_code) ON runtime.graph_nodes TO runtime_service;
