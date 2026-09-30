ALTER TABLE runtime.graph_runs ADD UNIQUE (tenant_id,project_id,run_id,plan_sha256);
CREATE TABLE runtime.definition_admissions (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL, run_id varchar(128) NOT NULL,
 plan_sha256 varchar(64) NOT NULL, validation_id varchar(128) NOT NULL, operation_id varchar(128) NOT NULL,
 PRIMARY KEY (tenant_id,project_id,run_id),
 UNIQUE (tenant_id,project_id,operation_id),
 FOREIGN KEY (tenant_id,project_id,run_id,plan_sha256) REFERENCES runtime.graph_runs(tenant_id,project_id,run_id,plan_sha256),
 FOREIGN KEY (tenant_id,project_id,validation_id) REFERENCES runtime.definition_validations,
 FOREIGN KEY (tenant_id,project_id,operation_id) REFERENCES runtime.commands(tenant_id,project_id,operation_id)
);
CREATE INDEX definition_admissions_plan ON runtime.definition_admissions(tenant_id,project_id,plan_sha256,run_id);
GRANT SELECT,INSERT ON runtime.definition_admissions TO runtime_service;
