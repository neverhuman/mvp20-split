ALTER TABLE runtime.runs ADD COLUMN tool_snapshot jsonb NOT NULL DEFAULT '{}'::jsonb
 CHECK (jsonb_typeof(tool_snapshot)='object');
CREATE TABLE runtime.intent_reservations (
 tenant_id varchar(128) NOT NULL, project_id varchar(128) NOT NULL,
 intent_id varchar(128) NOT NULL, output_binding varchar(128) NOT NULL,
 receipt jsonb NOT NULL CHECK (jsonb_typeof(receipt)='object'),
 PRIMARY KEY (tenant_id,project_id,intent_id,output_binding),
 FOREIGN KEY (tenant_id,project_id,intent_id) REFERENCES runtime.completion_intents
);
GRANT SELECT,INSERT ON runtime.intent_reservations TO runtime_service;
