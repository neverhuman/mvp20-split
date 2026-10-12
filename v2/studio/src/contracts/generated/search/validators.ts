// @ts-nocheck
// Generated standalone validators; change published schemas or the generator, never this file.
var __getOwnPropNames = Object.getOwnPropertyNames;
var __commonJS = (cb, mod) => function __require() {
  try {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  } catch (e) {
    throw mod = 0, e;
  }
};

// node_modules/ajv/dist/runtime/ucs2length.js
var require_ucs2length = __commonJS({
  "node_modules/ajv/dist/runtime/ucs2length.js"(exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    function ucs2length(str) {
      const len = str.length;
      let length = 0;
      let pos = 0;
      let value;
      while (pos < len) {
        length++;
        value = str.charCodeAt(pos++);
        if (value >= 55296 && value <= 56319 && pos < len) {
          value = str.charCodeAt(pos);
          if ((value & 64512) === 56320)
            pos++;
        }
      }
      return length;
    }
    exports.default = ucs2length;
    ucs2length.code = 'require("ajv/dist/runtime/ucs2length").default';
  }
});

// reviewed-validators.cjs
var require_reviewed_validators = __commonJS({
  "reviewed-validators.cjs"(exports) {
    exports.checkpoint = validate20;
    var schema31 = { "$defs": { "ArtifactRef": { "additionalProperties": false, "properties": { "artifact_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Artifact Id", "type": "string" }, "media_type": { "maxLength": 128, "minLength": 3, "pattern": "^[^\\s/]+/[^\\s/]+$", "title": "Media Type", "type": "string" }, "schema_ref": { "$ref": "#/$defs/SchemaRef" }, "scope": { "$ref": "#/$defs/Scope" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "size_bytes": { "maximum": 9007199254740991, "minimum": 0, "title": "Size Bytes", "type": "integer" } }, "required": ["artifact_id", "scope", "sha256", "media_type", "schema_ref", "size_bytes"], "title": "ArtifactRef", "type": "object" }, "CandidateAttempt": { "additionalProperties": false, "properties": { "candidate_id": { "pattern": "^[0-9a-f]{64}$", "title": "Candidate Id", "type": "string" }, "disposition": { "enum": ["proposed", "rejected", "duplicate"], "title": "Disposition", "type": "string" }, "draws": { "$ref": "#/$defs/RngInterval" }, "duplicate_of": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "title": "Duplicate Of" }, "generation": { "maximum": 1e4, "minimum": 0, "title": "Generation", "type": "integer" }, "genes": { "items": { "type": "number" }, "maxItems": 32, "minItems": 1, "title": "Genes", "type": "array" }, "operator": { "enum": ["seed", "variation"], "title": "Operator", "type": "string" }, "ordinal": { "maximum": 255, "minimum": 0, "title": "Ordinal", "type": "integer" }, "parents": { "items": { "pattern": "^[0-9a-f]{64}$", "type": "string" }, "maxItems": 2, "title": "Parents", "type": "array" }, "reason_code": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Reason Code" } }, "required": ["candidate_id", "generation", "ordinal", "operator", "genes", "parents", "draws", "disposition", "reason_code", "duplicate_of"], "title": "CandidateAttempt", "type": "object" }, "EvaluatedFitness": { "additionalProperties": false, "properties": { "constraint_violation": { "minimum": 0, "title": "Constraint Violation", "type": "number" }, "constraints_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Constraints Sha256", "type": "string" }, "evaluator": { "$ref": "#/$defs/ToolBinding" }, "evidence": { "items": { "$ref": "#/$defs/ArtifactRef" }, "maxItems": 32, "minItems": 1, "title": "Evidence", "type": "array" }, "objectives": { "items": { "$ref": "#/$defs/ObjectiveValue" }, "maxItems": 16, "minItems": 1, "title": "Objectives", "type": "array" }, "quality": { "enum": ["synthetic", "predicted", "measured"], "title": "Quality", "type": "string" }, "status": { "const": "evaluated", "title": "Status", "type": "string" } }, "required": ["status", "evaluator", "objectives", "constraint_violation", "constraints_sha256", "quality", "evidence"], "title": "EvaluatedFitness", "type": "object" }, "EvaluationObservation": { "additionalProperties": false, "properties": { "candidate_id": { "pattern": "^[0-9a-f]{64}$", "title": "Candidate Id", "type": "string" }, "evaluation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Evaluation Id", "type": "string" }, "outcome": { "discriminator": { "mapping": { "evaluated": "#/$defs/EvaluatedFitness", "failed": "#/$defs/UnavailableFitness", "inapplicable": "#/$defs/UnavailableFitness", "unknown": "#/$defs/UnavailableFitness" }, "propertyName": "status" }, "oneOf": [{ "$ref": "#/$defs/EvaluatedFitness" }, { "$ref": "#/$defs/UnavailableFitness" }], "title": "Outcome" }, "request_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Request Sha256", "type": "string" }, "schema_version": { "const": "1", "title": "Schema Version", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["schema_version", "scope", "evaluation_id", "candidate_id", "request_sha256", "outcome"], "title": "EvaluationObservation", "type": "object" }, "EvaluatorPolicy": { "additionalProperties": false, "properties": { "completion": { "const": "all_frozen_members_terminal", "title": "Completion", "type": "string" }, "constraints": { "$ref": "#/$defs/ArtifactRef" }, "context": { "items": { "$ref": "#/$defs/ArtifactRef" }, "maxItems": 32, "title": "Context", "type": "array" }, "tool": { "$ref": "#/$defs/ToolBinding" } }, "required": ["tool", "constraints", "context", "completion"], "title": "EvaluatorPolicy", "type": "object" }, "ImplementationPin": { "additionalProperties": false, "properties": { "name": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Name", "type": "string" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "version": { "maxLength": 128, "minLength": 1, "title": "Version", "type": "string" } }, "required": ["name", "version", "sha256"], "title": "ImplementationPin", "type": "object" }, "NumericObjective": { "additionalProperties": false, "properties": { "direction": { "enum": ["minimize", "maximize"], "title": "Direction", "type": "string" }, "objective_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Objective Id", "type": "string" }, "unit": { "maxLength": 64, "minLength": 1, "title": "Unit", "type": "string" } }, "required": ["objective_id", "unit", "direction"], "title": "NumericObjective", "type": "object" }, "NumericVariable": { "additionalProperties": false, "properties": { "lower": { "maximum": 1e100, "minimum": -1e100, "title": "Lower", "type": "number" }, "unit": { "maxLength": 64, "minLength": 1, "title": "Unit", "type": "string" }, "upper": { "maximum": 1e100, "minimum": -1e100, "title": "Upper", "type": "number" }, "variable_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Variable Id", "type": "string" } }, "required": ["variable_id", "unit", "lower", "upper"], "title": "NumericVariable", "type": "object" }, "ObjectiveValue": { "additionalProperties": false, "properties": { "objective_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Objective Id", "type": "string" }, "unit": { "maxLength": 64, "minLength": 1, "title": "Unit", "type": "string" }, "value": { "title": "Value", "type": "number" } }, "required": ["objective_id", "unit", "value"], "title": "ObjectiveValue", "type": "object" }, "PendingEvaluation": { "additionalProperties": false, "properties": { "candidate_id": { "pattern": "^[0-9a-f]{64}$", "title": "Candidate Id", "type": "string" }, "evaluation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Evaluation Id", "type": "string" }, "request_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Request Sha256", "type": "string" } }, "required": ["evaluation_id", "candidate_id", "request_sha256"], "title": "PendingEvaluation", "type": "object" }, "RngInterval": { "additionalProperties": false, "properties": { "end": { "maximum": 9007199254740991, "minimum": 0, "title": "End", "type": "integer" }, "start": { "maximum": 9007199254740991, "minimum": 0, "title": "Start", "type": "integer" } }, "required": ["start", "end"], "title": "RngInterval", "type": "object" }, "RngState": { "additionalProperties": false, "properties": { "algorithm": { "const": "sha256-counter-u53-v1", "title": "Algorithm", "type": "string" }, "counter": { "maximum": 9007199254740991, "minimum": 0, "title": "Counter", "type": "integer" }, "seed": { "pattern": "^[0-9a-f]{64}$", "title": "Seed", "type": "string" } }, "required": ["algorithm", "seed", "counter"], "title": "RngState", "type": "object" }, "SchemaRef": { "additionalProperties": false, "properties": { "schema_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Schema Id", "type": "string" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "version": { "const": "1", "title": "Version", "type": "string" } }, "required": ["schema_id", "version", "sha256"], "title": "SchemaRef", "type": "object" }, "Scope": { "additionalProperties": false, "properties": { "project_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Project Id", "type": "string" }, "tenant_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Tenant Id", "type": "string" } }, "required": ["tenant_id", "project_id"], "title": "Scope", "type": "object" }, "SearchBudget": { "additionalProperties": false, "properties": { "max_evaluations": { "maximum": 1e6, "minimum": 0, "title": "Max Evaluations", "type": "integer" }, "max_generations": { "maximum": 1e4, "minimum": 0, "title": "Max Generations", "type": "integer" }, "population_size": { "maximum": 128, "minimum": 1, "title": "Population Size", "type": "integer" }, "unchanged_front_limit": { "anyOf": [{ "maximum": 1e4, "minimum": 1, "type": "integer" }, { "type": "null" }], "title": "Unchanged Front Limit" } }, "required": ["population_size", "max_generations", "max_evaluations", "unchanged_front_limit"], "title": "SearchBudget", "type": "object" }, "SearchOperators": { "additionalProperties": false, "properties": { "crossover_probability": { "maximum": 1, "minimum": 0, "title": "Crossover Probability", "type": "number" }, "mutation_fraction": { "maximum": 1, "minimum": 0, "title": "Mutation Fraction", "type": "number" }, "mutation_probability": { "maximum": 1, "minimum": 0, "title": "Mutation Probability", "type": "number" }, "rng": { "const": "sha256-counter-u53-v1", "title": "Rng", "type": "string" }, "selection": { "const": "constrained-pareto-feasible-v1", "title": "Selection", "type": "string" }, "variation": { "const": "box-convex-uniform-v1", "title": "Variation", "type": "string" } }, "required": ["selection", "variation", "rng", "crossover_probability", "mutation_probability", "mutation_fraction"], "title": "SearchOperators", "type": "object" }, "SearchProgress": { "additionalProperties": false, "properties": { "evaluations_issued": { "maximum": 9007199254740991, "minimum": 0, "title": "Evaluations Issued", "type": "integer" }, "evaluations_terminal": { "maximum": 9007199254740991, "minimum": 0, "title": "Evaluations Terminal", "type": "integer" }, "generations_completed": { "maximum": 1e4, "minimum": 0, "title": "Generations Completed", "type": "integer" }, "unchanged_front_generations": { "maximum": 1e4, "minimum": 0, "title": "Unchanged Front Generations", "type": "integer" } }, "required": ["evaluations_issued", "evaluations_terminal", "generations_completed", "unchanged_front_generations"], "title": "SearchProgress", "type": "object" }, "SearchSpec": { "additionalProperties": false, "properties": { "budget": { "$ref": "#/$defs/SearchBudget" }, "evaluator": { "$ref": "#/$defs/EvaluatorPolicy" }, "implementations": { "items": { "$ref": "#/$defs/ImplementationPin" }, "maxItems": 32, "minItems": 1, "title": "Implementations", "type": "array" }, "objectives": { "items": { "$ref": "#/$defs/NumericObjective" }, "maxItems": 16, "minItems": 1, "title": "Objectives", "type": "array" }, "operators": { "$ref": "#/$defs/SearchOperators" }, "representation": { "$ref": "#/$defs/SchemaRef" }, "schema_version": { "const": "1", "title": "Schema Version", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" }, "search_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Search Id", "type": "string" }, "seed": { "pattern": "^[0-9a-f]{64}$", "title": "Seed", "type": "string" }, "variables": { "items": { "$ref": "#/$defs/NumericVariable" }, "maxItems": 32, "minItems": 1, "title": "Variables", "type": "array" } }, "required": ["schema_version", "scope", "search_id", "seed", "representation", "variables", "objectives", "evaluator", "operators", "budget", "implementations"], "title": "SearchSpec", "type": "object" }, "SelectionRank": { "additionalProperties": false, "properties": { "boundary": { "title": "Boundary", "type": "boolean" }, "candidate_id": { "pattern": "^[0-9a-f]{64}$", "title": "Candidate Id", "type": "string" }, "distance": { "maximum": 32, "minimum": 0, "title": "Distance", "type": "number" }, "feasible": { "title": "Feasible", "type": "boolean" }, "front": { "maximum": 255, "minimum": 0, "title": "Front", "type": "integer" } }, "required": ["candidate_id", "front", "boundary", "distance", "feasible"], "title": "SelectionRank", "type": "object" }, "SelectionReceipt": { "additionalProperties": false, "properties": { "disposition": { "enum": ["selected", "zero_requested", "no_feasible_candidates", "insufficient_feasible_candidates"], "title": "Disposition", "type": "string" }, "membership_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Membership Sha256", "type": "string" }, "policy": { "const": "constrained-pareto-feasible-v1", "title": "Policy", "type": "string" }, "ranks": { "items": { "$ref": "#/$defs/SelectionRank" }, "maxItems": 256, "title": "Ranks", "type": "array" }, "requested": { "maximum": 128, "minimum": 0, "title": "Requested", "type": "integer" }, "selected": { "items": { "pattern": "^[0-9a-f]{64}$", "type": "string" }, "maxItems": 128, "title": "Selected", "type": "array" } }, "required": ["policy", "membership_sha256", "requested", "selected", "ranks", "disposition"], "title": "SelectionReceipt", "type": "object" }, "ToolBinding": { "additionalProperties": false, "properties": { "capability_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Capability Id", "type": "string" }, "contract_version": { "const": "1", "title": "Contract Version", "type": "string" }, "image_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Image Sha256", "type": "string" }, "release": { "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$", "title": "Release", "type": "string" } }, "required": ["capability_id", "release", "image_sha256", "contract_version"], "title": "ToolBinding", "type": "object" }, "UnavailableFitness": { "additionalProperties": false, "properties": { "evidence": { "items": { "$ref": "#/$defs/ArtifactRef" }, "maxItems": 32, "title": "Evidence", "type": "array" }, "reason_code": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Reason Code", "type": "string" }, "status": { "enum": ["unknown", "failed", "inapplicable"], "title": "Status", "type": "string" } }, "required": ["status", "reason_code", "evidence"], "title": "UnavailableFitness", "type": "object" } }, "$id": "urn:amphora:search.checkpoint:1:serialization", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": { "attempts": { "items": { "$ref": "#/$defs/CandidateAttempt" }, "maxItems": 256, "minItems": 1, "title": "Attempts", "type": "array" }, "generation": { "maximum": 1e4, "minimum": 0, "title": "Generation", "type": "integer" }, "observations": { "items": { "$ref": "#/$defs/EvaluationObservation" }, "maxItems": 256, "title": "Observations", "type": "array" }, "pending": { "items": { "$ref": "#/$defs/PendingEvaluation" }, "maxItems": 256, "title": "Pending", "type": "array" }, "phase": { "enum": ["awaiting_evaluations", "ready_to_select", "selected", "stopped"], "title": "Phase", "type": "string" }, "population": { "items": { "pattern": "^[0-9a-f]{64}$", "type": "string" }, "maxItems": 128, "title": "Population", "type": "array" }, "previous": { "anyOf": [{ "$ref": "#/$defs/ArtifactRef" }, { "type": "null" }] }, "progress": { "$ref": "#/$defs/SearchProgress" }, "rng": { "$ref": "#/$defs/RngState" }, "schema_version": { "const": "1", "title": "Schema Version", "type": "string" }, "selection": { "anyOf": [{ "$ref": "#/$defs/SelectionReceipt" }, { "type": "null" }] }, "specification": { "$ref": "#/$defs/SearchSpec" }, "specification_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Specification Sha256", "type": "string" }, "stop_reason": { "anyOf": [{ "enum": ["generation_budget", "evaluation_budget", "unchanged_front", "no_feasible_candidates", "unavailable_fitness"], "type": "string" }, { "type": "null" }], "title": "Stop Reason" } }, "required": ["schema_version", "specification", "specification_sha256", "previous", "generation", "phase", "rng", "attempts", "population", "pending", "observations", "selection", "progress", "stop_reason"], "title": "SearchCheckpoint", "type": "object" };
    var func1 = Object.prototype.hasOwnProperty;
    var func3 = require_ucs2length().default;
    var schema32 = { "additionalProperties": false, "properties": { "candidate_id": { "pattern": "^[0-9a-f]{64}$", "title": "Candidate Id", "type": "string" }, "disposition": { "enum": ["proposed", "rejected", "duplicate"], "title": "Disposition", "type": "string" }, "draws": { "$ref": "#/$defs/RngInterval" }, "duplicate_of": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "title": "Duplicate Of" }, "generation": { "maximum": 1e4, "minimum": 0, "title": "Generation", "type": "integer" }, "genes": { "items": { "type": "number" }, "maxItems": 32, "minItems": 1, "title": "Genes", "type": "array" }, "operator": { "enum": ["seed", "variation"], "title": "Operator", "type": "string" }, "ordinal": { "maximum": 255, "minimum": 0, "title": "Ordinal", "type": "integer" }, "parents": { "items": { "pattern": "^[0-9a-f]{64}$", "type": "string" }, "maxItems": 2, "title": "Parents", "type": "array" }, "reason_code": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Reason Code" } }, "required": ["candidate_id", "generation", "ordinal", "operator", "genes", "parents", "draws", "disposition", "reason_code", "duplicate_of"], "title": "CandidateAttempt", "type": "object" };
    var pattern4 = new RegExp("^[0-9a-f]{64}$", "u");
    var pattern7 = new RegExp("^[A-Za-z0-9][A-Za-z0-9._:-]*$", "u");
    function validate21(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate21.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.candidate_id === void 0 && (missing0 = "candidate_id") || data.generation === void 0 && (missing0 = "generation") || data.ordinal === void 0 && (missing0 = "ordinal") || data.operator === void 0 && (missing0 = "operator") || data.genes === void 0 && (missing0 = "genes") || data.parents === void 0 && (missing0 = "parents") || data.draws === void 0 && (missing0 = "draws") || data.disposition === void 0 && (missing0 = "disposition") || data.reason_code === void 0 && (missing0 = "reason_code") || data.duplicate_of === void 0 && (missing0 = "duplicate_of")) {
            validate21.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func1.call(schema32.properties, key0)) {
                validate21.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.candidate_id !== void 0) {
                let data0 = data.candidate_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (!pattern4.test(data0)) {
                      validate21.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate21.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.disposition !== void 0) {
                  let data1 = data.disposition;
                  const _errs4 = errors;
                  if (typeof data1 !== "string") {
                    validate21.errors = [{ instancePath: instancePath + "/disposition", schemaPath: "#/properties/disposition/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "proposed" || data1 === "rejected" || data1 === "duplicate")) {
                    validate21.errors = [{ instancePath: instancePath + "/disposition", schemaPath: "#/properties/disposition/enum", keyword: "enum", params: { allowedValues: schema32.properties.disposition.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.draws !== void 0) {
                    let data2 = data.draws;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.start === void 0 && (missing1 = "start") || data2.end === void 0 && (missing1 = "end")) {
                          validate21.errors = [{ instancePath: instancePath + "/draws", schemaPath: "#/$defs/RngInterval/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "end" || key1 === "start")) {
                              validate21.errors = [{ instancePath: instancePath + "/draws", schemaPath: "#/$defs/RngInterval/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs9 === errors) {
                            if (data2.end !== void 0) {
                              let data3 = data2.end;
                              const _errs10 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                validate21.errors = [{ instancePath: instancePath + "/draws/end", schemaPath: "#/$defs/RngInterval/properties/end/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (errors === _errs10) {
                                if (typeof data3 == "number" && isFinite(data3)) {
                                  if (data3 > 9007199254740991 || isNaN(data3)) {
                                    validate21.errors = [{ instancePath: instancePath + "/draws/end", schemaPath: "#/$defs/RngInterval/properties/end/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                    return false;
                                  } else {
                                    if (data3 < 0 || isNaN(data3)) {
                                      validate21.errors = [{ instancePath: instancePath + "/draws/end", schemaPath: "#/$defs/RngInterval/properties/end/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                      return false;
                                    }
                                  }
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data2.start !== void 0) {
                                let data4 = data2.start;
                                const _errs12 = errors;
                                if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                                  validate21.errors = [{ instancePath: instancePath + "/draws/start", schemaPath: "#/$defs/RngInterval/properties/start/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                if (errors === _errs12) {
                                  if (typeof data4 == "number" && isFinite(data4)) {
                                    if (data4 > 9007199254740991 || isNaN(data4)) {
                                      validate21.errors = [{ instancePath: instancePath + "/draws/start", schemaPath: "#/$defs/RngInterval/properties/start/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                      return false;
                                    } else {
                                      if (data4 < 0 || isNaN(data4)) {
                                        validate21.errors = [{ instancePath: instancePath + "/draws/start", schemaPath: "#/$defs/RngInterval/properties/start/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                        return false;
                                      }
                                    }
                                  }
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                            }
                          }
                        }
                      } else {
                        validate21.errors = [{ instancePath: instancePath + "/draws", schemaPath: "#/$defs/RngInterval/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.duplicate_of !== void 0) {
                      let data5 = data.duplicate_of;
                      const _errs14 = errors;
                      const _errs15 = errors;
                      let valid3 = false;
                      const _errs16 = errors;
                      if (errors === _errs16) {
                        if (typeof data5 === "string") {
                          if (!pattern4.test(data5)) {
                            const err0 = { instancePath: instancePath + "/duplicate_of", schemaPath: "#/properties/duplicate_of/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                            if (vErrors === null) {
                              vErrors = [err0];
                            } else {
                              vErrors.push(err0);
                            }
                            errors++;
                          }
                        } else {
                          const err1 = { instancePath: instancePath + "/duplicate_of", schemaPath: "#/properties/duplicate_of/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err1];
                          } else {
                            vErrors.push(err1);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs16 === errors;
                      valid3 = valid3 || _valid0;
                      const _errs18 = errors;
                      if (data5 !== null) {
                        const err2 = { instancePath: instancePath + "/duplicate_of", schemaPath: "#/properties/duplicate_of/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                      }
                      var _valid0 = _errs18 === errors;
                      valid3 = valid3 || _valid0;
                      if (!valid3) {
                        const err3 = { instancePath: instancePath + "/duplicate_of", schemaPath: "#/properties/duplicate_of/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err3];
                        } else {
                          vErrors.push(err3);
                        }
                        errors++;
                        validate21.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs15;
                        if (vErrors !== null) {
                          if (_errs15) {
                            vErrors.length = _errs15;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs14 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.generation !== void 0) {
                        let data6 = data.generation;
                        const _errs20 = errors;
                        if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                          validate21.errors = [{ instancePath: instancePath + "/generation", schemaPath: "#/properties/generation/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                          return false;
                        }
                        if (errors === _errs20) {
                          if (typeof data6 == "number" && isFinite(data6)) {
                            if (data6 > 1e4 || isNaN(data6)) {
                              validate21.errors = [{ instancePath: instancePath + "/generation", schemaPath: "#/properties/generation/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e4 }, message: "must be <= 10000" }];
                              return false;
                            } else {
                              if (data6 < 0 || isNaN(data6)) {
                                validate21.errors = [{ instancePath: instancePath + "/generation", schemaPath: "#/properties/generation/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                return false;
                              }
                            }
                          }
                        }
                        var valid0 = _errs20 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.genes !== void 0) {
                          let data7 = data.genes;
                          const _errs22 = errors;
                          if (errors === _errs22) {
                            if (Array.isArray(data7)) {
                              if (data7.length > 32) {
                                validate21.errors = [{ instancePath: instancePath + "/genes", schemaPath: "#/properties/genes/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                                return false;
                              } else {
                                if (data7.length < 1) {
                                  validate21.errors = [{ instancePath: instancePath + "/genes", schemaPath: "#/properties/genes/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                                  return false;
                                } else {
                                  var valid4 = true;
                                  const len0 = data7.length;
                                  for (let i0 = 0; i0 < len0; i0++) {
                                    let data8 = data7[i0];
                                    const _errs24 = errors;
                                    if (!(typeof data8 == "number" && isFinite(data8))) {
                                      validate21.errors = [{ instancePath: instancePath + "/genes/" + i0, schemaPath: "#/properties/genes/items/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                      return false;
                                    }
                                    var valid4 = _errs24 === errors;
                                    if (!valid4) {
                                      break;
                                    }
                                  }
                                }
                              }
                            } else {
                              validate21.errors = [{ instancePath: instancePath + "/genes", schemaPath: "#/properties/genes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs22 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.operator !== void 0) {
                            let data9 = data.operator;
                            const _errs26 = errors;
                            if (typeof data9 !== "string") {
                              validate21.errors = [{ instancePath: instancePath + "/operator", schemaPath: "#/properties/operator/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if (!(data9 === "seed" || data9 === "variation")) {
                              validate21.errors = [{ instancePath: instancePath + "/operator", schemaPath: "#/properties/operator/enum", keyword: "enum", params: { allowedValues: schema32.properties.operator.enum }, message: "must be equal to one of the allowed values" }];
                              return false;
                            }
                            var valid0 = _errs26 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.ordinal !== void 0) {
                              let data10 = data.ordinal;
                              const _errs28 = errors;
                              if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)) && isFinite(data10))) {
                                validate21.errors = [{ instancePath: instancePath + "/ordinal", schemaPath: "#/properties/ordinal/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (errors === _errs28) {
                                if (typeof data10 == "number" && isFinite(data10)) {
                                  if (data10 > 255 || isNaN(data10)) {
                                    validate21.errors = [{ instancePath: instancePath + "/ordinal", schemaPath: "#/properties/ordinal/maximum", keyword: "maximum", params: { comparison: "<=", limit: 255 }, message: "must be <= 255" }];
                                    return false;
                                  } else {
                                    if (data10 < 0 || isNaN(data10)) {
                                      validate21.errors = [{ instancePath: instancePath + "/ordinal", schemaPath: "#/properties/ordinal/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                      return false;
                                    }
                                  }
                                }
                              }
                              var valid0 = _errs28 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.parents !== void 0) {
                                let data11 = data.parents;
                                const _errs30 = errors;
                                if (errors === _errs30) {
                                  if (Array.isArray(data11)) {
                                    if (data11.length > 2) {
                                      validate21.errors = [{ instancePath: instancePath + "/parents", schemaPath: "#/properties/parents/maxItems", keyword: "maxItems", params: { limit: 2 }, message: "must NOT have more than 2 items" }];
                                      return false;
                                    } else {
                                      var valid5 = true;
                                      const len1 = data11.length;
                                      for (let i1 = 0; i1 < len1; i1++) {
                                        let data12 = data11[i1];
                                        const _errs32 = errors;
                                        if (errors === _errs32) {
                                          if (typeof data12 === "string") {
                                            if (!pattern4.test(data12)) {
                                              validate21.errors = [{ instancePath: instancePath + "/parents/" + i1, schemaPath: "#/properties/parents/items/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                              return false;
                                            }
                                          } else {
                                            validate21.errors = [{ instancePath: instancePath + "/parents/" + i1, schemaPath: "#/properties/parents/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid5 = _errs32 === errors;
                                        if (!valid5) {
                                          break;
                                        }
                                      }
                                    }
                                  } else {
                                    validate21.errors = [{ instancePath: instancePath + "/parents", schemaPath: "#/properties/parents/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs30 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.reason_code !== void 0) {
                                  let data13 = data.reason_code;
                                  const _errs34 = errors;
                                  const _errs35 = errors;
                                  let valid6 = false;
                                  const _errs36 = errors;
                                  if (errors === _errs36) {
                                    if (typeof data13 === "string") {
                                      if (func3(data13) > 128) {
                                        const err4 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err4];
                                        } else {
                                          vErrors.push(err4);
                                        }
                                        errors++;
                                      } else {
                                        if (func3(data13) < 1) {
                                          const err5 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err5];
                                          } else {
                                            vErrors.push(err5);
                                          }
                                          errors++;
                                        } else {
                                          if (!pattern7.test(data13)) {
                                            const err6 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                            if (vErrors === null) {
                                              vErrors = [err6];
                                            } else {
                                              vErrors.push(err6);
                                            }
                                            errors++;
                                          }
                                        }
                                      }
                                    } else {
                                      const err7 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err7];
                                      } else {
                                        vErrors.push(err7);
                                      }
                                      errors++;
                                    }
                                  }
                                  var _valid1 = _errs36 === errors;
                                  valid6 = valid6 || _valid1;
                                  const _errs38 = errors;
                                  if (data13 !== null) {
                                    const err8 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                    if (vErrors === null) {
                                      vErrors = [err8];
                                    } else {
                                      vErrors.push(err8);
                                    }
                                    errors++;
                                  }
                                  var _valid1 = _errs38 === errors;
                                  valid6 = valid6 || _valid1;
                                  if (!valid6) {
                                    const err9 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                    if (vErrors === null) {
                                      vErrors = [err9];
                                    } else {
                                      vErrors.push(err9);
                                    }
                                    errors++;
                                    validate21.errors = vErrors;
                                    return false;
                                  } else {
                                    errors = _errs35;
                                    if (vErrors !== null) {
                                      if (_errs35) {
                                        vErrors.length = _errs35;
                                      } else {
                                        vErrors = null;
                                      }
                                    }
                                  }
                                  var valid0 = _errs34 === errors;
                                } else {
                                  var valid0 = true;
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate21.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate21.errors = vErrors;
      return errors === 0;
    }
    validate21.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema35 = { "additionalProperties": false, "properties": { "constraint_violation": { "minimum": 0, "title": "Constraint Violation", "type": "number" }, "constraints_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Constraints Sha256", "type": "string" }, "evaluator": { "$ref": "#/$defs/ToolBinding" }, "evidence": { "items": { "$ref": "#/$defs/ArtifactRef" }, "maxItems": 32, "minItems": 1, "title": "Evidence", "type": "array" }, "objectives": { "items": { "$ref": "#/$defs/ObjectiveValue" }, "maxItems": 16, "minItems": 1, "title": "Objectives", "type": "array" }, "quality": { "enum": ["synthetic", "predicted", "measured"], "title": "Quality", "type": "string" }, "status": { "const": "evaluated", "title": "Status", "type": "string" } }, "required": ["status", "evaluator", "objectives", "constraint_violation", "constraints_sha256", "quality", "evidence"], "title": "EvaluatedFitness", "type": "object" };
    var pattern13 = new RegExp("^[0-9]+\\.[0-9]+\\.[0-9]+$", "u");
    var pattern15 = new RegExp("^[^\\s/]+/[^\\s/]+$", "u");
    function validate25(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate25.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate25.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate25.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact_id !== void 0) {
                let data0 = data.artifact_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func3(data0) > 128) {
                      validate25.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func3(data0) < 1) {
                        validate25.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern7.test(data0)) {
                          validate25.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate25.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.media_type !== void 0) {
                  let data1 = data.media_type;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func3(data1) > 128) {
                        validate25.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func3(data1) < 3) {
                          validate25.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern15.test(data1)) {
                            validate25.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate25.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.schema_ref !== void 0) {
                    let data2 = data.schema_ref;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.schema_id === void 0 && (missing1 = "schema_id") || data2.version === void 0 && (missing1 = "version") || data2.sha256 === void 0 && (missing1 = "sha256")) {
                          validate25.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate25.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs9 === errors) {
                            if (data2.schema_id !== void 0) {
                              let data3 = data2.schema_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func3(data3) > 128) {
                                    validate25.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func3(data3) < 1) {
                                      validate25.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern7.test(data3)) {
                                        validate25.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate25.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data2.sha256 !== void 0) {
                                let data4 = data2.sha256;
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data4 === "string") {
                                    if (!pattern4.test(data4)) {
                                      validate25.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate25.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data2.version !== void 0) {
                                  let data5 = data2.version;
                                  const _errs14 = errors;
                                  if (typeof data5 !== "string") {
                                    validate25.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate25.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                              }
                            }
                          }
                        }
                      } else {
                        validate25.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.scope !== void 0) {
                      let data6 = data.scope;
                      const _errs16 = errors;
                      const _errs17 = errors;
                      if (errors === _errs17) {
                        if (data6 && typeof data6 == "object" && !Array.isArray(data6)) {
                          let missing2;
                          if (data6.tenant_id === void 0 && (missing2 = "tenant_id") || data6.project_id === void 0 && (missing2 = "project_id")) {
                            validate25.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate25.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs19 === errors) {
                              if (data6.project_id !== void 0) {
                                let data7 = data6.project_id;
                                const _errs20 = errors;
                                if (errors === _errs20) {
                                  if (typeof data7 === "string") {
                                    if (func3(data7) > 128) {
                                      validate25.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func3(data7) < 1) {
                                        validate25.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern7.test(data7)) {
                                          validate25.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate25.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid4 = _errs20 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data6.tenant_id !== void 0) {
                                  let data8 = data6.tenant_id;
                                  const _errs22 = errors;
                                  if (errors === _errs22) {
                                    if (typeof data8 === "string") {
                                      if (func3(data8) > 128) {
                                        validate25.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func3(data8) < 1) {
                                          validate25.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern7.test(data8)) {
                                            validate25.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate25.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid4 = _errs22 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate25.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs16 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.sha256 !== void 0) {
                        let data9 = data.sha256;
                        const _errs24 = errors;
                        if (errors === _errs24) {
                          if (typeof data9 === "string") {
                            if (!pattern4.test(data9)) {
                              validate25.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate25.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs24 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.size_bytes !== void 0) {
                          let data10 = data.size_bytes;
                          const _errs26 = errors;
                          if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)) && isFinite(data10))) {
                            validate25.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate25.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate25.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                  return false;
                                }
                              }
                            }
                          }
                          var valid0 = _errs26 === errors;
                        } else {
                          var valid0 = true;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate25.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate25.errors = vErrors;
      return errors === 0;
    }
    validate25.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate24(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate24.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.status === void 0 && (missing0 = "status") || data.evaluator === void 0 && (missing0 = "evaluator") || data.objectives === void 0 && (missing0 = "objectives") || data.constraint_violation === void 0 && (missing0 = "constraint_violation") || data.constraints_sha256 === void 0 && (missing0 = "constraints_sha256") || data.quality === void 0 && (missing0 = "quality") || data.evidence === void 0 && (missing0 = "evidence")) {
            validate24.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "constraint_violation" || key0 === "constraints_sha256" || key0 === "evaluator" || key0 === "evidence" || key0 === "objectives" || key0 === "quality" || key0 === "status")) {
                validate24.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.constraint_violation !== void 0) {
                let data0 = data.constraint_violation;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 < 0 || isNaN(data0)) {
                      validate24.errors = [{ instancePath: instancePath + "/constraint_violation", schemaPath: "#/properties/constraint_violation/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                      return false;
                    }
                  } else {
                    validate24.errors = [{ instancePath: instancePath + "/constraint_violation", schemaPath: "#/properties/constraint_violation/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.constraints_sha256 !== void 0) {
                  let data1 = data.constraints_sha256;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (!pattern4.test(data1)) {
                        validate24.errors = [{ instancePath: instancePath + "/constraints_sha256", schemaPath: "#/properties/constraints_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate24.errors = [{ instancePath: instancePath + "/constraints_sha256", schemaPath: "#/properties/constraints_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.evaluator !== void 0) {
                    let data2 = data.evaluator;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.capability_id === void 0 && (missing1 = "capability_id") || data2.release === void 0 && (missing1 = "release") || data2.image_sha256 === void 0 && (missing1 = "image_sha256") || data2.contract_version === void 0 && (missing1 = "contract_version")) {
                          validate24.errors = [{ instancePath: instancePath + "/evaluator", schemaPath: "#/$defs/ToolBinding/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "capability_id" || key1 === "contract_version" || key1 === "image_sha256" || key1 === "release")) {
                              validate24.errors = [{ instancePath: instancePath + "/evaluator", schemaPath: "#/$defs/ToolBinding/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs9 === errors) {
                            if (data2.capability_id !== void 0) {
                              let data3 = data2.capability_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func3(data3) > 128) {
                                    validate24.errors = [{ instancePath: instancePath + "/evaluator/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func3(data3) < 1) {
                                      validate24.errors = [{ instancePath: instancePath + "/evaluator/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern7.test(data3)) {
                                        validate24.errors = [{ instancePath: instancePath + "/evaluator/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate24.errors = [{ instancePath: instancePath + "/evaluator/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data2.contract_version !== void 0) {
                                let data4 = data2.contract_version;
                                const _errs12 = errors;
                                if (typeof data4 !== "string") {
                                  validate24.errors = [{ instancePath: instancePath + "/evaluator/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("1" !== data4) {
                                  validate24.errors = [{ instancePath: instancePath + "/evaluator/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data2.image_sha256 !== void 0) {
                                  let data5 = data2.image_sha256;
                                  const _errs14 = errors;
                                  if (errors === _errs14) {
                                    if (typeof data5 === "string") {
                                      if (!pattern4.test(data5)) {
                                        validate24.errors = [{ instancePath: instancePath + "/evaluator/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                        return false;
                                      }
                                    } else {
                                      validate24.errors = [{ instancePath: instancePath + "/evaluator/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                                if (valid2) {
                                  if (data2.release !== void 0) {
                                    let data6 = data2.release;
                                    const _errs16 = errors;
                                    if (errors === _errs16) {
                                      if (typeof data6 === "string") {
                                        if (!pattern13.test(data6)) {
                                          validate24.errors = [{ instancePath: instancePath + "/evaluator/release", schemaPath: "#/$defs/ToolBinding/properties/release/pattern", keyword: "pattern", params: { pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$" }, message: 'must match pattern "^[0-9]+\\.[0-9]+\\.[0-9]+$"' }];
                                          return false;
                                        }
                                      } else {
                                        validate24.errors = [{ instancePath: instancePath + "/evaluator/release", schemaPath: "#/$defs/ToolBinding/properties/release/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid2 = _errs16 === errors;
                                  } else {
                                    var valid2 = true;
                                  }
                                }
                              }
                            }
                          }
                        }
                      } else {
                        validate24.errors = [{ instancePath: instancePath + "/evaluator", schemaPath: "#/$defs/ToolBinding/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.evidence !== void 0) {
                      let data7 = data.evidence;
                      const _errs18 = errors;
                      if (errors === _errs18) {
                        if (Array.isArray(data7)) {
                          if (data7.length > 32) {
                            validate24.errors = [{ instancePath: instancePath + "/evidence", schemaPath: "#/properties/evidence/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                            return false;
                          } else {
                            if (data7.length < 1) {
                              validate24.errors = [{ instancePath: instancePath + "/evidence", schemaPath: "#/properties/evidence/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                              return false;
                            } else {
                              var valid3 = true;
                              const len0 = data7.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                const _errs20 = errors;
                                if (!validate25(data7[i0], { instancePath: instancePath + "/evidence/" + i0, parentData: data7, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
                                  errors = vErrors.length;
                                }
                                var valid3 = _errs20 === errors;
                                if (!valid3) {
                                  break;
                                }
                              }
                            }
                          }
                        } else {
                          validate24.errors = [{ instancePath: instancePath + "/evidence", schemaPath: "#/properties/evidence/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs18 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.objectives !== void 0) {
                        let data9 = data.objectives;
                        const _errs21 = errors;
                        if (errors === _errs21) {
                          if (Array.isArray(data9)) {
                            if (data9.length > 16) {
                              validate24.errors = [{ instancePath: instancePath + "/objectives", schemaPath: "#/properties/objectives/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                              return false;
                            } else {
                              if (data9.length < 1) {
                                validate24.errors = [{ instancePath: instancePath + "/objectives", schemaPath: "#/properties/objectives/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                                return false;
                              } else {
                                var valid4 = true;
                                const len1 = data9.length;
                                for (let i1 = 0; i1 < len1; i1++) {
                                  let data10 = data9[i1];
                                  const _errs23 = errors;
                                  const _errs24 = errors;
                                  if (errors === _errs24) {
                                    if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                                      let missing2;
                                      if (data10.objective_id === void 0 && (missing2 = "objective_id") || data10.unit === void 0 && (missing2 = "unit") || data10.value === void 0 && (missing2 = "value")) {
                                        validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1, schemaPath: "#/$defs/ObjectiveValue/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                        return false;
                                      } else {
                                        const _errs26 = errors;
                                        for (const key2 in data10) {
                                          if (!(key2 === "objective_id" || key2 === "unit" || key2 === "value")) {
                                            validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1, schemaPath: "#/$defs/ObjectiveValue/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                            return false;
                                            break;
                                          }
                                        }
                                        if (_errs26 === errors) {
                                          if (data10.objective_id !== void 0) {
                                            let data11 = data10.objective_id;
                                            const _errs27 = errors;
                                            if (errors === _errs27) {
                                              if (typeof data11 === "string") {
                                                if (func3(data11) > 128) {
                                                  validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/objective_id", schemaPath: "#/$defs/ObjectiveValue/properties/objective_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                  return false;
                                                } else {
                                                  if (func3(data11) < 1) {
                                                    validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/objective_id", schemaPath: "#/$defs/ObjectiveValue/properties/objective_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                    return false;
                                                  } else {
                                                    if (!pattern7.test(data11)) {
                                                      validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/objective_id", schemaPath: "#/$defs/ObjectiveValue/properties/objective_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                      return false;
                                                    }
                                                  }
                                                }
                                              } else {
                                                validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/objective_id", schemaPath: "#/$defs/ObjectiveValue/properties/objective_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                            }
                                            var valid6 = _errs27 === errors;
                                          } else {
                                            var valid6 = true;
                                          }
                                          if (valid6) {
                                            if (data10.unit !== void 0) {
                                              let data12 = data10.unit;
                                              const _errs29 = errors;
                                              if (errors === _errs29) {
                                                if (typeof data12 === "string") {
                                                  if (func3(data12) > 64) {
                                                    validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/unit", schemaPath: "#/$defs/ObjectiveValue/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" }];
                                                    return false;
                                                  } else {
                                                    if (func3(data12) < 1) {
                                                      validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/unit", schemaPath: "#/$defs/ObjectiveValue/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                      return false;
                                                    }
                                                  }
                                                } else {
                                                  validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/unit", schemaPath: "#/$defs/ObjectiveValue/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                  return false;
                                                }
                                              }
                                              var valid6 = _errs29 === errors;
                                            } else {
                                              var valid6 = true;
                                            }
                                            if (valid6) {
                                              if (data10.value !== void 0) {
                                                let data13 = data10.value;
                                                const _errs31 = errors;
                                                if (!(typeof data13 == "number" && isFinite(data13))) {
                                                  validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/value", schemaPath: "#/$defs/ObjectiveValue/properties/value/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                                  return false;
                                                }
                                                var valid6 = _errs31 === errors;
                                              } else {
                                                var valid6 = true;
                                              }
                                            }
                                          }
                                        }
                                      }
                                    } else {
                                      validate24.errors = [{ instancePath: instancePath + "/objectives/" + i1, schemaPath: "#/$defs/ObjectiveValue/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                      return false;
                                    }
                                  }
                                  var valid4 = _errs23 === errors;
                                  if (!valid4) {
                                    break;
                                  }
                                }
                              }
                            }
                          } else {
                            validate24.errors = [{ instancePath: instancePath + "/objectives", schemaPath: "#/properties/objectives/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs21 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.quality !== void 0) {
                          let data14 = data.quality;
                          const _errs33 = errors;
                          if (typeof data14 !== "string") {
                            validate24.errors = [{ instancePath: instancePath + "/quality", schemaPath: "#/properties/quality/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if (!(data14 === "synthetic" || data14 === "predicted" || data14 === "measured")) {
                            validate24.errors = [{ instancePath: instancePath + "/quality", schemaPath: "#/properties/quality/enum", keyword: "enum", params: { allowedValues: schema35.properties.quality.enum }, message: "must be equal to one of the allowed values" }];
                            return false;
                          }
                          var valid0 = _errs33 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.status !== void 0) {
                            let data15 = data.status;
                            const _errs35 = errors;
                            if (typeof data15 !== "string") {
                              validate24.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("evaluated" !== data15) {
                              validate24.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "evaluated" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs35 === errors;
                          } else {
                            var valid0 = true;
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate24.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate24.errors = vErrors;
      return errors === 0;
    }
    validate24.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema41 = { "additionalProperties": false, "properties": { "evidence": { "items": { "$ref": "#/$defs/ArtifactRef" }, "maxItems": 32, "title": "Evidence", "type": "array" }, "reason_code": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Reason Code", "type": "string" }, "status": { "enum": ["unknown", "failed", "inapplicable"], "title": "Status", "type": "string" } }, "required": ["status", "reason_code", "evidence"], "title": "UnavailableFitness", "type": "object" };
    function validate28(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate28.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.status === void 0 && (missing0 = "status") || data.reason_code === void 0 && (missing0 = "reason_code") || data.evidence === void 0 && (missing0 = "evidence")) {
            validate28.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "evidence" || key0 === "reason_code" || key0 === "status")) {
                validate28.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.evidence !== void 0) {
                let data0 = data.evidence;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 32) {
                      validate28.errors = [{ instancePath: instancePath + "/evidence", schemaPath: "#/properties/evidence/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate25(data0[i0], { instancePath: instancePath + "/evidence/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate28.errors = [{ instancePath: instancePath + "/evidence", schemaPath: "#/properties/evidence/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reason_code !== void 0) {
                  let data2 = data.reason_code;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (typeof data2 === "string") {
                      if (func3(data2) > 128) {
                        validate28.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func3(data2) < 1) {
                          validate28.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern7.test(data2)) {
                            validate28.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate28.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data3 = data.status;
                    const _errs7 = errors;
                    if (typeof data3 !== "string") {
                      validate28.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data3 === "unknown" || data3 === "failed" || data3 === "inapplicable")) {
                      validate28.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema41.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs7 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate28.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate28.errors = vErrors;
      return errors === 0;
    }
    validate28.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate23(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate23.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.schema_version === void 0 && (missing0 = "schema_version") || data.scope === void 0 && (missing0 = "scope") || data.evaluation_id === void 0 && (missing0 = "evaluation_id") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.outcome === void 0 && (missing0 = "outcome")) {
            validate23.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate_id" || key0 === "evaluation_id" || key0 === "outcome" || key0 === "request_sha256" || key0 === "schema_version" || key0 === "scope")) {
                validate23.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.candidate_id !== void 0) {
                let data0 = data.candidate_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (!pattern4.test(data0)) {
                      validate23.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate23.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.evaluation_id !== void 0) {
                  let data1 = data.evaluation_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func3(data1) > 128) {
                        validate23.errors = [{ instancePath: instancePath + "/evaluation_id", schemaPath: "#/properties/evaluation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func3(data1) < 1) {
                          validate23.errors = [{ instancePath: instancePath + "/evaluation_id", schemaPath: "#/properties/evaluation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern7.test(data1)) {
                            validate23.errors = [{ instancePath: instancePath + "/evaluation_id", schemaPath: "#/properties/evaluation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate23.errors = [{ instancePath: instancePath + "/evaluation_id", schemaPath: "#/properties/evaluation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.outcome !== void 0) {
                    let data2 = data.outcome;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    let valid1 = false;
                    let passing0 = null;
                    const _errs8 = errors;
                    if (!validate24(data2, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate24.errors : vErrors.concat(validate24.errors);
                      errors = vErrors.length;
                    }
                    var _valid0 = _errs8 === errors;
                    if (_valid0) {
                      valid1 = true;
                      passing0 = 0;
                      var props0 = true;
                    }
                    const _errs9 = errors;
                    if (!validate28(data2, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate28.errors : vErrors.concat(validate28.errors);
                      errors = vErrors.length;
                    }
                    var _valid0 = _errs9 === errors;
                    if (_valid0 && valid1) {
                      valid1 = false;
                      passing0 = [passing0, 1];
                    } else {
                      if (_valid0) {
                        valid1 = true;
                        passing0 = 1;
                        if (props0 !== true) {
                          props0 = true;
                        }
                      }
                    }
                    if (!valid1) {
                      const err0 = { instancePath: instancePath + "/outcome", schemaPath: "#/properties/outcome/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                      validate23.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs7;
                      if (vErrors !== null) {
                        if (_errs7) {
                          vErrors.length = _errs7;
                        } else {
                          vErrors = null;
                        }
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.request_sha256 !== void 0) {
                      let data3 = data.request_sha256;
                      const _errs11 = errors;
                      if (errors === _errs11) {
                        if (typeof data3 === "string") {
                          if (!pattern4.test(data3)) {
                            validate23.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                            return false;
                          }
                        } else {
                          validate23.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.schema_version !== void 0) {
                        let data4 = data.schema_version;
                        const _errs13 = errors;
                        if (typeof data4 !== "string") {
                          validate23.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data4) {
                          validate23.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs13 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.scope !== void 0) {
                          let data5 = data.scope;
                          const _errs15 = errors;
                          const _errs16 = errors;
                          if (errors === _errs16) {
                            if (data5 && typeof data5 == "object" && !Array.isArray(data5)) {
                              let missing1;
                              if (data5.tenant_id === void 0 && (missing1 = "tenant_id") || data5.project_id === void 0 && (missing1 = "project_id")) {
                                validate23.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                return false;
                              } else {
                                const _errs18 = errors;
                                for (const key1 in data5) {
                                  if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                    validate23.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs18 === errors) {
                                  if (data5.project_id !== void 0) {
                                    let data6 = data5.project_id;
                                    const _errs19 = errors;
                                    if (errors === _errs19) {
                                      if (typeof data6 === "string") {
                                        if (func3(data6) > 128) {
                                          validate23.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func3(data6) < 1) {
                                            validate23.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern7.test(data6)) {
                                              validate23.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate23.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid3 = _errs19 === errors;
                                  } else {
                                    var valid3 = true;
                                  }
                                  if (valid3) {
                                    if (data5.tenant_id !== void 0) {
                                      let data7 = data5.tenant_id;
                                      const _errs21 = errors;
                                      if (errors === _errs21) {
                                        if (typeof data7 === "string") {
                                          if (func3(data7) > 128) {
                                            validate23.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                            return false;
                                          } else {
                                            if (func3(data7) < 1) {
                                              validate23.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                              return false;
                                            } else {
                                              if (!pattern7.test(data7)) {
                                                validate23.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                return false;
                                              }
                                            }
                                          }
                                        } else {
                                          validate23.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                      }
                                      var valid3 = _errs21 === errors;
                                    } else {
                                      var valid3 = true;
                                    }
                                  }
                                }
                              }
                            } else {
                              validate23.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid0 = _errs15 === errors;
                        } else {
                          var valid0 = true;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate23.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate23.errors = vErrors;
      return errors === 0;
    }
    validate23.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema46 = { "additionalProperties": false, "properties": { "disposition": { "enum": ["selected", "zero_requested", "no_feasible_candidates", "insufficient_feasible_candidates"], "title": "Disposition", "type": "string" }, "membership_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Membership Sha256", "type": "string" }, "policy": { "const": "constrained-pareto-feasible-v1", "title": "Policy", "type": "string" }, "ranks": { "items": { "$ref": "#/$defs/SelectionRank" }, "maxItems": 256, "title": "Ranks", "type": "array" }, "requested": { "maximum": 128, "minimum": 0, "title": "Requested", "type": "integer" }, "selected": { "items": { "pattern": "^[0-9a-f]{64}$", "type": "string" }, "maxItems": 128, "title": "Selected", "type": "array" } }, "required": ["policy", "membership_sha256", "requested", "selected", "ranks", "disposition"], "title": "SelectionReceipt", "type": "object" };
    function validate33(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate33.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.policy === void 0 && (missing0 = "policy") || data.membership_sha256 === void 0 && (missing0 = "membership_sha256") || data.requested === void 0 && (missing0 = "requested") || data.selected === void 0 && (missing0 = "selected") || data.ranks === void 0 && (missing0 = "ranks") || data.disposition === void 0 && (missing0 = "disposition")) {
            validate33.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "disposition" || key0 === "membership_sha256" || key0 === "policy" || key0 === "ranks" || key0 === "requested" || key0 === "selected")) {
                validate33.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.disposition !== void 0) {
                let data0 = data.disposition;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate33.errors = [{ instancePath: instancePath + "/disposition", schemaPath: "#/properties/disposition/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if (!(data0 === "selected" || data0 === "zero_requested" || data0 === "no_feasible_candidates" || data0 === "insufficient_feasible_candidates")) {
                  validate33.errors = [{ instancePath: instancePath + "/disposition", schemaPath: "#/properties/disposition/enum", keyword: "enum", params: { allowedValues: schema46.properties.disposition.enum }, message: "must be equal to one of the allowed values" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.membership_sha256 !== void 0) {
                  let data1 = data.membership_sha256;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (!pattern4.test(data1)) {
                        validate33.errors = [{ instancePath: instancePath + "/membership_sha256", schemaPath: "#/properties/membership_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate33.errors = [{ instancePath: instancePath + "/membership_sha256", schemaPath: "#/properties/membership_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.policy !== void 0) {
                    let data2 = data.policy;
                    const _errs6 = errors;
                    if (typeof data2 !== "string") {
                      validate33.errors = [{ instancePath: instancePath + "/policy", schemaPath: "#/properties/policy/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("constrained-pareto-feasible-v1" !== data2) {
                      validate33.errors = [{ instancePath: instancePath + "/policy", schemaPath: "#/properties/policy/const", keyword: "const", params: { allowedValue: "constrained-pareto-feasible-v1" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.ranks !== void 0) {
                      let data3 = data.ranks;
                      const _errs8 = errors;
                      if (errors === _errs8) {
                        if (Array.isArray(data3)) {
                          if (data3.length > 256) {
                            validate33.errors = [{ instancePath: instancePath + "/ranks", schemaPath: "#/properties/ranks/maxItems", keyword: "maxItems", params: { limit: 256 }, message: "must NOT have more than 256 items" }];
                            return false;
                          } else {
                            var valid1 = true;
                            const len0 = data3.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              let data4 = data3[i0];
                              const _errs10 = errors;
                              const _errs11 = errors;
                              if (errors === _errs11) {
                                if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                                  let missing1;
                                  if (data4.candidate_id === void 0 && (missing1 = "candidate_id") || data4.front === void 0 && (missing1 = "front") || data4.boundary === void 0 && (missing1 = "boundary") || data4.distance === void 0 && (missing1 = "distance") || data4.feasible === void 0 && (missing1 = "feasible")) {
                                    validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0, schemaPath: "#/$defs/SelectionRank/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                    return false;
                                  } else {
                                    const _errs13 = errors;
                                    for (const key1 in data4) {
                                      if (!(key1 === "boundary" || key1 === "candidate_id" || key1 === "distance" || key1 === "feasible" || key1 === "front")) {
                                        validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0, schemaPath: "#/$defs/SelectionRank/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                        return false;
                                        break;
                                      }
                                    }
                                    if (_errs13 === errors) {
                                      if (data4.boundary !== void 0) {
                                        const _errs14 = errors;
                                        if (typeof data4.boundary !== "boolean") {
                                          validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/boundary", schemaPath: "#/$defs/SelectionRank/properties/boundary/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                          return false;
                                        }
                                        var valid3 = _errs14 === errors;
                                      } else {
                                        var valid3 = true;
                                      }
                                      if (valid3) {
                                        if (data4.candidate_id !== void 0) {
                                          let data6 = data4.candidate_id;
                                          const _errs16 = errors;
                                          if (errors === _errs16) {
                                            if (typeof data6 === "string") {
                                              if (!pattern4.test(data6)) {
                                                validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/candidate_id", schemaPath: "#/$defs/SelectionRank/properties/candidate_id/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                                return false;
                                              }
                                            } else {
                                              validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/candidate_id", schemaPath: "#/$defs/SelectionRank/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid3 = _errs16 === errors;
                                        } else {
                                          var valid3 = true;
                                        }
                                        if (valid3) {
                                          if (data4.distance !== void 0) {
                                            let data7 = data4.distance;
                                            const _errs18 = errors;
                                            if (errors === _errs18) {
                                              if (typeof data7 == "number" && isFinite(data7)) {
                                                if (data7 > 32 || isNaN(data7)) {
                                                  validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/distance", schemaPath: "#/$defs/SelectionRank/properties/distance/maximum", keyword: "maximum", params: { comparison: "<=", limit: 32 }, message: "must be <= 32" }];
                                                  return false;
                                                } else {
                                                  if (data7 < 0 || isNaN(data7)) {
                                                    validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/distance", schemaPath: "#/$defs/SelectionRank/properties/distance/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                    return false;
                                                  }
                                                }
                                              } else {
                                                validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/distance", schemaPath: "#/$defs/SelectionRank/properties/distance/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                                return false;
                                              }
                                            }
                                            var valid3 = _errs18 === errors;
                                          } else {
                                            var valid3 = true;
                                          }
                                          if (valid3) {
                                            if (data4.feasible !== void 0) {
                                              const _errs20 = errors;
                                              if (typeof data4.feasible !== "boolean") {
                                                validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/feasible", schemaPath: "#/$defs/SelectionRank/properties/feasible/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                                return false;
                                              }
                                              var valid3 = _errs20 === errors;
                                            } else {
                                              var valid3 = true;
                                            }
                                            if (valid3) {
                                              if (data4.front !== void 0) {
                                                let data9 = data4.front;
                                                const _errs22 = errors;
                                                if (!(typeof data9 == "number" && (!(data9 % 1) && !isNaN(data9)) && isFinite(data9))) {
                                                  validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/front", schemaPath: "#/$defs/SelectionRank/properties/front/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                  return false;
                                                }
                                                if (errors === _errs22) {
                                                  if (typeof data9 == "number" && isFinite(data9)) {
                                                    if (data9 > 255 || isNaN(data9)) {
                                                      validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/front", schemaPath: "#/$defs/SelectionRank/properties/front/maximum", keyword: "maximum", params: { comparison: "<=", limit: 255 }, message: "must be <= 255" }];
                                                      return false;
                                                    } else {
                                                      if (data9 < 0 || isNaN(data9)) {
                                                        validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0 + "/front", schemaPath: "#/$defs/SelectionRank/properties/front/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                        return false;
                                                      }
                                                    }
                                                  }
                                                }
                                                var valid3 = _errs22 === errors;
                                              } else {
                                                var valid3 = true;
                                              }
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                } else {
                                  validate33.errors = [{ instancePath: instancePath + "/ranks/" + i0, schemaPath: "#/$defs/SelectionRank/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                  return false;
                                }
                              }
                              var valid1 = _errs10 === errors;
                              if (!valid1) {
                                break;
                              }
                            }
                          }
                        } else {
                          validate33.errors = [{ instancePath: instancePath + "/ranks", schemaPath: "#/properties/ranks/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.requested !== void 0) {
                        let data10 = data.requested;
                        const _errs24 = errors;
                        if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)) && isFinite(data10))) {
                          validate33.errors = [{ instancePath: instancePath + "/requested", schemaPath: "#/properties/requested/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                          return false;
                        }
                        if (errors === _errs24) {
                          if (typeof data10 == "number" && isFinite(data10)) {
                            if (data10 > 128 || isNaN(data10)) {
                              validate33.errors = [{ instancePath: instancePath + "/requested", schemaPath: "#/properties/requested/maximum", keyword: "maximum", params: { comparison: "<=", limit: 128 }, message: "must be <= 128" }];
                              return false;
                            } else {
                              if (data10 < 0 || isNaN(data10)) {
                                validate33.errors = [{ instancePath: instancePath + "/requested", schemaPath: "#/properties/requested/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                return false;
                              }
                            }
                          }
                        }
                        var valid0 = _errs24 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.selected !== void 0) {
                          let data11 = data.selected;
                          const _errs26 = errors;
                          if (errors === _errs26) {
                            if (Array.isArray(data11)) {
                              if (data11.length > 128) {
                                validate33.errors = [{ instancePath: instancePath + "/selected", schemaPath: "#/properties/selected/maxItems", keyword: "maxItems", params: { limit: 128 }, message: "must NOT have more than 128 items" }];
                                return false;
                              } else {
                                var valid4 = true;
                                const len1 = data11.length;
                                for (let i1 = 0; i1 < len1; i1++) {
                                  let data12 = data11[i1];
                                  const _errs28 = errors;
                                  if (errors === _errs28) {
                                    if (typeof data12 === "string") {
                                      if (!pattern4.test(data12)) {
                                        validate33.errors = [{ instancePath: instancePath + "/selected/" + i1, schemaPath: "#/properties/selected/items/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                        return false;
                                      }
                                    } else {
                                      validate33.errors = [{ instancePath: instancePath + "/selected/" + i1, schemaPath: "#/properties/selected/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid4 = _errs28 === errors;
                                  if (!valid4) {
                                    break;
                                  }
                                }
                              }
                            } else {
                              validate33.errors = [{ instancePath: instancePath + "/selected", schemaPath: "#/properties/selected/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs26 === errors;
                        } else {
                          var valid0 = true;
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate33.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate33.errors = vErrors;
      return errors === 0;
    }
    validate33.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema48 = { "additionalProperties": false, "properties": { "budget": { "$ref": "#/$defs/SearchBudget" }, "evaluator": { "$ref": "#/$defs/EvaluatorPolicy" }, "implementations": { "items": { "$ref": "#/$defs/ImplementationPin" }, "maxItems": 32, "minItems": 1, "title": "Implementations", "type": "array" }, "objectives": { "items": { "$ref": "#/$defs/NumericObjective" }, "maxItems": 16, "minItems": 1, "title": "Objectives", "type": "array" }, "operators": { "$ref": "#/$defs/SearchOperators" }, "representation": { "$ref": "#/$defs/SchemaRef" }, "schema_version": { "const": "1", "title": "Schema Version", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" }, "search_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Search Id", "type": "string" }, "seed": { "pattern": "^[0-9a-f]{64}$", "title": "Seed", "type": "string" }, "variables": { "items": { "$ref": "#/$defs/NumericVariable" }, "maxItems": 32, "minItems": 1, "title": "Variables", "type": "array" } }, "required": ["schema_version", "scope", "search_id", "seed", "representation", "variables", "objectives", "evaluator", "operators", "budget", "implementations"], "title": "SearchSpec", "type": "object" };
    var schema53 = { "additionalProperties": false, "properties": { "direction": { "enum": ["minimize", "maximize"], "title": "Direction", "type": "string" }, "objective_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Objective Id", "type": "string" }, "unit": { "maxLength": 64, "minLength": 1, "title": "Unit", "type": "string" } }, "required": ["objective_id", "unit", "direction"], "title": "NumericObjective", "type": "object" };
    function validate36(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate36.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.tool === void 0 && (missing0 = "tool") || data.constraints === void 0 && (missing0 = "constraints") || data.context === void 0 && (missing0 = "context") || data.completion === void 0 && (missing0 = "completion")) {
            validate36.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "completion" || key0 === "constraints" || key0 === "context" || key0 === "tool")) {
                validate36.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.completion !== void 0) {
                let data0 = data.completion;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate36.errors = [{ instancePath: instancePath + "/completion", schemaPath: "#/properties/completion/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("all_frozen_members_terminal" !== data0) {
                  validate36.errors = [{ instancePath: instancePath + "/completion", schemaPath: "#/properties/completion/const", keyword: "const", params: { allowedValue: "all_frozen_members_terminal" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.constraints !== void 0) {
                  const _errs4 = errors;
                  if (!validate25(data.constraints, { instancePath: instancePath + "/constraints", parentData: data, parentDataProperty: "constraints", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.context !== void 0) {
                    let data2 = data.context;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (Array.isArray(data2)) {
                        if (data2.length > 32) {
                          validate36.errors = [{ instancePath: instancePath + "/context", schemaPath: "#/properties/context/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                          return false;
                        } else {
                          var valid1 = true;
                          const len0 = data2.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs7 = errors;
                            if (!validate25(data2[i0], { instancePath: instancePath + "/context/" + i0, parentData: data2, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
                              errors = vErrors.length;
                            }
                            var valid1 = _errs7 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate36.errors = [{ instancePath: instancePath + "/context", schemaPath: "#/properties/context/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.tool !== void 0) {
                      let data4 = data.tool;
                      const _errs8 = errors;
                      const _errs9 = errors;
                      if (errors === _errs9) {
                        if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                          let missing1;
                          if (data4.capability_id === void 0 && (missing1 = "capability_id") || data4.release === void 0 && (missing1 = "release") || data4.image_sha256 === void 0 && (missing1 = "image_sha256") || data4.contract_version === void 0 && (missing1 = "contract_version")) {
                            validate36.errors = [{ instancePath: instancePath + "/tool", schemaPath: "#/$defs/ToolBinding/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                            return false;
                          } else {
                            const _errs11 = errors;
                            for (const key1 in data4) {
                              if (!(key1 === "capability_id" || key1 === "contract_version" || key1 === "image_sha256" || key1 === "release")) {
                                validate36.errors = [{ instancePath: instancePath + "/tool", schemaPath: "#/$defs/ToolBinding/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs11 === errors) {
                              if (data4.capability_id !== void 0) {
                                let data5 = data4.capability_id;
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data5 === "string") {
                                    if (func3(data5) > 128) {
                                      validate36.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func3(data5) < 1) {
                                        validate36.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern7.test(data5)) {
                                          validate36.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate36.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid3 = _errs12 === errors;
                              } else {
                                var valid3 = true;
                              }
                              if (valid3) {
                                if (data4.contract_version !== void 0) {
                                  let data6 = data4.contract_version;
                                  const _errs14 = errors;
                                  if (typeof data6 !== "string") {
                                    validate36.errors = [{ instancePath: instancePath + "/tool/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data6) {
                                    validate36.errors = [{ instancePath: instancePath + "/tool/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid3 = _errs14 === errors;
                                } else {
                                  var valid3 = true;
                                }
                                if (valid3) {
                                  if (data4.image_sha256 !== void 0) {
                                    let data7 = data4.image_sha256;
                                    const _errs16 = errors;
                                    if (errors === _errs16) {
                                      if (typeof data7 === "string") {
                                        if (!pattern4.test(data7)) {
                                          validate36.errors = [{ instancePath: instancePath + "/tool/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                          return false;
                                        }
                                      } else {
                                        validate36.errors = [{ instancePath: instancePath + "/tool/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid3 = _errs16 === errors;
                                  } else {
                                    var valid3 = true;
                                  }
                                  if (valid3) {
                                    if (data4.release !== void 0) {
                                      let data8 = data4.release;
                                      const _errs18 = errors;
                                      if (errors === _errs18) {
                                        if (typeof data8 === "string") {
                                          if (!pattern13.test(data8)) {
                                            validate36.errors = [{ instancePath: instancePath + "/tool/release", schemaPath: "#/$defs/ToolBinding/properties/release/pattern", keyword: "pattern", params: { pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$" }, message: 'must match pattern "^[0-9]+\\.[0-9]+\\.[0-9]+$"' }];
                                            return false;
                                          }
                                        } else {
                                          validate36.errors = [{ instancePath: instancePath + "/tool/release", schemaPath: "#/$defs/ToolBinding/properties/release/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                      }
                                      var valid3 = _errs18 === errors;
                                    } else {
                                      var valid3 = true;
                                    }
                                  }
                                }
                              }
                            }
                          }
                        } else {
                          validate36.errors = [{ instancePath: instancePath + "/tool", schemaPath: "#/$defs/ToolBinding/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        } else {
          validate36.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate36.errors = vErrors;
      return errors === 0;
    }
    validate36.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate35(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate35.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.schema_version === void 0 && (missing0 = "schema_version") || data.scope === void 0 && (missing0 = "scope") || data.search_id === void 0 && (missing0 = "search_id") || data.seed === void 0 && (missing0 = "seed") || data.representation === void 0 && (missing0 = "representation") || data.variables === void 0 && (missing0 = "variables") || data.objectives === void 0 && (missing0 = "objectives") || data.evaluator === void 0 && (missing0 = "evaluator") || data.operators === void 0 && (missing0 = "operators") || data.budget === void 0 && (missing0 = "budget") || data.implementations === void 0 && (missing0 = "implementations")) {
            validate35.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func1.call(schema48.properties, key0)) {
                validate35.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.budget !== void 0) {
                let data0 = data.budget;
                const _errs2 = errors;
                const _errs3 = errors;
                if (errors === _errs3) {
                  if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                    let missing1;
                    if (data0.population_size === void 0 && (missing1 = "population_size") || data0.max_generations === void 0 && (missing1 = "max_generations") || data0.max_evaluations === void 0 && (missing1 = "max_evaluations") || data0.unchanged_front_limit === void 0 && (missing1 = "unchanged_front_limit")) {
                      validate35.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/$defs/SearchBudget/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                      return false;
                    } else {
                      const _errs5 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "max_evaluations" || key1 === "max_generations" || key1 === "population_size" || key1 === "unchanged_front_limit")) {
                          validate35.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/$defs/SearchBudget/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                          return false;
                          break;
                        }
                      }
                      if (_errs5 === errors) {
                        if (data0.max_evaluations !== void 0) {
                          let data1 = data0.max_evaluations;
                          const _errs6 = errors;
                          if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                            validate35.errors = [{ instancePath: instancePath + "/budget/max_evaluations", schemaPath: "#/$defs/SearchBudget/properties/max_evaluations/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs6) {
                            if (typeof data1 == "number" && isFinite(data1)) {
                              if (data1 > 1e6 || isNaN(data1)) {
                                validate35.errors = [{ instancePath: instancePath + "/budget/max_evaluations", schemaPath: "#/$defs/SearchBudget/properties/max_evaluations/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e6 }, message: "must be <= 1000000" }];
                                return false;
                              } else {
                                if (data1 < 0 || isNaN(data1)) {
                                  validate35.errors = [{ instancePath: instancePath + "/budget/max_evaluations", schemaPath: "#/$defs/SearchBudget/properties/max_evaluations/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                  return false;
                                }
                              }
                            }
                          }
                          var valid2 = _errs6 === errors;
                        } else {
                          var valid2 = true;
                        }
                        if (valid2) {
                          if (data0.max_generations !== void 0) {
                            let data2 = data0.max_generations;
                            const _errs8 = errors;
                            if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                              validate35.errors = [{ instancePath: instancePath + "/budget/max_generations", schemaPath: "#/$defs/SearchBudget/properties/max_generations/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            if (errors === _errs8) {
                              if (typeof data2 == "number" && isFinite(data2)) {
                                if (data2 > 1e4 || isNaN(data2)) {
                                  validate35.errors = [{ instancePath: instancePath + "/budget/max_generations", schemaPath: "#/$defs/SearchBudget/properties/max_generations/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e4 }, message: "must be <= 10000" }];
                                  return false;
                                } else {
                                  if (data2 < 0 || isNaN(data2)) {
                                    validate35.errors = [{ instancePath: instancePath + "/budget/max_generations", schemaPath: "#/$defs/SearchBudget/properties/max_generations/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                    return false;
                                  }
                                }
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data0.population_size !== void 0) {
                              let data3 = data0.population_size;
                              const _errs10 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                validate35.errors = [{ instancePath: instancePath + "/budget/population_size", schemaPath: "#/$defs/SearchBudget/properties/population_size/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (errors === _errs10) {
                                if (typeof data3 == "number" && isFinite(data3)) {
                                  if (data3 > 128 || isNaN(data3)) {
                                    validate35.errors = [{ instancePath: instancePath + "/budget/population_size", schemaPath: "#/$defs/SearchBudget/properties/population_size/maximum", keyword: "maximum", params: { comparison: "<=", limit: 128 }, message: "must be <= 128" }];
                                    return false;
                                  } else {
                                    if (data3 < 1 || isNaN(data3)) {
                                      validate35.errors = [{ instancePath: instancePath + "/budget/population_size", schemaPath: "#/$defs/SearchBudget/properties/population_size/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                      return false;
                                    }
                                  }
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data0.unchanged_front_limit !== void 0) {
                                let data4 = data0.unchanged_front_limit;
                                const _errs12 = errors;
                                const _errs13 = errors;
                                let valid3 = false;
                                const _errs14 = errors;
                                if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                                  const err0 = { instancePath: instancePath + "/budget/unchanged_front_limit", schemaPath: "#/$defs/SearchBudget/properties/unchanged_front_limit/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                  if (vErrors === null) {
                                    vErrors = [err0];
                                  } else {
                                    vErrors.push(err0);
                                  }
                                  errors++;
                                }
                                if (errors === _errs14) {
                                  if (typeof data4 == "number" && isFinite(data4)) {
                                    if (data4 > 1e4 || isNaN(data4)) {
                                      const err1 = { instancePath: instancePath + "/budget/unchanged_front_limit", schemaPath: "#/$defs/SearchBudget/properties/unchanged_front_limit/anyOf/0/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e4 }, message: "must be <= 10000" };
                                      if (vErrors === null) {
                                        vErrors = [err1];
                                      } else {
                                        vErrors.push(err1);
                                      }
                                      errors++;
                                    } else {
                                      if (data4 < 1 || isNaN(data4)) {
                                        const err2 = { instancePath: instancePath + "/budget/unchanged_front_limit", schemaPath: "#/$defs/SearchBudget/properties/unchanged_front_limit/anyOf/0/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" };
                                        if (vErrors === null) {
                                          vErrors = [err2];
                                        } else {
                                          vErrors.push(err2);
                                        }
                                        errors++;
                                      }
                                    }
                                  }
                                }
                                var _valid0 = _errs14 === errors;
                                valid3 = valid3 || _valid0;
                                const _errs16 = errors;
                                if (data4 !== null) {
                                  const err3 = { instancePath: instancePath + "/budget/unchanged_front_limit", schemaPath: "#/$defs/SearchBudget/properties/unchanged_front_limit/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                  if (vErrors === null) {
                                    vErrors = [err3];
                                  } else {
                                    vErrors.push(err3);
                                  }
                                  errors++;
                                }
                                var _valid0 = _errs16 === errors;
                                valid3 = valid3 || _valid0;
                                if (!valid3) {
                                  const err4 = { instancePath: instancePath + "/budget/unchanged_front_limit", schemaPath: "#/$defs/SearchBudget/properties/unchanged_front_limit/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                  if (vErrors === null) {
                                    vErrors = [err4];
                                  } else {
                                    vErrors.push(err4);
                                  }
                                  errors++;
                                  validate35.errors = vErrors;
                                  return false;
                                } else {
                                  errors = _errs13;
                                  if (vErrors !== null) {
                                    if (_errs13) {
                                      vErrors.length = _errs13;
                                    } else {
                                      vErrors = null;
                                    }
                                  }
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                            }
                          }
                        }
                      }
                    }
                  } else {
                    validate35.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/$defs/SearchBudget/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.evaluator !== void 0) {
                  const _errs18 = errors;
                  if (!validate36(data.evaluator, { instancePath: instancePath + "/evaluator", parentData: data, parentDataProperty: "evaluator", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate36.errors : vErrors.concat(validate36.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs18 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.implementations !== void 0) {
                    let data6 = data.implementations;
                    const _errs19 = errors;
                    if (errors === _errs19) {
                      if (Array.isArray(data6)) {
                        if (data6.length > 32) {
                          validate35.errors = [{ instancePath: instancePath + "/implementations", schemaPath: "#/properties/implementations/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                          return false;
                        } else {
                          if (data6.length < 1) {
                            validate35.errors = [{ instancePath: instancePath + "/implementations", schemaPath: "#/properties/implementations/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                            return false;
                          } else {
                            var valid4 = true;
                            const len0 = data6.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              let data7 = data6[i0];
                              const _errs21 = errors;
                              const _errs22 = errors;
                              if (errors === _errs22) {
                                if (data7 && typeof data7 == "object" && !Array.isArray(data7)) {
                                  let missing2;
                                  if (data7.name === void 0 && (missing2 = "name") || data7.version === void 0 && (missing2 = "version") || data7.sha256 === void 0 && (missing2 = "sha256")) {
                                    validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0, schemaPath: "#/$defs/ImplementationPin/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                    return false;
                                  } else {
                                    const _errs24 = errors;
                                    for (const key2 in data7) {
                                      if (!(key2 === "name" || key2 === "sha256" || key2 === "version")) {
                                        validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0, schemaPath: "#/$defs/ImplementationPin/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                        return false;
                                        break;
                                      }
                                    }
                                    if (_errs24 === errors) {
                                      if (data7.name !== void 0) {
                                        let data8 = data7.name;
                                        const _errs25 = errors;
                                        if (errors === _errs25) {
                                          if (typeof data8 === "string") {
                                            if (func3(data8) > 128) {
                                              validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0 + "/name", schemaPath: "#/$defs/ImplementationPin/properties/name/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                              return false;
                                            } else {
                                              if (func3(data8) < 1) {
                                                validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0 + "/name", schemaPath: "#/$defs/ImplementationPin/properties/name/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                return false;
                                              } else {
                                                if (!pattern7.test(data8)) {
                                                  validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0 + "/name", schemaPath: "#/$defs/ImplementationPin/properties/name/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                  return false;
                                                }
                                              }
                                            }
                                          } else {
                                            validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0 + "/name", schemaPath: "#/$defs/ImplementationPin/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid6 = _errs25 === errors;
                                      } else {
                                        var valid6 = true;
                                      }
                                      if (valid6) {
                                        if (data7.sha256 !== void 0) {
                                          let data9 = data7.sha256;
                                          const _errs27 = errors;
                                          if (errors === _errs27) {
                                            if (typeof data9 === "string") {
                                              if (!pattern4.test(data9)) {
                                                validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0 + "/sha256", schemaPath: "#/$defs/ImplementationPin/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                                return false;
                                              }
                                            } else {
                                              validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0 + "/sha256", schemaPath: "#/$defs/ImplementationPin/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid6 = _errs27 === errors;
                                        } else {
                                          var valid6 = true;
                                        }
                                        if (valid6) {
                                          if (data7.version !== void 0) {
                                            let data10 = data7.version;
                                            const _errs29 = errors;
                                            if (errors === _errs29) {
                                              if (typeof data10 === "string") {
                                                if (func3(data10) > 128) {
                                                  validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0 + "/version", schemaPath: "#/$defs/ImplementationPin/properties/version/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                  return false;
                                                } else {
                                                  if (func3(data10) < 1) {
                                                    validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0 + "/version", schemaPath: "#/$defs/ImplementationPin/properties/version/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                    return false;
                                                  }
                                                }
                                              } else {
                                                validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0 + "/version", schemaPath: "#/$defs/ImplementationPin/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                            }
                                            var valid6 = _errs29 === errors;
                                          } else {
                                            var valid6 = true;
                                          }
                                        }
                                      }
                                    }
                                  }
                                } else {
                                  validate35.errors = [{ instancePath: instancePath + "/implementations/" + i0, schemaPath: "#/$defs/ImplementationPin/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                  return false;
                                }
                              }
                              var valid4 = _errs21 === errors;
                              if (!valid4) {
                                break;
                              }
                            }
                          }
                        }
                      } else {
                        validate35.errors = [{ instancePath: instancePath + "/implementations", schemaPath: "#/properties/implementations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs19 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.objectives !== void 0) {
                      let data11 = data.objectives;
                      const _errs31 = errors;
                      if (errors === _errs31) {
                        if (Array.isArray(data11)) {
                          if (data11.length > 16) {
                            validate35.errors = [{ instancePath: instancePath + "/objectives", schemaPath: "#/properties/objectives/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                            return false;
                          } else {
                            if (data11.length < 1) {
                              validate35.errors = [{ instancePath: instancePath + "/objectives", schemaPath: "#/properties/objectives/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                              return false;
                            } else {
                              var valid7 = true;
                              const len1 = data11.length;
                              for (let i1 = 0; i1 < len1; i1++) {
                                let data12 = data11[i1];
                                const _errs33 = errors;
                                const _errs34 = errors;
                                if (errors === _errs34) {
                                  if (data12 && typeof data12 == "object" && !Array.isArray(data12)) {
                                    let missing3;
                                    if (data12.objective_id === void 0 && (missing3 = "objective_id") || data12.unit === void 0 && (missing3 = "unit") || data12.direction === void 0 && (missing3 = "direction")) {
                                      validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1, schemaPath: "#/$defs/NumericObjective/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" }];
                                      return false;
                                    } else {
                                      const _errs36 = errors;
                                      for (const key3 in data12) {
                                        if (!(key3 === "direction" || key3 === "objective_id" || key3 === "unit")) {
                                          validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1, schemaPath: "#/$defs/NumericObjective/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" }];
                                          return false;
                                          break;
                                        }
                                      }
                                      if (_errs36 === errors) {
                                        if (data12.direction !== void 0) {
                                          let data13 = data12.direction;
                                          const _errs37 = errors;
                                          if (typeof data13 !== "string") {
                                            validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/direction", schemaPath: "#/$defs/NumericObjective/properties/direction/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                          if (!(data13 === "minimize" || data13 === "maximize")) {
                                            validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/direction", schemaPath: "#/$defs/NumericObjective/properties/direction/enum", keyword: "enum", params: { allowedValues: schema53.properties.direction.enum }, message: "must be equal to one of the allowed values" }];
                                            return false;
                                          }
                                          var valid9 = _errs37 === errors;
                                        } else {
                                          var valid9 = true;
                                        }
                                        if (valid9) {
                                          if (data12.objective_id !== void 0) {
                                            let data14 = data12.objective_id;
                                            const _errs39 = errors;
                                            if (errors === _errs39) {
                                              if (typeof data14 === "string") {
                                                if (func3(data14) > 128) {
                                                  validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/objective_id", schemaPath: "#/$defs/NumericObjective/properties/objective_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                  return false;
                                                } else {
                                                  if (func3(data14) < 1) {
                                                    validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/objective_id", schemaPath: "#/$defs/NumericObjective/properties/objective_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                    return false;
                                                  } else {
                                                    if (!pattern7.test(data14)) {
                                                      validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/objective_id", schemaPath: "#/$defs/NumericObjective/properties/objective_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                      return false;
                                                    }
                                                  }
                                                }
                                              } else {
                                                validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/objective_id", schemaPath: "#/$defs/NumericObjective/properties/objective_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                            }
                                            var valid9 = _errs39 === errors;
                                          } else {
                                            var valid9 = true;
                                          }
                                          if (valid9) {
                                            if (data12.unit !== void 0) {
                                              let data15 = data12.unit;
                                              const _errs41 = errors;
                                              if (errors === _errs41) {
                                                if (typeof data15 === "string") {
                                                  if (func3(data15) > 64) {
                                                    validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/unit", schemaPath: "#/$defs/NumericObjective/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" }];
                                                    return false;
                                                  } else {
                                                    if (func3(data15) < 1) {
                                                      validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/unit", schemaPath: "#/$defs/NumericObjective/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                      return false;
                                                    }
                                                  }
                                                } else {
                                                  validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1 + "/unit", schemaPath: "#/$defs/NumericObjective/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                  return false;
                                                }
                                              }
                                              var valid9 = _errs41 === errors;
                                            } else {
                                              var valid9 = true;
                                            }
                                          }
                                        }
                                      }
                                    }
                                  } else {
                                    validate35.errors = [{ instancePath: instancePath + "/objectives/" + i1, schemaPath: "#/$defs/NumericObjective/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                    return false;
                                  }
                                }
                                var valid7 = _errs33 === errors;
                                if (!valid7) {
                                  break;
                                }
                              }
                            }
                          }
                        } else {
                          validate35.errors = [{ instancePath: instancePath + "/objectives", schemaPath: "#/properties/objectives/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs31 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.operators !== void 0) {
                        let data16 = data.operators;
                        const _errs43 = errors;
                        const _errs44 = errors;
                        if (errors === _errs44) {
                          if (data16 && typeof data16 == "object" && !Array.isArray(data16)) {
                            let missing4;
                            if (data16.selection === void 0 && (missing4 = "selection") || data16.variation === void 0 && (missing4 = "variation") || data16.rng === void 0 && (missing4 = "rng") || data16.crossover_probability === void 0 && (missing4 = "crossover_probability") || data16.mutation_probability === void 0 && (missing4 = "mutation_probability") || data16.mutation_fraction === void 0 && (missing4 = "mutation_fraction")) {
                              validate35.errors = [{ instancePath: instancePath + "/operators", schemaPath: "#/$defs/SearchOperators/required", keyword: "required", params: { missingProperty: missing4 }, message: "must have required property '" + missing4 + "'" }];
                              return false;
                            } else {
                              const _errs46 = errors;
                              for (const key4 in data16) {
                                if (!(key4 === "crossover_probability" || key4 === "mutation_fraction" || key4 === "mutation_probability" || key4 === "rng" || key4 === "selection" || key4 === "variation")) {
                                  validate35.errors = [{ instancePath: instancePath + "/operators", schemaPath: "#/$defs/SearchOperators/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key4 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs46 === errors) {
                                if (data16.crossover_probability !== void 0) {
                                  let data17 = data16.crossover_probability;
                                  const _errs47 = errors;
                                  if (errors === _errs47) {
                                    if (typeof data17 == "number" && isFinite(data17)) {
                                      if (data17 > 1 || isNaN(data17)) {
                                        validate35.errors = [{ instancePath: instancePath + "/operators/crossover_probability", schemaPath: "#/$defs/SearchOperators/properties/crossover_probability/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1 }, message: "must be <= 1" }];
                                        return false;
                                      } else {
                                        if (data17 < 0 || isNaN(data17)) {
                                          validate35.errors = [{ instancePath: instancePath + "/operators/crossover_probability", schemaPath: "#/$defs/SearchOperators/properties/crossover_probability/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                          return false;
                                        }
                                      }
                                    } else {
                                      validate35.errors = [{ instancePath: instancePath + "/operators/crossover_probability", schemaPath: "#/$defs/SearchOperators/properties/crossover_probability/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                      return false;
                                    }
                                  }
                                  var valid11 = _errs47 === errors;
                                } else {
                                  var valid11 = true;
                                }
                                if (valid11) {
                                  if (data16.mutation_fraction !== void 0) {
                                    let data18 = data16.mutation_fraction;
                                    const _errs49 = errors;
                                    if (errors === _errs49) {
                                      if (typeof data18 == "number" && isFinite(data18)) {
                                        if (data18 > 1 || isNaN(data18)) {
                                          validate35.errors = [{ instancePath: instancePath + "/operators/mutation_fraction", schemaPath: "#/$defs/SearchOperators/properties/mutation_fraction/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1 }, message: "must be <= 1" }];
                                          return false;
                                        } else {
                                          if (data18 < 0 || isNaN(data18)) {
                                            validate35.errors = [{ instancePath: instancePath + "/operators/mutation_fraction", schemaPath: "#/$defs/SearchOperators/properties/mutation_fraction/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                            return false;
                                          }
                                        }
                                      } else {
                                        validate35.errors = [{ instancePath: instancePath + "/operators/mutation_fraction", schemaPath: "#/$defs/SearchOperators/properties/mutation_fraction/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                        return false;
                                      }
                                    }
                                    var valid11 = _errs49 === errors;
                                  } else {
                                    var valid11 = true;
                                  }
                                  if (valid11) {
                                    if (data16.mutation_probability !== void 0) {
                                      let data19 = data16.mutation_probability;
                                      const _errs51 = errors;
                                      if (errors === _errs51) {
                                        if (typeof data19 == "number" && isFinite(data19)) {
                                          if (data19 > 1 || isNaN(data19)) {
                                            validate35.errors = [{ instancePath: instancePath + "/operators/mutation_probability", schemaPath: "#/$defs/SearchOperators/properties/mutation_probability/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1 }, message: "must be <= 1" }];
                                            return false;
                                          } else {
                                            if (data19 < 0 || isNaN(data19)) {
                                              validate35.errors = [{ instancePath: instancePath + "/operators/mutation_probability", schemaPath: "#/$defs/SearchOperators/properties/mutation_probability/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                              return false;
                                            }
                                          }
                                        } else {
                                          validate35.errors = [{ instancePath: instancePath + "/operators/mutation_probability", schemaPath: "#/$defs/SearchOperators/properties/mutation_probability/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                          return false;
                                        }
                                      }
                                      var valid11 = _errs51 === errors;
                                    } else {
                                      var valid11 = true;
                                    }
                                    if (valid11) {
                                      if (data16.rng !== void 0) {
                                        let data20 = data16.rng;
                                        const _errs53 = errors;
                                        if (typeof data20 !== "string") {
                                          validate35.errors = [{ instancePath: instancePath + "/operators/rng", schemaPath: "#/$defs/SearchOperators/properties/rng/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        if ("sha256-counter-u53-v1" !== data20) {
                                          validate35.errors = [{ instancePath: instancePath + "/operators/rng", schemaPath: "#/$defs/SearchOperators/properties/rng/const", keyword: "const", params: { allowedValue: "sha256-counter-u53-v1" }, message: "must be equal to constant" }];
                                          return false;
                                        }
                                        var valid11 = _errs53 === errors;
                                      } else {
                                        var valid11 = true;
                                      }
                                      if (valid11) {
                                        if (data16.selection !== void 0) {
                                          let data21 = data16.selection;
                                          const _errs55 = errors;
                                          if (typeof data21 !== "string") {
                                            validate35.errors = [{ instancePath: instancePath + "/operators/selection", schemaPath: "#/$defs/SearchOperators/properties/selection/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                          if ("constrained-pareto-feasible-v1" !== data21) {
                                            validate35.errors = [{ instancePath: instancePath + "/operators/selection", schemaPath: "#/$defs/SearchOperators/properties/selection/const", keyword: "const", params: { allowedValue: "constrained-pareto-feasible-v1" }, message: "must be equal to constant" }];
                                            return false;
                                          }
                                          var valid11 = _errs55 === errors;
                                        } else {
                                          var valid11 = true;
                                        }
                                        if (valid11) {
                                          if (data16.variation !== void 0) {
                                            let data22 = data16.variation;
                                            const _errs57 = errors;
                                            if (typeof data22 !== "string") {
                                              validate35.errors = [{ instancePath: instancePath + "/operators/variation", schemaPath: "#/$defs/SearchOperators/properties/variation/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                            if ("box-convex-uniform-v1" !== data22) {
                                              validate35.errors = [{ instancePath: instancePath + "/operators/variation", schemaPath: "#/$defs/SearchOperators/properties/variation/const", keyword: "const", params: { allowedValue: "box-convex-uniform-v1" }, message: "must be equal to constant" }];
                                              return false;
                                            }
                                            var valid11 = _errs57 === errors;
                                          } else {
                                            var valid11 = true;
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            validate35.errors = [{ instancePath: instancePath + "/operators", schemaPath: "#/$defs/SearchOperators/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                            return false;
                          }
                        }
                        var valid0 = _errs43 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.representation !== void 0) {
                          let data23 = data.representation;
                          const _errs59 = errors;
                          const _errs60 = errors;
                          if (errors === _errs60) {
                            if (data23 && typeof data23 == "object" && !Array.isArray(data23)) {
                              let missing5;
                              if (data23.schema_id === void 0 && (missing5 = "schema_id") || data23.version === void 0 && (missing5 = "version") || data23.sha256 === void 0 && (missing5 = "sha256")) {
                                validate35.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing5 }, message: "must have required property '" + missing5 + "'" }];
                                return false;
                              } else {
                                const _errs62 = errors;
                                for (const key5 in data23) {
                                  if (!(key5 === "schema_id" || key5 === "sha256" || key5 === "version")) {
                                    validate35.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key5 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs62 === errors) {
                                  if (data23.schema_id !== void 0) {
                                    let data24 = data23.schema_id;
                                    const _errs63 = errors;
                                    if (errors === _errs63) {
                                      if (typeof data24 === "string") {
                                        if (func3(data24) > 128) {
                                          validate35.errors = [{ instancePath: instancePath + "/representation/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func3(data24) < 1) {
                                            validate35.errors = [{ instancePath: instancePath + "/representation/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern7.test(data24)) {
                                              validate35.errors = [{ instancePath: instancePath + "/representation/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate35.errors = [{ instancePath: instancePath + "/representation/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid13 = _errs63 === errors;
                                  } else {
                                    var valid13 = true;
                                  }
                                  if (valid13) {
                                    if (data23.sha256 !== void 0) {
                                      let data25 = data23.sha256;
                                      const _errs65 = errors;
                                      if (errors === _errs65) {
                                        if (typeof data25 === "string") {
                                          if (!pattern4.test(data25)) {
                                            validate35.errors = [{ instancePath: instancePath + "/representation/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                            return false;
                                          }
                                        } else {
                                          validate35.errors = [{ instancePath: instancePath + "/representation/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                      }
                                      var valid13 = _errs65 === errors;
                                    } else {
                                      var valid13 = true;
                                    }
                                    if (valid13) {
                                      if (data23.version !== void 0) {
                                        let data26 = data23.version;
                                        const _errs67 = errors;
                                        if (typeof data26 !== "string") {
                                          validate35.errors = [{ instancePath: instancePath + "/representation/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        if ("1" !== data26) {
                                          validate35.errors = [{ instancePath: instancePath + "/representation/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                          return false;
                                        }
                                        var valid13 = _errs67 === errors;
                                      } else {
                                        var valid13 = true;
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              validate35.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid0 = _errs59 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.schema_version !== void 0) {
                            let data27 = data.schema_version;
                            const _errs69 = errors;
                            if (typeof data27 !== "string") {
                              validate35.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("1" !== data27) {
                              validate35.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs69 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.scope !== void 0) {
                              let data28 = data.scope;
                              const _errs71 = errors;
                              const _errs72 = errors;
                              if (errors === _errs72) {
                                if (data28 && typeof data28 == "object" && !Array.isArray(data28)) {
                                  let missing6;
                                  if (data28.tenant_id === void 0 && (missing6 = "tenant_id") || data28.project_id === void 0 && (missing6 = "project_id")) {
                                    validate35.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing6 }, message: "must have required property '" + missing6 + "'" }];
                                    return false;
                                  } else {
                                    const _errs74 = errors;
                                    for (const key6 in data28) {
                                      if (!(key6 === "project_id" || key6 === "tenant_id")) {
                                        validate35.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key6 }, message: "must NOT have additional properties" }];
                                        return false;
                                        break;
                                      }
                                    }
                                    if (_errs74 === errors) {
                                      if (data28.project_id !== void 0) {
                                        let data29 = data28.project_id;
                                        const _errs75 = errors;
                                        if (errors === _errs75) {
                                          if (typeof data29 === "string") {
                                            if (func3(data29) > 128) {
                                              validate35.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                              return false;
                                            } else {
                                              if (func3(data29) < 1) {
                                                validate35.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                return false;
                                              } else {
                                                if (!pattern7.test(data29)) {
                                                  validate35.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                  return false;
                                                }
                                              }
                                            }
                                          } else {
                                            validate35.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid15 = _errs75 === errors;
                                      } else {
                                        var valid15 = true;
                                      }
                                      if (valid15) {
                                        if (data28.tenant_id !== void 0) {
                                          let data30 = data28.tenant_id;
                                          const _errs77 = errors;
                                          if (errors === _errs77) {
                                            if (typeof data30 === "string") {
                                              if (func3(data30) > 128) {
                                                validate35.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                return false;
                                              } else {
                                                if (func3(data30) < 1) {
                                                  validate35.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                  return false;
                                                } else {
                                                  if (!pattern7.test(data30)) {
                                                    validate35.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            } else {
                                              validate35.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid15 = _errs77 === errors;
                                        } else {
                                          var valid15 = true;
                                        }
                                      }
                                    }
                                  }
                                } else {
                                  validate35.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs71 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.search_id !== void 0) {
                                let data31 = data.search_id;
                                const _errs79 = errors;
                                if (errors === _errs79) {
                                  if (typeof data31 === "string") {
                                    if (func3(data31) > 128) {
                                      validate35.errors = [{ instancePath: instancePath + "/search_id", schemaPath: "#/properties/search_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func3(data31) < 1) {
                                        validate35.errors = [{ instancePath: instancePath + "/search_id", schemaPath: "#/properties/search_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern7.test(data31)) {
                                          validate35.errors = [{ instancePath: instancePath + "/search_id", schemaPath: "#/properties/search_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate35.errors = [{ instancePath: instancePath + "/search_id", schemaPath: "#/properties/search_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs79 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.seed !== void 0) {
                                  let data32 = data.seed;
                                  const _errs81 = errors;
                                  if (errors === _errs81) {
                                    if (typeof data32 === "string") {
                                      if (!pattern4.test(data32)) {
                                        validate35.errors = [{ instancePath: instancePath + "/seed", schemaPath: "#/properties/seed/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                        return false;
                                      }
                                    } else {
                                      validate35.errors = [{ instancePath: instancePath + "/seed", schemaPath: "#/properties/seed/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid0 = _errs81 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.variables !== void 0) {
                                    let data33 = data.variables;
                                    const _errs83 = errors;
                                    if (errors === _errs83) {
                                      if (Array.isArray(data33)) {
                                        if (data33.length > 32) {
                                          validate35.errors = [{ instancePath: instancePath + "/variables", schemaPath: "#/properties/variables/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                                          return false;
                                        } else {
                                          if (data33.length < 1) {
                                            validate35.errors = [{ instancePath: instancePath + "/variables", schemaPath: "#/properties/variables/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                                            return false;
                                          } else {
                                            var valid16 = true;
                                            const len2 = data33.length;
                                            for (let i2 = 0; i2 < len2; i2++) {
                                              let data34 = data33[i2];
                                              const _errs85 = errors;
                                              const _errs86 = errors;
                                              if (errors === _errs86) {
                                                if (data34 && typeof data34 == "object" && !Array.isArray(data34)) {
                                                  let missing7;
                                                  if (data34.variable_id === void 0 && (missing7 = "variable_id") || data34.unit === void 0 && (missing7 = "unit") || data34.lower === void 0 && (missing7 = "lower") || data34.upper === void 0 && (missing7 = "upper")) {
                                                    validate35.errors = [{ instancePath: instancePath + "/variables/" + i2, schemaPath: "#/$defs/NumericVariable/required", keyword: "required", params: { missingProperty: missing7 }, message: "must have required property '" + missing7 + "'" }];
                                                    return false;
                                                  } else {
                                                    const _errs88 = errors;
                                                    for (const key7 in data34) {
                                                      if (!(key7 === "lower" || key7 === "unit" || key7 === "upper" || key7 === "variable_id")) {
                                                        validate35.errors = [{ instancePath: instancePath + "/variables/" + i2, schemaPath: "#/$defs/NumericVariable/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key7 }, message: "must NOT have additional properties" }];
                                                        return false;
                                                        break;
                                                      }
                                                    }
                                                    if (_errs88 === errors) {
                                                      if (data34.lower !== void 0) {
                                                        let data35 = data34.lower;
                                                        const _errs89 = errors;
                                                        if (errors === _errs89) {
                                                          if (typeof data35 == "number" && isFinite(data35)) {
                                                            if (data35 > 1e100 || isNaN(data35)) {
                                                              validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/lower", schemaPath: "#/$defs/NumericVariable/properties/lower/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e100 }, message: "must be <= 1e+100" }];
                                                              return false;
                                                            } else {
                                                              if (data35 < -1e100 || isNaN(data35)) {
                                                                validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/lower", schemaPath: "#/$defs/NumericVariable/properties/lower/minimum", keyword: "minimum", params: { comparison: ">=", limit: -1e100 }, message: "must be >= -1e+100" }];
                                                                return false;
                                                              }
                                                            }
                                                          } else {
                                                            validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/lower", schemaPath: "#/$defs/NumericVariable/properties/lower/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                                            return false;
                                                          }
                                                        }
                                                        var valid18 = _errs89 === errors;
                                                      } else {
                                                        var valid18 = true;
                                                      }
                                                      if (valid18) {
                                                        if (data34.unit !== void 0) {
                                                          let data36 = data34.unit;
                                                          const _errs91 = errors;
                                                          if (errors === _errs91) {
                                                            if (typeof data36 === "string") {
                                                              if (func3(data36) > 64) {
                                                                validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/unit", schemaPath: "#/$defs/NumericVariable/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" }];
                                                                return false;
                                                              } else {
                                                                if (func3(data36) < 1) {
                                                                  validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/unit", schemaPath: "#/$defs/NumericVariable/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                                  return false;
                                                                }
                                                              }
                                                            } else {
                                                              validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/unit", schemaPath: "#/$defs/NumericVariable/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                              return false;
                                                            }
                                                          }
                                                          var valid18 = _errs91 === errors;
                                                        } else {
                                                          var valid18 = true;
                                                        }
                                                        if (valid18) {
                                                          if (data34.upper !== void 0) {
                                                            let data37 = data34.upper;
                                                            const _errs93 = errors;
                                                            if (errors === _errs93) {
                                                              if (typeof data37 == "number" && isFinite(data37)) {
                                                                if (data37 > 1e100 || isNaN(data37)) {
                                                                  validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/upper", schemaPath: "#/$defs/NumericVariable/properties/upper/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e100 }, message: "must be <= 1e+100" }];
                                                                  return false;
                                                                } else {
                                                                  if (data37 < -1e100 || isNaN(data37)) {
                                                                    validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/upper", schemaPath: "#/$defs/NumericVariable/properties/upper/minimum", keyword: "minimum", params: { comparison: ">=", limit: -1e100 }, message: "must be >= -1e+100" }];
                                                                    return false;
                                                                  }
                                                                }
                                                              } else {
                                                                validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/upper", schemaPath: "#/$defs/NumericVariable/properties/upper/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                                                return false;
                                                              }
                                                            }
                                                            var valid18 = _errs93 === errors;
                                                          } else {
                                                            var valid18 = true;
                                                          }
                                                          if (valid18) {
                                                            if (data34.variable_id !== void 0) {
                                                              let data38 = data34.variable_id;
                                                              const _errs95 = errors;
                                                              if (errors === _errs95) {
                                                                if (typeof data38 === "string") {
                                                                  if (func3(data38) > 128) {
                                                                    validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/variable_id", schemaPath: "#/$defs/NumericVariable/properties/variable_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                                    return false;
                                                                  } else {
                                                                    if (func3(data38) < 1) {
                                                                      validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/variable_id", schemaPath: "#/$defs/NumericVariable/properties/variable_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                                      return false;
                                                                    } else {
                                                                      if (!pattern7.test(data38)) {
                                                                        validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/variable_id", schemaPath: "#/$defs/NumericVariable/properties/variable_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                                        return false;
                                                                      }
                                                                    }
                                                                  }
                                                                } else {
                                                                  validate35.errors = [{ instancePath: instancePath + "/variables/" + i2 + "/variable_id", schemaPath: "#/$defs/NumericVariable/properties/variable_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                                  return false;
                                                                }
                                                              }
                                                              var valid18 = _errs95 === errors;
                                                            } else {
                                                              var valid18 = true;
                                                            }
                                                          }
                                                        }
                                                      }
                                                    }
                                                  }
                                                } else {
                                                  validate35.errors = [{ instancePath: instancePath + "/variables/" + i2, schemaPath: "#/$defs/NumericVariable/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                                  return false;
                                                }
                                              }
                                              var valid16 = _errs85 === errors;
                                              if (!valid16) {
                                                break;
                                              }
                                            }
                                          }
                                        }
                                      } else {
                                        validate35.errors = [{ instancePath: instancePath + "/variables", schemaPath: "#/properties/variables/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                        return false;
                                      }
                                    }
                                    var valid0 = _errs83 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate35.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate35.errors = vErrors;
      return errors === 0;
    }
    validate35.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate20(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate20.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.schema_version === void 0 && (missing0 = "schema_version") || data.specification === void 0 && (missing0 = "specification") || data.specification_sha256 === void 0 && (missing0 = "specification_sha256") || data.previous === void 0 && (missing0 = "previous") || data.generation === void 0 && (missing0 = "generation") || data.phase === void 0 && (missing0 = "phase") || data.rng === void 0 && (missing0 = "rng") || data.attempts === void 0 && (missing0 = "attempts") || data.population === void 0 && (missing0 = "population") || data.pending === void 0 && (missing0 = "pending") || data.observations === void 0 && (missing0 = "observations") || data.selection === void 0 && (missing0 = "selection") || data.progress === void 0 && (missing0 = "progress") || data.stop_reason === void 0 && (missing0 = "stop_reason")) {
            validate20.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func1.call(schema31.properties, key0)) {
                validate20.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.attempts !== void 0) {
                let data0 = data.attempts;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 256) {
                      validate20.errors = [{ instancePath: instancePath + "/attempts", schemaPath: "#/properties/attempts/maxItems", keyword: "maxItems", params: { limit: 256 }, message: "must NOT have more than 256 items" }];
                      return false;
                    } else {
                      if (data0.length < 1) {
                        validate20.errors = [{ instancePath: instancePath + "/attempts", schemaPath: "#/properties/attempts/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                        return false;
                      } else {
                        var valid1 = true;
                        const len0 = data0.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs4 = errors;
                          if (!validate21(data0[i0], { instancePath: instancePath + "/attempts/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                            errors = vErrors.length;
                          }
                          var valid1 = _errs4 === errors;
                          if (!valid1) {
                            break;
                          }
                        }
                      }
                    }
                  } else {
                    validate20.errors = [{ instancePath: instancePath + "/attempts", schemaPath: "#/properties/attempts/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.generation !== void 0) {
                  let data2 = data.generation;
                  const _errs5 = errors;
                  if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                    validate20.errors = [{ instancePath: instancePath + "/generation", schemaPath: "#/properties/generation/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs5) {
                    if (typeof data2 == "number" && isFinite(data2)) {
                      if (data2 > 1e4 || isNaN(data2)) {
                        validate20.errors = [{ instancePath: instancePath + "/generation", schemaPath: "#/properties/generation/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e4 }, message: "must be <= 10000" }];
                        return false;
                      } else {
                        if (data2 < 0 || isNaN(data2)) {
                          validate20.errors = [{ instancePath: instancePath + "/generation", schemaPath: "#/properties/generation/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.observations !== void 0) {
                    let data3 = data.observations;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (Array.isArray(data3)) {
                        if (data3.length > 256) {
                          validate20.errors = [{ instancePath: instancePath + "/observations", schemaPath: "#/properties/observations/maxItems", keyword: "maxItems", params: { limit: 256 }, message: "must NOT have more than 256 items" }];
                          return false;
                        } else {
                          var valid2 = true;
                          const len1 = data3.length;
                          for (let i1 = 0; i1 < len1; i1++) {
                            const _errs9 = errors;
                            if (!validate23(data3[i1], { instancePath: instancePath + "/observations/" + i1, parentData: data3, parentDataProperty: i1, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate23.errors : vErrors.concat(validate23.errors);
                              errors = vErrors.length;
                            }
                            var valid2 = _errs9 === errors;
                            if (!valid2) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate20.errors = [{ instancePath: instancePath + "/observations", schemaPath: "#/properties/observations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs7 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.pending !== void 0) {
                      let data5 = data.pending;
                      const _errs10 = errors;
                      if (errors === _errs10) {
                        if (Array.isArray(data5)) {
                          if (data5.length > 256) {
                            validate20.errors = [{ instancePath: instancePath + "/pending", schemaPath: "#/properties/pending/maxItems", keyword: "maxItems", params: { limit: 256 }, message: "must NOT have more than 256 items" }];
                            return false;
                          } else {
                            var valid3 = true;
                            const len2 = data5.length;
                            for (let i2 = 0; i2 < len2; i2++) {
                              let data6 = data5[i2];
                              const _errs12 = errors;
                              const _errs13 = errors;
                              if (errors === _errs13) {
                                if (data6 && typeof data6 == "object" && !Array.isArray(data6)) {
                                  let missing1;
                                  if (data6.evaluation_id === void 0 && (missing1 = "evaluation_id") || data6.candidate_id === void 0 && (missing1 = "candidate_id") || data6.request_sha256 === void 0 && (missing1 = "request_sha256")) {
                                    validate20.errors = [{ instancePath: instancePath + "/pending/" + i2, schemaPath: "#/$defs/PendingEvaluation/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                    return false;
                                  } else {
                                    const _errs15 = errors;
                                    for (const key1 in data6) {
                                      if (!(key1 === "candidate_id" || key1 === "evaluation_id" || key1 === "request_sha256")) {
                                        validate20.errors = [{ instancePath: instancePath + "/pending/" + i2, schemaPath: "#/$defs/PendingEvaluation/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                        return false;
                                        break;
                                      }
                                    }
                                    if (_errs15 === errors) {
                                      if (data6.candidate_id !== void 0) {
                                        let data7 = data6.candidate_id;
                                        const _errs16 = errors;
                                        if (errors === _errs16) {
                                          if (typeof data7 === "string") {
                                            if (!pattern4.test(data7)) {
                                              validate20.errors = [{ instancePath: instancePath + "/pending/" + i2 + "/candidate_id", schemaPath: "#/$defs/PendingEvaluation/properties/candidate_id/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                              return false;
                                            }
                                          } else {
                                            validate20.errors = [{ instancePath: instancePath + "/pending/" + i2 + "/candidate_id", schemaPath: "#/$defs/PendingEvaluation/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid5 = _errs16 === errors;
                                      } else {
                                        var valid5 = true;
                                      }
                                      if (valid5) {
                                        if (data6.evaluation_id !== void 0) {
                                          let data8 = data6.evaluation_id;
                                          const _errs18 = errors;
                                          if (errors === _errs18) {
                                            if (typeof data8 === "string") {
                                              if (func3(data8) > 128) {
                                                validate20.errors = [{ instancePath: instancePath + "/pending/" + i2 + "/evaluation_id", schemaPath: "#/$defs/PendingEvaluation/properties/evaluation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                return false;
                                              } else {
                                                if (func3(data8) < 1) {
                                                  validate20.errors = [{ instancePath: instancePath + "/pending/" + i2 + "/evaluation_id", schemaPath: "#/$defs/PendingEvaluation/properties/evaluation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                  return false;
                                                } else {
                                                  if (!pattern7.test(data8)) {
                                                    validate20.errors = [{ instancePath: instancePath + "/pending/" + i2 + "/evaluation_id", schemaPath: "#/$defs/PendingEvaluation/properties/evaluation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            } else {
                                              validate20.errors = [{ instancePath: instancePath + "/pending/" + i2 + "/evaluation_id", schemaPath: "#/$defs/PendingEvaluation/properties/evaluation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid5 = _errs18 === errors;
                                        } else {
                                          var valid5 = true;
                                        }
                                        if (valid5) {
                                          if (data6.request_sha256 !== void 0) {
                                            let data9 = data6.request_sha256;
                                            const _errs20 = errors;
                                            if (errors === _errs20) {
                                              if (typeof data9 === "string") {
                                                if (!pattern4.test(data9)) {
                                                  validate20.errors = [{ instancePath: instancePath + "/pending/" + i2 + "/request_sha256", schemaPath: "#/$defs/PendingEvaluation/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                                  return false;
                                                }
                                              } else {
                                                validate20.errors = [{ instancePath: instancePath + "/pending/" + i2 + "/request_sha256", schemaPath: "#/$defs/PendingEvaluation/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                            }
                                            var valid5 = _errs20 === errors;
                                          } else {
                                            var valid5 = true;
                                          }
                                        }
                                      }
                                    }
                                  }
                                } else {
                                  validate20.errors = [{ instancePath: instancePath + "/pending/" + i2, schemaPath: "#/$defs/PendingEvaluation/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                  return false;
                                }
                              }
                              var valid3 = _errs12 === errors;
                              if (!valid3) {
                                break;
                              }
                            }
                          }
                        } else {
                          validate20.errors = [{ instancePath: instancePath + "/pending", schemaPath: "#/properties/pending/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs10 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.phase !== void 0) {
                        let data10 = data.phase;
                        const _errs22 = errors;
                        if (typeof data10 !== "string") {
                          validate20.errors = [{ instancePath: instancePath + "/phase", schemaPath: "#/properties/phase/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if (!(data10 === "awaiting_evaluations" || data10 === "ready_to_select" || data10 === "selected" || data10 === "stopped")) {
                          validate20.errors = [{ instancePath: instancePath + "/phase", schemaPath: "#/properties/phase/enum", keyword: "enum", params: { allowedValues: schema31.properties.phase.enum }, message: "must be equal to one of the allowed values" }];
                          return false;
                        }
                        var valid0 = _errs22 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.population !== void 0) {
                          let data11 = data.population;
                          const _errs24 = errors;
                          if (errors === _errs24) {
                            if (Array.isArray(data11)) {
                              if (data11.length > 128) {
                                validate20.errors = [{ instancePath: instancePath + "/population", schemaPath: "#/properties/population/maxItems", keyword: "maxItems", params: { limit: 128 }, message: "must NOT have more than 128 items" }];
                                return false;
                              } else {
                                var valid6 = true;
                                const len3 = data11.length;
                                for (let i3 = 0; i3 < len3; i3++) {
                                  let data12 = data11[i3];
                                  const _errs26 = errors;
                                  if (errors === _errs26) {
                                    if (typeof data12 === "string") {
                                      if (!pattern4.test(data12)) {
                                        validate20.errors = [{ instancePath: instancePath + "/population/" + i3, schemaPath: "#/properties/population/items/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                        return false;
                                      }
                                    } else {
                                      validate20.errors = [{ instancePath: instancePath + "/population/" + i3, schemaPath: "#/properties/population/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid6 = _errs26 === errors;
                                  if (!valid6) {
                                    break;
                                  }
                                }
                              }
                            } else {
                              validate20.errors = [{ instancePath: instancePath + "/population", schemaPath: "#/properties/population/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs24 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.previous !== void 0) {
                            let data13 = data.previous;
                            const _errs28 = errors;
                            const _errs29 = errors;
                            let valid7 = false;
                            const _errs30 = errors;
                            if (!validate25(data13, { instancePath: instancePath + "/previous", parentData: data, parentDataProperty: "previous", rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
                              errors = vErrors.length;
                            }
                            var _valid0 = _errs30 === errors;
                            valid7 = valid7 || _valid0;
                            const _errs31 = errors;
                            if (data13 !== null) {
                              const err0 = { instancePath: instancePath + "/previous", schemaPath: "#/properties/previous/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            }
                            var _valid0 = _errs31 === errors;
                            valid7 = valid7 || _valid0;
                            if (!valid7) {
                              const err1 = { instancePath: instancePath + "/previous", schemaPath: "#/properties/previous/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err1];
                              } else {
                                vErrors.push(err1);
                              }
                              errors++;
                              validate20.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs29;
                              if (vErrors !== null) {
                                if (_errs29) {
                                  vErrors.length = _errs29;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs28 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.progress !== void 0) {
                              let data14 = data.progress;
                              const _errs33 = errors;
                              const _errs34 = errors;
                              if (errors === _errs34) {
                                if (data14 && typeof data14 == "object" && !Array.isArray(data14)) {
                                  let missing2;
                                  if (data14.evaluations_issued === void 0 && (missing2 = "evaluations_issued") || data14.evaluations_terminal === void 0 && (missing2 = "evaluations_terminal") || data14.generations_completed === void 0 && (missing2 = "generations_completed") || data14.unchanged_front_generations === void 0 && (missing2 = "unchanged_front_generations")) {
                                    validate20.errors = [{ instancePath: instancePath + "/progress", schemaPath: "#/$defs/SearchProgress/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                    return false;
                                  } else {
                                    const _errs36 = errors;
                                    for (const key2 in data14) {
                                      if (!(key2 === "evaluations_issued" || key2 === "evaluations_terminal" || key2 === "generations_completed" || key2 === "unchanged_front_generations")) {
                                        validate20.errors = [{ instancePath: instancePath + "/progress", schemaPath: "#/$defs/SearchProgress/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                        return false;
                                        break;
                                      }
                                    }
                                    if (_errs36 === errors) {
                                      if (data14.evaluations_issued !== void 0) {
                                        let data15 = data14.evaluations_issued;
                                        const _errs37 = errors;
                                        if (!(typeof data15 == "number" && (!(data15 % 1) && !isNaN(data15)) && isFinite(data15))) {
                                          validate20.errors = [{ instancePath: instancePath + "/progress/evaluations_issued", schemaPath: "#/$defs/SearchProgress/properties/evaluations_issued/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                          return false;
                                        }
                                        if (errors === _errs37) {
                                          if (typeof data15 == "number" && isFinite(data15)) {
                                            if (data15 > 9007199254740991 || isNaN(data15)) {
                                              validate20.errors = [{ instancePath: instancePath + "/progress/evaluations_issued", schemaPath: "#/$defs/SearchProgress/properties/evaluations_issued/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                              return false;
                                            } else {
                                              if (data15 < 0 || isNaN(data15)) {
                                                validate20.errors = [{ instancePath: instancePath + "/progress/evaluations_issued", schemaPath: "#/$defs/SearchProgress/properties/evaluations_issued/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                return false;
                                              }
                                            }
                                          }
                                        }
                                        var valid9 = _errs37 === errors;
                                      } else {
                                        var valid9 = true;
                                      }
                                      if (valid9) {
                                        if (data14.evaluations_terminal !== void 0) {
                                          let data16 = data14.evaluations_terminal;
                                          const _errs39 = errors;
                                          if (!(typeof data16 == "number" && (!(data16 % 1) && !isNaN(data16)) && isFinite(data16))) {
                                            validate20.errors = [{ instancePath: instancePath + "/progress/evaluations_terminal", schemaPath: "#/$defs/SearchProgress/properties/evaluations_terminal/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                            return false;
                                          }
                                          if (errors === _errs39) {
                                            if (typeof data16 == "number" && isFinite(data16)) {
                                              if (data16 > 9007199254740991 || isNaN(data16)) {
                                                validate20.errors = [{ instancePath: instancePath + "/progress/evaluations_terminal", schemaPath: "#/$defs/SearchProgress/properties/evaluations_terminal/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                                return false;
                                              } else {
                                                if (data16 < 0 || isNaN(data16)) {
                                                  validate20.errors = [{ instancePath: instancePath + "/progress/evaluations_terminal", schemaPath: "#/$defs/SearchProgress/properties/evaluations_terminal/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                  return false;
                                                }
                                              }
                                            }
                                          }
                                          var valid9 = _errs39 === errors;
                                        } else {
                                          var valid9 = true;
                                        }
                                        if (valid9) {
                                          if (data14.generations_completed !== void 0) {
                                            let data17 = data14.generations_completed;
                                            const _errs41 = errors;
                                            if (!(typeof data17 == "number" && (!(data17 % 1) && !isNaN(data17)) && isFinite(data17))) {
                                              validate20.errors = [{ instancePath: instancePath + "/progress/generations_completed", schemaPath: "#/$defs/SearchProgress/properties/generations_completed/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                              return false;
                                            }
                                            if (errors === _errs41) {
                                              if (typeof data17 == "number" && isFinite(data17)) {
                                                if (data17 > 1e4 || isNaN(data17)) {
                                                  validate20.errors = [{ instancePath: instancePath + "/progress/generations_completed", schemaPath: "#/$defs/SearchProgress/properties/generations_completed/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e4 }, message: "must be <= 10000" }];
                                                  return false;
                                                } else {
                                                  if (data17 < 0 || isNaN(data17)) {
                                                    validate20.errors = [{ instancePath: instancePath + "/progress/generations_completed", schemaPath: "#/$defs/SearchProgress/properties/generations_completed/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            }
                                            var valid9 = _errs41 === errors;
                                          } else {
                                            var valid9 = true;
                                          }
                                          if (valid9) {
                                            if (data14.unchanged_front_generations !== void 0) {
                                              let data18 = data14.unchanged_front_generations;
                                              const _errs43 = errors;
                                              if (!(typeof data18 == "number" && (!(data18 % 1) && !isNaN(data18)) && isFinite(data18))) {
                                                validate20.errors = [{ instancePath: instancePath + "/progress/unchanged_front_generations", schemaPath: "#/$defs/SearchProgress/properties/unchanged_front_generations/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                return false;
                                              }
                                              if (errors === _errs43) {
                                                if (typeof data18 == "number" && isFinite(data18)) {
                                                  if (data18 > 1e4 || isNaN(data18)) {
                                                    validate20.errors = [{ instancePath: instancePath + "/progress/unchanged_front_generations", schemaPath: "#/$defs/SearchProgress/properties/unchanged_front_generations/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e4 }, message: "must be <= 10000" }];
                                                    return false;
                                                  } else {
                                                    if (data18 < 0 || isNaN(data18)) {
                                                      validate20.errors = [{ instancePath: instancePath + "/progress/unchanged_front_generations", schemaPath: "#/$defs/SearchProgress/properties/unchanged_front_generations/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                      return false;
                                                    }
                                                  }
                                                }
                                              }
                                              var valid9 = _errs43 === errors;
                                            } else {
                                              var valid9 = true;
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                } else {
                                  validate20.errors = [{ instancePath: instancePath + "/progress", schemaPath: "#/$defs/SearchProgress/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs33 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.rng !== void 0) {
                                let data19 = data.rng;
                                const _errs45 = errors;
                                const _errs46 = errors;
                                if (errors === _errs46) {
                                  if (data19 && typeof data19 == "object" && !Array.isArray(data19)) {
                                    let missing3;
                                    if (data19.algorithm === void 0 && (missing3 = "algorithm") || data19.seed === void 0 && (missing3 = "seed") || data19.counter === void 0 && (missing3 = "counter")) {
                                      validate20.errors = [{ instancePath: instancePath + "/rng", schemaPath: "#/$defs/RngState/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" }];
                                      return false;
                                    } else {
                                      const _errs48 = errors;
                                      for (const key3 in data19) {
                                        if (!(key3 === "algorithm" || key3 === "counter" || key3 === "seed")) {
                                          validate20.errors = [{ instancePath: instancePath + "/rng", schemaPath: "#/$defs/RngState/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" }];
                                          return false;
                                          break;
                                        }
                                      }
                                      if (_errs48 === errors) {
                                        if (data19.algorithm !== void 0) {
                                          let data20 = data19.algorithm;
                                          const _errs49 = errors;
                                          if (typeof data20 !== "string") {
                                            validate20.errors = [{ instancePath: instancePath + "/rng/algorithm", schemaPath: "#/$defs/RngState/properties/algorithm/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                          if ("sha256-counter-u53-v1" !== data20) {
                                            validate20.errors = [{ instancePath: instancePath + "/rng/algorithm", schemaPath: "#/$defs/RngState/properties/algorithm/const", keyword: "const", params: { allowedValue: "sha256-counter-u53-v1" }, message: "must be equal to constant" }];
                                            return false;
                                          }
                                          var valid11 = _errs49 === errors;
                                        } else {
                                          var valid11 = true;
                                        }
                                        if (valid11) {
                                          if (data19.counter !== void 0) {
                                            let data21 = data19.counter;
                                            const _errs51 = errors;
                                            if (!(typeof data21 == "number" && (!(data21 % 1) && !isNaN(data21)) && isFinite(data21))) {
                                              validate20.errors = [{ instancePath: instancePath + "/rng/counter", schemaPath: "#/$defs/RngState/properties/counter/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                              return false;
                                            }
                                            if (errors === _errs51) {
                                              if (typeof data21 == "number" && isFinite(data21)) {
                                                if (data21 > 9007199254740991 || isNaN(data21)) {
                                                  validate20.errors = [{ instancePath: instancePath + "/rng/counter", schemaPath: "#/$defs/RngState/properties/counter/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                                  return false;
                                                } else {
                                                  if (data21 < 0 || isNaN(data21)) {
                                                    validate20.errors = [{ instancePath: instancePath + "/rng/counter", schemaPath: "#/$defs/RngState/properties/counter/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            }
                                            var valid11 = _errs51 === errors;
                                          } else {
                                            var valid11 = true;
                                          }
                                          if (valid11) {
                                            if (data19.seed !== void 0) {
                                              let data22 = data19.seed;
                                              const _errs53 = errors;
                                              if (errors === _errs53) {
                                                if (typeof data22 === "string") {
                                                  if (!pattern4.test(data22)) {
                                                    validate20.errors = [{ instancePath: instancePath + "/rng/seed", schemaPath: "#/$defs/RngState/properties/seed/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                                    return false;
                                                  }
                                                } else {
                                                  validate20.errors = [{ instancePath: instancePath + "/rng/seed", schemaPath: "#/$defs/RngState/properties/seed/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                  return false;
                                                }
                                              }
                                              var valid11 = _errs53 === errors;
                                            } else {
                                              var valid11 = true;
                                            }
                                          }
                                        }
                                      }
                                    }
                                  } else {
                                    validate20.errors = [{ instancePath: instancePath + "/rng", schemaPath: "#/$defs/RngState/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs45 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.schema_version !== void 0) {
                                  let data23 = data.schema_version;
                                  const _errs55 = errors;
                                  if (typeof data23 !== "string") {
                                    validate20.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data23) {
                                    validate20.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid0 = _errs55 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.selection !== void 0) {
                                    let data24 = data.selection;
                                    const _errs57 = errors;
                                    const _errs58 = errors;
                                    let valid12 = false;
                                    const _errs59 = errors;
                                    if (!validate33(data24, { instancePath: instancePath + "/selection", parentData: data, parentDataProperty: "selection", rootData, dynamicAnchors })) {
                                      vErrors = vErrors === null ? validate33.errors : vErrors.concat(validate33.errors);
                                      errors = vErrors.length;
                                    }
                                    var _valid1 = _errs59 === errors;
                                    valid12 = valid12 || _valid1;
                                    const _errs60 = errors;
                                    if (data24 !== null) {
                                      const err2 = { instancePath: instancePath + "/selection", schemaPath: "#/properties/selection/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                      if (vErrors === null) {
                                        vErrors = [err2];
                                      } else {
                                        vErrors.push(err2);
                                      }
                                      errors++;
                                    }
                                    var _valid1 = _errs60 === errors;
                                    valid12 = valid12 || _valid1;
                                    if (!valid12) {
                                      const err3 = { instancePath: instancePath + "/selection", schemaPath: "#/properties/selection/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                      if (vErrors === null) {
                                        vErrors = [err3];
                                      } else {
                                        vErrors.push(err3);
                                      }
                                      errors++;
                                      validate20.errors = vErrors;
                                      return false;
                                    } else {
                                      errors = _errs58;
                                      if (vErrors !== null) {
                                        if (_errs58) {
                                          vErrors.length = _errs58;
                                        } else {
                                          vErrors = null;
                                        }
                                      }
                                    }
                                    var valid0 = _errs57 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                  if (valid0) {
                                    if (data.specification !== void 0) {
                                      const _errs62 = errors;
                                      if (!validate35(data.specification, { instancePath: instancePath + "/specification", parentData: data, parentDataProperty: "specification", rootData, dynamicAnchors })) {
                                        vErrors = vErrors === null ? validate35.errors : vErrors.concat(validate35.errors);
                                        errors = vErrors.length;
                                      }
                                      var valid0 = _errs62 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                    if (valid0) {
                                      if (data.specification_sha256 !== void 0) {
                                        let data26 = data.specification_sha256;
                                        const _errs63 = errors;
                                        if (errors === _errs63) {
                                          if (typeof data26 === "string") {
                                            if (!pattern4.test(data26)) {
                                              validate20.errors = [{ instancePath: instancePath + "/specification_sha256", schemaPath: "#/properties/specification_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                              return false;
                                            }
                                          } else {
                                            validate20.errors = [{ instancePath: instancePath + "/specification_sha256", schemaPath: "#/properties/specification_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid0 = _errs63 === errors;
                                      } else {
                                        var valid0 = true;
                                      }
                                      if (valid0) {
                                        if (data.stop_reason !== void 0) {
                                          let data27 = data.stop_reason;
                                          const _errs65 = errors;
                                          const _errs66 = errors;
                                          let valid13 = false;
                                          const _errs67 = errors;
                                          if (typeof data27 !== "string") {
                                            const err4 = { instancePath: instancePath + "/stop_reason", schemaPath: "#/properties/stop_reason/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                            if (vErrors === null) {
                                              vErrors = [err4];
                                            } else {
                                              vErrors.push(err4);
                                            }
                                            errors++;
                                          }
                                          if (!(data27 === "generation_budget" || data27 === "evaluation_budget" || data27 === "unchanged_front" || data27 === "no_feasible_candidates" || data27 === "unavailable_fitness")) {
                                            const err5 = { instancePath: instancePath + "/stop_reason", schemaPath: "#/properties/stop_reason/anyOf/0/enum", keyword: "enum", params: { allowedValues: schema31.properties.stop_reason.anyOf[0].enum }, message: "must be equal to one of the allowed values" };
                                            if (vErrors === null) {
                                              vErrors = [err5];
                                            } else {
                                              vErrors.push(err5);
                                            }
                                            errors++;
                                          }
                                          var _valid2 = _errs67 === errors;
                                          valid13 = valid13 || _valid2;
                                          const _errs69 = errors;
                                          if (data27 !== null) {
                                            const err6 = { instancePath: instancePath + "/stop_reason", schemaPath: "#/properties/stop_reason/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                            if (vErrors === null) {
                                              vErrors = [err6];
                                            } else {
                                              vErrors.push(err6);
                                            }
                                            errors++;
                                          }
                                          var _valid2 = _errs69 === errors;
                                          valid13 = valid13 || _valid2;
                                          if (!valid13) {
                                            const err7 = { instancePath: instancePath + "/stop_reason", schemaPath: "#/properties/stop_reason/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                            if (vErrors === null) {
                                              vErrors = [err7];
                                            } else {
                                              vErrors.push(err7);
                                            }
                                            errors++;
                                            validate20.errors = vErrors;
                                            return false;
                                          } else {
                                            errors = _errs66;
                                            if (vErrors !== null) {
                                              if (_errs66) {
                                                vErrors.length = _errs66;
                                              } else {
                                                vErrors = null;
                                              }
                                            }
                                          }
                                          var valid0 = _errs65 === errors;
                                        } else {
                                          var valid0 = true;
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate20.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate20.errors = vErrors;
      return errors === 0;
    }
    validate20.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
  }
});
export default require_reviewed_validators();
