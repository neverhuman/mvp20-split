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
    exports.search_request = validate20;
    var schema31 = { "$defs": { "DomainGraphRef": { "additionalProperties": false, "properties": { "graph_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Graph Id", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "graph_id"], "title": "DomainGraphRef", "type": "object" }, "DomainRevisionRef": { "additionalProperties": false, "properties": { "graph": { "$ref": "#/$defs/DomainGraphRef" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" } }, "required": ["graph", "revision", "sha256"], "title": "DomainRevisionRef", "type": "object" }, "GraphViewPosition": { "additionalProperties": false, "properties": { "assertion_offset": { "maximum": 8192, "minimum": 0, "title": "Assertion Offset", "type": "integer" }, "entity_offset": { "maximum": 4096, "minimum": 0, "title": "Entity Offset", "type": "integer" }, "query_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Query Sha256", "type": "string" } }, "required": ["query_sha256", "entity_offset", "assertion_offset"], "title": "GraphViewPosition", "type": "object" }, "Scope": { "additionalProperties": false, "properties": { "project_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Project Id", "type": "string" }, "tenant_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Tenant Id", "type": "string" } }, "required": ["tenant_id", "project_id"], "title": "Scope", "type": "object" } }, "$id": "urn:amphora:knowledge.entity-search-request:1:serialization", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": { "entity_type": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "default": null, "title": "Entity Type" }, "history": { "default": "current", "enum": ["current", "retained"], "title": "History", "type": "string" }, "limit": { "default": 50, "maximum": 50, "minimum": 1, "title": "Limit", "type": "integer" }, "position": { "anyOf": [{ "$ref": "#/$defs/GraphViewPosition" }, { "type": "null" }], "default": null }, "revision": { "$ref": "#/$defs/DomainRevisionRef" }, "text": { "default": "", "maxLength": 128, "title": "Text", "type": "string" }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" } }, "required": ["wire_version", "revision"], "title": "GraphEntitySearchRequest", "type": "object" };
    var func1 = require_ucs2length().default;
    var pattern4 = new RegExp("^[A-Za-z0-9][A-Za-z0-9._:-]*$", "u");
    var pattern5 = new RegExp("^[0-9a-f]{64}$", "u");
    function validate22(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate22.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.graph_id === void 0 && (missing0 = "graph_id")) {
            validate22.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph_id" || key0 === "scope")) {
                validate22.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph_id !== void 0) {
                let data0 = data.graph_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate22.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate22.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate22.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate22.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  let data1 = data.scope;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.tenant_id === void 0 && (missing1 = "tenant_id") || data1.project_id === void 0 && (missing1 = "project_id")) {
                        validate22.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate22.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.project_id !== void 0) {
                            let data2 = data1.project_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate22.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate22.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate22.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate22.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.tenant_id !== void 0) {
                              let data3 = data1.tenant_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate22.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate22.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate22.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate22.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                          }
                        }
                      }
                    } else {
                      validate22.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate22.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate22.errors = vErrors;
      return errors === 0;
    }
    validate22.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.graph === void 0 && (missing0 = "graph") || data.revision === void 0 && (missing0 = "revision") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate21.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph" || key0 === "revision" || key0 === "sha256")) {
                validate21.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph !== void 0) {
                const _errs2 = errors;
                if (!validate22(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate22.errors : vErrors.concat(validate22.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate21.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate21.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate21.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sha256 !== void 0) {
                    let data2 = data.sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern5.test(data2)) {
                          validate21.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate21.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.revision === void 0 && (missing0 = "revision")) {
            validate20.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entity_type" || key0 === "history" || key0 === "limit" || key0 === "position" || key0 === "revision" || key0 === "text" || key0 === "wire_version")) {
                validate20.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entity_type !== void 0) {
                let data0 = data.entity_type;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (errors === _errs4) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      const err0 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    } else {
                      if (func1(data0) < 1) {
                        const err1 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      } else {
                        if (!pattern4.test(data0)) {
                          const err2 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                          if (vErrors === null) {
                            vErrors = [err2];
                          } else {
                            vErrors.push(err2);
                          }
                          errors++;
                        }
                      }
                    }
                  } else {
                    const err3 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs6 = errors;
                if (data0 !== null) {
                  const err4 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err4];
                  } else {
                    vErrors.push(err4);
                  }
                  errors++;
                }
                var _valid0 = _errs6 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err5 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err5];
                  } else {
                    vErrors.push(err5);
                  }
                  errors++;
                  validate20.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.history !== void 0) {
                  let data1 = data.history;
                  const _errs8 = errors;
                  if (typeof data1 !== "string") {
                    validate20.errors = [{ instancePath: instancePath + "/history", schemaPath: "#/properties/history/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "current" || data1 === "retained")) {
                    validate20.errors = [{ instancePath: instancePath + "/history", schemaPath: "#/properties/history/enum", keyword: "enum", params: { allowedValues: schema31.properties.history.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.limit !== void 0) {
                    let data2 = data.limit;
                    const _errs10 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate20.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs10) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 50 || isNaN(data2)) {
                          validate20.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 50 }, message: "must be <= 50" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate20.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.position !== void 0) {
                      let data3 = data.position;
                      const _errs12 = errors;
                      const _errs13 = errors;
                      let valid2 = false;
                      const _errs14 = errors;
                      const _errs15 = errors;
                      if (errors === _errs15) {
                        if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                          let missing1;
                          if (data3.query_sha256 === void 0 && (missing1 = "query_sha256") || data3.entity_offset === void 0 && (missing1 = "entity_offset") || data3.assertion_offset === void 0 && (missing1 = "assertion_offset")) {
                            const err6 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                            if (vErrors === null) {
                              vErrors = [err6];
                            } else {
                              vErrors.push(err6);
                            }
                            errors++;
                          } else {
                            const _errs17 = errors;
                            for (const key1 in data3) {
                              if (!(key1 === "assertion_offset" || key1 === "entity_offset" || key1 === "query_sha256")) {
                                const err7 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                if (vErrors === null) {
                                  vErrors = [err7];
                                } else {
                                  vErrors.push(err7);
                                }
                                errors++;
                                break;
                              }
                            }
                            if (_errs17 === errors) {
                              if (data3.assertion_offset !== void 0) {
                                let data4 = data3.assertion_offset;
                                const _errs18 = errors;
                                if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                                  const err8 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                  if (vErrors === null) {
                                    vErrors = [err8];
                                  } else {
                                    vErrors.push(err8);
                                  }
                                  errors++;
                                }
                                if (errors === _errs18) {
                                  if (typeof data4 == "number" && isFinite(data4)) {
                                    if (data4 > 8192 || isNaN(data4)) {
                                      const err9 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 8192 }, message: "must be <= 8192" };
                                      if (vErrors === null) {
                                        vErrors = [err9];
                                      } else {
                                        vErrors.push(err9);
                                      }
                                      errors++;
                                    } else {
                                      if (data4 < 0 || isNaN(data4)) {
                                        const err10 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                        if (vErrors === null) {
                                          vErrors = [err10];
                                        } else {
                                          vErrors.push(err10);
                                        }
                                        errors++;
                                      }
                                    }
                                  }
                                }
                                var valid4 = _errs18 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data3.entity_offset !== void 0) {
                                  let data5 = data3.entity_offset;
                                  const _errs20 = errors;
                                  if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                    const err11 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                    if (vErrors === null) {
                                      vErrors = [err11];
                                    } else {
                                      vErrors.push(err11);
                                    }
                                    errors++;
                                  }
                                  if (errors === _errs20) {
                                    if (typeof data5 == "number" && isFinite(data5)) {
                                      if (data5 > 4096 || isNaN(data5)) {
                                        const err12 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                        if (vErrors === null) {
                                          vErrors = [err12];
                                        } else {
                                          vErrors.push(err12);
                                        }
                                        errors++;
                                      } else {
                                        if (data5 < 0 || isNaN(data5)) {
                                          const err13 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                          if (vErrors === null) {
                                            vErrors = [err13];
                                          } else {
                                            vErrors.push(err13);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  }
                                  var valid4 = _errs20 === errors;
                                } else {
                                  var valid4 = true;
                                }
                                if (valid4) {
                                  if (data3.query_sha256 !== void 0) {
                                    let data6 = data3.query_sha256;
                                    const _errs22 = errors;
                                    if (errors === _errs22) {
                                      if (typeof data6 === "string") {
                                        if (!pattern5.test(data6)) {
                                          const err14 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                          if (vErrors === null) {
                                            vErrors = [err14];
                                          } else {
                                            vErrors.push(err14);
                                          }
                                          errors++;
                                        }
                                      } else {
                                        const err15 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err15];
                                        } else {
                                          vErrors.push(err15);
                                        }
                                        errors++;
                                      }
                                    }
                                    var valid4 = _errs22 === errors;
                                  } else {
                                    var valid4 = true;
                                  }
                                }
                              }
                            }
                          }
                        } else {
                          const err16 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                          if (vErrors === null) {
                            vErrors = [err16];
                          } else {
                            vErrors.push(err16);
                          }
                          errors++;
                        }
                      }
                      var _valid1 = _errs14 === errors;
                      valid2 = valid2 || _valid1;
                      const _errs24 = errors;
                      if (data3 !== null) {
                        const err17 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err17];
                        } else {
                          vErrors.push(err17);
                        }
                        errors++;
                      }
                      var _valid1 = _errs24 === errors;
                      valid2 = valid2 || _valid1;
                      if (!valid2) {
                        const err18 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err18];
                        } else {
                          vErrors.push(err18);
                        }
                        errors++;
                        validate20.errors = vErrors;
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
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.revision !== void 0) {
                        const _errs26 = errors;
                        if (!validate21(data.revision, { instancePath: instancePath + "/revision", parentData: data, parentDataProperty: "revision", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.text !== void 0) {
                          let data8 = data.text;
                          const _errs27 = errors;
                          if (errors === _errs27) {
                            if (typeof data8 === "string") {
                              if (func1(data8) > 128) {
                                validate20.errors = [{ instancePath: instancePath + "/text", schemaPath: "#/properties/text/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                return false;
                              }
                            } else {
                              validate20.errors = [{ instancePath: instancePath + "/text", schemaPath: "#/properties/text/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid0 = _errs27 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.wire_version !== void 0) {
                            let data9 = data.wire_version;
                            const _errs29 = errors;
                            if (typeof data9 !== "string") {
                              validate20.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("1" !== data9) {
                              validate20.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs29 === errors;
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
          validate20.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate20.errors = vErrors;
      return errors === 0;
    }
    validate20.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.search_page = validate25;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.graph_id === void 0 && (missing0 = "graph_id")) {
            validate28.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph_id" || key0 === "scope")) {
                validate28.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph_id !== void 0) {
                let data0 = data.graph_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate28.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate28.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate28.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate28.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  let data1 = data.scope;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.tenant_id === void 0 && (missing1 = "tenant_id") || data1.project_id === void 0 && (missing1 = "project_id")) {
                        validate28.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate28.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.project_id !== void 0) {
                            let data2 = data1.project_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate28.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate28.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate28.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate28.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.tenant_id !== void 0) {
                              let data3 = data1.tenant_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate28.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate28.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate28.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate28.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                          }
                        }
                      }
                    } else {
                      validate28.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
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
    function validate27(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate27.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.entity_id === void 0 && (missing0 = "entity_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate27.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entity_id" || key0 === "graph" || key0 === "revision")) {
                validate27.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entity_id !== void 0) {
                let data0 = data.entity_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate27.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate27.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate27.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate27.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.graph !== void 0) {
                  const _errs4 = errors;
                  if (!validate28(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate28.errors : vErrors.concat(validate28.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    let data2 = data.revision;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate27.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate27.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate27.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate27.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate27.errors = vErrors;
      return errors === 0;
    }
    validate27.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate26(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate26.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.reference === void 0 && (missing0 = "reference") || data.entity_type === void 0 && (missing0 = "entity_type") || data.label === void 0 && (missing0 = "label") || data.is_latest === void 0 && (missing0 = "is_latest") || data.alias_target === void 0 && (missing0 = "alias_target")) {
            validate26.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "alias_target" || key0 === "entity_type" || key0 === "is_latest" || key0 === "label" || key0 === "reference")) {
                validate26.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.alias_target !== void 0) {
                let data0 = data.alias_target;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate27(data0, { instancePath: instancePath + "/alias_target", parentData: data, parentDataProperty: "alias_target", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate27.errors : vErrors.concat(validate27.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/alias_target", schemaPath: "#/properties/alias_target/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs5 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err1 = { instancePath: instancePath + "/alias_target", schemaPath: "#/properties/alias_target/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate26.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.entity_type !== void 0) {
                  let data1 = data.entity_type;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate26.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate26.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate26.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate26.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.is_latest !== void 0) {
                    const _errs9 = errors;
                    if (typeof data.is_latest !== "boolean") {
                      validate26.errors = [{ instancePath: instancePath + "/is_latest", schemaPath: "#/properties/is_latest/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.label !== void 0) {
                      let data3 = data.label;
                      const _errs11 = errors;
                      if (errors === _errs11) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 512) {
                            validate26.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/maxLength", keyword: "maxLength", params: { limit: 512 }, message: "must NOT have more than 512 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate26.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            }
                          }
                        } else {
                          validate26.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.reference !== void 0) {
                        const _errs13 = errors;
                        if (!validate27(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate27.errors : vErrors.concat(validate27.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs13 === errors;
                      } else {
                        var valid0 = true;
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate26.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate26.errors = vErrors;
      return errors === 0;
    }
    validate26.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema42 = { "additionalProperties": false, "properties": { "entity_type": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "default": null, "title": "Entity Type" }, "history": { "default": "current", "enum": ["current", "retained"], "title": "History", "type": "string" }, "limit": { "default": 50, "maximum": 50, "minimum": 1, "title": "Limit", "type": "integer" }, "position": { "anyOf": [{ "$ref": "#/$defs/GraphViewPosition" }, { "type": "null" }], "default": null }, "revision": { "$ref": "#/$defs/DomainRevisionRef" }, "text": { "default": "", "maxLength": 128, "title": "Text", "type": "string" }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" } }, "required": ["wire_version", "revision"], "title": "GraphEntitySearchRequest", "type": "object" };
    function validate34(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate34.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.revision === void 0 && (missing0 = "revision") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate34.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph" || key0 === "revision" || key0 === "sha256")) {
                validate34.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph !== void 0) {
                const _errs2 = errors;
                if (!validate28(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate28.errors : vErrors.concat(validate28.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate34.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate34.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate34.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sha256 !== void 0) {
                    let data2 = data.sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern5.test(data2)) {
                          validate34.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate34.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate34.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate34.errors = vErrors;
      return errors === 0;
    }
    validate34.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.revision === void 0 && (missing0 = "revision")) {
            validate33.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entity_type" || key0 === "history" || key0 === "limit" || key0 === "position" || key0 === "revision" || key0 === "text" || key0 === "wire_version")) {
                validate33.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entity_type !== void 0) {
                let data0 = data.entity_type;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (errors === _errs4) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      const err0 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    } else {
                      if (func1(data0) < 1) {
                        const err1 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      } else {
                        if (!pattern4.test(data0)) {
                          const err2 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                          if (vErrors === null) {
                            vErrors = [err2];
                          } else {
                            vErrors.push(err2);
                          }
                          errors++;
                        }
                      }
                    }
                  } else {
                    const err3 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs6 = errors;
                if (data0 !== null) {
                  const err4 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err4];
                  } else {
                    vErrors.push(err4);
                  }
                  errors++;
                }
                var _valid0 = _errs6 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err5 = { instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err5];
                  } else {
                    vErrors.push(err5);
                  }
                  errors++;
                  validate33.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.history !== void 0) {
                  let data1 = data.history;
                  const _errs8 = errors;
                  if (typeof data1 !== "string") {
                    validate33.errors = [{ instancePath: instancePath + "/history", schemaPath: "#/properties/history/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "current" || data1 === "retained")) {
                    validate33.errors = [{ instancePath: instancePath + "/history", schemaPath: "#/properties/history/enum", keyword: "enum", params: { allowedValues: schema42.properties.history.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.limit !== void 0) {
                    let data2 = data.limit;
                    const _errs10 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate33.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs10) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 50 || isNaN(data2)) {
                          validate33.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 50 }, message: "must be <= 50" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate33.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.position !== void 0) {
                      let data3 = data.position;
                      const _errs12 = errors;
                      const _errs13 = errors;
                      let valid2 = false;
                      const _errs14 = errors;
                      const _errs15 = errors;
                      if (errors === _errs15) {
                        if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                          let missing1;
                          if (data3.query_sha256 === void 0 && (missing1 = "query_sha256") || data3.entity_offset === void 0 && (missing1 = "entity_offset") || data3.assertion_offset === void 0 && (missing1 = "assertion_offset")) {
                            const err6 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                            if (vErrors === null) {
                              vErrors = [err6];
                            } else {
                              vErrors.push(err6);
                            }
                            errors++;
                          } else {
                            const _errs17 = errors;
                            for (const key1 in data3) {
                              if (!(key1 === "assertion_offset" || key1 === "entity_offset" || key1 === "query_sha256")) {
                                const err7 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                if (vErrors === null) {
                                  vErrors = [err7];
                                } else {
                                  vErrors.push(err7);
                                }
                                errors++;
                                break;
                              }
                            }
                            if (_errs17 === errors) {
                              if (data3.assertion_offset !== void 0) {
                                let data4 = data3.assertion_offset;
                                const _errs18 = errors;
                                if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                                  const err8 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                  if (vErrors === null) {
                                    vErrors = [err8];
                                  } else {
                                    vErrors.push(err8);
                                  }
                                  errors++;
                                }
                                if (errors === _errs18) {
                                  if (typeof data4 == "number" && isFinite(data4)) {
                                    if (data4 > 8192 || isNaN(data4)) {
                                      const err9 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 8192 }, message: "must be <= 8192" };
                                      if (vErrors === null) {
                                        vErrors = [err9];
                                      } else {
                                        vErrors.push(err9);
                                      }
                                      errors++;
                                    } else {
                                      if (data4 < 0 || isNaN(data4)) {
                                        const err10 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                        if (vErrors === null) {
                                          vErrors = [err10];
                                        } else {
                                          vErrors.push(err10);
                                        }
                                        errors++;
                                      }
                                    }
                                  }
                                }
                                var valid4 = _errs18 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data3.entity_offset !== void 0) {
                                  let data5 = data3.entity_offset;
                                  const _errs20 = errors;
                                  if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                    const err11 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                    if (vErrors === null) {
                                      vErrors = [err11];
                                    } else {
                                      vErrors.push(err11);
                                    }
                                    errors++;
                                  }
                                  if (errors === _errs20) {
                                    if (typeof data5 == "number" && isFinite(data5)) {
                                      if (data5 > 4096 || isNaN(data5)) {
                                        const err12 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                        if (vErrors === null) {
                                          vErrors = [err12];
                                        } else {
                                          vErrors.push(err12);
                                        }
                                        errors++;
                                      } else {
                                        if (data5 < 0 || isNaN(data5)) {
                                          const err13 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                          if (vErrors === null) {
                                            vErrors = [err13];
                                          } else {
                                            vErrors.push(err13);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  }
                                  var valid4 = _errs20 === errors;
                                } else {
                                  var valid4 = true;
                                }
                                if (valid4) {
                                  if (data3.query_sha256 !== void 0) {
                                    let data6 = data3.query_sha256;
                                    const _errs22 = errors;
                                    if (errors === _errs22) {
                                      if (typeof data6 === "string") {
                                        if (!pattern5.test(data6)) {
                                          const err14 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                          if (vErrors === null) {
                                            vErrors = [err14];
                                          } else {
                                            vErrors.push(err14);
                                          }
                                          errors++;
                                        }
                                      } else {
                                        const err15 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err15];
                                        } else {
                                          vErrors.push(err15);
                                        }
                                        errors++;
                                      }
                                    }
                                    var valid4 = _errs22 === errors;
                                  } else {
                                    var valid4 = true;
                                  }
                                }
                              }
                            }
                          }
                        } else {
                          const err16 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                          if (vErrors === null) {
                            vErrors = [err16];
                          } else {
                            vErrors.push(err16);
                          }
                          errors++;
                        }
                      }
                      var _valid1 = _errs14 === errors;
                      valid2 = valid2 || _valid1;
                      const _errs24 = errors;
                      if (data3 !== null) {
                        const err17 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err17];
                        } else {
                          vErrors.push(err17);
                        }
                        errors++;
                      }
                      var _valid1 = _errs24 === errors;
                      valid2 = valid2 || _valid1;
                      if (!valid2) {
                        const err18 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err18];
                        } else {
                          vErrors.push(err18);
                        }
                        errors++;
                        validate33.errors = vErrors;
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
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.revision !== void 0) {
                        const _errs26 = errors;
                        if (!validate34(data.revision, { instancePath: instancePath + "/revision", parentData: data, parentDataProperty: "revision", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate34.errors : vErrors.concat(validate34.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.text !== void 0) {
                          let data8 = data.text;
                          const _errs27 = errors;
                          if (errors === _errs27) {
                            if (typeof data8 === "string") {
                              if (func1(data8) > 128) {
                                validate33.errors = [{ instancePath: instancePath + "/text", schemaPath: "#/properties/text/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                return false;
                              }
                            } else {
                              validate33.errors = [{ instancePath: instancePath + "/text", schemaPath: "#/properties/text/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid0 = _errs27 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.wire_version !== void 0) {
                            let data9 = data.wire_version;
                            const _errs29 = errors;
                            if (typeof data9 !== "string") {
                              validate33.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("1" !== data9) {
                              validate33.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs29 === errors;
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
          validate33.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate33.errors = vErrors;
      return errors === 0;
    }
    validate33.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate25(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.request === void 0 && (missing0 = "request") || data.query_sha256 === void 0 && (missing0 = "query_sha256") || data.total === void 0 && (missing0 = "total") || data.entities === void 0 && (missing0 = "entities") || data.next_position === void 0 && (missing0 = "next_position")) {
            validate25.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entities" || key0 === "next_position" || key0 === "query_sha256" || key0 === "request" || key0 === "total" || key0 === "wire_version")) {
                validate25.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entities !== void 0) {
                let data0 = data.entities;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 50) {
                      validate25.errors = [{ instancePath: instancePath + "/entities", schemaPath: "#/properties/entities/maxItems", keyword: "maxItems", params: { limit: 50 }, message: "must NOT have more than 50 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate26(data0[i0], { instancePath: instancePath + "/entities/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate25.errors = [{ instancePath: instancePath + "/entities", schemaPath: "#/properties/entities/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.next_position !== void 0) {
                  let data2 = data.next_position;
                  const _errs5 = errors;
                  const _errs6 = errors;
                  let valid2 = false;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                      let missing1;
                      if (data2.query_sha256 === void 0 && (missing1 = "query_sha256") || data2.entity_offset === void 0 && (missing1 = "entity_offset") || data2.assertion_offset === void 0 && (missing1 = "assertion_offset")) {
                        const err0 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/GraphViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        const _errs10 = errors;
                        for (const key1 in data2) {
                          if (!(key1 === "assertion_offset" || key1 === "entity_offset" || key1 === "query_sha256")) {
                            const err1 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/GraphViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                            if (vErrors === null) {
                              vErrors = [err1];
                            } else {
                              vErrors.push(err1);
                            }
                            errors++;
                            break;
                          }
                        }
                        if (_errs10 === errors) {
                          if (data2.assertion_offset !== void 0) {
                            let data3 = data2.assertion_offset;
                            const _errs11 = errors;
                            if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                              const err2 = { instancePath: instancePath + "/next_position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                            }
                            if (errors === _errs11) {
                              if (typeof data3 == "number" && isFinite(data3)) {
                                if (data3 > 8192 || isNaN(data3)) {
                                  const err3 = { instancePath: instancePath + "/next_position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 8192 }, message: "must be <= 8192" };
                                  if (vErrors === null) {
                                    vErrors = [err3];
                                  } else {
                                    vErrors.push(err3);
                                  }
                                  errors++;
                                } else {
                                  if (data3 < 0 || isNaN(data3)) {
                                    const err4 = { instancePath: instancePath + "/next_position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                    if (vErrors === null) {
                                      vErrors = [err4];
                                    } else {
                                      vErrors.push(err4);
                                    }
                                    errors++;
                                  }
                                }
                              }
                            }
                            var valid4 = _errs11 === errors;
                          } else {
                            var valid4 = true;
                          }
                          if (valid4) {
                            if (data2.entity_offset !== void 0) {
                              let data4 = data2.entity_offset;
                              const _errs13 = errors;
                              if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                                const err5 = { instancePath: instancePath + "/next_position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                if (vErrors === null) {
                                  vErrors = [err5];
                                } else {
                                  vErrors.push(err5);
                                }
                                errors++;
                              }
                              if (errors === _errs13) {
                                if (typeof data4 == "number" && isFinite(data4)) {
                                  if (data4 > 4096 || isNaN(data4)) {
                                    const err6 = { instancePath: instancePath + "/next_position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                    if (vErrors === null) {
                                      vErrors = [err6];
                                    } else {
                                      vErrors.push(err6);
                                    }
                                    errors++;
                                  } else {
                                    if (data4 < 0 || isNaN(data4)) {
                                      const err7 = { instancePath: instancePath + "/next_position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                      if (vErrors === null) {
                                        vErrors = [err7];
                                      } else {
                                        vErrors.push(err7);
                                      }
                                      errors++;
                                    }
                                  }
                                }
                              }
                              var valid4 = _errs13 === errors;
                            } else {
                              var valid4 = true;
                            }
                            if (valid4) {
                              if (data2.query_sha256 !== void 0) {
                                let data5 = data2.query_sha256;
                                const _errs15 = errors;
                                if (errors === _errs15) {
                                  if (typeof data5 === "string") {
                                    if (!pattern5.test(data5)) {
                                      const err8 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                      if (vErrors === null) {
                                        vErrors = [err8];
                                      } else {
                                        vErrors.push(err8);
                                      }
                                      errors++;
                                    }
                                  } else {
                                    const err9 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err9];
                                    } else {
                                      vErrors.push(err9);
                                    }
                                    errors++;
                                  }
                                }
                                var valid4 = _errs15 === errors;
                              } else {
                                var valid4 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      const err10 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/GraphViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err10];
                      } else {
                        vErrors.push(err10);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs7 === errors;
                  valid2 = valid2 || _valid0;
                  const _errs17 = errors;
                  if (data2 !== null) {
                    const err11 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err11];
                    } else {
                      vErrors.push(err11);
                    }
                    errors++;
                  }
                  var _valid0 = _errs17 === errors;
                  valid2 = valid2 || _valid0;
                  if (!valid2) {
                    const err12 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err12];
                    } else {
                      vErrors.push(err12);
                    }
                    errors++;
                    validate25.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs6;
                    if (vErrors !== null) {
                      if (_errs6) {
                        vErrors.length = _errs6;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.query_sha256 !== void 0) {
                    let data6 = data.query_sha256;
                    const _errs19 = errors;
                    if (errors === _errs19) {
                      if (typeof data6 === "string") {
                        if (!pattern5.test(data6)) {
                          validate25.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate25.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs19 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.request !== void 0) {
                      const _errs21 = errors;
                      if (!validate33(data.request, { instancePath: instancePath + "/request", parentData: data, parentDataProperty: "request", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate33.errors : vErrors.concat(validate33.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs21 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.total !== void 0) {
                        let data8 = data.total;
                        const _errs22 = errors;
                        if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)) && isFinite(data8))) {
                          validate25.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                          return false;
                        }
                        if (errors === _errs22) {
                          if (typeof data8 == "number" && isFinite(data8)) {
                            if (data8 > 4096 || isNaN(data8)) {
                              validate25.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" }];
                              return false;
                            } else {
                              if (data8 < 0 || isNaN(data8)) {
                                validate25.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                return false;
                              }
                            }
                          }
                        }
                        var valid0 = _errs22 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.wire_version !== void 0) {
                          let data9 = data.wire_version;
                          const _errs24 = errors;
                          if (typeof data9 !== "string") {
                            validate25.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("1" !== data9) {
                            validate25.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs24 === errors;
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
    exports.neighborhood_request = validate38;
    var schema45 = { "$defs": { "DomainGraphRef": { "additionalProperties": false, "properties": { "graph_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Graph Id", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "graph_id"], "title": "DomainGraphRef", "type": "object" }, "DomainRevisionRef": { "additionalProperties": false, "properties": { "graph": { "$ref": "#/$defs/DomainGraphRef" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" } }, "required": ["graph", "revision", "sha256"], "title": "DomainRevisionRef", "type": "object" }, "EntityRevisionRef": { "additionalProperties": false, "properties": { "entity_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Entity Id", "type": "string" }, "graph": { "$ref": "#/$defs/DomainGraphRef" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" } }, "required": ["graph", "entity_id", "revision"], "title": "EntityRevisionRef", "type": "object" }, "GraphViewPosition": { "additionalProperties": false, "properties": { "assertion_offset": { "maximum": 8192, "minimum": 0, "title": "Assertion Offset", "type": "integer" }, "entity_offset": { "maximum": 4096, "minimum": 0, "title": "Entity Offset", "type": "integer" }, "query_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Query Sha256", "type": "string" } }, "required": ["query_sha256", "entity_offset", "assertion_offset"], "title": "GraphViewPosition", "type": "object" }, "Scope": { "additionalProperties": false, "properties": { "project_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Project Id", "type": "string" }, "tenant_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Tenant Id", "type": "string" } }, "required": ["tenant_id", "project_id"], "title": "Scope", "type": "object" } }, "$id": "urn:amphora:knowledge.neighborhood-request:1:serialization", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": { "assertion_limit": { "default": 128, "maximum": 128, "minimum": 1, "title": "Assertion Limit", "type": "integer" }, "entity_limit": { "default": 64, "maximum": 64, "minimum": 1, "title": "Entity Limit", "type": "integer" }, "focus": { "$ref": "#/$defs/EntityRevisionRef" }, "history": { "default": "current", "enum": ["current", "retained"], "title": "History", "type": "string" }, "position": { "anyOf": [{ "$ref": "#/$defs/GraphViewPosition" }, { "type": "null" }], "default": null }, "radius": { "default": 1, "maximum": 2, "minimum": 0, "title": "Radius", "type": "integer" }, "revision": { "$ref": "#/$defs/DomainRevisionRef" }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" } }, "required": ["wire_version", "revision", "focus"], "title": "GraphNeighborhoodRequest", "type": "object" };
    function validate40(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate40.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.graph_id === void 0 && (missing0 = "graph_id")) {
            validate40.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph_id" || key0 === "scope")) {
                validate40.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph_id !== void 0) {
                let data0 = data.graph_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate40.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate40.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate40.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate40.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  let data1 = data.scope;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.tenant_id === void 0 && (missing1 = "tenant_id") || data1.project_id === void 0 && (missing1 = "project_id")) {
                        validate40.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate40.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.project_id !== void 0) {
                            let data2 = data1.project_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate40.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate40.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate40.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate40.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.tenant_id !== void 0) {
                              let data3 = data1.tenant_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate40.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate40.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate40.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate40.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                          }
                        }
                      }
                    } else {
                      validate40.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate40.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate40.errors = vErrors;
      return errors === 0;
    }
    validate40.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate39(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate39.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.entity_id === void 0 && (missing0 = "entity_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate39.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entity_id" || key0 === "graph" || key0 === "revision")) {
                validate39.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entity_id !== void 0) {
                let data0 = data.entity_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate39.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate39.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate39.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate39.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.graph !== void 0) {
                  const _errs4 = errors;
                  if (!validate40(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    let data2 = data.revision;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate39.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate39.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate39.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate39.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate39.errors = vErrors;
      return errors === 0;
    }
    validate39.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate43(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate43.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.revision === void 0 && (missing0 = "revision") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate43.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph" || key0 === "revision" || key0 === "sha256")) {
                validate43.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph !== void 0) {
                const _errs2 = errors;
                if (!validate40(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate43.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate43.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate43.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sha256 !== void 0) {
                    let data2 = data.sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern5.test(data2)) {
                          validate43.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate43.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate43.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate43.errors = vErrors;
      return errors === 0;
    }
    validate43.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate38(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate38.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.revision === void 0 && (missing0 = "revision") || data.focus === void 0 && (missing0 = "focus")) {
            validate38.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "assertion_limit" || key0 === "entity_limit" || key0 === "focus" || key0 === "history" || key0 === "position" || key0 === "radius" || key0 === "revision" || key0 === "wire_version")) {
                validate38.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assertion_limit !== void 0) {
                let data0 = data.assertion_limit;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate38.errors = [{ instancePath: instancePath + "/assertion_limit", schemaPath: "#/properties/assertion_limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 128 || isNaN(data0)) {
                      validate38.errors = [{ instancePath: instancePath + "/assertion_limit", schemaPath: "#/properties/assertion_limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 128 }, message: "must be <= 128" }];
                      return false;
                    } else {
                      if (data0 < 1 || isNaN(data0)) {
                        validate38.errors = [{ instancePath: instancePath + "/assertion_limit", schemaPath: "#/properties/assertion_limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                        return false;
                      }
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.entity_limit !== void 0) {
                  let data1 = data.entity_limit;
                  const _errs4 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate38.errors = [{ instancePath: instancePath + "/entity_limit", schemaPath: "#/properties/entity_limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 64 || isNaN(data1)) {
                        validate38.errors = [{ instancePath: instancePath + "/entity_limit", schemaPath: "#/properties/entity_limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 64 }, message: "must be <= 64" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate38.errors = [{ instancePath: instancePath + "/entity_limit", schemaPath: "#/properties/entity_limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.focus !== void 0) {
                    const _errs6 = errors;
                    if (!validate39(data.focus, { instancePath: instancePath + "/focus", parentData: data, parentDataProperty: "focus", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate39.errors : vErrors.concat(validate39.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.history !== void 0) {
                      let data3 = data.history;
                      const _errs7 = errors;
                      if (typeof data3 !== "string") {
                        validate38.errors = [{ instancePath: instancePath + "/history", schemaPath: "#/properties/history/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if (!(data3 === "current" || data3 === "retained")) {
                        validate38.errors = [{ instancePath: instancePath + "/history", schemaPath: "#/properties/history/enum", keyword: "enum", params: { allowedValues: schema45.properties.history.enum }, message: "must be equal to one of the allowed values" }];
                        return false;
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.position !== void 0) {
                        let data4 = data.position;
                        const _errs9 = errors;
                        const _errs10 = errors;
                        let valid1 = false;
                        const _errs11 = errors;
                        const _errs12 = errors;
                        if (errors === _errs12) {
                          if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                            let missing1;
                            if (data4.query_sha256 === void 0 && (missing1 = "query_sha256") || data4.entity_offset === void 0 && (missing1 = "entity_offset") || data4.assertion_offset === void 0 && (missing1 = "assertion_offset")) {
                              const err0 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            } else {
                              const _errs14 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "assertion_offset" || key1 === "entity_offset" || key1 === "query_sha256")) {
                                  const err1 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                  if (vErrors === null) {
                                    vErrors = [err1];
                                  } else {
                                    vErrors.push(err1);
                                  }
                                  errors++;
                                  break;
                                }
                              }
                              if (_errs14 === errors) {
                                if (data4.assertion_offset !== void 0) {
                                  let data5 = data4.assertion_offset;
                                  const _errs15 = errors;
                                  if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                    const err2 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                    if (vErrors === null) {
                                      vErrors = [err2];
                                    } else {
                                      vErrors.push(err2);
                                    }
                                    errors++;
                                  }
                                  if (errors === _errs15) {
                                    if (typeof data5 == "number" && isFinite(data5)) {
                                      if (data5 > 8192 || isNaN(data5)) {
                                        const err3 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 8192 }, message: "must be <= 8192" };
                                        if (vErrors === null) {
                                          vErrors = [err3];
                                        } else {
                                          vErrors.push(err3);
                                        }
                                        errors++;
                                      } else {
                                        if (data5 < 0 || isNaN(data5)) {
                                          const err4 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                          if (vErrors === null) {
                                            vErrors = [err4];
                                          } else {
                                            vErrors.push(err4);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  }
                                  var valid3 = _errs15 === errors;
                                } else {
                                  var valid3 = true;
                                }
                                if (valid3) {
                                  if (data4.entity_offset !== void 0) {
                                    let data6 = data4.entity_offset;
                                    const _errs17 = errors;
                                    if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                                      const err5 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                    }
                                    if (errors === _errs17) {
                                      if (typeof data6 == "number" && isFinite(data6)) {
                                        if (data6 > 4096 || isNaN(data6)) {
                                          const err6 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                          if (vErrors === null) {
                                            vErrors = [err6];
                                          } else {
                                            vErrors.push(err6);
                                          }
                                          errors++;
                                        } else {
                                          if (data6 < 0 || isNaN(data6)) {
                                            const err7 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                            if (vErrors === null) {
                                              vErrors = [err7];
                                            } else {
                                              vErrors.push(err7);
                                            }
                                            errors++;
                                          }
                                        }
                                      }
                                    }
                                    var valid3 = _errs17 === errors;
                                  } else {
                                    var valid3 = true;
                                  }
                                  if (valid3) {
                                    if (data4.query_sha256 !== void 0) {
                                      let data7 = data4.query_sha256;
                                      const _errs19 = errors;
                                      if (errors === _errs19) {
                                        if (typeof data7 === "string") {
                                          if (!pattern5.test(data7)) {
                                            const err8 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                            if (vErrors === null) {
                                              vErrors = [err8];
                                            } else {
                                              vErrors.push(err8);
                                            }
                                            errors++;
                                          }
                                        } else {
                                          const err9 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err9];
                                          } else {
                                            vErrors.push(err9);
                                          }
                                          errors++;
                                        }
                                      }
                                      var valid3 = _errs19 === errors;
                                    } else {
                                      var valid3 = true;
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            const err10 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err10];
                            } else {
                              vErrors.push(err10);
                            }
                            errors++;
                          }
                        }
                        var _valid0 = _errs11 === errors;
                        valid1 = valid1 || _valid0;
                        const _errs21 = errors;
                        if (data4 !== null) {
                          const err11 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                        }
                        var _valid0 = _errs21 === errors;
                        valid1 = valid1 || _valid0;
                        if (!valid1) {
                          const err12 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err12];
                          } else {
                            vErrors.push(err12);
                          }
                          errors++;
                          validate38.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs10;
                          if (vErrors !== null) {
                            if (_errs10) {
                              vErrors.length = _errs10;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs9 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.radius !== void 0) {
                          let data8 = data.radius;
                          const _errs23 = errors;
                          if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)) && isFinite(data8))) {
                            validate38.errors = [{ instancePath: instancePath + "/radius", schemaPath: "#/properties/radius/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs23) {
                            if (typeof data8 == "number" && isFinite(data8)) {
                              if (data8 > 2 || isNaN(data8)) {
                                validate38.errors = [{ instancePath: instancePath + "/radius", schemaPath: "#/properties/radius/maximum", keyword: "maximum", params: { comparison: "<=", limit: 2 }, message: "must be <= 2" }];
                                return false;
                              } else {
                                if (data8 < 0 || isNaN(data8)) {
                                  validate38.errors = [{ instancePath: instancePath + "/radius", schemaPath: "#/properties/radius/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                  return false;
                                }
                              }
                            }
                          }
                          var valid0 = _errs23 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.revision !== void 0) {
                            const _errs25 = errors;
                            if (!validate43(data.revision, { instancePath: instancePath + "/revision", parentData: data, parentDataProperty: "revision", rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate43.errors : vErrors.concat(validate43.errors);
                              errors = vErrors.length;
                            }
                            var valid0 = _errs25 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.wire_version !== void 0) {
                              let data10 = data.wire_version;
                              const _errs26 = errors;
                              if (typeof data10 !== "string") {
                                validate38.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("1" !== data10) {
                                validate38.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                return false;
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
            }
          }
        } else {
          validate38.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate38.errors = vErrors;
      return errors === 0;
    }
    validate38.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.neighborhood_page = validate46;
    var schema51 = { "$defs": { "AssertionRevisionRef": { "additionalProperties": false, "properties": { "assertion_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Assertion Id", "type": "string" }, "graph": { "$ref": "#/$defs/DomainGraphRef" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" } }, "required": ["graph", "assertion_id", "revision"], "title": "AssertionRevisionRef", "type": "object" }, "DomainGraphRef": { "additionalProperties": false, "properties": { "graph_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Graph Id", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "graph_id"], "title": "DomainGraphRef", "type": "object" }, "DomainRevisionRef": { "additionalProperties": false, "properties": { "graph": { "$ref": "#/$defs/DomainGraphRef" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" } }, "required": ["graph", "revision", "sha256"], "title": "DomainRevisionRef", "type": "object" }, "EntityRevisionRef": { "additionalProperties": false, "properties": { "entity_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Entity Id", "type": "string" }, "graph": { "$ref": "#/$defs/DomainGraphRef" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" } }, "required": ["graph", "entity_id", "revision"], "title": "EntityRevisionRef", "type": "object" }, "GraphAssertionSummary": { "additionalProperties": false, "properties": { "is_latest": { "title": "Is Latest", "type": "boolean" }, "object": { "$ref": "#/$defs/EntityRevisionRef" }, "polarity": { "enum": ["affirmed", "negated"], "title": "Polarity", "type": "string" }, "posture": { "enum": ["reported", "hypothesis", "unresolved"], "title": "Posture", "type": "string" }, "predicate": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Predicate", "type": "string" }, "reference": { "$ref": "#/$defs/AssertionRevisionRef" }, "retracted": { "title": "Retracted", "type": "boolean" }, "subject": { "$ref": "#/$defs/EntityRevisionRef" } }, "required": ["reference", "subject", "predicate", "object", "polarity", "posture", "is_latest", "retracted"], "title": "GraphAssertionSummary", "type": "object" }, "GraphEntitySummary": { "additionalProperties": false, "properties": { "alias_target": { "anyOf": [{ "$ref": "#/$defs/EntityRevisionRef" }, { "type": "null" }] }, "entity_type": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Entity Type", "type": "string" }, "is_latest": { "title": "Is Latest", "type": "boolean" }, "label": { "maxLength": 512, "minLength": 1, "title": "Label", "type": "string" }, "reference": { "$ref": "#/$defs/EntityRevisionRef" } }, "required": ["reference", "entity_type", "label", "is_latest", "alias_target"], "title": "GraphEntitySummary", "type": "object" }, "GraphNeighborhoodRequest": { "additionalProperties": false, "properties": { "assertion_limit": { "default": 128, "maximum": 128, "minimum": 1, "title": "Assertion Limit", "type": "integer" }, "entity_limit": { "default": 64, "maximum": 64, "minimum": 1, "title": "Entity Limit", "type": "integer" }, "focus": { "$ref": "#/$defs/EntityRevisionRef" }, "history": { "default": "current", "enum": ["current", "retained"], "title": "History", "type": "string" }, "position": { "anyOf": [{ "$ref": "#/$defs/GraphViewPosition" }, { "type": "null" }], "default": null }, "radius": { "default": 1, "maximum": 2, "minimum": 0, "title": "Radius", "type": "integer" }, "revision": { "$ref": "#/$defs/DomainRevisionRef" }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" } }, "required": ["wire_version", "revision", "focus"], "title": "GraphNeighborhoodRequest", "type": "object" }, "GraphViewPosition": { "additionalProperties": false, "properties": { "assertion_offset": { "maximum": 8192, "minimum": 0, "title": "Assertion Offset", "type": "integer" }, "entity_offset": { "maximum": 4096, "minimum": 0, "title": "Entity Offset", "type": "integer" }, "query_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Query Sha256", "type": "string" } }, "required": ["query_sha256", "entity_offset", "assertion_offset"], "title": "GraphViewPosition", "type": "object" }, "Scope": { "additionalProperties": false, "properties": { "project_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Project Id", "type": "string" }, "tenant_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Tenant Id", "type": "string" } }, "required": ["tenant_id", "project_id"], "title": "Scope", "type": "object" } }, "$id": "urn:amphora:knowledge.neighborhood-page:1:serialization", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": { "assertion_total": { "maximum": 8192, "minimum": 0, "title": "Assertion Total", "type": "integer" }, "assertions": { "items": { "$ref": "#/$defs/GraphAssertionSummary" }, "maxItems": 128, "title": "Assertions", "type": "array" }, "entities": { "items": { "$ref": "#/$defs/GraphEntitySummary" }, "maxItems": 64, "title": "Entities", "type": "array" }, "entity_total": { "maximum": 4096, "minimum": 0, "title": "Entity Total", "type": "integer" }, "next_position": { "anyOf": [{ "$ref": "#/$defs/GraphViewPosition" }, { "type": "null" }] }, "query_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Query Sha256", "type": "string" }, "request": { "$ref": "#/$defs/GraphNeighborhoodRequest" }, "unresolved_entities": { "items": { "$ref": "#/$defs/EntityRevisionRef" }, "maxItems": 320, "title": "Unresolved Entities", "type": "array" }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" } }, "required": ["wire_version", "request", "query_sha256", "entity_total", "assertion_total", "entities", "assertions", "unresolved_entities", "next_position"], "title": "GraphNeighborhoodPage", "type": "object" };
    var func33 = Object.prototype.hasOwnProperty;
    var schema52 = { "additionalProperties": false, "properties": { "is_latest": { "title": "Is Latest", "type": "boolean" }, "object": { "$ref": "#/$defs/EntityRevisionRef" }, "polarity": { "enum": ["affirmed", "negated"], "title": "Polarity", "type": "string" }, "posture": { "enum": ["reported", "hypothesis", "unresolved"], "title": "Posture", "type": "string" }, "predicate": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Predicate", "type": "string" }, "reference": { "$ref": "#/$defs/AssertionRevisionRef" }, "retracted": { "title": "Retracted", "type": "boolean" }, "subject": { "$ref": "#/$defs/EntityRevisionRef" } }, "required": ["reference", "subject", "predicate", "object", "polarity", "posture", "is_latest", "retracted"], "title": "GraphAssertionSummary", "type": "object" };
    function validate49(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate49.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.graph_id === void 0 && (missing0 = "graph_id")) {
            validate49.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph_id" || key0 === "scope")) {
                validate49.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph_id !== void 0) {
                let data0 = data.graph_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate49.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate49.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate49.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate49.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  let data1 = data.scope;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.tenant_id === void 0 && (missing1 = "tenant_id") || data1.project_id === void 0 && (missing1 = "project_id")) {
                        validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.project_id !== void 0) {
                            let data2 = data1.project_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.tenant_id !== void 0) {
                              let data3 = data1.tenant_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                          }
                        }
                      }
                    } else {
                      validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate49.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate49.errors = vErrors;
      return errors === 0;
    }
    validate49.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate48(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate48.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.entity_id === void 0 && (missing0 = "entity_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate48.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entity_id" || key0 === "graph" || key0 === "revision")) {
                validate48.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entity_id !== void 0) {
                let data0 = data.entity_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate48.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate48.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate48.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate48.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.graph !== void 0) {
                  const _errs4 = errors;
                  if (!validate49(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    let data2 = data.revision;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate48.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate48.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate48.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate48.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate48.errors = vErrors;
      return errors === 0;
    }
    validate48.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate52(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate52.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.assertion_id === void 0 && (missing0 = "assertion_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate52.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "assertion_id" || key0 === "graph" || key0 === "revision")) {
                validate52.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assertion_id !== void 0) {
                let data0 = data.assertion_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate52.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate52.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate52.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate52.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.graph !== void 0) {
                  const _errs4 = errors;
                  if (!validate49(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    let data2 = data.revision;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate52.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate52.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate52.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate52.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate52.errors = vErrors;
      return errors === 0;
    }
    validate52.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate47(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate47.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.reference === void 0 && (missing0 = "reference") || data.subject === void 0 && (missing0 = "subject") || data.predicate === void 0 && (missing0 = "predicate") || data.object === void 0 && (missing0 = "object") || data.polarity === void 0 && (missing0 = "polarity") || data.posture === void 0 && (missing0 = "posture") || data.is_latest === void 0 && (missing0 = "is_latest") || data.retracted === void 0 && (missing0 = "retracted")) {
            validate47.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "is_latest" || key0 === "object" || key0 === "polarity" || key0 === "posture" || key0 === "predicate" || key0 === "reference" || key0 === "retracted" || key0 === "subject")) {
                validate47.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.is_latest !== void 0) {
                const _errs2 = errors;
                if (typeof data.is_latest !== "boolean") {
                  validate47.errors = [{ instancePath: instancePath + "/is_latest", schemaPath: "#/properties/is_latest/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.object !== void 0) {
                  const _errs4 = errors;
                  if (!validate48(data.object, { instancePath: instancePath + "/object", parentData: data, parentDataProperty: "object", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.polarity !== void 0) {
                    let data2 = data.polarity;
                    const _errs5 = errors;
                    if (typeof data2 !== "string") {
                      validate47.errors = [{ instancePath: instancePath + "/polarity", schemaPath: "#/properties/polarity/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data2 === "affirmed" || data2 === "negated")) {
                      validate47.errors = [{ instancePath: instancePath + "/polarity", schemaPath: "#/properties/polarity/enum", keyword: "enum", params: { allowedValues: schema52.properties.polarity.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.posture !== void 0) {
                      let data3 = data.posture;
                      const _errs7 = errors;
                      if (typeof data3 !== "string") {
                        validate47.errors = [{ instancePath: instancePath + "/posture", schemaPath: "#/properties/posture/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if (!(data3 === "reported" || data3 === "hypothesis" || data3 === "unresolved")) {
                        validate47.errors = [{ instancePath: instancePath + "/posture", schemaPath: "#/properties/posture/enum", keyword: "enum", params: { allowedValues: schema52.properties.posture.enum }, message: "must be equal to one of the allowed values" }];
                        return false;
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.predicate !== void 0) {
                        let data4 = data.predicate;
                        const _errs9 = errors;
                        if (errors === _errs9) {
                          if (typeof data4 === "string") {
                            if (func1(data4) > 128) {
                              validate47.errors = [{ instancePath: instancePath + "/predicate", schemaPath: "#/properties/predicate/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func1(data4) < 1) {
                                validate47.errors = [{ instancePath: instancePath + "/predicate", schemaPath: "#/properties/predicate/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern4.test(data4)) {
                                  validate47.errors = [{ instancePath: instancePath + "/predicate", schemaPath: "#/properties/predicate/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate47.errors = [{ instancePath: instancePath + "/predicate", schemaPath: "#/properties/predicate/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs9 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.reference !== void 0) {
                          const _errs11 = errors;
                          if (!validate52(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate52.errors : vErrors.concat(validate52.errors);
                            errors = vErrors.length;
                          }
                          var valid0 = _errs11 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.retracted !== void 0) {
                            const _errs12 = errors;
                            if (typeof data.retracted !== "boolean") {
                              validate47.errors = [{ instancePath: instancePath + "/retracted", schemaPath: "#/properties/retracted/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                              return false;
                            }
                            var valid0 = _errs12 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.subject !== void 0) {
                              const _errs14 = errors;
                              if (!validate48(data.subject, { instancePath: instancePath + "/subject", parentData: data, parentDataProperty: "subject", rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
                                errors = vErrors.length;
                              }
                              var valid0 = _errs14 === errors;
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
        } else {
          validate47.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate47.errors = vErrors;
      return errors === 0;
    }
    validate47.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate57(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate57.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.reference === void 0 && (missing0 = "reference") || data.entity_type === void 0 && (missing0 = "entity_type") || data.label === void 0 && (missing0 = "label") || data.is_latest === void 0 && (missing0 = "is_latest") || data.alias_target === void 0 && (missing0 = "alias_target")) {
            validate57.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "alias_target" || key0 === "entity_type" || key0 === "is_latest" || key0 === "label" || key0 === "reference")) {
                validate57.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.alias_target !== void 0) {
                let data0 = data.alias_target;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate48(data0, { instancePath: instancePath + "/alias_target", parentData: data, parentDataProperty: "alias_target", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/alias_target", schemaPath: "#/properties/alias_target/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs5 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err1 = { instancePath: instancePath + "/alias_target", schemaPath: "#/properties/alias_target/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate57.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.entity_type !== void 0) {
                  let data1 = data.entity_type;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate57.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate57.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate57.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate57.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.is_latest !== void 0) {
                    const _errs9 = errors;
                    if (typeof data.is_latest !== "boolean") {
                      validate57.errors = [{ instancePath: instancePath + "/is_latest", schemaPath: "#/properties/is_latest/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.label !== void 0) {
                      let data3 = data.label;
                      const _errs11 = errors;
                      if (errors === _errs11) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 512) {
                            validate57.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/maxLength", keyword: "maxLength", params: { limit: 512 }, message: "must NOT have more than 512 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate57.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            }
                          }
                        } else {
                          validate57.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.reference !== void 0) {
                        const _errs13 = errors;
                        if (!validate48(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs13 === errors;
                      } else {
                        var valid0 = true;
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate57.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate57.errors = vErrors;
      return errors === 0;
    }
    validate57.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema59 = { "additionalProperties": false, "properties": { "assertion_limit": { "default": 128, "maximum": 128, "minimum": 1, "title": "Assertion Limit", "type": "integer" }, "entity_limit": { "default": 64, "maximum": 64, "minimum": 1, "title": "Entity Limit", "type": "integer" }, "focus": { "$ref": "#/$defs/EntityRevisionRef" }, "history": { "default": "current", "enum": ["current", "retained"], "title": "History", "type": "string" }, "position": { "anyOf": [{ "$ref": "#/$defs/GraphViewPosition" }, { "type": "null" }], "default": null }, "radius": { "default": 1, "maximum": 2, "minimum": 0, "title": "Radius", "type": "integer" }, "revision": { "$ref": "#/$defs/DomainRevisionRef" }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" } }, "required": ["wire_version", "revision", "focus"], "title": "GraphNeighborhoodRequest", "type": "object" };
    function validate63(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate63.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.revision === void 0 && (missing0 = "revision") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate63.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph" || key0 === "revision" || key0 === "sha256")) {
                validate63.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph !== void 0) {
                const _errs2 = errors;
                if (!validate49(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate63.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate63.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate63.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sha256 !== void 0) {
                    let data2 = data.sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern5.test(data2)) {
                          validate63.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate63.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate63.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate63.errors = vErrors;
      return errors === 0;
    }
    validate63.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate61(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate61.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.revision === void 0 && (missing0 = "revision") || data.focus === void 0 && (missing0 = "focus")) {
            validate61.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "assertion_limit" || key0 === "entity_limit" || key0 === "focus" || key0 === "history" || key0 === "position" || key0 === "radius" || key0 === "revision" || key0 === "wire_version")) {
                validate61.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assertion_limit !== void 0) {
                let data0 = data.assertion_limit;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate61.errors = [{ instancePath: instancePath + "/assertion_limit", schemaPath: "#/properties/assertion_limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 128 || isNaN(data0)) {
                      validate61.errors = [{ instancePath: instancePath + "/assertion_limit", schemaPath: "#/properties/assertion_limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 128 }, message: "must be <= 128" }];
                      return false;
                    } else {
                      if (data0 < 1 || isNaN(data0)) {
                        validate61.errors = [{ instancePath: instancePath + "/assertion_limit", schemaPath: "#/properties/assertion_limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                        return false;
                      }
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.entity_limit !== void 0) {
                  let data1 = data.entity_limit;
                  const _errs4 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate61.errors = [{ instancePath: instancePath + "/entity_limit", schemaPath: "#/properties/entity_limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 64 || isNaN(data1)) {
                        validate61.errors = [{ instancePath: instancePath + "/entity_limit", schemaPath: "#/properties/entity_limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 64 }, message: "must be <= 64" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate61.errors = [{ instancePath: instancePath + "/entity_limit", schemaPath: "#/properties/entity_limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.focus !== void 0) {
                    const _errs6 = errors;
                    if (!validate48(data.focus, { instancePath: instancePath + "/focus", parentData: data, parentDataProperty: "focus", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.history !== void 0) {
                      let data3 = data.history;
                      const _errs7 = errors;
                      if (typeof data3 !== "string") {
                        validate61.errors = [{ instancePath: instancePath + "/history", schemaPath: "#/properties/history/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if (!(data3 === "current" || data3 === "retained")) {
                        validate61.errors = [{ instancePath: instancePath + "/history", schemaPath: "#/properties/history/enum", keyword: "enum", params: { allowedValues: schema59.properties.history.enum }, message: "must be equal to one of the allowed values" }];
                        return false;
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.position !== void 0) {
                        let data4 = data.position;
                        const _errs9 = errors;
                        const _errs10 = errors;
                        let valid1 = false;
                        const _errs11 = errors;
                        const _errs12 = errors;
                        if (errors === _errs12) {
                          if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                            let missing1;
                            if (data4.query_sha256 === void 0 && (missing1 = "query_sha256") || data4.entity_offset === void 0 && (missing1 = "entity_offset") || data4.assertion_offset === void 0 && (missing1 = "assertion_offset")) {
                              const err0 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            } else {
                              const _errs14 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "assertion_offset" || key1 === "entity_offset" || key1 === "query_sha256")) {
                                  const err1 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                  if (vErrors === null) {
                                    vErrors = [err1];
                                  } else {
                                    vErrors.push(err1);
                                  }
                                  errors++;
                                  break;
                                }
                              }
                              if (_errs14 === errors) {
                                if (data4.assertion_offset !== void 0) {
                                  let data5 = data4.assertion_offset;
                                  const _errs15 = errors;
                                  if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                    const err2 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                    if (vErrors === null) {
                                      vErrors = [err2];
                                    } else {
                                      vErrors.push(err2);
                                    }
                                    errors++;
                                  }
                                  if (errors === _errs15) {
                                    if (typeof data5 == "number" && isFinite(data5)) {
                                      if (data5 > 8192 || isNaN(data5)) {
                                        const err3 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 8192 }, message: "must be <= 8192" };
                                        if (vErrors === null) {
                                          vErrors = [err3];
                                        } else {
                                          vErrors.push(err3);
                                        }
                                        errors++;
                                      } else {
                                        if (data5 < 0 || isNaN(data5)) {
                                          const err4 = { instancePath: instancePath + "/position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                          if (vErrors === null) {
                                            vErrors = [err4];
                                          } else {
                                            vErrors.push(err4);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  }
                                  var valid3 = _errs15 === errors;
                                } else {
                                  var valid3 = true;
                                }
                                if (valid3) {
                                  if (data4.entity_offset !== void 0) {
                                    let data6 = data4.entity_offset;
                                    const _errs17 = errors;
                                    if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                                      const err5 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                    }
                                    if (errors === _errs17) {
                                      if (typeof data6 == "number" && isFinite(data6)) {
                                        if (data6 > 4096 || isNaN(data6)) {
                                          const err6 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                          if (vErrors === null) {
                                            vErrors = [err6];
                                          } else {
                                            vErrors.push(err6);
                                          }
                                          errors++;
                                        } else {
                                          if (data6 < 0 || isNaN(data6)) {
                                            const err7 = { instancePath: instancePath + "/position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                            if (vErrors === null) {
                                              vErrors = [err7];
                                            } else {
                                              vErrors.push(err7);
                                            }
                                            errors++;
                                          }
                                        }
                                      }
                                    }
                                    var valid3 = _errs17 === errors;
                                  } else {
                                    var valid3 = true;
                                  }
                                  if (valid3) {
                                    if (data4.query_sha256 !== void 0) {
                                      let data7 = data4.query_sha256;
                                      const _errs19 = errors;
                                      if (errors === _errs19) {
                                        if (typeof data7 === "string") {
                                          if (!pattern5.test(data7)) {
                                            const err8 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                            if (vErrors === null) {
                                              vErrors = [err8];
                                            } else {
                                              vErrors.push(err8);
                                            }
                                            errors++;
                                          }
                                        } else {
                                          const err9 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err9];
                                          } else {
                                            vErrors.push(err9);
                                          }
                                          errors++;
                                        }
                                      }
                                      var valid3 = _errs19 === errors;
                                    } else {
                                      var valid3 = true;
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            const err10 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/GraphViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err10];
                            } else {
                              vErrors.push(err10);
                            }
                            errors++;
                          }
                        }
                        var _valid0 = _errs11 === errors;
                        valid1 = valid1 || _valid0;
                        const _errs21 = errors;
                        if (data4 !== null) {
                          const err11 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                        }
                        var _valid0 = _errs21 === errors;
                        valid1 = valid1 || _valid0;
                        if (!valid1) {
                          const err12 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err12];
                          } else {
                            vErrors.push(err12);
                          }
                          errors++;
                          validate61.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs10;
                          if (vErrors !== null) {
                            if (_errs10) {
                              vErrors.length = _errs10;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs9 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.radius !== void 0) {
                          let data8 = data.radius;
                          const _errs23 = errors;
                          if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)) && isFinite(data8))) {
                            validate61.errors = [{ instancePath: instancePath + "/radius", schemaPath: "#/properties/radius/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs23) {
                            if (typeof data8 == "number" && isFinite(data8)) {
                              if (data8 > 2 || isNaN(data8)) {
                                validate61.errors = [{ instancePath: instancePath + "/radius", schemaPath: "#/properties/radius/maximum", keyword: "maximum", params: { comparison: "<=", limit: 2 }, message: "must be <= 2" }];
                                return false;
                              } else {
                                if (data8 < 0 || isNaN(data8)) {
                                  validate61.errors = [{ instancePath: instancePath + "/radius", schemaPath: "#/properties/radius/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                  return false;
                                }
                              }
                            }
                          }
                          var valid0 = _errs23 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.revision !== void 0) {
                            const _errs25 = errors;
                            if (!validate63(data.revision, { instancePath: instancePath + "/revision", parentData: data, parentDataProperty: "revision", rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate63.errors : vErrors.concat(validate63.errors);
                              errors = vErrors.length;
                            }
                            var valid0 = _errs25 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.wire_version !== void 0) {
                              let data10 = data.wire_version;
                              const _errs26 = errors;
                              if (typeof data10 !== "string") {
                                validate61.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("1" !== data10) {
                                validate61.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                return false;
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
            }
          }
        } else {
          validate61.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate61.errors = vErrors;
      return errors === 0;
    }
    validate61.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate46(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate46.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.request === void 0 && (missing0 = "request") || data.query_sha256 === void 0 && (missing0 = "query_sha256") || data.entity_total === void 0 && (missing0 = "entity_total") || data.assertion_total === void 0 && (missing0 = "assertion_total") || data.entities === void 0 && (missing0 = "entities") || data.assertions === void 0 && (missing0 = "assertions") || data.unresolved_entities === void 0 && (missing0 = "unresolved_entities") || data.next_position === void 0 && (missing0 = "next_position")) {
            validate46.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func33.call(schema51.properties, key0)) {
                validate46.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assertion_total !== void 0) {
                let data0 = data.assertion_total;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate46.errors = [{ instancePath: instancePath + "/assertion_total", schemaPath: "#/properties/assertion_total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 8192 || isNaN(data0)) {
                      validate46.errors = [{ instancePath: instancePath + "/assertion_total", schemaPath: "#/properties/assertion_total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 8192 }, message: "must be <= 8192" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate46.errors = [{ instancePath: instancePath + "/assertion_total", schemaPath: "#/properties/assertion_total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                        return false;
                      }
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.assertions !== void 0) {
                  let data1 = data.assertions;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (Array.isArray(data1)) {
                      if (data1.length > 128) {
                        validate46.errors = [{ instancePath: instancePath + "/assertions", schemaPath: "#/properties/assertions/maxItems", keyword: "maxItems", params: { limit: 128 }, message: "must NOT have more than 128 items" }];
                        return false;
                      } else {
                        var valid1 = true;
                        const len0 = data1.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs6 = errors;
                          if (!validate47(data1[i0], { instancePath: instancePath + "/assertions/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate47.errors : vErrors.concat(validate47.errors);
                            errors = vErrors.length;
                          }
                          var valid1 = _errs6 === errors;
                          if (!valid1) {
                            break;
                          }
                        }
                      }
                    } else {
                      validate46.errors = [{ instancePath: instancePath + "/assertions", schemaPath: "#/properties/assertions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.entities !== void 0) {
                    let data3 = data.entities;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (Array.isArray(data3)) {
                        if (data3.length > 64) {
                          validate46.errors = [{ instancePath: instancePath + "/entities", schemaPath: "#/properties/entities/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                          return false;
                        } else {
                          var valid2 = true;
                          const len1 = data3.length;
                          for (let i1 = 0; i1 < len1; i1++) {
                            const _errs9 = errors;
                            if (!validate57(data3[i1], { instancePath: instancePath + "/entities/" + i1, parentData: data3, parentDataProperty: i1, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate57.errors : vErrors.concat(validate57.errors);
                              errors = vErrors.length;
                            }
                            var valid2 = _errs9 === errors;
                            if (!valid2) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate46.errors = [{ instancePath: instancePath + "/entities", schemaPath: "#/properties/entities/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs7 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.entity_total !== void 0) {
                      let data5 = data.entity_total;
                      const _errs10 = errors;
                      if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                        validate46.errors = [{ instancePath: instancePath + "/entity_total", schemaPath: "#/properties/entity_total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      if (errors === _errs10) {
                        if (typeof data5 == "number" && isFinite(data5)) {
                          if (data5 > 4096 || isNaN(data5)) {
                            validate46.errors = [{ instancePath: instancePath + "/entity_total", schemaPath: "#/properties/entity_total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" }];
                            return false;
                          } else {
                            if (data5 < 0 || isNaN(data5)) {
                              validate46.errors = [{ instancePath: instancePath + "/entity_total", schemaPath: "#/properties/entity_total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                              return false;
                            }
                          }
                        }
                      }
                      var valid0 = _errs10 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.next_position !== void 0) {
                        let data6 = data.next_position;
                        const _errs12 = errors;
                        const _errs13 = errors;
                        let valid3 = false;
                        const _errs14 = errors;
                        const _errs15 = errors;
                        if (errors === _errs15) {
                          if (data6 && typeof data6 == "object" && !Array.isArray(data6)) {
                            let missing1;
                            if (data6.query_sha256 === void 0 && (missing1 = "query_sha256") || data6.entity_offset === void 0 && (missing1 = "entity_offset") || data6.assertion_offset === void 0 && (missing1 = "assertion_offset")) {
                              const err0 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/GraphViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            } else {
                              const _errs17 = errors;
                              for (const key1 in data6) {
                                if (!(key1 === "assertion_offset" || key1 === "entity_offset" || key1 === "query_sha256")) {
                                  const err1 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/GraphViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                  if (vErrors === null) {
                                    vErrors = [err1];
                                  } else {
                                    vErrors.push(err1);
                                  }
                                  errors++;
                                  break;
                                }
                              }
                              if (_errs17 === errors) {
                                if (data6.assertion_offset !== void 0) {
                                  let data7 = data6.assertion_offset;
                                  const _errs18 = errors;
                                  if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                                    const err2 = { instancePath: instancePath + "/next_position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                    if (vErrors === null) {
                                      vErrors = [err2];
                                    } else {
                                      vErrors.push(err2);
                                    }
                                    errors++;
                                  }
                                  if (errors === _errs18) {
                                    if (typeof data7 == "number" && isFinite(data7)) {
                                      if (data7 > 8192 || isNaN(data7)) {
                                        const err3 = { instancePath: instancePath + "/next_position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 8192 }, message: "must be <= 8192" };
                                        if (vErrors === null) {
                                          vErrors = [err3];
                                        } else {
                                          vErrors.push(err3);
                                        }
                                        errors++;
                                      } else {
                                        if (data7 < 0 || isNaN(data7)) {
                                          const err4 = { instancePath: instancePath + "/next_position/assertion_offset", schemaPath: "#/$defs/GraphViewPosition/properties/assertion_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                          if (vErrors === null) {
                                            vErrors = [err4];
                                          } else {
                                            vErrors.push(err4);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  }
                                  var valid5 = _errs18 === errors;
                                } else {
                                  var valid5 = true;
                                }
                                if (valid5) {
                                  if (data6.entity_offset !== void 0) {
                                    let data8 = data6.entity_offset;
                                    const _errs20 = errors;
                                    if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)) && isFinite(data8))) {
                                      const err5 = { instancePath: instancePath + "/next_position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                    }
                                    if (errors === _errs20) {
                                      if (typeof data8 == "number" && isFinite(data8)) {
                                        if (data8 > 4096 || isNaN(data8)) {
                                          const err6 = { instancePath: instancePath + "/next_position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                          if (vErrors === null) {
                                            vErrors = [err6];
                                          } else {
                                            vErrors.push(err6);
                                          }
                                          errors++;
                                        } else {
                                          if (data8 < 0 || isNaN(data8)) {
                                            const err7 = { instancePath: instancePath + "/next_position/entity_offset", schemaPath: "#/$defs/GraphViewPosition/properties/entity_offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                            if (vErrors === null) {
                                              vErrors = [err7];
                                            } else {
                                              vErrors.push(err7);
                                            }
                                            errors++;
                                          }
                                        }
                                      }
                                    }
                                    var valid5 = _errs20 === errors;
                                  } else {
                                    var valid5 = true;
                                  }
                                  if (valid5) {
                                    if (data6.query_sha256 !== void 0) {
                                      let data9 = data6.query_sha256;
                                      const _errs22 = errors;
                                      if (errors === _errs22) {
                                        if (typeof data9 === "string") {
                                          if (!pattern5.test(data9)) {
                                            const err8 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                            if (vErrors === null) {
                                              vErrors = [err8];
                                            } else {
                                              vErrors.push(err8);
                                            }
                                            errors++;
                                          }
                                        } else {
                                          const err9 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/GraphViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err9];
                                          } else {
                                            vErrors.push(err9);
                                          }
                                          errors++;
                                        }
                                      }
                                      var valid5 = _errs22 === errors;
                                    } else {
                                      var valid5 = true;
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            const err10 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/GraphViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err10];
                            } else {
                              vErrors.push(err10);
                            }
                            errors++;
                          }
                        }
                        var _valid0 = _errs14 === errors;
                        valid3 = valid3 || _valid0;
                        const _errs24 = errors;
                        if (data6 !== null) {
                          const err11 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                        }
                        var _valid0 = _errs24 === errors;
                        valid3 = valid3 || _valid0;
                        if (!valid3) {
                          const err12 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err12];
                          } else {
                            vErrors.push(err12);
                          }
                          errors++;
                          validate46.errors = vErrors;
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
                        var valid0 = _errs12 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.query_sha256 !== void 0) {
                          let data10 = data.query_sha256;
                          const _errs26 = errors;
                          if (errors === _errs26) {
                            if (typeof data10 === "string") {
                              if (!pattern5.test(data10)) {
                                validate46.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                return false;
                              }
                            } else {
                              validate46.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid0 = _errs26 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.request !== void 0) {
                            const _errs28 = errors;
                            if (!validate61(data.request, { instancePath: instancePath + "/request", parentData: data, parentDataProperty: "request", rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate61.errors : vErrors.concat(validate61.errors);
                              errors = vErrors.length;
                            }
                            var valid0 = _errs28 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.unresolved_entities !== void 0) {
                              let data12 = data.unresolved_entities;
                              const _errs29 = errors;
                              if (errors === _errs29) {
                                if (Array.isArray(data12)) {
                                  if (data12.length > 320) {
                                    validate46.errors = [{ instancePath: instancePath + "/unresolved_entities", schemaPath: "#/properties/unresolved_entities/maxItems", keyword: "maxItems", params: { limit: 320 }, message: "must NOT have more than 320 items" }];
                                    return false;
                                  } else {
                                    var valid6 = true;
                                    const len2 = data12.length;
                                    for (let i2 = 0; i2 < len2; i2++) {
                                      const _errs31 = errors;
                                      if (!validate48(data12[i2], { instancePath: instancePath + "/unresolved_entities/" + i2, parentData: data12, parentDataProperty: i2, rootData, dynamicAnchors })) {
                                        vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
                                        errors = vErrors.length;
                                      }
                                      var valid6 = _errs31 === errors;
                                      if (!valid6) {
                                        break;
                                      }
                                    }
                                  }
                                } else {
                                  validate46.errors = [{ instancePath: instancePath + "/unresolved_entities", schemaPath: "#/properties/unresolved_entities/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs29 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.wire_version !== void 0) {
                                let data14 = data.wire_version;
                                const _errs32 = errors;
                                if (typeof data14 !== "string") {
                                  validate46.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("1" !== data14) {
                                  validate46.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid0 = _errs32 === errors;
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
        } else {
          validate46.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate46.errors = vErrors;
      return errors === 0;
    }
    validate46.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.object_request = validate68;
    function validate70(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate70.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.graph_id === void 0 && (missing0 = "graph_id")) {
            validate70.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph_id" || key0 === "scope")) {
                validate70.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph_id !== void 0) {
                let data0 = data.graph_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate70.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate70.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate70.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate70.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  let data1 = data.scope;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.tenant_id === void 0 && (missing1 = "tenant_id") || data1.project_id === void 0 && (missing1 = "project_id")) {
                        validate70.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate70.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.project_id !== void 0) {
                            let data2 = data1.project_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate70.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate70.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate70.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate70.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.tenant_id !== void 0) {
                              let data3 = data1.tenant_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate70.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate70.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate70.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate70.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                          }
                        }
                      }
                    } else {
                      validate70.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate70.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate70.errors = vErrors;
      return errors === 0;
    }
    validate70.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate69(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate69.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.revision === void 0 && (missing0 = "revision") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate69.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph" || key0 === "revision" || key0 === "sha256")) {
                validate69.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph !== void 0) {
                const _errs2 = errors;
                if (!validate70(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate70.errors : vErrors.concat(validate70.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate69.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate69.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate69.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sha256 !== void 0) {
                    let data2 = data.sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern5.test(data2)) {
                          validate69.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate69.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate69.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate69.errors = vErrors;
      return errors === 0;
    }
    validate69.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate74(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate74.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.entity_id === void 0 && (missing0 = "entity_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate74.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entity_id" || key0 === "graph" || key0 === "revision")) {
                validate74.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entity_id !== void 0) {
                let data0 = data.entity_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate74.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate74.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate74.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate74.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.graph !== void 0) {
                  const _errs4 = errors;
                  if (!validate70(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate70.errors : vErrors.concat(validate70.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    let data2 = data.revision;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate74.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate74.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate74.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate74.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate74.errors = vErrors;
      return errors === 0;
    }
    validate74.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate73(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate73.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.reference === void 0 && (missing0 = "reference")) {
            validate73.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "kind" || key0 === "reference")) {
                validate73.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.kind !== void 0) {
                let data0 = data.kind;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate73.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("entity" !== data0) {
                  validate73.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "entity" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reference !== void 0) {
                  const _errs4 = errors;
                  if (!validate74(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate74.errors : vErrors.concat(validate74.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate73.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate73.errors = vErrors;
      return errors === 0;
    }
    validate73.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate79(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate79.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.assertion_id === void 0 && (missing0 = "assertion_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate79.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "assertion_id" || key0 === "graph" || key0 === "revision")) {
                validate79.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assertion_id !== void 0) {
                let data0 = data.assertion_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate79.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate79.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate79.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate79.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.graph !== void 0) {
                  const _errs4 = errors;
                  if (!validate70(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate70.errors : vErrors.concat(validate70.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    let data2 = data.revision;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate79.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate79.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate79.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate79.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate79.errors = vErrors;
      return errors === 0;
    }
    validate79.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate78(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate78.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.reference === void 0 && (missing0 = "reference")) {
            validate78.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "kind" || key0 === "reference")) {
                validate78.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.kind !== void 0) {
                let data0 = data.kind;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate78.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("assertion" !== data0) {
                  validate78.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "assertion" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reference !== void 0) {
                  const _errs4 = errors;
                  if (!validate79(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate79.errors : vErrors.concat(validate79.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate78.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate78.errors = vErrors;
      return errors === 0;
    }
    validate78.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate68(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate68.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.revision === void 0 && (missing0 = "revision") || data.selection === void 0 && (missing0 = "selection")) {
            validate68.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "revision" || key0 === "selection" || key0 === "wire_version")) {
                validate68.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.revision !== void 0) {
                const _errs2 = errors;
                if (!validate69(data.revision, { instancePath: instancePath + "/revision", parentData: data, parentDataProperty: "revision", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate69.errors : vErrors.concat(validate69.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.selection !== void 0) {
                  let data1 = data.selection;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  let valid1 = false;
                  let passing0 = null;
                  const _errs5 = errors;
                  if (!validate73(data1, { instancePath: instancePath + "/selection", parentData: data, parentDataProperty: "selection", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate73.errors : vErrors.concat(validate73.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs5 === errors;
                  if (_valid0) {
                    valid1 = true;
                    passing0 = 0;
                    var props0 = true;
                  }
                  const _errs6 = errors;
                  if (!validate78(data1, { instancePath: instancePath + "/selection", parentData: data, parentDataProperty: "selection", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate78.errors : vErrors.concat(validate78.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs6 === errors;
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
                    const err0 = { instancePath: instancePath + "/selection", schemaPath: "#/properties/selection/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                    validate68.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs4;
                    if (vErrors !== null) {
                      if (_errs4) {
                        vErrors.length = _errs4;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.wire_version !== void 0) {
                    let data2 = data.wire_version;
                    const _errs8 = errors;
                    if (typeof data2 !== "string") {
                      validate68.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("1" !== data2) {
                      validate68.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs8 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate68.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate68.errors = vErrors;
      return errors === 0;
    }
    validate68.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.object_detail = validate83;
    function validate86(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate86.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.graph_id === void 0 && (missing0 = "graph_id")) {
            validate86.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph_id" || key0 === "scope")) {
                validate86.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph_id !== void 0) {
                let data0 = data.graph_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate86.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate86.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate86.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate86.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  let data1 = data.scope;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.tenant_id === void 0 && (missing1 = "tenant_id") || data1.project_id === void 0 && (missing1 = "project_id")) {
                        validate86.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate86.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.project_id !== void 0) {
                            let data2 = data1.project_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate86.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate86.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate86.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate86.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.tenant_id !== void 0) {
                              let data3 = data1.tenant_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate86.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate86.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate86.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate86.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                          }
                        }
                      }
                    } else {
                      validate86.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate86.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate86.errors = vErrors;
      return errors === 0;
    }
    validate86.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate85(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate85.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.entity_id === void 0 && (missing0 = "entity_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate85.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entity_id" || key0 === "graph" || key0 === "revision")) {
                validate85.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entity_id !== void 0) {
                let data0 = data.entity_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate85.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate85.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate85.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate85.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.graph !== void 0) {
                  const _errs4 = errors;
                  if (!validate86(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate86.errors : vErrors.concat(validate86.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    let data2 = data.revision;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate85.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate85.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate85.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate85.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate85.errors = vErrors;
      return errors === 0;
    }
    validate85.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var pattern48 = new RegExp("^[^\\s/]+/[^\\s/]+$", "u");
    function validate90(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate90.evaluated;
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
            validate90.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate90.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func1(data0) > 128) {
                      validate90.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate90.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate90.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate90.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      if (func1(data1) > 128) {
                        validate90.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate90.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern48.test(data1)) {
                            validate90.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate90.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate90.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate90.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                  if (func1(data3) > 128) {
                                    validate90.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate90.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate90.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate90.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    if (!pattern5.test(data4)) {
                                      validate90.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate90.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate90.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate90.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate90.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate90.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate90.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                    if (func1(data7) > 128) {
                                      validate90.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate90.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
                                          validate90.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate90.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      if (func1(data8) > 128) {
                                        validate90.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate90.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
                                            validate90.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate90.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate90.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            if (!pattern5.test(data9)) {
                              validate90.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate90.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate90.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate90.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate90.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate90.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate90.errors = vErrors;
      return errors === 0;
    }
    validate90.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate89(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate89.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.reference === void 0 && (missing0 = "reference") || data.entity_type === void 0 && (missing0 = "entity_type") || data.label === void 0 && (missing0 = "label") || data.context === void 0 && (missing0 = "context") || data.supersedes === void 0 && (missing0 = "supersedes")) {
            validate89.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "context" || key0 === "entity_type" || key0 === "label" || key0 === "reference" || key0 === "supersedes")) {
                validate89.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.context !== void 0) {
                const _errs2 = errors;
                if (!validate90(data.context, { instancePath: instancePath + "/context", parentData: data, parentDataProperty: "context", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate90.errors : vErrors.concat(validate90.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.entity_type !== void 0) {
                  let data1 = data.entity_type;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate89.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate89.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate89.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate89.errors = [{ instancePath: instancePath + "/entity_type", schemaPath: "#/properties/entity_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.label !== void 0) {
                    let data2 = data.label;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 512) {
                          validate89.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/maxLength", keyword: "maxLength", params: { limit: 512 }, message: "must NOT have more than 512 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate89.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          }
                        }
                      } else {
                        validate89.errors = [{ instancePath: instancePath + "/label", schemaPath: "#/properties/label/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.reference !== void 0) {
                      const _errs7 = errors;
                      if (!validate85(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate85.errors : vErrors.concat(validate85.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.supersedes !== void 0) {
                        let data4 = data.supersedes;
                        const _errs8 = errors;
                        const _errs9 = errors;
                        let valid1 = false;
                        const _errs10 = errors;
                        if (!validate85(data4, { instancePath: instancePath + "/supersedes", parentData: data, parentDataProperty: "supersedes", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate85.errors : vErrors.concat(validate85.errors);
                          errors = vErrors.length;
                        }
                        var _valid0 = _errs10 === errors;
                        valid1 = valid1 || _valid0;
                        const _errs11 = errors;
                        if (data4 !== null) {
                          const err0 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        }
                        var _valid0 = _errs11 === errors;
                        valid1 = valid1 || _valid0;
                        if (!valid1) {
                          const err1 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err1];
                          } else {
                            vErrors.push(err1);
                          }
                          errors++;
                          validate89.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs9;
                          if (vErrors !== null) {
                            if (_errs9) {
                              vErrors.length = _errs9;
                            } else {
                              vErrors = null;
                            }
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
          }
        } else {
          validate89.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate89.errors = vErrors;
      return errors === 0;
    }
    validate89.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate84(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate84.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.record === void 0 && (missing0 = "record") || data.is_latest === void 0 && (missing0 = "is_latest") || data.alias_target === void 0 && (missing0 = "alias_target")) {
            validate84.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "alias_target" || key0 === "is_latest" || key0 === "kind" || key0 === "record")) {
                validate84.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.alias_target !== void 0) {
                let data0 = data.alias_target;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate85(data0, { instancePath: instancePath + "/alias_target", parentData: data, parentDataProperty: "alias_target", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate85.errors : vErrors.concat(validate85.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/alias_target", schemaPath: "#/properties/alias_target/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs5 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err1 = { instancePath: instancePath + "/alias_target", schemaPath: "#/properties/alias_target/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate84.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.is_latest !== void 0) {
                  const _errs7 = errors;
                  if (typeof data.is_latest !== "boolean") {
                    validate84.errors = [{ instancePath: instancePath + "/is_latest", schemaPath: "#/properties/is_latest/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                    return false;
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.kind !== void 0) {
                    let data2 = data.kind;
                    const _errs9 = errors;
                    if (typeof data2 !== "string") {
                      validate84.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("entity" !== data2) {
                      validate84.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "entity" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.record !== void 0) {
                      const _errs11 = errors;
                      if (!validate89(data.record, { instancePath: instancePath + "/record", parentData: data, parentDataProperty: "record", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate89.errors : vErrors.concat(validate89.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        } else {
          validate84.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate84.errors = vErrors;
      return errors === 0;
    }
    validate84.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema80 = { "additionalProperties": false, "properties": { "applicability": { "$ref": "#/$defs/ArtifactRef" }, "grounding": { "$ref": "#/$defs/ClaimGrounding" }, "object": { "$ref": "#/$defs/EntityRevisionRef" }, "polarity": { "enum": ["affirmed", "negated"], "title": "Polarity", "type": "string" }, "posture": { "enum": ["reported", "hypothesis", "unresolved"], "title": "Posture", "type": "string" }, "predicate": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Predicate", "type": "string" }, "reference": { "$ref": "#/$defs/AssertionRevisionRef" }, "research_links": { "items": { "$ref": "#/$defs/QuestionEvidenceLink" }, "maxItems": 32, "title": "Research Links", "type": "array" }, "statement": { "maxLength": 4096, "minLength": 1, "title": "Statement", "type": "string" }, "subject": { "$ref": "#/$defs/EntityRevisionRef" }, "supersedes": { "anyOf": [{ "$ref": "#/$defs/AssertionRevisionRef" }, { "type": "null" }] } }, "required": ["reference", "subject", "predicate", "object", "statement", "polarity", "posture", "applicability", "grounding", "research_links", "supersedes"], "title": "DomainAssertion", "type": "object" };
    function validate100(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate100.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.trace_id === void 0 && (missing0 = "trace_id") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate100.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "scope" || key0 === "sha256" || key0 === "trace_id")) {
                validate100.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.scope !== void 0) {
                let data0 = data.scope;
                const _errs2 = errors;
                const _errs3 = errors;
                if (errors === _errs3) {
                  if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                    let missing1;
                    if (data0.tenant_id === void 0 && (missing1 = "tenant_id") || data0.project_id === void 0 && (missing1 = "project_id")) {
                      validate100.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                      return false;
                    } else {
                      const _errs5 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "project_id" || key1 === "tenant_id")) {
                          validate100.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                          return false;
                          break;
                        }
                      }
                      if (_errs5 === errors) {
                        if (data0.project_id !== void 0) {
                          let data1 = data0.project_id;
                          const _errs6 = errors;
                          if (errors === _errs6) {
                            if (typeof data1 === "string") {
                              if (func1(data1) > 128) {
                                validate100.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                return false;
                              } else {
                                if (func1(data1) < 1) {
                                  validate100.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                } else {
                                  if (!pattern4.test(data1)) {
                                    validate100.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                    return false;
                                  }
                                }
                              }
                            } else {
                              validate100.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid2 = _errs6 === errors;
                        } else {
                          var valid2 = true;
                        }
                        if (valid2) {
                          if (data0.tenant_id !== void 0) {
                            let data2 = data0.tenant_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate100.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate100.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate100.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate100.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                        }
                      }
                    }
                  } else {
                    validate100.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.sha256 !== void 0) {
                  let data3 = data.sha256;
                  const _errs10 = errors;
                  if (errors === _errs10) {
                    if (typeof data3 === "string") {
                      if (!pattern5.test(data3)) {
                        validate100.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate100.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.trace_id !== void 0) {
                    let data4 = data.trace_id;
                    const _errs12 = errors;
                    if (errors === _errs12) {
                      if (typeof data4 === "string") {
                        if (func1(data4) > 128) {
                          validate100.errors = [{ instancePath: instancePath + "/trace_id", schemaPath: "#/properties/trace_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func1(data4) < 1) {
                            validate100.errors = [{ instancePath: instancePath + "/trace_id", schemaPath: "#/properties/trace_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern4.test(data4)) {
                              validate100.errors = [{ instancePath: instancePath + "/trace_id", schemaPath: "#/properties/trace_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate100.errors = [{ instancePath: instancePath + "/trace_id", schemaPath: "#/properties/trace_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate100.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate100.errors = vErrors;
      return errors === 0;
    }
    validate100.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate104(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate104.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.source_id === void 0 && (missing0 = "source_id") || data.revision_id === void 0 && (missing0 = "revision_id") || data.raw === void 0 && (missing0 = "raw")) {
            validate104.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "raw" || key0 === "revision_id" || key0 === "scope" || key0 === "source_id")) {
                validate104.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.raw !== void 0) {
                const _errs2 = errors;
                if (!validate90(data.raw, { instancePath: instancePath + "/raw", parentData: data, parentDataProperty: "raw", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate90.errors : vErrors.concat(validate90.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision_id !== void 0) {
                  let data1 = data.revision_id;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate104.errors = [{ instancePath: instancePath + "/revision_id", schemaPath: "#/properties/revision_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate104.errors = [{ instancePath: instancePath + "/revision_id", schemaPath: "#/properties/revision_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate104.errors = [{ instancePath: instancePath + "/revision_id", schemaPath: "#/properties/revision_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate104.errors = [{ instancePath: instancePath + "/revision_id", schemaPath: "#/properties/revision_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.scope !== void 0) {
                    let data2 = data.scope;
                    const _errs5 = errors;
                    const _errs6 = errors;
                    if (errors === _errs6) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.tenant_id === void 0 && (missing1 = "tenant_id") || data2.project_id === void 0 && (missing1 = "project_id")) {
                          validate104.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs8 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate104.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs8 === errors) {
                            if (data2.project_id !== void 0) {
                              let data3 = data2.project_id;
                              const _errs9 = errors;
                              if (errors === _errs9) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate104.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate104.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate104.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate104.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs9 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data2.tenant_id !== void 0) {
                                let data4 = data2.tenant_id;
                                const _errs11 = errors;
                                if (errors === _errs11) {
                                  if (typeof data4 === "string") {
                                    if (func1(data4) > 128) {
                                      validate104.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate104.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate104.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate104.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid2 = _errs11 === errors;
                              } else {
                                var valid2 = true;
                              }
                            }
                          }
                        }
                      } else {
                        validate104.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.source_id !== void 0) {
                      let data5 = data.source_id;
                      const _errs13 = errors;
                      if (errors === _errs13) {
                        if (typeof data5 === "string") {
                          if (func1(data5) > 128) {
                            validate104.errors = [{ instancePath: instancePath + "/source_id", schemaPath: "#/properties/source_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data5) < 1) {
                              validate104.errors = [{ instancePath: instancePath + "/source_id", schemaPath: "#/properties/source_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern4.test(data5)) {
                                validate104.errors = [{ instancePath: instancePath + "/source_id", schemaPath: "#/properties/source_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate104.errors = [{ instancePath: instancePath + "/source_id", schemaPath: "#/properties/source_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs13 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        } else {
          validate104.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate104.errors = vErrors;
      return errors === 0;
    }
    validate104.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate103(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate103.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.source === void 0 && (missing0 = "source") || data.unit === void 0 && (missing0 = "unit") || data.start === void 0 && (missing0 = "start") || data.end === void 0 && (missing0 = "end") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate103.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "end" || key0 === "sha256" || key0 === "source" || key0 === "start" || key0 === "unit")) {
                validate103.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.end !== void 0) {
                let data0 = data.end;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate103.errors = [{ instancePath: instancePath + "/end", schemaPath: "#/properties/end/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate103.errors = [{ instancePath: instancePath + "/end", schemaPath: "#/properties/end/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate103.errors = [{ instancePath: instancePath + "/end", schemaPath: "#/properties/end/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                        return false;
                      }
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.sha256 !== void 0) {
                  let data1 = data.sha256;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (!pattern5.test(data1)) {
                        validate103.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate103.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.source !== void 0) {
                    const _errs6 = errors;
                    if (!validate104(data.source, { instancePath: instancePath + "/source", parentData: data, parentDataProperty: "source", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate104.errors : vErrors.concat(validate104.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.start !== void 0) {
                      let data3 = data.start;
                      const _errs7 = errors;
                      if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                        validate103.errors = [{ instancePath: instancePath + "/start", schemaPath: "#/properties/start/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      if (errors === _errs7) {
                        if (typeof data3 == "number" && isFinite(data3)) {
                          if (data3 > 9007199254740991 || isNaN(data3)) {
                            validate103.errors = [{ instancePath: instancePath + "/start", schemaPath: "#/properties/start/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                            return false;
                          } else {
                            if (data3 < 0 || isNaN(data3)) {
                              validate103.errors = [{ instancePath: instancePath + "/start", schemaPath: "#/properties/start/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                              return false;
                            }
                          }
                        }
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.unit !== void 0) {
                        let data4 = data.unit;
                        const _errs9 = errors;
                        if (typeof data4 !== "string") {
                          validate103.errors = [{ instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("byte" !== data4) {
                          validate103.errors = [{ instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/const", keyword: "const", params: { allowedValue: "byte" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs9 === errors;
                      } else {
                        var valid0 = true;
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate103.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate103.errors = vErrors;
      return errors === 0;
    }
    validate103.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate99(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate99.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.spans === void 0 && (missing0 = "spans") || data.conversion_traces === void 0 && (missing0 = "conversion_traces") || data.interpretation_artifacts === void 0 && (missing0 = "interpretation_artifacts")) {
            validate99.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "conversion_traces" || key0 === "interpretation_artifacts" || key0 === "spans")) {
                validate99.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.conversion_traces !== void 0) {
                let data0 = data.conversion_traces;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 64) {
                      validate99.errors = [{ instancePath: instancePath + "/conversion_traces", schemaPath: "#/properties/conversion_traces/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                      return false;
                    } else {
                      if (data0.length < 1) {
                        validate99.errors = [{ instancePath: instancePath + "/conversion_traces", schemaPath: "#/properties/conversion_traces/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                        return false;
                      } else {
                        var valid1 = true;
                        const len0 = data0.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs4 = errors;
                          if (!validate100(data0[i0], { instancePath: instancePath + "/conversion_traces/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate100.errors : vErrors.concat(validate100.errors);
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
                    validate99.errors = [{ instancePath: instancePath + "/conversion_traces", schemaPath: "#/properties/conversion_traces/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.interpretation_artifacts !== void 0) {
                  let data2 = data.interpretation_artifacts;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (Array.isArray(data2)) {
                      if (data2.length > 16) {
                        validate99.errors = [{ instancePath: instancePath + "/interpretation_artifacts", schemaPath: "#/properties/interpretation_artifacts/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                        return false;
                      } else {
                        var valid2 = true;
                        const len1 = data2.length;
                        for (let i1 = 0; i1 < len1; i1++) {
                          const _errs7 = errors;
                          if (!validate90(data2[i1], { instancePath: instancePath + "/interpretation_artifacts/" + i1, parentData: data2, parentDataProperty: i1, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate90.errors : vErrors.concat(validate90.errors);
                            errors = vErrors.length;
                          }
                          var valid2 = _errs7 === errors;
                          if (!valid2) {
                            break;
                          }
                        }
                      }
                    } else {
                      validate99.errors = [{ instancePath: instancePath + "/interpretation_artifacts", schemaPath: "#/properties/interpretation_artifacts/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.spans !== void 0) {
                    let data4 = data.spans;
                    const _errs8 = errors;
                    if (errors === _errs8) {
                      if (Array.isArray(data4)) {
                        if (data4.length > 64) {
                          validate99.errors = [{ instancePath: instancePath + "/spans", schemaPath: "#/properties/spans/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                          return false;
                        } else {
                          if (data4.length < 1) {
                            validate99.errors = [{ instancePath: instancePath + "/spans", schemaPath: "#/properties/spans/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                            return false;
                          } else {
                            var valid3 = true;
                            const len2 = data4.length;
                            for (let i2 = 0; i2 < len2; i2++) {
                              const _errs10 = errors;
                              if (!validate103(data4[i2], { instancePath: instancePath + "/spans/" + i2, parentData: data4, parentDataProperty: i2, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate103.errors : vErrors.concat(validate103.errors);
                                errors = vErrors.length;
                              }
                              var valid3 = _errs10 === errors;
                              if (!valid3) {
                                break;
                              }
                            }
                          }
                        }
                      } else {
                        validate99.errors = [{ instancePath: instancePath + "/spans", schemaPath: "#/properties/spans/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
        } else {
          validate99.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate99.errors = vErrors;
      return errors === 0;
    }
    validate99.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate110(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate110.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.assertion_id === void 0 && (missing0 = "assertion_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate110.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "assertion_id" || key0 === "graph" || key0 === "revision")) {
                validate110.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assertion_id !== void 0) {
                let data0 = data.assertion_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate110.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate110.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate110.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate110.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.graph !== void 0) {
                  const _errs4 = errors;
                  if (!validate86(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate86.errors : vErrors.concat(validate86.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    let data2 = data.revision;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate110.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate110.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate110.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate110.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate110.errors = vErrors;
      return errors === 0;
    }
    validate110.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema88 = { "additionalProperties": false, "properties": { "answer_proposal": { "anyOf": [{ "$ref": "#/$defs/ArtifactRef" }, { "type": "null" }] }, "need": { "anyOf": [{ "$ref": "#/$defs/EvidenceNeedRef" }, { "type": "null" }] }, "question": { "$ref": "#/$defs/ResearchQuestionRef" }, "role": { "enum": ["proposed_answer", "support", "contradiction", "context"], "title": "Role", "type": "string" }, "validation_method": { "anyOf": [{ "$ref": "#/$defs/SchemaRef" }, { "type": "null" }] } }, "required": ["question", "need", "role", "answer_proposal", "validation_method"], "title": "QuestionEvidenceLink", "type": "object" };
    function validate115(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate115.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.need_id === void 0 && (missing0 = "need_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate115.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "need_id" || key0 === "revision" || key0 === "scope")) {
                validate115.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.need_id !== void 0) {
                let data0 = data.need_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate115.errors = [{ instancePath: instancePath + "/need_id", schemaPath: "#/properties/need_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate115.errors = [{ instancePath: instancePath + "/need_id", schemaPath: "#/properties/need_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate115.errors = [{ instancePath: instancePath + "/need_id", schemaPath: "#/properties/need_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate115.errors = [{ instancePath: instancePath + "/need_id", schemaPath: "#/properties/need_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs4 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate115.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate115.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate115.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.scope !== void 0) {
                    let data2 = data.scope;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.tenant_id === void 0 && (missing1 = "tenant_id") || data2.project_id === void 0 && (missing1 = "project_id")) {
                          validate115.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate115.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs9 === errors) {
                            if (data2.project_id !== void 0) {
                              let data3 = data2.project_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate115.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate115.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate115.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate115.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data2.tenant_id !== void 0) {
                                let data4 = data2.tenant_id;
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data4 === "string") {
                                    if (func1(data4) > 128) {
                                      validate115.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate115.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate115.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate115.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
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
                        validate115.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate115.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate115.errors = vErrors;
      return errors === 0;
    }
    validate115.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate117(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate117.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.question_id === void 0 && (missing0 = "question_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate117.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "question_id" || key0 === "revision" || key0 === "scope")) {
                validate117.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.question_id !== void 0) {
                let data0 = data.question_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate117.errors = [{ instancePath: instancePath + "/question_id", schemaPath: "#/properties/question_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate117.errors = [{ instancePath: instancePath + "/question_id", schemaPath: "#/properties/question_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate117.errors = [{ instancePath: instancePath + "/question_id", schemaPath: "#/properties/question_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate117.errors = [{ instancePath: instancePath + "/question_id", schemaPath: "#/properties/question_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs4 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate117.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate117.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate117.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.scope !== void 0) {
                    let data2 = data.scope;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.tenant_id === void 0 && (missing1 = "tenant_id") || data2.project_id === void 0 && (missing1 = "project_id")) {
                          validate117.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate117.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs9 === errors) {
                            if (data2.project_id !== void 0) {
                              let data3 = data2.project_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate117.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate117.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate117.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate117.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data2.tenant_id !== void 0) {
                                let data4 = data2.tenant_id;
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data4 === "string") {
                                    if (func1(data4) > 128) {
                                      validate117.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate117.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate117.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate117.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
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
                        validate117.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate117.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate117.errors = vErrors;
      return errors === 0;
    }
    validate117.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate113(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate113.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.question === void 0 && (missing0 = "question") || data.need === void 0 && (missing0 = "need") || data.role === void 0 && (missing0 = "role") || data.answer_proposal === void 0 && (missing0 = "answer_proposal") || data.validation_method === void 0 && (missing0 = "validation_method")) {
            validate113.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "answer_proposal" || key0 === "need" || key0 === "question" || key0 === "role" || key0 === "validation_method")) {
                validate113.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.answer_proposal !== void 0) {
                let data0 = data.answer_proposal;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate90(data0, { instancePath: instancePath + "/answer_proposal", parentData: data, parentDataProperty: "answer_proposal", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate90.errors : vErrors.concat(validate90.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/answer_proposal", schemaPath: "#/properties/answer_proposal/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                }
                var _valid0 = _errs5 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err1 = { instancePath: instancePath + "/answer_proposal", schemaPath: "#/properties/answer_proposal/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate113.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.need !== void 0) {
                  let data1 = data.need;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid2 = false;
                  const _errs9 = errors;
                  if (!validate115(data1, { instancePath: instancePath + "/need", parentData: data, parentDataProperty: "need", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate115.errors : vErrors.concat(validate115.errors);
                    errors = vErrors.length;
                  }
                  var _valid1 = _errs9 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs10 = errors;
                  if (data1 !== null) {
                    const err2 = { instancePath: instancePath + "/need", schemaPath: "#/properties/need/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                  }
                  var _valid1 = _errs10 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err3 = { instancePath: instancePath + "/need", schemaPath: "#/properties/need/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                    validate113.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs8;
                    if (vErrors !== null) {
                      if (_errs8) {
                        vErrors.length = _errs8;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.question !== void 0) {
                    const _errs12 = errors;
                    if (!validate117(data.question, { instancePath: instancePath + "/question", parentData: data, parentDataProperty: "question", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate117.errors : vErrors.concat(validate117.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.role !== void 0) {
                      let data3 = data.role;
                      const _errs13 = errors;
                      if (typeof data3 !== "string") {
                        validate113.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if (!(data3 === "proposed_answer" || data3 === "support" || data3 === "contradiction" || data3 === "context")) {
                        validate113.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/enum", keyword: "enum", params: { allowedValues: schema88.properties.role.enum }, message: "must be equal to one of the allowed values" }];
                        return false;
                      }
                      var valid0 = _errs13 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.validation_method !== void 0) {
                        let data4 = data.validation_method;
                        const _errs15 = errors;
                        const _errs16 = errors;
                        let valid3 = false;
                        const _errs17 = errors;
                        const _errs18 = errors;
                        if (errors === _errs18) {
                          if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                            let missing1;
                            if (data4.schema_id === void 0 && (missing1 = "schema_id") || data4.version === void 0 && (missing1 = "version") || data4.sha256 === void 0 && (missing1 = "sha256")) {
                              const err4 = { instancePath: instancePath + "/validation_method", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                              if (vErrors === null) {
                                vErrors = [err4];
                              } else {
                                vErrors.push(err4);
                              }
                              errors++;
                            } else {
                              const _errs20 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                                  const err5 = { instancePath: instancePath + "/validation_method", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                  if (vErrors === null) {
                                    vErrors = [err5];
                                  } else {
                                    vErrors.push(err5);
                                  }
                                  errors++;
                                  break;
                                }
                              }
                              if (_errs20 === errors) {
                                if (data4.schema_id !== void 0) {
                                  let data5 = data4.schema_id;
                                  const _errs21 = errors;
                                  if (errors === _errs21) {
                                    if (typeof data5 === "string") {
                                      if (func1(data5) > 128) {
                                        const err6 = { instancePath: instancePath + "/validation_method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err6];
                                        } else {
                                          vErrors.push(err6);
                                        }
                                        errors++;
                                      } else {
                                        if (func1(data5) < 1) {
                                          const err7 = { instancePath: instancePath + "/validation_method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err7];
                                          } else {
                                            vErrors.push(err7);
                                          }
                                          errors++;
                                        } else {
                                          if (!pattern4.test(data5)) {
                                            const err8 = { instancePath: instancePath + "/validation_method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                            if (vErrors === null) {
                                              vErrors = [err8];
                                            } else {
                                              vErrors.push(err8);
                                            }
                                            errors++;
                                          }
                                        }
                                      }
                                    } else {
                                      const err9 = { instancePath: instancePath + "/validation_method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err9];
                                      } else {
                                        vErrors.push(err9);
                                      }
                                      errors++;
                                    }
                                  }
                                  var valid5 = _errs21 === errors;
                                } else {
                                  var valid5 = true;
                                }
                                if (valid5) {
                                  if (data4.sha256 !== void 0) {
                                    let data6 = data4.sha256;
                                    const _errs23 = errors;
                                    if (errors === _errs23) {
                                      if (typeof data6 === "string") {
                                        if (!pattern5.test(data6)) {
                                          const err10 = { instancePath: instancePath + "/validation_method/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                          if (vErrors === null) {
                                            vErrors = [err10];
                                          } else {
                                            vErrors.push(err10);
                                          }
                                          errors++;
                                        }
                                      } else {
                                        const err11 = { instancePath: instancePath + "/validation_method/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err11];
                                        } else {
                                          vErrors.push(err11);
                                        }
                                        errors++;
                                      }
                                    }
                                    var valid5 = _errs23 === errors;
                                  } else {
                                    var valid5 = true;
                                  }
                                  if (valid5) {
                                    if (data4.version !== void 0) {
                                      let data7 = data4.version;
                                      const _errs25 = errors;
                                      if (typeof data7 !== "string") {
                                        const err12 = { instancePath: instancePath + "/validation_method/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err12];
                                        } else {
                                          vErrors.push(err12);
                                        }
                                        errors++;
                                      }
                                      if ("1" !== data7) {
                                        const err13 = { instancePath: instancePath + "/validation_method/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" };
                                        if (vErrors === null) {
                                          vErrors = [err13];
                                        } else {
                                          vErrors.push(err13);
                                        }
                                        errors++;
                                      }
                                      var valid5 = _errs25 === errors;
                                    } else {
                                      var valid5 = true;
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            const err14 = { instancePath: instancePath + "/validation_method", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err14];
                            } else {
                              vErrors.push(err14);
                            }
                            errors++;
                          }
                        }
                        var _valid2 = _errs17 === errors;
                        valid3 = valid3 || _valid2;
                        const _errs27 = errors;
                        if (data4 !== null) {
                          const err15 = { instancePath: instancePath + "/validation_method", schemaPath: "#/properties/validation_method/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err15];
                          } else {
                            vErrors.push(err15);
                          }
                          errors++;
                        }
                        var _valid2 = _errs27 === errors;
                        valid3 = valid3 || _valid2;
                        if (!valid3) {
                          const err16 = { instancePath: instancePath + "/validation_method", schemaPath: "#/properties/validation_method/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err16];
                          } else {
                            vErrors.push(err16);
                          }
                          errors++;
                          validate113.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs16;
                          if (vErrors !== null) {
                            if (_errs16) {
                              vErrors.length = _errs16;
                            } else {
                              vErrors = null;
                            }
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
        } else {
          validate113.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate113.errors = vErrors;
      return errors === 0;
    }
    validate113.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate97(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate97.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.reference === void 0 && (missing0 = "reference") || data.subject === void 0 && (missing0 = "subject") || data.predicate === void 0 && (missing0 = "predicate") || data.object === void 0 && (missing0 = "object") || data.statement === void 0 && (missing0 = "statement") || data.polarity === void 0 && (missing0 = "polarity") || data.posture === void 0 && (missing0 = "posture") || data.applicability === void 0 && (missing0 = "applicability") || data.grounding === void 0 && (missing0 = "grounding") || data.research_links === void 0 && (missing0 = "research_links") || data.supersedes === void 0 && (missing0 = "supersedes")) {
            validate97.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func33.call(schema80.properties, key0)) {
                validate97.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.applicability !== void 0) {
                const _errs2 = errors;
                if (!validate90(data.applicability, { instancePath: instancePath + "/applicability", parentData: data, parentDataProperty: "applicability", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate90.errors : vErrors.concat(validate90.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.grounding !== void 0) {
                  const _errs3 = errors;
                  if (!validate99(data.grounding, { instancePath: instancePath + "/grounding", parentData: data, parentDataProperty: "grounding", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate99.errors : vErrors.concat(validate99.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.object !== void 0) {
                    const _errs4 = errors;
                    if (!validate85(data.object, { instancePath: instancePath + "/object", parentData: data, parentDataProperty: "object", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate85.errors : vErrors.concat(validate85.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs4 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.polarity !== void 0) {
                      let data3 = data.polarity;
                      const _errs5 = errors;
                      if (typeof data3 !== "string") {
                        validate97.errors = [{ instancePath: instancePath + "/polarity", schemaPath: "#/properties/polarity/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if (!(data3 === "affirmed" || data3 === "negated")) {
                        validate97.errors = [{ instancePath: instancePath + "/polarity", schemaPath: "#/properties/polarity/enum", keyword: "enum", params: { allowedValues: schema80.properties.polarity.enum }, message: "must be equal to one of the allowed values" }];
                        return false;
                      }
                      var valid0 = _errs5 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.posture !== void 0) {
                        let data4 = data.posture;
                        const _errs7 = errors;
                        if (typeof data4 !== "string") {
                          validate97.errors = [{ instancePath: instancePath + "/posture", schemaPath: "#/properties/posture/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if (!(data4 === "reported" || data4 === "hypothesis" || data4 === "unresolved")) {
                          validate97.errors = [{ instancePath: instancePath + "/posture", schemaPath: "#/properties/posture/enum", keyword: "enum", params: { allowedValues: schema80.properties.posture.enum }, message: "must be equal to one of the allowed values" }];
                          return false;
                        }
                        var valid0 = _errs7 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.predicate !== void 0) {
                          let data5 = data.predicate;
                          const _errs9 = errors;
                          if (errors === _errs9) {
                            if (typeof data5 === "string") {
                              if (func1(data5) > 128) {
                                validate97.errors = [{ instancePath: instancePath + "/predicate", schemaPath: "#/properties/predicate/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                return false;
                              } else {
                                if (func1(data5) < 1) {
                                  validate97.errors = [{ instancePath: instancePath + "/predicate", schemaPath: "#/properties/predicate/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                } else {
                                  if (!pattern4.test(data5)) {
                                    validate97.errors = [{ instancePath: instancePath + "/predicate", schemaPath: "#/properties/predicate/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                    return false;
                                  }
                                }
                              }
                            } else {
                              validate97.errors = [{ instancePath: instancePath + "/predicate", schemaPath: "#/properties/predicate/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid0 = _errs9 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.reference !== void 0) {
                            const _errs11 = errors;
                            if (!validate110(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate110.errors : vErrors.concat(validate110.errors);
                              errors = vErrors.length;
                            }
                            var valid0 = _errs11 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.research_links !== void 0) {
                              let data7 = data.research_links;
                              const _errs12 = errors;
                              if (errors === _errs12) {
                                if (Array.isArray(data7)) {
                                  if (data7.length > 32) {
                                    validate97.errors = [{ instancePath: instancePath + "/research_links", schemaPath: "#/properties/research_links/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                                    return false;
                                  } else {
                                    var valid1 = true;
                                    const len0 = data7.length;
                                    for (let i0 = 0; i0 < len0; i0++) {
                                      const _errs14 = errors;
                                      if (!validate113(data7[i0], { instancePath: instancePath + "/research_links/" + i0, parentData: data7, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                        vErrors = vErrors === null ? validate113.errors : vErrors.concat(validate113.errors);
                                        errors = vErrors.length;
                                      }
                                      var valid1 = _errs14 === errors;
                                      if (!valid1) {
                                        break;
                                      }
                                    }
                                  }
                                } else {
                                  validate97.errors = [{ instancePath: instancePath + "/research_links", schemaPath: "#/properties/research_links/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs12 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.statement !== void 0) {
                                let data9 = data.statement;
                                const _errs15 = errors;
                                if (errors === _errs15) {
                                  if (typeof data9 === "string") {
                                    if (func1(data9) > 4096) {
                                      validate97.errors = [{ instancePath: instancePath + "/statement", schemaPath: "#/properties/statement/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data9) < 1) {
                                        validate97.errors = [{ instancePath: instancePath + "/statement", schemaPath: "#/properties/statement/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      }
                                    }
                                  } else {
                                    validate97.errors = [{ instancePath: instancePath + "/statement", schemaPath: "#/properties/statement/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs15 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.subject !== void 0) {
                                  const _errs17 = errors;
                                  if (!validate85(data.subject, { instancePath: instancePath + "/subject", parentData: data, parentDataProperty: "subject", rootData, dynamicAnchors })) {
                                    vErrors = vErrors === null ? validate85.errors : vErrors.concat(validate85.errors);
                                    errors = vErrors.length;
                                  }
                                  var valid0 = _errs17 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.supersedes !== void 0) {
                                    let data11 = data.supersedes;
                                    const _errs18 = errors;
                                    const _errs19 = errors;
                                    let valid2 = false;
                                    const _errs20 = errors;
                                    if (!validate110(data11, { instancePath: instancePath + "/supersedes", parentData: data, parentDataProperty: "supersedes", rootData, dynamicAnchors })) {
                                      vErrors = vErrors === null ? validate110.errors : vErrors.concat(validate110.errors);
                                      errors = vErrors.length;
                                    }
                                    var _valid0 = _errs20 === errors;
                                    valid2 = valid2 || _valid0;
                                    const _errs21 = errors;
                                    if (data11 !== null) {
                                      const err0 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                      if (vErrors === null) {
                                        vErrors = [err0];
                                      } else {
                                        vErrors.push(err0);
                                      }
                                      errors++;
                                    }
                                    var _valid0 = _errs21 === errors;
                                    valid2 = valid2 || _valid0;
                                    if (!valid2) {
                                      const err1 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                      if (vErrors === null) {
                                        vErrors = [err1];
                                      } else {
                                        vErrors.push(err1);
                                      }
                                      errors++;
                                      validate97.errors = vErrors;
                                      return false;
                                    } else {
                                      errors = _errs19;
                                      if (vErrors !== null) {
                                        if (_errs19) {
                                          vErrors.length = _errs19;
                                        } else {
                                          vErrors = null;
                                        }
                                      }
                                    }
                                    var valid0 = _errs18 === errors;
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
          validate97.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate97.errors = vErrors;
      return errors === 0;
    }
    validate97.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate96(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate96.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.record === void 0 && (missing0 = "record") || data.is_latest === void 0 && (missing0 = "is_latest") || data.retracted === void 0 && (missing0 = "retracted")) {
            validate96.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "is_latest" || key0 === "kind" || key0 === "record" || key0 === "retracted")) {
                validate96.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.is_latest !== void 0) {
                const _errs2 = errors;
                if (typeof data.is_latest !== "boolean") {
                  validate96.errors = [{ instancePath: instancePath + "/is_latest", schemaPath: "#/properties/is_latest/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.kind !== void 0) {
                  let data1 = data.kind;
                  const _errs4 = errors;
                  if (typeof data1 !== "string") {
                    validate96.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("assertion" !== data1) {
                    validate96.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "assertion" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.record !== void 0) {
                    const _errs6 = errors;
                    if (!validate97(data.record, { instancePath: instancePath + "/record", parentData: data, parentDataProperty: "record", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate97.errors : vErrors.concat(validate97.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.retracted !== void 0) {
                      const _errs7 = errors;
                      if (typeof data.retracted !== "boolean") {
                        validate96.errors = [{ instancePath: instancePath + "/retracted", schemaPath: "#/properties/retracted/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
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
          }
        } else {
          validate96.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate96.errors = vErrors;
      return errors === 0;
    }
    validate96.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate125(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate125.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.revision === void 0 && (missing0 = "revision") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate125.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph" || key0 === "revision" || key0 === "sha256")) {
                validate125.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph !== void 0) {
                const _errs2 = errors;
                if (!validate86(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate86.errors : vErrors.concat(validate86.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate125.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate125.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate125.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sha256 !== void 0) {
                    let data2 = data.sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern5.test(data2)) {
                          validate125.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate125.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate125.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate125.errors = vErrors;
      return errors === 0;
    }
    validate125.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate128(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate128.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.reference === void 0 && (missing0 = "reference")) {
            validate128.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "kind" || key0 === "reference")) {
                validate128.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.kind !== void 0) {
                let data0 = data.kind;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate128.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("entity" !== data0) {
                  validate128.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "entity" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reference !== void 0) {
                  const _errs4 = errors;
                  if (!validate85(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate85.errors : vErrors.concat(validate85.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate128.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate128.errors = vErrors;
      return errors === 0;
    }
    validate128.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate131(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate131.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.reference === void 0 && (missing0 = "reference")) {
            validate131.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "kind" || key0 === "reference")) {
                validate131.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.kind !== void 0) {
                let data0 = data.kind;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate131.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("assertion" !== data0) {
                  validate131.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "assertion" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reference !== void 0) {
                  const _errs4 = errors;
                  if (!validate110(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate110.errors : vErrors.concat(validate110.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate131.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate131.errors = vErrors;
      return errors === 0;
    }
    validate131.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate124(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate124.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.revision === void 0 && (missing0 = "revision") || data.selection === void 0 && (missing0 = "selection")) {
            validate124.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "revision" || key0 === "selection" || key0 === "wire_version")) {
                validate124.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.revision !== void 0) {
                const _errs2 = errors;
                if (!validate125(data.revision, { instancePath: instancePath + "/revision", parentData: data, parentDataProperty: "revision", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate125.errors : vErrors.concat(validate125.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.selection !== void 0) {
                  let data1 = data.selection;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  let valid1 = false;
                  let passing0 = null;
                  const _errs5 = errors;
                  if (!validate128(data1, { instancePath: instancePath + "/selection", parentData: data, parentDataProperty: "selection", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate128.errors : vErrors.concat(validate128.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs5 === errors;
                  if (_valid0) {
                    valid1 = true;
                    passing0 = 0;
                    var props0 = true;
                  }
                  const _errs6 = errors;
                  if (!validate131(data1, { instancePath: instancePath + "/selection", parentData: data, parentDataProperty: "selection", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate131.errors : vErrors.concat(validate131.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs6 === errors;
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
                    const err0 = { instancePath: instancePath + "/selection", schemaPath: "#/properties/selection/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                    validate124.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs4;
                    if (vErrors !== null) {
                      if (_errs4) {
                        vErrors.length = _errs4;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.wire_version !== void 0) {
                    let data2 = data.wire_version;
                    const _errs8 = errors;
                    if (typeof data2 !== "string") {
                      validate124.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("1" !== data2) {
                      validate124.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs8 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate124.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate124.errors = vErrors;
      return errors === 0;
    }
    validate124.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate83(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate83.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.request === void 0 && (missing0 = "request") || data.detail === void 0 && (missing0 = "detail")) {
            validate83.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "detail" || key0 === "request" || key0 === "wire_version")) {
                validate83.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.detail !== void 0) {
                let data0 = data.detail;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                let passing0 = null;
                const _errs4 = errors;
                if (!validate84(data0, { instancePath: instancePath + "/detail", parentData: data, parentDataProperty: "detail", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate84.errors : vErrors.concat(validate84.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                if (_valid0) {
                  valid1 = true;
                  passing0 = 0;
                  var props0 = true;
                }
                const _errs5 = errors;
                if (!validate96(data0, { instancePath: instancePath + "/detail", parentData: data, parentDataProperty: "detail", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate96.errors : vErrors.concat(validate96.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs5 === errors;
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
                  const err0 = { instancePath: instancePath + "/detail", schemaPath: "#/properties/detail/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                  if (vErrors === null) {
                    vErrors = [err0];
                  } else {
                    vErrors.push(err0);
                  }
                  errors++;
                  validate83.errors = vErrors;
                  return false;
                } else {
                  errors = _errs3;
                  if (vErrors !== null) {
                    if (_errs3) {
                      vErrors.length = _errs3;
                    } else {
                      vErrors = null;
                    }
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.request !== void 0) {
                  const _errs7 = errors;
                  if (!validate124(data.request, { instancePath: instancePath + "/request", parentData: data, parentDataProperty: "request", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate124.errors : vErrors.concat(validate124.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.wire_version !== void 0) {
                    let data2 = data.wire_version;
                    const _errs8 = errors;
                    if (typeof data2 !== "string") {
                      validate83.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("1" !== data2) {
                      validate83.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs8 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate83.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate83.errors = vErrors;
      return errors === 0;
    }
    validate83.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.catalog = validate135;
    function validate137(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate137.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.graph_id === void 0 && (missing0 = "graph_id")) {
            validate137.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph_id" || key0 === "scope")) {
                validate137.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph_id !== void 0) {
                let data0 = data.graph_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate137.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate137.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate137.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate137.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.scope !== void 0) {
                  let data1 = data.scope;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.tenant_id === void 0 && (missing1 = "tenant_id") || data1.project_id === void 0 && (missing1 = "project_id")) {
                        validate137.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate137.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.project_id !== void 0) {
                            let data2 = data1.project_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate137.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate137.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate137.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate137.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.tenant_id !== void 0) {
                              let data3 = data1.tenant_id;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate137.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate137.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate137.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate137.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                          }
                        }
                      }
                    } else {
                      validate137.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate137.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate137.errors = vErrors;
      return errors === 0;
    }
    validate137.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate136(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate136.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.graph === void 0 && (missing0 = "graph") || data.revision === void 0 && (missing0 = "revision") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate136.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph" || key0 === "revision" || key0 === "sha256")) {
                validate136.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph !== void 0) {
                const _errs2 = errors;
                if (!validate137(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate137.errors : vErrors.concat(validate137.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate136.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate136.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate136.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sha256 !== void 0) {
                    let data2 = data.sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern5.test(data2)) {
                          validate136.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate136.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate136.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate136.errors = vErrors;
      return errors === 0;
    }
    validate136.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema103 = { "additionalProperties": false, "properties": { "result_schema": { "$ref": "#/$defs/SchemaRef" }, "version": { "const": "1", "title": "Version", "type": "string" }, "view_id": { "enum": ["entity_search", "neighborhood", "object_detail"], "title": "View Id", "type": "string" } }, "required": ["view_id", "version", "result_schema"], "title": "GraphExploreCapability", "type": "object" };
    function validate140(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate140.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.view_id === void 0 && (missing0 = "view_id") || data.version === void 0 && (missing0 = "version") || data.result_schema === void 0 && (missing0 = "result_schema")) {
            validate140.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "result_schema" || key0 === "version" || key0 === "view_id")) {
                validate140.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.result_schema !== void 0) {
                let data0 = data.result_schema;
                const _errs2 = errors;
                const _errs3 = errors;
                if (errors === _errs3) {
                  if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                    let missing1;
                    if (data0.schema_id === void 0 && (missing1 = "schema_id") || data0.version === void 0 && (missing1 = "version") || data0.sha256 === void 0 && (missing1 = "sha256")) {
                      validate140.errors = [{ instancePath: instancePath + "/result_schema", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                      return false;
                    } else {
                      const _errs5 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                          validate140.errors = [{ instancePath: instancePath + "/result_schema", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                          return false;
                          break;
                        }
                      }
                      if (_errs5 === errors) {
                        if (data0.schema_id !== void 0) {
                          let data1 = data0.schema_id;
                          const _errs6 = errors;
                          if (errors === _errs6) {
                            if (typeof data1 === "string") {
                              if (func1(data1) > 128) {
                                validate140.errors = [{ instancePath: instancePath + "/result_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                return false;
                              } else {
                                if (func1(data1) < 1) {
                                  validate140.errors = [{ instancePath: instancePath + "/result_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                } else {
                                  if (!pattern4.test(data1)) {
                                    validate140.errors = [{ instancePath: instancePath + "/result_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                    return false;
                                  }
                                }
                              }
                            } else {
                              validate140.errors = [{ instancePath: instancePath + "/result_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid2 = _errs6 === errors;
                        } else {
                          var valid2 = true;
                        }
                        if (valid2) {
                          if (data0.sha256 !== void 0) {
                            let data2 = data0.sha256;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (!pattern5.test(data2)) {
                                  validate140.errors = [{ instancePath: instancePath + "/result_schema/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate140.errors = [{ instancePath: instancePath + "/result_schema/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data0.version !== void 0) {
                              let data3 = data0.version;
                              const _errs10 = errors;
                              if (typeof data3 !== "string") {
                                validate140.errors = [{ instancePath: instancePath + "/result_schema/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("1" !== data3) {
                                validate140.errors = [{ instancePath: instancePath + "/result_schema/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                          }
                        }
                      }
                    }
                  } else {
                    validate140.errors = [{ instancePath: instancePath + "/result_schema", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.version !== void 0) {
                  let data4 = data.version;
                  const _errs12 = errors;
                  if (typeof data4 !== "string") {
                    validate140.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("1" !== data4) {
                    validate140.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.view_id !== void 0) {
                    let data5 = data.view_id;
                    const _errs14 = errors;
                    if (typeof data5 !== "string") {
                      validate140.errors = [{ instancePath: instancePath + "/view_id", schemaPath: "#/properties/view_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data5 === "entity_search" || data5 === "neighborhood" || data5 === "object_detail")) {
                      validate140.errors = [{ instancePath: instancePath + "/view_id", schemaPath: "#/properties/view_id/enum", keyword: "enum", params: { allowedValues: schema103.properties.view_id.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs14 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate140.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate140.errors = vErrors;
      return errors === 0;
    }
    validate140.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate135(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate135.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.owner === void 0 && (missing0 = "owner") || data.revision === void 0 && (missing0 = "revision") || data.views === void 0 && (missing0 = "views") || data.limits === void 0 && (missing0 = "limits")) {
            validate135.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "limits" || key0 === "owner" || key0 === "revision" || key0 === "views" || key0 === "wire_version")) {
                validate135.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.limits !== void 0) {
                let data0 = data.limits;
                const _errs2 = errors;
                const _errs3 = errors;
                if (errors === _errs3) {
                  if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                    let missing1;
                    if (data0.search_page === void 0 && (missing1 = "search_page") || data0.entity_page === void 0 && (missing1 = "entity_page") || data0.assertion_page === void 0 && (missing1 = "assertion_page") || data0.radius === void 0 && (missing1 = "radius") || data0.response_bytes === void 0 && (missing1 = "response_bytes") || data0.source_fetch === void 0 && (missing1 = "source_fetch")) {
                      validate135.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/GraphExploreLimits/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                      return false;
                    } else {
                      const _errs5 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "assertion_page" || key1 === "entity_page" || key1 === "radius" || key1 === "response_bytes" || key1 === "search_page" || key1 === "source_fetch")) {
                          validate135.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/GraphExploreLimits/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                          return false;
                          break;
                        }
                      }
                      if (_errs5 === errors) {
                        if (data0.assertion_page !== void 0) {
                          let data1 = data0.assertion_page;
                          const _errs6 = errors;
                          if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                            validate135.errors = [{ instancePath: instancePath + "/limits/assertion_page", schemaPath: "#/$defs/GraphExploreLimits/properties/assertion_page/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (128 !== data1) {
                            validate135.errors = [{ instancePath: instancePath + "/limits/assertion_page", schemaPath: "#/$defs/GraphExploreLimits/properties/assertion_page/const", keyword: "const", params: { allowedValue: 128 }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid2 = _errs6 === errors;
                        } else {
                          var valid2 = true;
                        }
                        if (valid2) {
                          if (data0.entity_page !== void 0) {
                            let data2 = data0.entity_page;
                            const _errs8 = errors;
                            if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                              validate135.errors = [{ instancePath: instancePath + "/limits/entity_page", schemaPath: "#/$defs/GraphExploreLimits/properties/entity_page/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            if (64 !== data2) {
                              validate135.errors = [{ instancePath: instancePath + "/limits/entity_page", schemaPath: "#/$defs/GraphExploreLimits/properties/entity_page/const", keyword: "const", params: { allowedValue: 64 }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data0.radius !== void 0) {
                              let data3 = data0.radius;
                              const _errs10 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                validate135.errors = [{ instancePath: instancePath + "/limits/radius", schemaPath: "#/$defs/GraphExploreLimits/properties/radius/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (2 !== data3) {
                                validate135.errors = [{ instancePath: instancePath + "/limits/radius", schemaPath: "#/$defs/GraphExploreLimits/properties/radius/const", keyword: "const", params: { allowedValue: 2 }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data0.response_bytes !== void 0) {
                                let data4 = data0.response_bytes;
                                const _errs12 = errors;
                                if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                                  validate135.errors = [{ instancePath: instancePath + "/limits/response_bytes", schemaPath: "#/$defs/GraphExploreLimits/properties/response_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                if (1048576 !== data4) {
                                  validate135.errors = [{ instancePath: instancePath + "/limits/response_bytes", schemaPath: "#/$defs/GraphExploreLimits/properties/response_bytes/const", keyword: "const", params: { allowedValue: 1048576 }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data0.search_page !== void 0) {
                                  let data5 = data0.search_page;
                                  const _errs14 = errors;
                                  if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                    validate135.errors = [{ instancePath: instancePath + "/limits/search_page", schemaPath: "#/$defs/GraphExploreLimits/properties/search_page/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                    return false;
                                  }
                                  if (50 !== data5) {
                                    validate135.errors = [{ instancePath: instancePath + "/limits/search_page", schemaPath: "#/$defs/GraphExploreLimits/properties/search_page/const", keyword: "const", params: { allowedValue: 50 }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                                if (valid2) {
                                  if (data0.source_fetch !== void 0) {
                                    let data6 = data0.source_fetch;
                                    const _errs16 = errors;
                                    if (typeof data6 !== "string") {
                                      validate135.errors = [{ instancePath: instancePath + "/limits/source_fetch", schemaPath: "#/$defs/GraphExploreLimits/properties/source_fetch/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                    if ("separate_data_authority" !== data6) {
                                      validate135.errors = [{ instancePath: instancePath + "/limits/source_fetch", schemaPath: "#/$defs/GraphExploreLimits/properties/source_fetch/const", keyword: "const", params: { allowedValue: "separate_data_authority" }, message: "must be equal to constant" }];
                                      return false;
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
                      }
                    }
                  } else {
                    validate135.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/GraphExploreLimits/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.owner !== void 0) {
                  let data7 = data.owner;
                  const _errs18 = errors;
                  if (typeof data7 !== "string") {
                    validate135.errors = [{ instancePath: instancePath + "/owner", schemaPath: "#/properties/owner/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("knowledge" !== data7) {
                    validate135.errors = [{ instancePath: instancePath + "/owner", schemaPath: "#/properties/owner/const", keyword: "const", params: { allowedValue: "knowledge" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs18 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    const _errs20 = errors;
                    if (!validate136(data.revision, { instancePath: instancePath + "/revision", parentData: data, parentDataProperty: "revision", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate136.errors : vErrors.concat(validate136.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs20 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.views !== void 0) {
                      let data9 = data.views;
                      const _errs21 = errors;
                      if (errors === _errs21) {
                        if (Array.isArray(data9)) {
                          if (data9.length > 3) {
                            validate135.errors = [{ instancePath: instancePath + "/views", schemaPath: "#/properties/views/maxItems", keyword: "maxItems", params: { limit: 3 }, message: "must NOT have more than 3 items" }];
                            return false;
                          } else {
                            if (data9.length < 3) {
                              validate135.errors = [{ instancePath: instancePath + "/views", schemaPath: "#/properties/views/minItems", keyword: "minItems", params: { limit: 3 }, message: "must NOT have fewer than 3 items" }];
                              return false;
                            } else {
                              var valid3 = true;
                              const len0 = data9.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                const _errs23 = errors;
                                if (!validate140(data9[i0], { instancePath: instancePath + "/views/" + i0, parentData: data9, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate140.errors : vErrors.concat(validate140.errors);
                                  errors = vErrors.length;
                                }
                                var valid3 = _errs23 === errors;
                                if (!valid3) {
                                  break;
                                }
                              }
                            }
                          }
                        } else {
                          validate135.errors = [{ instancePath: instancePath + "/views", schemaPath: "#/properties/views/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs21 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.wire_version !== void 0) {
                        let data11 = data.wire_version;
                        const _errs24 = errors;
                        if (typeof data11 !== "string") {
                          validate135.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data11) {
                          validate135.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs24 === errors;
                      } else {
                        var valid0 = true;
                      }
                    }
                  }
                }
              }
            }
          }
        } else {
          validate135.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate135.errors = vErrors;
      return errors === 0;
    }
    validate135.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
  }
});
export default require_reviewed_validators();
