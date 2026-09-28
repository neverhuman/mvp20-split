CREATE TABLE runtime.attempt_reports (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 report_id varchar(128) NOT NULL, intent_id varchar(128) NOT NULL,
 run_id varchar(128) NOT NULL, activation_id varchar(128) NOT NULL,
 attempt_id varchar(128) NOT NULL, fence bigint NOT NULL,
 result jsonb NOT NULL, reservations jsonb NOT NULL,
 PRIMARY KEY (tenant_id,project_id,report_id),
 UNIQUE (tenant_id,project_id,run_id,attempt_id),
 FOREIGN KEY (tenant_id,project_id,intent_id,run_id,activation_id,attempt_id,fence)
 REFERENCES runtime.completion_intents(tenant_id,project_id,intent_id,run_id,activation_id,attempt_id,fence)
);
GRANT SELECT,INSERT ON runtime.attempt_reports TO runtime_service;
