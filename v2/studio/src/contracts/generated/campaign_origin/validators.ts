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
    exports.origin = validate20;
    var schema32 = { "additionalProperties": false, "properties": { "authority": { "const": "historical_compiler_provenance", "title": "Authority", "type": "string" }, "draft": { "$ref": "#/$defs/CampaignOriginDraft" }, "knowledge": { "anyOf": [{ "$ref": "#/$defs/CampaignOriginKnowledge" }, { "type": "null" }] }, "limitations": { "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 16, "minItems": 1, "title": "Limitations", "type": "array" }, "proposal": { "$ref": "#/$defs/CampaignOriginProposal" }, "research": { "$ref": "#/$defs/CampaignOriginResearch" }, "save": { "$ref": "#/$defs/CampaignOriginSave" }, "schema_version": { "const": "2", "default": "2", "title": "Schema Version", "type": "string" }, "tools": { "items": { "$ref": "#/$defs/CampaignOriginTool" }, "maxItems": 4096, "title": "Tools", "type": "array" } }, "required": ["authority", "draft", "proposal", "save", "research", "tools", "limitations", "knowledge"], "title": "CampaignOriginBodyV2", "type": "object" };
    var func1 = Object.prototype.hasOwnProperty;
    var func2 = require_ucs2length().default;
    var pattern4 = new RegExp("^[0-9a-f]{64}$", "u");
    var pattern5 = new RegExp("^[A-Za-z0-9][A-Za-z0-9._:-]*$", "u");
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
          if (data.scope === void 0 && (missing0 = "scope") || data.draft_id === void 0 && (missing0 = "draft_id") || data.revision === void 0 && (missing0 = "revision") || data.content_sha256 === void 0 && (missing0 = "content_sha256")) {
            validate22.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "content_sha256" || key0 === "draft_id" || key0 === "revision" || key0 === "scope")) {
                validate22.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.content_sha256 !== void 0) {
                let data0 = data.content_sha256;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (!pattern4.test(data0)) {
                      validate22.errors = [{ instancePath: instancePath + "/content_sha256", schemaPath: "#/properties/content_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate22.errors = [{ instancePath: instancePath + "/content_sha256", schemaPath: "#/properties/content_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.draft_id !== void 0) {
                  let data1 = data.draft_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func2(data1) > 128) {
                        validate22.errors = [{ instancePath: instancePath + "/draft_id", schemaPath: "#/properties/draft_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func2(data1) < 1) {
                          validate22.errors = [{ instancePath: instancePath + "/draft_id", schemaPath: "#/properties/draft_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data1)) {
                            validate22.errors = [{ instancePath: instancePath + "/draft_id", schemaPath: "#/properties/draft_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate22.errors = [{ instancePath: instancePath + "/draft_id", schemaPath: "#/properties/draft_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.revision !== void 0) {
                    let data2 = data.revision;
                    const _errs6 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate22.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate22.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate22.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.scope !== void 0) {
                      let data3 = data.scope;
                      const _errs8 = errors;
                      const _errs9 = errors;
                      if (errors === _errs9) {
                        if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                          let missing1;
                          if (data3.tenant_id === void 0 && (missing1 = "tenant_id") || data3.project_id === void 0 && (missing1 = "project_id")) {
                            validate22.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                            return false;
                          } else {
                            const _errs11 = errors;
                            for (const key1 in data3) {
                              if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                validate22.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs11 === errors) {
                              if (data3.project_id !== void 0) {
                                let data4 = data3.project_id;
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data4 === "string") {
                                    if (func2(data4) > 128) {
                                      validate22.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func2(data4) < 1) {
                                        validate22.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data4)) {
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
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data3.tenant_id !== void 0) {
                                  let data5 = data3.tenant_id;
                                  const _errs14 = errors;
                                  if (errors === _errs14) {
                                    if (typeof data5 === "string") {
                                      if (func2(data5) > 128) {
                                        validate22.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func2(data5) < 1) {
                                          validate22.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data5)) {
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
                                  var valid2 = _errs14 === errors;
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
          validate22.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate22.errors = vErrors;
      return errors === 0;
    }
    validate22.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema35 = { "additionalProperties": false, "properties": { "assertions": { "items": { "$ref": "#/$defs/AssertionRevisionRef" }, "maxItems": 256, "title": "Assertions", "type": "array" }, "context_sha256": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "title": "Context Sha256" }, "entities": { "items": { "$ref": "#/$defs/EntityRevisionRef" }, "maxItems": 256, "title": "Entities", "type": "array" }, "graph": { "$ref": "#/$defs/DomainGraphRef" }, "head": { "anyOf": [{ "$ref": "#/$defs/DomainHead" }, { "type": "null" }] }, "policy": { "anyOf": [{ "$ref": "#/$defs/StructuralPolicyRef" }, { "type": "null" }] }, "selection_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Selection Sha256", "type": "string" }, "status": { "enum": ["available", "unavailable"], "title": "Status", "type": "string" }, "unavailable": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Unavailable" }, "vocabulary": { "anyOf": [{ "$ref": "#/$defs/VocabularyRef" }, { "type": "null" }] } }, "required": ["status", "graph", "head", "vocabulary", "policy", "entities", "assertions", "selection_sha256", "context_sha256", "unavailable"], "title": "CampaignOriginKnowledge", "type": "object" };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.graph_id === void 0 && (missing0 = "graph_id")) {
            validate26.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph_id" || key0 === "scope")) {
                validate26.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func2(data0) > 128) {
                      validate26.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate26.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate26.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate26.errors = [{ instancePath: instancePath + "/graph_id", schemaPath: "#/properties/graph_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate26.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate26.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                if (func2(data2) > 128) {
                                  validate26.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func2(data2) < 1) {
                                    validate26.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern5.test(data2)) {
                                      validate26.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate26.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                  if (func2(data3) > 128) {
                                    validate26.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func2(data3) < 1) {
                                      validate26.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate26.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate26.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate26.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate26.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate26.errors = vErrors;
      return errors === 0;
    }
    validate26.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.graph === void 0 && (missing0 = "graph") || data.assertion_id === void 0 && (missing0 = "assertion_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate25.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "assertion_id" || key0 === "graph" || key0 === "revision")) {
                validate25.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func2(data0) > 128) {
                      validate25.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate25.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate25.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate25.errors = [{ instancePath: instancePath + "/assertion_id", schemaPath: "#/properties/assertion_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  if (!validate26(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
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
                      validate25.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate25.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate25.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
          validate25.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate25.errors = vErrors;
      return errors === 0;
    }
    validate25.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate29(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate29.evaluated;
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
            validate29.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entity_id" || key0 === "graph" || key0 === "revision")) {
                validate29.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func2(data0) > 128) {
                      validate29.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate29.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate29.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate29.errors = [{ instancePath: instancePath + "/entity_id", schemaPath: "#/properties/entity_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  if (!validate26(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
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
                      validate29.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate29.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate29.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
          validate29.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate29.errors = vErrors;
      return errors === 0;
    }
    validate29.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.graph === void 0 && (missing0 = "graph") || data.change_id === void 0 && (missing0 = "change_id") || data.position === void 0 && (missing0 = "position") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate34.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "change_id" || key0 === "graph" || key0 === "position" || key0 === "sha256")) {
                validate34.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.change_id !== void 0) {
                let data0 = data.change_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func2(data0) > 128) {
                      validate34.errors = [{ instancePath: instancePath + "/change_id", schemaPath: "#/properties/change_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate34.errors = [{ instancePath: instancePath + "/change_id", schemaPath: "#/properties/change_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate34.errors = [{ instancePath: instancePath + "/change_id", schemaPath: "#/properties/change_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate34.errors = [{ instancePath: instancePath + "/change_id", schemaPath: "#/properties/change_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                  if (!validate26(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.position !== void 0) {
                    let data2 = data.position;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate34.errors = [{ instancePath: instancePath + "/position", schemaPath: "#/properties/position/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate34.errors = [{ instancePath: instancePath + "/position", schemaPath: "#/properties/position/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 1 || isNaN(data2)) {
                            validate34.errors = [{ instancePath: instancePath + "/position", schemaPath: "#/properties/position/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                    if (data.sha256 !== void 0) {
                      let data3 = data.sha256;
                      const _errs7 = errors;
                      if (errors === _errs7) {
                        if (typeof data3 === "string") {
                          if (!pattern4.test(data3)) {
                            validate34.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                            return false;
                          }
                        } else {
                          validate34.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
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
          validate34.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate34.errors = vErrors;
      return errors === 0;
    }
    validate34.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate37(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate37.evaluated;
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
            validate37.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "graph" || key0 === "revision" || key0 === "sha256")) {
                validate37.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.graph !== void 0) {
                const _errs2 = errors;
                if (!validate26(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
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
                    validate37.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate37.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate37.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                        if (!pattern4.test(data2)) {
                          validate37.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate37.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          validate37.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate37.errors = vErrors;
      return errors === 0;
    }
    validate37.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.snapshot === void 0 && (missing0 = "snapshot") || data.change === void 0 && (missing0 = "change")) {
            validate33.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "change" || key0 === "snapshot")) {
                validate33.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.change !== void 0) {
                const _errs2 = errors;
                if (!validate34(data.change, { instancePath: instancePath + "/change", parentData: data, parentDataProperty: "change", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate34.errors : vErrors.concat(validate34.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.snapshot !== void 0) {
                  const _errs3 = errors;
                  if (!validate37(data.snapshot, { instancePath: instancePath + "/snapshot", parentData: data, parentDataProperty: "snapshot", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate37.errors : vErrors.concat(validate37.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
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
          if (data.status === void 0 && (missing0 = "status") || data.graph === void 0 && (missing0 = "graph") || data.head === void 0 && (missing0 = "head") || data.vocabulary === void 0 && (missing0 = "vocabulary") || data.policy === void 0 && (missing0 = "policy") || data.entities === void 0 && (missing0 = "entities") || data.assertions === void 0 && (missing0 = "assertions") || data.selection_sha256 === void 0 && (missing0 = "selection_sha256") || data.context_sha256 === void 0 && (missing0 = "context_sha256") || data.unavailable === void 0 && (missing0 = "unavailable")) {
            validate24.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func1.call(schema35.properties, key0)) {
                validate24.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assertions !== void 0) {
                let data0 = data.assertions;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 256) {
                      validate24.errors = [{ instancePath: instancePath + "/assertions", schemaPath: "#/properties/assertions/maxItems", keyword: "maxItems", params: { limit: 256 }, message: "must NOT have more than 256 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate25(data0[i0], { instancePath: instancePath + "/assertions/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
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
                    validate24.errors = [{ instancePath: instancePath + "/assertions", schemaPath: "#/properties/assertions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.context_sha256 !== void 0) {
                  let data2 = data.context_sha256;
                  const _errs5 = errors;
                  const _errs6 = errors;
                  let valid2 = false;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (typeof data2 === "string") {
                      if (!pattern4.test(data2)) {
                        const err0 = { instancePath: instancePath + "/context_sha256", schemaPath: "#/properties/context_sha256/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      }
                    } else {
                      const err1 = { instancePath: instancePath + "/context_sha256", schemaPath: "#/properties/context_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err1];
                      } else {
                        vErrors.push(err1);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs7 === errors;
                  valid2 = valid2 || _valid0;
                  const _errs9 = errors;
                  if (data2 !== null) {
                    const err2 = { instancePath: instancePath + "/context_sha256", schemaPath: "#/properties/context_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid2 = valid2 || _valid0;
                  if (!valid2) {
                    const err3 = { instancePath: instancePath + "/context_sha256", schemaPath: "#/properties/context_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                    validate24.errors = vErrors;
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
                  if (data.entities !== void 0) {
                    let data3 = data.entities;
                    const _errs11 = errors;
                    if (errors === _errs11) {
                      if (Array.isArray(data3)) {
                        if (data3.length > 256) {
                          validate24.errors = [{ instancePath: instancePath + "/entities", schemaPath: "#/properties/entities/maxItems", keyword: "maxItems", params: { limit: 256 }, message: "must NOT have more than 256 items" }];
                          return false;
                        } else {
                          var valid3 = true;
                          const len1 = data3.length;
                          for (let i1 = 0; i1 < len1; i1++) {
                            const _errs13 = errors;
                            if (!validate29(data3[i1], { instancePath: instancePath + "/entities/" + i1, parentData: data3, parentDataProperty: i1, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate29.errors : vErrors.concat(validate29.errors);
                              errors = vErrors.length;
                            }
                            var valid3 = _errs13 === errors;
                            if (!valid3) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate24.errors = [{ instancePath: instancePath + "/entities", schemaPath: "#/properties/entities/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs11 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.graph !== void 0) {
                      const _errs14 = errors;
                      if (!validate26(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs14 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.head !== void 0) {
                        let data6 = data.head;
                        const _errs15 = errors;
                        const _errs16 = errors;
                        let valid4 = false;
                        const _errs17 = errors;
                        if (!validate33(data6, { instancePath: instancePath + "/head", parentData: data, parentDataProperty: "head", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate33.errors : vErrors.concat(validate33.errors);
                          errors = vErrors.length;
                        }
                        var _valid1 = _errs17 === errors;
                        valid4 = valid4 || _valid1;
                        const _errs18 = errors;
                        if (data6 !== null) {
                          const err4 = { instancePath: instancePath + "/head", schemaPath: "#/properties/head/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err4];
                          } else {
                            vErrors.push(err4);
                          }
                          errors++;
                        }
                        var _valid1 = _errs18 === errors;
                        valid4 = valid4 || _valid1;
                        if (!valid4) {
                          const err5 = { instancePath: instancePath + "/head", schemaPath: "#/properties/head/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err5];
                          } else {
                            vErrors.push(err5);
                          }
                          errors++;
                          validate24.errors = vErrors;
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
                      if (valid0) {
                        if (data.policy !== void 0) {
                          let data7 = data.policy;
                          const _errs20 = errors;
                          const _errs21 = errors;
                          let valid5 = false;
                          const _errs22 = errors;
                          const _errs23 = errors;
                          if (errors === _errs23) {
                            if (data7 && typeof data7 == "object" && !Array.isArray(data7)) {
                              let missing1;
                              if (data7.policy_id === void 0 && (missing1 = "policy_id") || data7.version === void 0 && (missing1 = "version") || data7.sha256 === void 0 && (missing1 = "sha256")) {
                                const err6 = { instancePath: instancePath + "/policy", schemaPath: "#/$defs/StructuralPolicyRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                                if (vErrors === null) {
                                  vErrors = [err6];
                                } else {
                                  vErrors.push(err6);
                                }
                                errors++;
                              } else {
                                const _errs25 = errors;
                                for (const key1 in data7) {
                                  if (!(key1 === "policy_id" || key1 === "sha256" || key1 === "version")) {
                                    const err7 = { instancePath: instancePath + "/policy", schemaPath: "#/$defs/StructuralPolicyRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                    if (vErrors === null) {
                                      vErrors = [err7];
                                    } else {
                                      vErrors.push(err7);
                                    }
                                    errors++;
                                    break;
                                  }
                                }
                                if (_errs25 === errors) {
                                  if (data7.policy_id !== void 0) {
                                    let data8 = data7.policy_id;
                                    const _errs26 = errors;
                                    if (errors === _errs26) {
                                      if (typeof data8 === "string") {
                                        if (func2(data8) > 128) {
                                          const err8 = { instancePath: instancePath + "/policy/policy_id", schemaPath: "#/$defs/StructuralPolicyRef/properties/policy_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err8];
                                          } else {
                                            vErrors.push(err8);
                                          }
                                          errors++;
                                        } else {
                                          if (func2(data8) < 1) {
                                            const err9 = { instancePath: instancePath + "/policy/policy_id", schemaPath: "#/$defs/StructuralPolicyRef/properties/policy_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                            if (vErrors === null) {
                                              vErrors = [err9];
                                            } else {
                                              vErrors.push(err9);
                                            }
                                            errors++;
                                          } else {
                                            if (!pattern5.test(data8)) {
                                              const err10 = { instancePath: instancePath + "/policy/policy_id", schemaPath: "#/$defs/StructuralPolicyRef/properties/policy_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                              if (vErrors === null) {
                                                vErrors = [err10];
                                              } else {
                                                vErrors.push(err10);
                                              }
                                              errors++;
                                            }
                                          }
                                        }
                                      } else {
                                        const err11 = { instancePath: instancePath + "/policy/policy_id", schemaPath: "#/$defs/StructuralPolicyRef/properties/policy_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err11];
                                        } else {
                                          vErrors.push(err11);
                                        }
                                        errors++;
                                      }
                                    }
                                    var valid7 = _errs26 === errors;
                                  } else {
                                    var valid7 = true;
                                  }
                                  if (valid7) {
                                    if (data7.sha256 !== void 0) {
                                      let data9 = data7.sha256;
                                      const _errs28 = errors;
                                      if (errors === _errs28) {
                                        if (typeof data9 === "string") {
                                          if (!pattern4.test(data9)) {
                                            const err12 = { instancePath: instancePath + "/policy/sha256", schemaPath: "#/$defs/StructuralPolicyRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                            if (vErrors === null) {
                                              vErrors = [err12];
                                            } else {
                                              vErrors.push(err12);
                                            }
                                            errors++;
                                          }
                                        } else {
                                          const err13 = { instancePath: instancePath + "/policy/sha256", schemaPath: "#/$defs/StructuralPolicyRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err13];
                                          } else {
                                            vErrors.push(err13);
                                          }
                                          errors++;
                                        }
                                      }
                                      var valid7 = _errs28 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                    if (valid7) {
                                      if (data7.version !== void 0) {
                                        let data10 = data7.version;
                                        const _errs30 = errors;
                                        if (errors === _errs30) {
                                          if (typeof data10 === "string") {
                                            if (func2(data10) > 128) {
                                              const err14 = { instancePath: instancePath + "/policy/version", schemaPath: "#/$defs/StructuralPolicyRef/properties/version/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                              if (vErrors === null) {
                                                vErrors = [err14];
                                              } else {
                                                vErrors.push(err14);
                                              }
                                              errors++;
                                            } else {
                                              if (func2(data10) < 1) {
                                                const err15 = { instancePath: instancePath + "/policy/version", schemaPath: "#/$defs/StructuralPolicyRef/properties/version/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                if (vErrors === null) {
                                                  vErrors = [err15];
                                                } else {
                                                  vErrors.push(err15);
                                                }
                                                errors++;
                                              } else {
                                                if (!pattern5.test(data10)) {
                                                  const err16 = { instancePath: instancePath + "/policy/version", schemaPath: "#/$defs/StructuralPolicyRef/properties/version/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                                  if (vErrors === null) {
                                                    vErrors = [err16];
                                                  } else {
                                                    vErrors.push(err16);
                                                  }
                                                  errors++;
                                                }
                                              }
                                            }
                                          } else {
                                            const err17 = { instancePath: instancePath + "/policy/version", schemaPath: "#/$defs/StructuralPolicyRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                            if (vErrors === null) {
                                              vErrors = [err17];
                                            } else {
                                              vErrors.push(err17);
                                            }
                                            errors++;
                                          }
                                        }
                                        var valid7 = _errs30 === errors;
                                      } else {
                                        var valid7 = true;
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              const err18 = { instancePath: instancePath + "/policy", schemaPath: "#/$defs/StructuralPolicyRef/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                              if (vErrors === null) {
                                vErrors = [err18];
                              } else {
                                vErrors.push(err18);
                              }
                              errors++;
                            }
                          }
                          var _valid2 = _errs22 === errors;
                          valid5 = valid5 || _valid2;
                          const _errs32 = errors;
                          if (data7 !== null) {
                            const err19 = { instancePath: instancePath + "/policy", schemaPath: "#/properties/policy/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err19];
                            } else {
                              vErrors.push(err19);
                            }
                            errors++;
                          }
                          var _valid2 = _errs32 === errors;
                          valid5 = valid5 || _valid2;
                          if (!valid5) {
                            const err20 = { instancePath: instancePath + "/policy", schemaPath: "#/properties/policy/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err20];
                            } else {
                              vErrors.push(err20);
                            }
                            errors++;
                            validate24.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs21;
                            if (vErrors !== null) {
                              if (_errs21) {
                                vErrors.length = _errs21;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs20 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.selection_sha256 !== void 0) {
                            let data11 = data.selection_sha256;
                            const _errs34 = errors;
                            if (errors === _errs34) {
                              if (typeof data11 === "string") {
                                if (!pattern4.test(data11)) {
                                  validate24.errors = [{ instancePath: instancePath + "/selection_sha256", schemaPath: "#/properties/selection_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate24.errors = [{ instancePath: instancePath + "/selection_sha256", schemaPath: "#/properties/selection_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid0 = _errs34 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.status !== void 0) {
                              let data12 = data.status;
                              const _errs36 = errors;
                              if (typeof data12 !== "string") {
                                validate24.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if (!(data12 === "available" || data12 === "unavailable")) {
                                validate24.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema35.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                                return false;
                              }
                              var valid0 = _errs36 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.unavailable !== void 0) {
                                let data13 = data.unavailable;
                                const _errs38 = errors;
                                const _errs39 = errors;
                                let valid8 = false;
                                const _errs40 = errors;
                                if (errors === _errs40) {
                                  if (typeof data13 === "string") {
                                    if (func2(data13) > 128) {
                                      const err21 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err21];
                                      } else {
                                        vErrors.push(err21);
                                      }
                                      errors++;
                                    } else {
                                      if (func2(data13) < 1) {
                                        const err22 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err22];
                                        } else {
                                          vErrors.push(err22);
                                        }
                                        errors++;
                                      } else {
                                        if (!pattern5.test(data13)) {
                                          const err23 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                          if (vErrors === null) {
                                            vErrors = [err23];
                                          } else {
                                            vErrors.push(err23);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  } else {
                                    const err24 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err24];
                                    } else {
                                      vErrors.push(err24);
                                    }
                                    errors++;
                                  }
                                }
                                var _valid3 = _errs40 === errors;
                                valid8 = valid8 || _valid3;
                                const _errs42 = errors;
                                if (data13 !== null) {
                                  const err25 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                  if (vErrors === null) {
                                    vErrors = [err25];
                                  } else {
                                    vErrors.push(err25);
                                  }
                                  errors++;
                                }
                                var _valid3 = _errs42 === errors;
                                valid8 = valid8 || _valid3;
                                if (!valid8) {
                                  const err26 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                  if (vErrors === null) {
                                    vErrors = [err26];
                                  } else {
                                    vErrors.push(err26);
                                  }
                                  errors++;
                                  validate24.errors = vErrors;
                                  return false;
                                } else {
                                  errors = _errs39;
                                  if (vErrors !== null) {
                                    if (_errs39) {
                                      vErrors.length = _errs39;
                                    } else {
                                      vErrors = null;
                                    }
                                  }
                                }
                                var valid0 = _errs38 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.vocabulary !== void 0) {
                                  let data14 = data.vocabulary;
                                  const _errs44 = errors;
                                  const _errs45 = errors;
                                  let valid9 = false;
                                  const _errs46 = errors;
                                  const _errs47 = errors;
                                  if (errors === _errs47) {
                                    if (data14 && typeof data14 == "object" && !Array.isArray(data14)) {
                                      let missing2;
                                      if (data14.vocabulary_id === void 0 && (missing2 = "vocabulary_id") || data14.version === void 0 && (missing2 = "version") || data14.sha256 === void 0 && (missing2 = "sha256")) {
                                        const err27 = { instancePath: instancePath + "/vocabulary", schemaPath: "#/$defs/VocabularyRef/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                                        if (vErrors === null) {
                                          vErrors = [err27];
                                        } else {
                                          vErrors.push(err27);
                                        }
                                        errors++;
                                      } else {
                                        const _errs49 = errors;
                                        for (const key2 in data14) {
                                          if (!(key2 === "sha256" || key2 === "version" || key2 === "vocabulary_id")) {
                                            const err28 = { instancePath: instancePath + "/vocabulary", schemaPath: "#/$defs/VocabularyRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                                            if (vErrors === null) {
                                              vErrors = [err28];
                                            } else {
                                              vErrors.push(err28);
                                            }
                                            errors++;
                                            break;
                                          }
                                        }
                                        if (_errs49 === errors) {
                                          if (data14.sha256 !== void 0) {
                                            let data15 = data14.sha256;
                                            const _errs50 = errors;
                                            if (errors === _errs50) {
                                              if (typeof data15 === "string") {
                                                if (!pattern4.test(data15)) {
                                                  const err29 = { instancePath: instancePath + "/vocabulary/sha256", schemaPath: "#/$defs/VocabularyRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                                  if (vErrors === null) {
                                                    vErrors = [err29];
                                                  } else {
                                                    vErrors.push(err29);
                                                  }
                                                  errors++;
                                                }
                                              } else {
                                                const err30 = { instancePath: instancePath + "/vocabulary/sha256", schemaPath: "#/$defs/VocabularyRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                if (vErrors === null) {
                                                  vErrors = [err30];
                                                } else {
                                                  vErrors.push(err30);
                                                }
                                                errors++;
                                              }
                                            }
                                            var valid11 = _errs50 === errors;
                                          } else {
                                            var valid11 = true;
                                          }
                                          if (valid11) {
                                            if (data14.version !== void 0) {
                                              let data16 = data14.version;
                                              const _errs52 = errors;
                                              if (errors === _errs52) {
                                                if (typeof data16 === "string") {
                                                  if (func2(data16) > 128) {
                                                    const err31 = { instancePath: instancePath + "/vocabulary/version", schemaPath: "#/$defs/VocabularyRef/properties/version/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                                    if (vErrors === null) {
                                                      vErrors = [err31];
                                                    } else {
                                                      vErrors.push(err31);
                                                    }
                                                    errors++;
                                                  } else {
                                                    if (func2(data16) < 1) {
                                                      const err32 = { instancePath: instancePath + "/vocabulary/version", schemaPath: "#/$defs/VocabularyRef/properties/version/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                      if (vErrors === null) {
                                                        vErrors = [err32];
                                                      } else {
                                                        vErrors.push(err32);
                                                      }
                                                      errors++;
                                                    } else {
                                                      if (!pattern5.test(data16)) {
                                                        const err33 = { instancePath: instancePath + "/vocabulary/version", schemaPath: "#/$defs/VocabularyRef/properties/version/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                                        if (vErrors === null) {
                                                          vErrors = [err33];
                                                        } else {
                                                          vErrors.push(err33);
                                                        }
                                                        errors++;
                                                      }
                                                    }
                                                  }
                                                } else {
                                                  const err34 = { instancePath: instancePath + "/vocabulary/version", schemaPath: "#/$defs/VocabularyRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                  if (vErrors === null) {
                                                    vErrors = [err34];
                                                  } else {
                                                    vErrors.push(err34);
                                                  }
                                                  errors++;
                                                }
                                              }
                                              var valid11 = _errs52 === errors;
                                            } else {
                                              var valid11 = true;
                                            }
                                            if (valid11) {
                                              if (data14.vocabulary_id !== void 0) {
                                                let data17 = data14.vocabulary_id;
                                                const _errs54 = errors;
                                                if (errors === _errs54) {
                                                  if (typeof data17 === "string") {
                                                    if (func2(data17) > 128) {
                                                      const err35 = { instancePath: instancePath + "/vocabulary/vocabulary_id", schemaPath: "#/$defs/VocabularyRef/properties/vocabulary_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                                      if (vErrors === null) {
                                                        vErrors = [err35];
                                                      } else {
                                                        vErrors.push(err35);
                                                      }
                                                      errors++;
                                                    } else {
                                                      if (func2(data17) < 1) {
                                                        const err36 = { instancePath: instancePath + "/vocabulary/vocabulary_id", schemaPath: "#/$defs/VocabularyRef/properties/vocabulary_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                        if (vErrors === null) {
                                                          vErrors = [err36];
                                                        } else {
                                                          vErrors.push(err36);
                                                        }
                                                        errors++;
                                                      } else {
                                                        if (!pattern5.test(data17)) {
                                                          const err37 = { instancePath: instancePath + "/vocabulary/vocabulary_id", schemaPath: "#/$defs/VocabularyRef/properties/vocabulary_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                                          if (vErrors === null) {
                                                            vErrors = [err37];
                                                          } else {
                                                            vErrors.push(err37);
                                                          }
                                                          errors++;
                                                        }
                                                      }
                                                    }
                                                  } else {
                                                    const err38 = { instancePath: instancePath + "/vocabulary/vocabulary_id", schemaPath: "#/$defs/VocabularyRef/properties/vocabulary_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                    if (vErrors === null) {
                                                      vErrors = [err38];
                                                    } else {
                                                      vErrors.push(err38);
                                                    }
                                                    errors++;
                                                  }
                                                }
                                                var valid11 = _errs54 === errors;
                                              } else {
                                                var valid11 = true;
                                              }
                                            }
                                          }
                                        }
                                      }
                                    } else {
                                      const err39 = { instancePath: instancePath + "/vocabulary", schemaPath: "#/$defs/VocabularyRef/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                      if (vErrors === null) {
                                        vErrors = [err39];
                                      } else {
                                        vErrors.push(err39);
                                      }
                                      errors++;
                                    }
                                  }
                                  var _valid4 = _errs46 === errors;
                                  valid9 = valid9 || _valid4;
                                  const _errs56 = errors;
                                  if (data14 !== null) {
                                    const err40 = { instancePath: instancePath + "/vocabulary", schemaPath: "#/properties/vocabulary/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                    if (vErrors === null) {
                                      vErrors = [err40];
                                    } else {
                                      vErrors.push(err40);
                                    }
                                    errors++;
                                  }
                                  var _valid4 = _errs56 === errors;
                                  valid9 = valid9 || _valid4;
                                  if (!valid9) {
                                    const err41 = { instancePath: instancePath + "/vocabulary", schemaPath: "#/properties/vocabulary/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                    if (vErrors === null) {
                                      vErrors = [err41];
                                    } else {
                                      vErrors.push(err41);
                                    }
                                    errors++;
                                    validate24.errors = vErrors;
                                    return false;
                                  } else {
                                    errors = _errs45;
                                    if (vErrors !== null) {
                                      if (_errs45) {
                                        vErrors.length = _errs45;
                                      } else {
                                        vErrors = null;
                                      }
                                    }
                                  }
                                  var valid0 = _errs44 === errors;
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
          validate24.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate24.errors = vErrors;
      return errors === 0;
    }
    validate24.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema45 = { "additionalProperties": false, "properties": { "action": { "const": "propose_campaign", "title": "Action", "type": "string" }, "actor_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Actor Id", "type": "string" }, "attempt": { "$ref": "#/$defs/ProviderAttemptRef" }, "capture_publication": { "const": "not_published", "title": "Capture Publication", "type": "string" }, "context": { "$ref": "#/$defs/ContextManifest" }, "output_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Output Sha256", "type": "string" }, "preparation_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Preparation Sha256", "type": "string" }, "prepared_proposal_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Prepared Proposal Sha256", "type": "string" }, "rationale": { "maxLength": 4096, "minLength": 1, "title": "Rationale", "type": "string" }, "usage": { "$ref": "#/$defs/ProviderUsage" } }, "required": ["actor_id", "attempt", "preparation_sha256", "prepared_proposal_sha256", "output_sha256", "action", "rationale", "context", "usage", "capture_publication"], "title": "CampaignOriginProposal", "type": "object" };
    var schema60 = { "additionalProperties": false, "properties": { "accounting_units": { "anyOf": [{ "maximum": 9007199254740991, "minimum": 0, "type": "integer" }, { "type": "null" }], "title": "Accounting Units" }, "certainty": { "enum": ["reported", "unknown"], "title": "Certainty", "type": "string" }, "input_tokens": { "anyOf": [{ "maximum": 16777216, "minimum": 0, "type": "integer" }, { "type": "null" }], "title": "Input Tokens" }, "output_tokens": { "anyOf": [{ "maximum": 16777216, "minimum": 0, "type": "integer" }, { "type": "null" }], "title": "Output Tokens" } }, "required": ["input_tokens", "output_tokens", "accounting_units", "certainty"], "title": "ProviderUsage", "type": "object" };
    function validate44(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate44.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.engagement_id === void 0 && (missing0 = "engagement_id")) {
            validate44.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "engagement_id" || key0 === "scope")) {
                validate44.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.engagement_id !== void 0) {
                let data0 = data.engagement_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func2(data0) > 128) {
                      validate44.errors = [{ instancePath: instancePath + "/engagement_id", schemaPath: "#/properties/engagement_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate44.errors = [{ instancePath: instancePath + "/engagement_id", schemaPath: "#/properties/engagement_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate44.errors = [{ instancePath: instancePath + "/engagement_id", schemaPath: "#/properties/engagement_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate44.errors = [{ instancePath: instancePath + "/engagement_id", schemaPath: "#/properties/engagement_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate44.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate44.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                if (func2(data2) > 128) {
                                  validate44.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func2(data2) < 1) {
                                    validate44.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern5.test(data2)) {
                                      validate44.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate44.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                  if (func2(data3) > 128) {
                                    validate44.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func2(data3) < 1) {
                                      validate44.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate44.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate44.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate44.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate44.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate44.errors = vErrors;
      return errors === 0;
    }
    validate44.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.engagement === void 0 && (missing0 = "engagement") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.ordinal === void 0 && (missing0 = "ordinal")) {
            validate43.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "engagement" || key0 === "ordinal" || key0 === "request_sha256")) {
                validate43.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.engagement !== void 0) {
                const _errs2 = errors;
                if (!validate44(data.engagement, { instancePath: instancePath + "/engagement", parentData: data, parentDataProperty: "engagement", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate44.errors : vErrors.concat(validate44.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.ordinal !== void 0) {
                  let data1 = data.ordinal;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate43.errors = [{ instancePath: instancePath + "/ordinal", schemaPath: "#/properties/ordinal/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 16 || isNaN(data1)) {
                        validate43.errors = [{ instancePath: instancePath + "/ordinal", schemaPath: "#/properties/ordinal/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate43.errors = [{ instancePath: instancePath + "/ordinal", schemaPath: "#/properties/ordinal/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                  if (data.request_sha256 !== void 0) {
                    let data2 = data.request_sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern4.test(data2)) {
                          validate43.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate43.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
    var schema49 = { "additionalProperties": false, "properties": { "allowed_actions": { "items": { "enum": ["abstain", "request_evidence", "propose_knowledge_change", "propose_campaign"], "type": "string" }, "maxItems": 4, "minItems": 1, "title": "Allowed Actions", "type": "array" }, "entries": { "items": { "$ref": "#/$defs/ContextEntry" }, "maxItems": 128, "title": "Entries", "type": "array" }, "limits": { "$ref": "#/$defs/CallLimits" }, "model": { "$ref": "#/$defs/ModelBinding" }, "objective": { "$ref": "#/$defs/ArtifactRef" }, "omissions": { "items": { "$ref": "#/$defs/ContextOmission" }, "maxItems": 128, "title": "Omissions", "type": "array" }, "output_schema": { "$ref": "#/$defs/SchemaRef" }, "policy": { "$ref": "#/$defs/ArtifactRef" }, "prompt": { "$ref": "#/$defs/ArtifactRef" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "objective", "prompt", "policy", "model", "entries", "omissions", "allowed_actions", "output_schema", "limits"], "title": "ContextManifest", "type": "object" };
    var schema50 = { "additionalProperties": false, "properties": { "artifact": { "$ref": "#/$defs/ArtifactRef" }, "required": { "title": "Required", "type": "boolean" }, "role": { "enum": ["constraint", "source", "capability", "knowledge", "result"], "title": "Role", "type": "string" } }, "required": ["artifact", "role", "required"], "title": "ContextEntry", "type": "object" };
    var pattern32 = new RegExp("^[^\\s/]+/[^\\s/]+$", "u");
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate49.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate49.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func2(data0) > 128) {
                      validate49.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate49.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate49.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate49.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      if (func2(data1) > 128) {
                        validate49.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func2(data1) < 3) {
                          validate49.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern32.test(data1)) {
                            validate49.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate49.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate49.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate49.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                  if (func2(data3) > 128) {
                                    validate49.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func2(data3) < 1) {
                                      validate49.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate49.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate49.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate49.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate49.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate49.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate49.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate49.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                    if (func2(data7) > 128) {
                                      validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func2(data7) < 1) {
                                        validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data7)) {
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
                                      if (func2(data8) > 128) {
                                        validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func2(data8) < 1) {
                                          validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data8)) {
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
                                  var valid4 = _errs22 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                              validate49.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate49.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate49.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate49.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate49.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          if (data.artifact === void 0 && (missing0 = "artifact") || data.role === void 0 && (missing0 = "role") || data.required === void 0 && (missing0 = "required")) {
            validate48.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "required" || key0 === "role")) {
                validate48.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                const _errs2 = errors;
                if (!validate49(data.artifact, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.required !== void 0) {
                  const _errs3 = errors;
                  if (typeof data.required !== "boolean") {
                    validate48.errors = [{ instancePath: instancePath + "/required", schemaPath: "#/properties/required/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.role !== void 0) {
                    let data2 = data.role;
                    const _errs5 = errors;
                    if (typeof data2 !== "string") {
                      validate48.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data2 === "constraint" || data2 === "source" || data2 === "capability" || data2 === "knowledge" || data2 === "result")) {
                      validate48.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/enum", keyword: "enum", params: { allowedValues: schema50.properties.role.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
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
          if (data.provider_id === void 0 && (missing0 = "provider_id") || data.model_id === void 0 && (missing0 = "model_id") || data.model_revision === void 0 && (missing0 = "model_revision") || data.configuration === void 0 && (missing0 = "configuration") || data.tokenizer === void 0 && (missing0 = "tokenizer") || data.context_window_tokens === void 0 && (missing0 = "context_window_tokens")) {
            validate52.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "configuration" || key0 === "context_window_tokens" || key0 === "model_id" || key0 === "model_revision" || key0 === "provider_id" || key0 === "tokenizer")) {
                validate52.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.configuration !== void 0) {
                const _errs2 = errors;
                if (!validate49(data.configuration, { instancePath: instancePath + "/configuration", parentData: data, parentDataProperty: "configuration", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.context_window_tokens !== void 0) {
                  let data1 = data.context_window_tokens;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate52.errors = [{ instancePath: instancePath + "/context_window_tokens", schemaPath: "#/properties/context_window_tokens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 16777216 || isNaN(data1)) {
                        validate52.errors = [{ instancePath: instancePath + "/context_window_tokens", schemaPath: "#/properties/context_window_tokens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16777216 }, message: "must be <= 16777216" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate52.errors = [{ instancePath: instancePath + "/context_window_tokens", schemaPath: "#/properties/context_window_tokens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                  if (data.model_id !== void 0) {
                    let data2 = data.model_id;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (func2(data2) > 128) {
                          validate52.errors = [{ instancePath: instancePath + "/model_id", schemaPath: "#/properties/model_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func2(data2) < 1) {
                            validate52.errors = [{ instancePath: instancePath + "/model_id", schemaPath: "#/properties/model_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern5.test(data2)) {
                              validate52.errors = [{ instancePath: instancePath + "/model_id", schemaPath: "#/properties/model_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate52.errors = [{ instancePath: instancePath + "/model_id", schemaPath: "#/properties/model_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.model_revision !== void 0) {
                      let data3 = data.model_revision;
                      const _errs7 = errors;
                      if (errors === _errs7) {
                        if (typeof data3 === "string") {
                          if (func2(data3) > 128) {
                            validate52.errors = [{ instancePath: instancePath + "/model_revision", schemaPath: "#/properties/model_revision/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func2(data3) < 1) {
                              validate52.errors = [{ instancePath: instancePath + "/model_revision", schemaPath: "#/properties/model_revision/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern5.test(data3)) {
                                validate52.errors = [{ instancePath: instancePath + "/model_revision", schemaPath: "#/properties/model_revision/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate52.errors = [{ instancePath: instancePath + "/model_revision", schemaPath: "#/properties/model_revision/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.provider_id !== void 0) {
                        let data4 = data.provider_id;
                        const _errs9 = errors;
                        if (errors === _errs9) {
                          if (typeof data4 === "string") {
                            if (func2(data4) > 128) {
                              validate52.errors = [{ instancePath: instancePath + "/provider_id", schemaPath: "#/properties/provider_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func2(data4) < 1) {
                                validate52.errors = [{ instancePath: instancePath + "/provider_id", schemaPath: "#/properties/provider_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern5.test(data4)) {
                                  validate52.errors = [{ instancePath: instancePath + "/provider_id", schemaPath: "#/properties/provider_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate52.errors = [{ instancePath: instancePath + "/provider_id", schemaPath: "#/properties/provider_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs9 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.tokenizer !== void 0) {
                          let data5 = data.tokenizer;
                          const _errs11 = errors;
                          const _errs12 = errors;
                          if (errors === _errs12) {
                            if (data5 && typeof data5 == "object" && !Array.isArray(data5)) {
                              let missing1;
                              if (data5.schema_id === void 0 && (missing1 = "schema_id") || data5.version === void 0 && (missing1 = "version") || data5.sha256 === void 0 && (missing1 = "sha256")) {
                                validate52.errors = [{ instancePath: instancePath + "/tokenizer", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                return false;
                              } else {
                                const _errs14 = errors;
                                for (const key1 in data5) {
                                  if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                                    validate52.errors = [{ instancePath: instancePath + "/tokenizer", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs14 === errors) {
                                  if (data5.schema_id !== void 0) {
                                    let data6 = data5.schema_id;
                                    const _errs15 = errors;
                                    if (errors === _errs15) {
                                      if (typeof data6 === "string") {
                                        if (func2(data6) > 128) {
                                          validate52.errors = [{ instancePath: instancePath + "/tokenizer/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func2(data6) < 1) {
                                            validate52.errors = [{ instancePath: instancePath + "/tokenizer/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data6)) {
                                              validate52.errors = [{ instancePath: instancePath + "/tokenizer/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate52.errors = [{ instancePath: instancePath + "/tokenizer/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid2 = _errs15 === errors;
                                  } else {
                                    var valid2 = true;
                                  }
                                  if (valid2) {
                                    if (data5.sha256 !== void 0) {
                                      let data7 = data5.sha256;
                                      const _errs17 = errors;
                                      if (errors === _errs17) {
                                        if (typeof data7 === "string") {
                                          if (!pattern4.test(data7)) {
                                            validate52.errors = [{ instancePath: instancePath + "/tokenizer/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                            return false;
                                          }
                                        } else {
                                          validate52.errors = [{ instancePath: instancePath + "/tokenizer/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                      }
                                      var valid2 = _errs17 === errors;
                                    } else {
                                      var valid2 = true;
                                    }
                                    if (valid2) {
                                      if (data5.version !== void 0) {
                                        let data8 = data5.version;
                                        const _errs19 = errors;
                                        if (typeof data8 !== "string") {
                                          validate52.errors = [{ instancePath: instancePath + "/tokenizer/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        if ("1" !== data8) {
                                          validate52.errors = [{ instancePath: instancePath + "/tokenizer/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                          return false;
                                        }
                                        var valid2 = _errs19 === errors;
                                      } else {
                                        var valid2 = true;
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              validate52.errors = [{ instancePath: instancePath + "/tokenizer", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
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
    var schema57 = { "additionalProperties": false, "properties": { "artifact": { "$ref": "#/$defs/ArtifactRef" }, "reason": { "enum": ["budget", "not_relevant", "unavailable", "not_authorized"], "title": "Reason", "type": "string" } }, "required": ["artifact", "reason"], "title": "ContextOmission", "type": "object" };
    function validate56(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate56.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.artifact === void 0 && (missing0 = "artifact") || data.reason === void 0 && (missing0 = "reason")) {
            validate56.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "reason")) {
                validate56.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                const _errs2 = errors;
                if (!validate49(data.artifact, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reason !== void 0) {
                  let data1 = data.reason;
                  const _errs3 = errors;
                  if (typeof data1 !== "string") {
                    validate56.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "budget" || data1 === "not_relevant" || data1 === "unavailable" || data1 === "not_authorized")) {
                    validate56.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/enum", keyword: "enum", params: { allowedValues: schema57.properties.reason.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate56.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate56.errors = vErrors;
      return errors === 0;
    }
    validate56.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.objective === void 0 && (missing0 = "objective") || data.prompt === void 0 && (missing0 = "prompt") || data.policy === void 0 && (missing0 = "policy") || data.model === void 0 && (missing0 = "model") || data.entries === void 0 && (missing0 = "entries") || data.omissions === void 0 && (missing0 = "omissions") || data.allowed_actions === void 0 && (missing0 = "allowed_actions") || data.output_schema === void 0 && (missing0 = "output_schema") || data.limits === void 0 && (missing0 = "limits")) {
            validate47.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func1.call(schema49.properties, key0)) {
                validate47.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.allowed_actions !== void 0) {
                let data0 = data.allowed_actions;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 4) {
                      validate47.errors = [{ instancePath: instancePath + "/allowed_actions", schemaPath: "#/properties/allowed_actions/maxItems", keyword: "maxItems", params: { limit: 4 }, message: "must NOT have more than 4 items" }];
                      return false;
                    } else {
                      if (data0.length < 1) {
                        validate47.errors = [{ instancePath: instancePath + "/allowed_actions", schemaPath: "#/properties/allowed_actions/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                        return false;
                      } else {
                        var valid1 = true;
                        const len0 = data0.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          let data1 = data0[i0];
                          const _errs4 = errors;
                          if (typeof data1 !== "string") {
                            validate47.errors = [{ instancePath: instancePath + "/allowed_actions/" + i0, schemaPath: "#/properties/allowed_actions/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if (!(data1 === "abstain" || data1 === "request_evidence" || data1 === "propose_knowledge_change" || data1 === "propose_campaign")) {
                            validate47.errors = [{ instancePath: instancePath + "/allowed_actions/" + i0, schemaPath: "#/properties/allowed_actions/items/enum", keyword: "enum", params: { allowedValues: schema49.properties.allowed_actions.items.enum }, message: "must be equal to one of the allowed values" }];
                            return false;
                          }
                          var valid1 = _errs4 === errors;
                          if (!valid1) {
                            break;
                          }
                        }
                      }
                    }
                  } else {
                    validate47.errors = [{ instancePath: instancePath + "/allowed_actions", schemaPath: "#/properties/allowed_actions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.entries !== void 0) {
                  let data2 = data.entries;
                  const _errs6 = errors;
                  if (errors === _errs6) {
                    if (Array.isArray(data2)) {
                      if (data2.length > 128) {
                        validate47.errors = [{ instancePath: instancePath + "/entries", schemaPath: "#/properties/entries/maxItems", keyword: "maxItems", params: { limit: 128 }, message: "must NOT have more than 128 items" }];
                        return false;
                      } else {
                        var valid2 = true;
                        const len1 = data2.length;
                        for (let i1 = 0; i1 < len1; i1++) {
                          const _errs8 = errors;
                          if (!validate48(data2[i1], { instancePath: instancePath + "/entries/" + i1, parentData: data2, parentDataProperty: i1, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
                            errors = vErrors.length;
                          }
                          var valid2 = _errs8 === errors;
                          if (!valid2) {
                            break;
                          }
                        }
                      }
                    } else {
                      validate47.errors = [{ instancePath: instancePath + "/entries", schemaPath: "#/properties/entries/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs6 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.limits !== void 0) {
                    let data4 = data.limits;
                    const _errs9 = errors;
                    const _errs10 = errors;
                    if (errors === _errs10) {
                      if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                        let missing1;
                        if (data4.max_input_tokens === void 0 && (missing1 = "max_input_tokens") || data4.max_output_tokens === void 0 && (missing1 = "max_output_tokens") || data4.max_attempts === void 0 && (missing1 = "max_attempts") || data4.total_tokens === void 0 && (missing1 = "total_tokens") || data4.total_accounting_units === void 0 && (missing1 = "total_accounting_units") || data4.accounting_unit === void 0 && (missing1 = "accounting_unit")) {
                          validate47.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/CallLimits/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs12 = errors;
                          for (const key1 in data4) {
                            if (!(key1 === "accounting_unit" || key1 === "max_attempts" || key1 === "max_input_tokens" || key1 === "max_output_tokens" || key1 === "total_accounting_units" || key1 === "total_tokens")) {
                              validate47.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/CallLimits/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs12 === errors) {
                            if (data4.accounting_unit !== void 0) {
                              let data5 = data4.accounting_unit;
                              const _errs13 = errors;
                              if (errors === _errs13) {
                                if (typeof data5 === "string") {
                                  if (func2(data5) > 128) {
                                    validate47.errors = [{ instancePath: instancePath + "/limits/accounting_unit", schemaPath: "#/$defs/CallLimits/properties/accounting_unit/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func2(data5) < 1) {
                                      validate47.errors = [{ instancePath: instancePath + "/limits/accounting_unit", schemaPath: "#/$defs/CallLimits/properties/accounting_unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data5)) {
                                        validate47.errors = [{ instancePath: instancePath + "/limits/accounting_unit", schemaPath: "#/$defs/CallLimits/properties/accounting_unit/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate47.errors = [{ instancePath: instancePath + "/limits/accounting_unit", schemaPath: "#/$defs/CallLimits/properties/accounting_unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid4 = _errs13 === errors;
                            } else {
                              var valid4 = true;
                            }
                            if (valid4) {
                              if (data4.max_attempts !== void 0) {
                                let data6 = data4.max_attempts;
                                const _errs15 = errors;
                                if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                                  validate47.errors = [{ instancePath: instancePath + "/limits/max_attempts", schemaPath: "#/$defs/CallLimits/properties/max_attempts/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                if (errors === _errs15) {
                                  if (typeof data6 == "number" && isFinite(data6)) {
                                    if (data6 > 16 || isNaN(data6)) {
                                      validate47.errors = [{ instancePath: instancePath + "/limits/max_attempts", schemaPath: "#/$defs/CallLimits/properties/max_attempts/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                                      return false;
                                    } else {
                                      if (data6 < 1 || isNaN(data6)) {
                                        validate47.errors = [{ instancePath: instancePath + "/limits/max_attempts", schemaPath: "#/$defs/CallLimits/properties/max_attempts/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                        return false;
                                      }
                                    }
                                  }
                                }
                                var valid4 = _errs15 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data4.max_input_tokens !== void 0) {
                                  let data7 = data4.max_input_tokens;
                                  const _errs17 = errors;
                                  if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                                    validate47.errors = [{ instancePath: instancePath + "/limits/max_input_tokens", schemaPath: "#/$defs/CallLimits/properties/max_input_tokens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                    return false;
                                  }
                                  if (errors === _errs17) {
                                    if (typeof data7 == "number" && isFinite(data7)) {
                                      if (data7 > 16777216 || isNaN(data7)) {
                                        validate47.errors = [{ instancePath: instancePath + "/limits/max_input_tokens", schemaPath: "#/$defs/CallLimits/properties/max_input_tokens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16777216 }, message: "must be <= 16777216" }];
                                        return false;
                                      } else {
                                        if (data7 < 1 || isNaN(data7)) {
                                          validate47.errors = [{ instancePath: instancePath + "/limits/max_input_tokens", schemaPath: "#/$defs/CallLimits/properties/max_input_tokens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                          return false;
                                        }
                                      }
                                    }
                                  }
                                  var valid4 = _errs17 === errors;
                                } else {
                                  var valid4 = true;
                                }
                                if (valid4) {
                                  if (data4.max_output_tokens !== void 0) {
                                    let data8 = data4.max_output_tokens;
                                    const _errs19 = errors;
                                    if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)) && isFinite(data8))) {
                                      validate47.errors = [{ instancePath: instancePath + "/limits/max_output_tokens", schemaPath: "#/$defs/CallLimits/properties/max_output_tokens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                      return false;
                                    }
                                    if (errors === _errs19) {
                                      if (typeof data8 == "number" && isFinite(data8)) {
                                        if (data8 > 16777216 || isNaN(data8)) {
                                          validate47.errors = [{ instancePath: instancePath + "/limits/max_output_tokens", schemaPath: "#/$defs/CallLimits/properties/max_output_tokens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16777216 }, message: "must be <= 16777216" }];
                                          return false;
                                        } else {
                                          if (data8 < 1 || isNaN(data8)) {
                                            validate47.errors = [{ instancePath: instancePath + "/limits/max_output_tokens", schemaPath: "#/$defs/CallLimits/properties/max_output_tokens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                            return false;
                                          }
                                        }
                                      }
                                    }
                                    var valid4 = _errs19 === errors;
                                  } else {
                                    var valid4 = true;
                                  }
                                  if (valid4) {
                                    if (data4.total_accounting_units !== void 0) {
                                      let data9 = data4.total_accounting_units;
                                      const _errs21 = errors;
                                      if (!(typeof data9 == "number" && (!(data9 % 1) && !isNaN(data9)) && isFinite(data9))) {
                                        validate47.errors = [{ instancePath: instancePath + "/limits/total_accounting_units", schemaPath: "#/$defs/CallLimits/properties/total_accounting_units/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                        return false;
                                      }
                                      if (errors === _errs21) {
                                        if (typeof data9 == "number" && isFinite(data9)) {
                                          if (data9 > 9007199254740991 || isNaN(data9)) {
                                            validate47.errors = [{ instancePath: instancePath + "/limits/total_accounting_units", schemaPath: "#/$defs/CallLimits/properties/total_accounting_units/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                            return false;
                                          } else {
                                            if (data9 < 1 || isNaN(data9)) {
                                              validate47.errors = [{ instancePath: instancePath + "/limits/total_accounting_units", schemaPath: "#/$defs/CallLimits/properties/total_accounting_units/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                              return false;
                                            }
                                          }
                                        }
                                      }
                                      var valid4 = _errs21 === errors;
                                    } else {
                                      var valid4 = true;
                                    }
                                    if (valid4) {
                                      if (data4.total_tokens !== void 0) {
                                        let data10 = data4.total_tokens;
                                        const _errs23 = errors;
                                        if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)) && isFinite(data10))) {
                                          validate47.errors = [{ instancePath: instancePath + "/limits/total_tokens", schemaPath: "#/$defs/CallLimits/properties/total_tokens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                          return false;
                                        }
                                        if (errors === _errs23) {
                                          if (typeof data10 == "number" && isFinite(data10)) {
                                            if (data10 > 268435456 || isNaN(data10)) {
                                              validate47.errors = [{ instancePath: instancePath + "/limits/total_tokens", schemaPath: "#/$defs/CallLimits/properties/total_tokens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 268435456 }, message: "must be <= 268435456" }];
                                              return false;
                                            } else {
                                              if (data10 < 1 || isNaN(data10)) {
                                                validate47.errors = [{ instancePath: instancePath + "/limits/total_tokens", schemaPath: "#/$defs/CallLimits/properties/total_tokens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                                return false;
                                              }
                                            }
                                          }
                                        }
                                        var valid4 = _errs23 === errors;
                                      } else {
                                        var valid4 = true;
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      } else {
                        validate47.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/CallLimits/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.model !== void 0) {
                      const _errs25 = errors;
                      if (!validate52(data.model, { instancePath: instancePath + "/model", parentData: data, parentDataProperty: "model", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate52.errors : vErrors.concat(validate52.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs25 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.objective !== void 0) {
                        const _errs26 = errors;
                        if (!validate49(data.objective, { instancePath: instancePath + "/objective", parentData: data, parentDataProperty: "objective", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.omissions !== void 0) {
                          let data13 = data.omissions;
                          const _errs27 = errors;
                          if (errors === _errs27) {
                            if (Array.isArray(data13)) {
                              if (data13.length > 128) {
                                validate47.errors = [{ instancePath: instancePath + "/omissions", schemaPath: "#/properties/omissions/maxItems", keyword: "maxItems", params: { limit: 128 }, message: "must NOT have more than 128 items" }];
                                return false;
                              } else {
                                var valid5 = true;
                                const len2 = data13.length;
                                for (let i2 = 0; i2 < len2; i2++) {
                                  const _errs29 = errors;
                                  if (!validate56(data13[i2], { instancePath: instancePath + "/omissions/" + i2, parentData: data13, parentDataProperty: i2, rootData, dynamicAnchors })) {
                                    vErrors = vErrors === null ? validate56.errors : vErrors.concat(validate56.errors);
                                    errors = vErrors.length;
                                  }
                                  var valid5 = _errs29 === errors;
                                  if (!valid5) {
                                    break;
                                  }
                                }
                              }
                            } else {
                              validate47.errors = [{ instancePath: instancePath + "/omissions", schemaPath: "#/properties/omissions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs27 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.output_schema !== void 0) {
                            let data15 = data.output_schema;
                            const _errs30 = errors;
                            const _errs31 = errors;
                            if (errors === _errs31) {
                              if (data15 && typeof data15 == "object" && !Array.isArray(data15)) {
                                let missing2;
                                if (data15.schema_id === void 0 && (missing2 = "schema_id") || data15.version === void 0 && (missing2 = "version") || data15.sha256 === void 0 && (missing2 = "sha256")) {
                                  validate47.errors = [{ instancePath: instancePath + "/output_schema", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                  return false;
                                } else {
                                  const _errs33 = errors;
                                  for (const key2 in data15) {
                                    if (!(key2 === "schema_id" || key2 === "sha256" || key2 === "version")) {
                                      validate47.errors = [{ instancePath: instancePath + "/output_schema", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                      return false;
                                      break;
                                    }
                                  }
                                  if (_errs33 === errors) {
                                    if (data15.schema_id !== void 0) {
                                      let data16 = data15.schema_id;
                                      const _errs34 = errors;
                                      if (errors === _errs34) {
                                        if (typeof data16 === "string") {
                                          if (func2(data16) > 128) {
                                            validate47.errors = [{ instancePath: instancePath + "/output_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                            return false;
                                          } else {
                                            if (func2(data16) < 1) {
                                              validate47.errors = [{ instancePath: instancePath + "/output_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                              return false;
                                            } else {
                                              if (!pattern5.test(data16)) {
                                                validate47.errors = [{ instancePath: instancePath + "/output_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                return false;
                                              }
                                            }
                                          }
                                        } else {
                                          validate47.errors = [{ instancePath: instancePath + "/output_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                      }
                                      var valid7 = _errs34 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                    if (valid7) {
                                      if (data15.sha256 !== void 0) {
                                        let data17 = data15.sha256;
                                        const _errs36 = errors;
                                        if (errors === _errs36) {
                                          if (typeof data17 === "string") {
                                            if (!pattern4.test(data17)) {
                                              validate47.errors = [{ instancePath: instancePath + "/output_schema/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                              return false;
                                            }
                                          } else {
                                            validate47.errors = [{ instancePath: instancePath + "/output_schema/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid7 = _errs36 === errors;
                                      } else {
                                        var valid7 = true;
                                      }
                                      if (valid7) {
                                        if (data15.version !== void 0) {
                                          let data18 = data15.version;
                                          const _errs38 = errors;
                                          if (typeof data18 !== "string") {
                                            validate47.errors = [{ instancePath: instancePath + "/output_schema/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                          if ("1" !== data18) {
                                            validate47.errors = [{ instancePath: instancePath + "/output_schema/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                            return false;
                                          }
                                          var valid7 = _errs38 === errors;
                                        } else {
                                          var valid7 = true;
                                        }
                                      }
                                    }
                                  }
                                }
                              } else {
                                validate47.errors = [{ instancePath: instancePath + "/output_schema", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                return false;
                              }
                            }
                            var valid0 = _errs30 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.policy !== void 0) {
                              const _errs40 = errors;
                              if (!validate49(data.policy, { instancePath: instancePath + "/policy", parentData: data, parentDataProperty: "policy", rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                                errors = vErrors.length;
                              }
                              var valid0 = _errs40 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.prompt !== void 0) {
                                const _errs41 = errors;
                                if (!validate49(data.prompt, { instancePath: instancePath + "/prompt", parentData: data, parentDataProperty: "prompt", rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                                  errors = vErrors.length;
                                }
                                var valid0 = _errs41 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.schema_version !== void 0) {
                                  let data21 = data.schema_version;
                                  const _errs42 = errors;
                                  if (typeof data21 !== "string") {
                                    validate47.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data21) {
                                    validate47.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid0 = _errs42 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.scope !== void 0) {
                                    let data22 = data.scope;
                                    const _errs44 = errors;
                                    const _errs45 = errors;
                                    if (errors === _errs45) {
                                      if (data22 && typeof data22 == "object" && !Array.isArray(data22)) {
                                        let missing3;
                                        if (data22.tenant_id === void 0 && (missing3 = "tenant_id") || data22.project_id === void 0 && (missing3 = "project_id")) {
                                          validate47.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" }];
                                          return false;
                                        } else {
                                          const _errs47 = errors;
                                          for (const key3 in data22) {
                                            if (!(key3 === "project_id" || key3 === "tenant_id")) {
                                              validate47.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" }];
                                              return false;
                                              break;
                                            }
                                          }
                                          if (_errs47 === errors) {
                                            if (data22.project_id !== void 0) {
                                              let data23 = data22.project_id;
                                              const _errs48 = errors;
                                              if (errors === _errs48) {
                                                if (typeof data23 === "string") {
                                                  if (func2(data23) > 128) {
                                                    validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                    return false;
                                                  } else {
                                                    if (func2(data23) < 1) {
                                                      validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                      return false;
                                                    } else {
                                                      if (!pattern5.test(data23)) {
                                                        validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                        return false;
                                                      }
                                                    }
                                                  }
                                                } else {
                                                  validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                  return false;
                                                }
                                              }
                                              var valid9 = _errs48 === errors;
                                            } else {
                                              var valid9 = true;
                                            }
                                            if (valid9) {
                                              if (data22.tenant_id !== void 0) {
                                                let data24 = data22.tenant_id;
                                                const _errs50 = errors;
                                                if (errors === _errs50) {
                                                  if (typeof data24 === "string") {
                                                    if (func2(data24) > 128) {
                                                      validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                      return false;
                                                    } else {
                                                      if (func2(data24) < 1) {
                                                        validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                        return false;
                                                      } else {
                                                        if (!pattern5.test(data24)) {
                                                          validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                          return false;
                                                        }
                                                      }
                                                    }
                                                  } else {
                                                    validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                    return false;
                                                  }
                                                }
                                                var valid9 = _errs50 === errors;
                                              } else {
                                                var valid9 = true;
                                              }
                                            }
                                          }
                                        }
                                      } else {
                                        validate47.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                        return false;
                                      }
                                    }
                                    var valid0 = _errs44 === errors;
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
          validate47.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate47.errors = vErrors;
      return errors === 0;
    }
    validate47.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate42(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate42.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.actor_id === void 0 && (missing0 = "actor_id") || data.attempt === void 0 && (missing0 = "attempt") || data.preparation_sha256 === void 0 && (missing0 = "preparation_sha256") || data.prepared_proposal_sha256 === void 0 && (missing0 = "prepared_proposal_sha256") || data.output_sha256 === void 0 && (missing0 = "output_sha256") || data.action === void 0 && (missing0 = "action") || data.rationale === void 0 && (missing0 = "rationale") || data.context === void 0 && (missing0 = "context") || data.usage === void 0 && (missing0 = "usage") || data.capture_publication === void 0 && (missing0 = "capture_publication")) {
            validate42.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func1.call(schema45.properties, key0)) {
                validate42.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.action !== void 0) {
                let data0 = data.action;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate42.errors = [{ instancePath: instancePath + "/action", schemaPath: "#/properties/action/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("propose_campaign" !== data0) {
                  validate42.errors = [{ instancePath: instancePath + "/action", schemaPath: "#/properties/action/const", keyword: "const", params: { allowedValue: "propose_campaign" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.actor_id !== void 0) {
                  let data1 = data.actor_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func2(data1) > 128) {
                        validate42.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func2(data1) < 1) {
                          validate42.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data1)) {
                            validate42.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate42.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.attempt !== void 0) {
                    const _errs6 = errors;
                    if (!validate43(data.attempt, { instancePath: instancePath + "/attempt", parentData: data, parentDataProperty: "attempt", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate43.errors : vErrors.concat(validate43.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.capture_publication !== void 0) {
                      let data3 = data.capture_publication;
                      const _errs7 = errors;
                      if (typeof data3 !== "string") {
                        validate42.errors = [{ instancePath: instancePath + "/capture_publication", schemaPath: "#/properties/capture_publication/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("not_published" !== data3) {
                        validate42.errors = [{ instancePath: instancePath + "/capture_publication", schemaPath: "#/properties/capture_publication/const", keyword: "const", params: { allowedValue: "not_published" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.context !== void 0) {
                        const _errs9 = errors;
                        if (!validate47(data.context, { instancePath: instancePath + "/context", parentData: data, parentDataProperty: "context", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate47.errors : vErrors.concat(validate47.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs9 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.output_sha256 !== void 0) {
                          let data5 = data.output_sha256;
                          const _errs10 = errors;
                          if (errors === _errs10) {
                            if (typeof data5 === "string") {
                              if (!pattern4.test(data5)) {
                                validate42.errors = [{ instancePath: instancePath + "/output_sha256", schemaPath: "#/properties/output_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                return false;
                              }
                            } else {
                              validate42.errors = [{ instancePath: instancePath + "/output_sha256", schemaPath: "#/properties/output_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid0 = _errs10 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.preparation_sha256 !== void 0) {
                            let data6 = data.preparation_sha256;
                            const _errs12 = errors;
                            if (errors === _errs12) {
                              if (typeof data6 === "string") {
                                if (!pattern4.test(data6)) {
                                  validate42.errors = [{ instancePath: instancePath + "/preparation_sha256", schemaPath: "#/properties/preparation_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate42.errors = [{ instancePath: instancePath + "/preparation_sha256", schemaPath: "#/properties/preparation_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid0 = _errs12 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.prepared_proposal_sha256 !== void 0) {
                              let data7 = data.prepared_proposal_sha256;
                              const _errs14 = errors;
                              if (errors === _errs14) {
                                if (typeof data7 === "string") {
                                  if (!pattern4.test(data7)) {
                                    validate42.errors = [{ instancePath: instancePath + "/prepared_proposal_sha256", schemaPath: "#/properties/prepared_proposal_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                    return false;
                                  }
                                } else {
                                  validate42.errors = [{ instancePath: instancePath + "/prepared_proposal_sha256", schemaPath: "#/properties/prepared_proposal_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs14 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.rationale !== void 0) {
                                let data8 = data.rationale;
                                const _errs16 = errors;
                                if (errors === _errs16) {
                                  if (typeof data8 === "string") {
                                    if (func2(data8) > 4096) {
                                      validate42.errors = [{ instancePath: instancePath + "/rationale", schemaPath: "#/properties/rationale/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                                      return false;
                                    } else {
                                      if (func2(data8) < 1) {
                                        validate42.errors = [{ instancePath: instancePath + "/rationale", schemaPath: "#/properties/rationale/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      }
                                    }
                                  } else {
                                    validate42.errors = [{ instancePath: instancePath + "/rationale", schemaPath: "#/properties/rationale/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs16 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.usage !== void 0) {
                                  let data9 = data.usage;
                                  const _errs18 = errors;
                                  const _errs19 = errors;
                                  if (errors === _errs19) {
                                    if (data9 && typeof data9 == "object" && !Array.isArray(data9)) {
                                      let missing1;
                                      if (data9.input_tokens === void 0 && (missing1 = "input_tokens") || data9.output_tokens === void 0 && (missing1 = "output_tokens") || data9.accounting_units === void 0 && (missing1 = "accounting_units") || data9.certainty === void 0 && (missing1 = "certainty")) {
                                        validate42.errors = [{ instancePath: instancePath + "/usage", schemaPath: "#/$defs/ProviderUsage/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                        return false;
                                      } else {
                                        const _errs21 = errors;
                                        for (const key1 in data9) {
                                          if (!(key1 === "accounting_units" || key1 === "certainty" || key1 === "input_tokens" || key1 === "output_tokens")) {
                                            validate42.errors = [{ instancePath: instancePath + "/usage", schemaPath: "#/$defs/ProviderUsage/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                            return false;
                                            break;
                                          }
                                        }
                                        if (_errs21 === errors) {
                                          if (data9.accounting_units !== void 0) {
                                            let data10 = data9.accounting_units;
                                            const _errs22 = errors;
                                            const _errs23 = errors;
                                            let valid3 = false;
                                            const _errs24 = errors;
                                            if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)) && isFinite(data10))) {
                                              const err0 = { instancePath: instancePath + "/usage/accounting_units", schemaPath: "#/$defs/ProviderUsage/properties/accounting_units/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                              if (vErrors === null) {
                                                vErrors = [err0];
                                              } else {
                                                vErrors.push(err0);
                                              }
                                              errors++;
                                            }
                                            if (errors === _errs24) {
                                              if (typeof data10 == "number" && isFinite(data10)) {
                                                if (data10 > 9007199254740991 || isNaN(data10)) {
                                                  const err1 = { instancePath: instancePath + "/usage/accounting_units", schemaPath: "#/$defs/ProviderUsage/properties/accounting_units/anyOf/0/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" };
                                                  if (vErrors === null) {
                                                    vErrors = [err1];
                                                  } else {
                                                    vErrors.push(err1);
                                                  }
                                                  errors++;
                                                } else {
                                                  if (data10 < 0 || isNaN(data10)) {
                                                    const err2 = { instancePath: instancePath + "/usage/accounting_units", schemaPath: "#/$defs/ProviderUsage/properties/accounting_units/anyOf/0/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                                            var _valid0 = _errs24 === errors;
                                            valid3 = valid3 || _valid0;
                                            const _errs26 = errors;
                                            if (data10 !== null) {
                                              const err3 = { instancePath: instancePath + "/usage/accounting_units", schemaPath: "#/$defs/ProviderUsage/properties/accounting_units/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                              if (vErrors === null) {
                                                vErrors = [err3];
                                              } else {
                                                vErrors.push(err3);
                                              }
                                              errors++;
                                            }
                                            var _valid0 = _errs26 === errors;
                                            valid3 = valid3 || _valid0;
                                            if (!valid3) {
                                              const err4 = { instancePath: instancePath + "/usage/accounting_units", schemaPath: "#/$defs/ProviderUsage/properties/accounting_units/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                              if (vErrors === null) {
                                                vErrors = [err4];
                                              } else {
                                                vErrors.push(err4);
                                              }
                                              errors++;
                                              validate42.errors = vErrors;
                                              return false;
                                            } else {
                                              errors = _errs23;
                                              if (vErrors !== null) {
                                                if (_errs23) {
                                                  vErrors.length = _errs23;
                                                } else {
                                                  vErrors = null;
                                                }
                                              }
                                            }
                                            var valid2 = _errs22 === errors;
                                          } else {
                                            var valid2 = true;
                                          }
                                          if (valid2) {
                                            if (data9.certainty !== void 0) {
                                              let data11 = data9.certainty;
                                              const _errs28 = errors;
                                              if (typeof data11 !== "string") {
                                                validate42.errors = [{ instancePath: instancePath + "/usage/certainty", schemaPath: "#/$defs/ProviderUsage/properties/certainty/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                              if (!(data11 === "reported" || data11 === "unknown")) {
                                                validate42.errors = [{ instancePath: instancePath + "/usage/certainty", schemaPath: "#/$defs/ProviderUsage/properties/certainty/enum", keyword: "enum", params: { allowedValues: schema60.properties.certainty.enum }, message: "must be equal to one of the allowed values" }];
                                                return false;
                                              }
                                              var valid2 = _errs28 === errors;
                                            } else {
                                              var valid2 = true;
                                            }
                                            if (valid2) {
                                              if (data9.input_tokens !== void 0) {
                                                let data12 = data9.input_tokens;
                                                const _errs30 = errors;
                                                const _errs31 = errors;
                                                let valid4 = false;
                                                const _errs32 = errors;
                                                if (!(typeof data12 == "number" && (!(data12 % 1) && !isNaN(data12)) && isFinite(data12))) {
                                                  const err5 = { instancePath: instancePath + "/usage/input_tokens", schemaPath: "#/$defs/ProviderUsage/properties/input_tokens/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                                  if (vErrors === null) {
                                                    vErrors = [err5];
                                                  } else {
                                                    vErrors.push(err5);
                                                  }
                                                  errors++;
                                                }
                                                if (errors === _errs32) {
                                                  if (typeof data12 == "number" && isFinite(data12)) {
                                                    if (data12 > 16777216 || isNaN(data12)) {
                                                      const err6 = { instancePath: instancePath + "/usage/input_tokens", schemaPath: "#/$defs/ProviderUsage/properties/input_tokens/anyOf/0/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16777216 }, message: "must be <= 16777216" };
                                                      if (vErrors === null) {
                                                        vErrors = [err6];
                                                      } else {
                                                        vErrors.push(err6);
                                                      }
                                                      errors++;
                                                    } else {
                                                      if (data12 < 0 || isNaN(data12)) {
                                                        const err7 = { instancePath: instancePath + "/usage/input_tokens", schemaPath: "#/$defs/ProviderUsage/properties/input_tokens/anyOf/0/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                                                var _valid1 = _errs32 === errors;
                                                valid4 = valid4 || _valid1;
                                                const _errs34 = errors;
                                                if (data12 !== null) {
                                                  const err8 = { instancePath: instancePath + "/usage/input_tokens", schemaPath: "#/$defs/ProviderUsage/properties/input_tokens/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                  if (vErrors === null) {
                                                    vErrors = [err8];
                                                  } else {
                                                    vErrors.push(err8);
                                                  }
                                                  errors++;
                                                }
                                                var _valid1 = _errs34 === errors;
                                                valid4 = valid4 || _valid1;
                                                if (!valid4) {
                                                  const err9 = { instancePath: instancePath + "/usage/input_tokens", schemaPath: "#/$defs/ProviderUsage/properties/input_tokens/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                  if (vErrors === null) {
                                                    vErrors = [err9];
                                                  } else {
                                                    vErrors.push(err9);
                                                  }
                                                  errors++;
                                                  validate42.errors = vErrors;
                                                  return false;
                                                } else {
                                                  errors = _errs31;
                                                  if (vErrors !== null) {
                                                    if (_errs31) {
                                                      vErrors.length = _errs31;
                                                    } else {
                                                      vErrors = null;
                                                    }
                                                  }
                                                }
                                                var valid2 = _errs30 === errors;
                                              } else {
                                                var valid2 = true;
                                              }
                                              if (valid2) {
                                                if (data9.output_tokens !== void 0) {
                                                  let data13 = data9.output_tokens;
                                                  const _errs36 = errors;
                                                  const _errs37 = errors;
                                                  let valid5 = false;
                                                  const _errs38 = errors;
                                                  if (!(typeof data13 == "number" && (!(data13 % 1) && !isNaN(data13)) && isFinite(data13))) {
                                                    const err10 = { instancePath: instancePath + "/usage/output_tokens", schemaPath: "#/$defs/ProviderUsage/properties/output_tokens/anyOf/0/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                                    if (vErrors === null) {
                                                      vErrors = [err10];
                                                    } else {
                                                      vErrors.push(err10);
                                                    }
                                                    errors++;
                                                  }
                                                  if (errors === _errs38) {
                                                    if (typeof data13 == "number" && isFinite(data13)) {
                                                      if (data13 > 16777216 || isNaN(data13)) {
                                                        const err11 = { instancePath: instancePath + "/usage/output_tokens", schemaPath: "#/$defs/ProviderUsage/properties/output_tokens/anyOf/0/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16777216 }, message: "must be <= 16777216" };
                                                        if (vErrors === null) {
                                                          vErrors = [err11];
                                                        } else {
                                                          vErrors.push(err11);
                                                        }
                                                        errors++;
                                                      } else {
                                                        if (data13 < 0 || isNaN(data13)) {
                                                          const err12 = { instancePath: instancePath + "/usage/output_tokens", schemaPath: "#/$defs/ProviderUsage/properties/output_tokens/anyOf/0/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                                          if (vErrors === null) {
                                                            vErrors = [err12];
                                                          } else {
                                                            vErrors.push(err12);
                                                          }
                                                          errors++;
                                                        }
                                                      }
                                                    }
                                                  }
                                                  var _valid2 = _errs38 === errors;
                                                  valid5 = valid5 || _valid2;
                                                  const _errs40 = errors;
                                                  if (data13 !== null) {
                                                    const err13 = { instancePath: instancePath + "/usage/output_tokens", schemaPath: "#/$defs/ProviderUsage/properties/output_tokens/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                                    if (vErrors === null) {
                                                      vErrors = [err13];
                                                    } else {
                                                      vErrors.push(err13);
                                                    }
                                                    errors++;
                                                  }
                                                  var _valid2 = _errs40 === errors;
                                                  valid5 = valid5 || _valid2;
                                                  if (!valid5) {
                                                    const err14 = { instancePath: instancePath + "/usage/output_tokens", schemaPath: "#/$defs/ProviderUsage/properties/output_tokens/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                                    if (vErrors === null) {
                                                      vErrors = [err14];
                                                    } else {
                                                      vErrors.push(err14);
                                                    }
                                                    errors++;
                                                    validate42.errors = vErrors;
                                                    return false;
                                                  } else {
                                                    errors = _errs37;
                                                    if (vErrors !== null) {
                                                      if (_errs37) {
                                                        vErrors.length = _errs37;
                                                      } else {
                                                        vErrors = null;
                                                      }
                                                    }
                                                  }
                                                  var valid2 = _errs36 === errors;
                                                } else {
                                                  var valid2 = true;
                                                }
                                              }
                                            }
                                          }
                                        }
                                      }
                                    } else {
                                      validate42.errors = [{ instancePath: instancePath + "/usage", schemaPath: "#/$defs/ProviderUsage/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                      return false;
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
        } else {
          validate42.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate42.errors = vErrors;
      return errors === 0;
    }
    validate42.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema62 = { "additionalProperties": false, "properties": { "criterion_ids": { "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 32, "title": "Criterion Ids", "type": "array" }, "kind": { "enum": ["question", "need", "assessment"], "title": "Kind", "type": "string" }, "record_sha256": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "title": "Record Sha256" }, "reference": { "anyOf": [{ "$ref": "#/$defs/ResearchQuestionRef" }, { "$ref": "#/$defs/EvidenceNeedRef" }, { "$ref": "#/$defs/EvidenceAssessmentRequest" }], "title": "Reference" }, "unavailable": { "anyOf": [{ "enum": ["not_provided", "unavailable", "denied", "pending", "failed"], "type": "string" }, { "type": "null" }], "title": "Unavailable" } }, "required": ["kind", "reference", "record_sha256", "unavailable", "criterion_ids"], "title": "CampaignOriginResearchRecord", "type": "object" };
    function validate65(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate65.evaluated;
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
            validate65.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "question_id" || key0 === "revision" || key0 === "scope")) {
                validate65.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func2(data0) > 128) {
                      validate65.errors = [{ instancePath: instancePath + "/question_id", schemaPath: "#/properties/question_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate65.errors = [{ instancePath: instancePath + "/question_id", schemaPath: "#/properties/question_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate65.errors = [{ instancePath: instancePath + "/question_id", schemaPath: "#/properties/question_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate65.errors = [{ instancePath: instancePath + "/question_id", schemaPath: "#/properties/question_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate65.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate65.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate65.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate65.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate65.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                  if (func2(data3) > 128) {
                                    validate65.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func2(data3) < 1) {
                                      validate65.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate65.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate65.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    if (func2(data4) > 128) {
                                      validate65.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func2(data4) < 1) {
                                        validate65.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data4)) {
                                          validate65.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate65.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate65.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate65.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate65.errors = vErrors;
      return errors === 0;
    }
    validate65.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate67(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate67.evaluated;
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
            validate67.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "need_id" || key0 === "revision" || key0 === "scope")) {
                validate67.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func2(data0) > 128) {
                      validate67.errors = [{ instancePath: instancePath + "/need_id", schemaPath: "#/properties/need_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate67.errors = [{ instancePath: instancePath + "/need_id", schemaPath: "#/properties/need_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate67.errors = [{ instancePath: instancePath + "/need_id", schemaPath: "#/properties/need_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate67.errors = [{ instancePath: instancePath + "/need_id", schemaPath: "#/properties/need_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate67.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate67.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate67.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate67.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate67.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                  if (func2(data3) > 128) {
                                    validate67.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func2(data3) < 1) {
                                      validate67.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate67.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate67.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    if (func2(data4) > 128) {
                                      validate67.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func2(data4) < 1) {
                                        validate67.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data4)) {
                                          validate67.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate67.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate67.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate67.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate67.errors = vErrors;
      return errors === 0;
    }
    validate67.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.criterion_id === void 0 && (missing0 = "criterion_id") || data.artifact === void 0 && (missing0 = "artifact")) {
            validate70.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "criterion_id")) {
                validate70.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                const _errs2 = errors;
                if (!validate49(data.artifact, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.criterion_id !== void 0) {
                  let data1 = data.criterion_id;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (func2(data1) > 128) {
                        validate70.errors = [{ instancePath: instancePath + "/criterion_id", schemaPath: "#/properties/criterion_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func2(data1) < 1) {
                          validate70.errors = [{ instancePath: instancePath + "/criterion_id", schemaPath: "#/properties/criterion_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data1)) {
                            validate70.errors = [{ instancePath: instancePath + "/criterion_id", schemaPath: "#/properties/criterion_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate70.errors = [{ instancePath: instancePath + "/criterion_id", schemaPath: "#/properties/criterion_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.profile_id === void 0 && (missing0 = "profile_id") || data.version === void 0 && (missing0 = "version") || data.sha256 === void 0 && (missing0 = "sha256")) {
            validate73.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "profile_id" || key0 === "scope" || key0 === "sha256" || key0 === "version")) {
                validate73.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.profile_id !== void 0) {
                let data0 = data.profile_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func2(data0) > 128) {
                      validate73.errors = [{ instancePath: instancePath + "/profile_id", schemaPath: "#/properties/profile_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate73.errors = [{ instancePath: instancePath + "/profile_id", schemaPath: "#/properties/profile_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate73.errors = [{ instancePath: instancePath + "/profile_id", schemaPath: "#/properties/profile_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate73.errors = [{ instancePath: instancePath + "/profile_id", schemaPath: "#/properties/profile_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate73.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate73.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                if (func2(data2) > 128) {
                                  validate73.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func2(data2) < 1) {
                                    validate73.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern5.test(data2)) {
                                      validate73.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate73.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                  if (func2(data3) > 128) {
                                    validate73.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func2(data3) < 1) {
                                      validate73.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate73.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate73.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate73.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.sha256 !== void 0) {
                    let data4 = data.sha256;
                    const _errs12 = errors;
                    if (errors === _errs12) {
                      if (typeof data4 === "string") {
                        if (!pattern4.test(data4)) {
                          validate73.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate73.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs12 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.version !== void 0) {
                      let data5 = data.version;
                      const _errs14 = errors;
                      if (errors === _errs14) {
                        if (typeof data5 === "string") {
                          if (func2(data5) > 128) {
                            validate73.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func2(data5) < 1) {
                              validate73.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern5.test(data5)) {
                                validate73.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate73.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
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
        } else {
          validate73.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate73.errors = vErrors;
      return errors === 0;
    }
    validate73.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.assessment_id === void 0 && (missing0 = "assessment_id") || data.profile === void 0 && (missing0 = "profile") || data.question === void 0 && (missing0 = "question") || data.answers === void 0 && (missing0 = "answers") || data.receipts === void 0 && (missing0 = "receipts")) {
            validate69.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "answers" || key0 === "assessment_id" || key0 === "profile" || key0 === "question" || key0 === "receipts" || key0 === "wire_version")) {
                validate69.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.answers !== void 0) {
                let data0 = data.answers;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 32) {
                      validate69.errors = [{ instancePath: instancePath + "/answers", schemaPath: "#/properties/answers/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate70(data0[i0], { instancePath: instancePath + "/answers/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate70.errors : vErrors.concat(validate70.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate69.errors = [{ instancePath: instancePath + "/answers", schemaPath: "#/properties/answers/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.assessment_id !== void 0) {
                  let data2 = data.assessment_id;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (typeof data2 === "string") {
                      if (func2(data2) > 128) {
                        validate69.errors = [{ instancePath: instancePath + "/assessment_id", schemaPath: "#/properties/assessment_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func2(data2) < 1) {
                          validate69.errors = [{ instancePath: instancePath + "/assessment_id", schemaPath: "#/properties/assessment_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data2)) {
                            validate69.errors = [{ instancePath: instancePath + "/assessment_id", schemaPath: "#/properties/assessment_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate69.errors = [{ instancePath: instancePath + "/assessment_id", schemaPath: "#/properties/assessment_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.profile !== void 0) {
                    const _errs7 = errors;
                    if (!validate73(data.profile, { instancePath: instancePath + "/profile", parentData: data, parentDataProperty: "profile", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate73.errors : vErrors.concat(validate73.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs7 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.question !== void 0) {
                      const _errs8 = errors;
                      if (!validate65(data.question, { instancePath: instancePath + "/question", parentData: data, parentDataProperty: "question", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate65.errors : vErrors.concat(validate65.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.receipts !== void 0) {
                        let data5 = data.receipts;
                        const _errs9 = errors;
                        if (errors === _errs9) {
                          if (Array.isArray(data5)) {
                            if (data5.length > 256) {
                              validate69.errors = [{ instancePath: instancePath + "/receipts", schemaPath: "#/properties/receipts/maxItems", keyword: "maxItems", params: { limit: 256 }, message: "must NOT have more than 256 items" }];
                              return false;
                            } else {
                              var valid2 = true;
                              const len1 = data5.length;
                              for (let i1 = 0; i1 < len1; i1++) {
                                const _errs11 = errors;
                                if (!validate49(data5[i1], { instancePath: instancePath + "/receipts/" + i1, parentData: data5, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                                  errors = vErrors.length;
                                }
                                var valid2 = _errs11 === errors;
                                if (!valid2) {
                                  break;
                                }
                              }
                            }
                          } else {
                            validate69.errors = [{ instancePath: instancePath + "/receipts", schemaPath: "#/properties/receipts/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs9 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.wire_version !== void 0) {
                          let data7 = data.wire_version;
                          const _errs12 = errors;
                          if (typeof data7 !== "string") {
                            validate69.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("1" !== data7) {
                            validate69.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs12 === errors;
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
          validate69.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate69.errors = vErrors;
      return errors === 0;
    }
    validate69.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate64(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate64.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.reference === void 0 && (missing0 = "reference") || data.record_sha256 === void 0 && (missing0 = "record_sha256") || data.unavailable === void 0 && (missing0 = "unavailable") || data.criterion_ids === void 0 && (missing0 = "criterion_ids")) {
            validate64.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "criterion_ids" || key0 === "kind" || key0 === "record_sha256" || key0 === "reference" || key0 === "unavailable")) {
                validate64.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.criterion_ids !== void 0) {
                let data0 = data.criterion_ids;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 32) {
                      validate64.errors = [{ instancePath: instancePath + "/criterion_ids", schemaPath: "#/properties/criterion_ids/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        let data1 = data0[i0];
                        const _errs4 = errors;
                        if (errors === _errs4) {
                          if (typeof data1 === "string") {
                            if (func2(data1) > 128) {
                              validate64.errors = [{ instancePath: instancePath + "/criterion_ids/" + i0, schemaPath: "#/properties/criterion_ids/items/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func2(data1) < 1) {
                                validate64.errors = [{ instancePath: instancePath + "/criterion_ids/" + i0, schemaPath: "#/properties/criterion_ids/items/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern5.test(data1)) {
                                  validate64.errors = [{ instancePath: instancePath + "/criterion_ids/" + i0, schemaPath: "#/properties/criterion_ids/items/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate64.errors = [{ instancePath: instancePath + "/criterion_ids/" + i0, schemaPath: "#/properties/criterion_ids/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate64.errors = [{ instancePath: instancePath + "/criterion_ids", schemaPath: "#/properties/criterion_ids/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.kind !== void 0) {
                  let data2 = data.kind;
                  const _errs6 = errors;
                  if (typeof data2 !== "string") {
                    validate64.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data2 === "question" || data2 === "need" || data2 === "assessment")) {
                    validate64.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/enum", keyword: "enum", params: { allowedValues: schema62.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs6 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.record_sha256 !== void 0) {
                    let data3 = data.record_sha256;
                    const _errs8 = errors;
                    const _errs9 = errors;
                    let valid2 = false;
                    const _errs10 = errors;
                    if (errors === _errs10) {
                      if (typeof data3 === "string") {
                        if (!pattern4.test(data3)) {
                          const err0 = { instancePath: instancePath + "/record_sha256", schemaPath: "#/properties/record_sha256/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        }
                      } else {
                        const err1 = { instancePath: instancePath + "/record_sha256", schemaPath: "#/properties/record_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs10 === errors;
                    valid2 = valid2 || _valid0;
                    const _errs12 = errors;
                    if (data3 !== null) {
                      const err2 = { instancePath: instancePath + "/record_sha256", schemaPath: "#/properties/record_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err2];
                      } else {
                        vErrors.push(err2);
                      }
                      errors++;
                    }
                    var _valid0 = _errs12 === errors;
                    valid2 = valid2 || _valid0;
                    if (!valid2) {
                      const err3 = { instancePath: instancePath + "/record_sha256", schemaPath: "#/properties/record_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err3];
                      } else {
                        vErrors.push(err3);
                      }
                      errors++;
                      validate64.errors = vErrors;
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
                  if (valid0) {
                    if (data.reference !== void 0) {
                      let data4 = data.reference;
                      const _errs14 = errors;
                      const _errs15 = errors;
                      let valid3 = false;
                      const _errs16 = errors;
                      if (!validate65(data4, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate65.errors : vErrors.concat(validate65.errors);
                        errors = vErrors.length;
                      }
                      var _valid1 = _errs16 === errors;
                      valid3 = valid3 || _valid1;
                      if (_valid1) {
                        var props0 = true;
                      }
                      const _errs17 = errors;
                      if (!validate67(data4, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate67.errors : vErrors.concat(validate67.errors);
                        errors = vErrors.length;
                      }
                      var _valid1 = _errs17 === errors;
                      valid3 = valid3 || _valid1;
                      if (_valid1) {
                        if (props0 !== true) {
                          props0 = true;
                        }
                      }
                      const _errs18 = errors;
                      if (!validate69(data4, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate69.errors : vErrors.concat(validate69.errors);
                        errors = vErrors.length;
                      }
                      var _valid1 = _errs18 === errors;
                      valid3 = valid3 || _valid1;
                      if (_valid1) {
                        if (props0 !== true) {
                          props0 = true;
                        }
                      }
                      if (!valid3) {
                        const err4 = { instancePath: instancePath + "/reference", schemaPath: "#/properties/reference/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                        validate64.errors = vErrors;
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
                      if (data.unavailable !== void 0) {
                        let data5 = data.unavailable;
                        const _errs19 = errors;
                        const _errs20 = errors;
                        let valid4 = false;
                        const _errs21 = errors;
                        if (typeof data5 !== "string") {
                          const err5 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err5];
                          } else {
                            vErrors.push(err5);
                          }
                          errors++;
                        }
                        if (!(data5 === "not_provided" || data5 === "unavailable" || data5 === "denied" || data5 === "pending" || data5 === "failed")) {
                          const err6 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf/0/enum", keyword: "enum", params: { allowedValues: schema62.properties.unavailable.anyOf[0].enum }, message: "must be equal to one of the allowed values" };
                          if (vErrors === null) {
                            vErrors = [err6];
                          } else {
                            vErrors.push(err6);
                          }
                          errors++;
                        }
                        var _valid2 = _errs21 === errors;
                        valid4 = valid4 || _valid2;
                        const _errs23 = errors;
                        if (data5 !== null) {
                          const err7 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err7];
                          } else {
                            vErrors.push(err7);
                          }
                          errors++;
                        }
                        var _valid2 = _errs23 === errors;
                        valid4 = valid4 || _valid2;
                        if (!valid4) {
                          const err8 = { instancePath: instancePath + "/unavailable", schemaPath: "#/properties/unavailable/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err8];
                          } else {
                            vErrors.push(err8);
                          }
                          errors++;
                          validate64.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs20;
                          if (vErrors !== null) {
                            if (_errs20) {
                              vErrors.length = _errs20;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs19 === errors;
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
          validate64.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate64.errors = vErrors;
      return errors === 0;
    }
    validate64.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate80(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate80.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.request === void 0 && (missing0 = "request") || data.status_sha256 === void 0 && (missing0 = "status_sha256")) {
            validate80.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "request" || key0 === "status_sha256")) {
                validate80.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.request !== void 0) {
                const _errs2 = errors;
                if (!validate69(data.request, { instancePath: instancePath + "/request", parentData: data, parentDataProperty: "request", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate69.errors : vErrors.concat(validate69.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.status_sha256 !== void 0) {
                  let data1 = data.status_sha256;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (!pattern4.test(data1)) {
                        validate80.errors = [{ instancePath: instancePath + "/status_sha256", schemaPath: "#/properties/status_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate80.errors = [{ instancePath: instancePath + "/status_sha256", schemaPath: "#/properties/status_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate80.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate80.errors = vErrors;
      return errors === 0;
    }
    validate80.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.engagement === void 0 && (missing0 = "engagement") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.questions === void 0 && (missing0 = "questions") || data.needs === void 0 && (missing0 = "needs") || data.assessments === void 0 && (missing0 = "assessments")) {
            validate79.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "assessments" || key0 === "engagement" || key0 === "needs" || key0 === "questions" || key0 === "request_sha256" || key0 === "schema_version")) {
                validate79.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assessments !== void 0) {
                let data0 = data.assessments;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 32) {
                      validate79.errors = [{ instancePath: instancePath + "/assessments", schemaPath: "#/properties/assessments/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate80(data0[i0], { instancePath: instancePath + "/assessments/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate80.errors : vErrors.concat(validate80.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate79.errors = [{ instancePath: instancePath + "/assessments", schemaPath: "#/properties/assessments/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.engagement !== void 0) {
                  const _errs5 = errors;
                  if (!validate44(data.engagement, { instancePath: instancePath + "/engagement", parentData: data, parentDataProperty: "engagement", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate44.errors : vErrors.concat(validate44.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.needs !== void 0) {
                    let data3 = data.needs;
                    const _errs6 = errors;
                    if (errors === _errs6) {
                      if (Array.isArray(data3)) {
                        if (data3.length > 64) {
                          validate79.errors = [{ instancePath: instancePath + "/needs", schemaPath: "#/properties/needs/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                          return false;
                        } else {
                          var valid2 = true;
                          const len1 = data3.length;
                          for (let i1 = 0; i1 < len1; i1++) {
                            const _errs8 = errors;
                            if (!validate67(data3[i1], { instancePath: instancePath + "/needs/" + i1, parentData: data3, parentDataProperty: i1, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate67.errors : vErrors.concat(validate67.errors);
                              errors = vErrors.length;
                            }
                            var valid2 = _errs8 === errors;
                            if (!valid2) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate79.errors = [{ instancePath: instancePath + "/needs", schemaPath: "#/properties/needs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.questions !== void 0) {
                      let data5 = data.questions;
                      const _errs9 = errors;
                      if (errors === _errs9) {
                        if (Array.isArray(data5)) {
                          if (data5.length > 64) {
                            validate79.errors = [{ instancePath: instancePath + "/questions", schemaPath: "#/properties/questions/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                            return false;
                          } else {
                            var valid3 = true;
                            const len2 = data5.length;
                            for (let i2 = 0; i2 < len2; i2++) {
                              const _errs11 = errors;
                              if (!validate65(data5[i2], { instancePath: instancePath + "/questions/" + i2, parentData: data5, parentDataProperty: i2, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate65.errors : vErrors.concat(validate65.errors);
                                errors = vErrors.length;
                              }
                              var valid3 = _errs11 === errors;
                              if (!valid3) {
                                break;
                              }
                            }
                          }
                        } else {
                          validate79.errors = [{ instancePath: instancePath + "/questions", schemaPath: "#/properties/questions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs9 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.request_sha256 !== void 0) {
                        let data7 = data.request_sha256;
                        const _errs12 = errors;
                        if (errors === _errs12) {
                          if (typeof data7 === "string") {
                            if (!pattern4.test(data7)) {
                              validate79.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate79.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs12 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.schema_version !== void 0) {
                          let data8 = data.schema_version;
                          const _errs14 = errors;
                          if (typeof data8 !== "string") {
                            validate79.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("1" !== data8) {
                            validate79.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
          if (data.question === void 0 && (missing0 = "question") || data.need === void 0 && (missing0 = "need") || data.criterion_id === void 0 && (missing0 = "criterion_id") || data.assessment === void 0 && (missing0 = "assessment")) {
            validate89.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "assessment" || key0 === "criterion_id" || key0 === "need" || key0 === "question")) {
                validate89.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assessment !== void 0) {
                let data0 = data.assessment;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate80(data0, { instancePath: instancePath + "/assessment", parentData: data, parentDataProperty: "assessment", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate80.errors : vErrors.concat(validate80.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/assessment", schemaPath: "#/properties/assessment/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err1 = { instancePath: instancePath + "/assessment", schemaPath: "#/properties/assessment/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate89.errors = vErrors;
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
                if (data.criterion_id !== void 0) {
                  let data1 = data.criterion_id;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (typeof data1 === "string") {
                      if (func2(data1) > 128) {
                        validate89.errors = [{ instancePath: instancePath + "/criterion_id", schemaPath: "#/properties/criterion_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func2(data1) < 1) {
                          validate89.errors = [{ instancePath: instancePath + "/criterion_id", schemaPath: "#/properties/criterion_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data1)) {
                            validate89.errors = [{ instancePath: instancePath + "/criterion_id", schemaPath: "#/properties/criterion_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate89.errors = [{ instancePath: instancePath + "/criterion_id", schemaPath: "#/properties/criterion_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.need !== void 0) {
                    const _errs9 = errors;
                    if (!validate67(data.need, { instancePath: instancePath + "/need", parentData: data, parentDataProperty: "need", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate67.errors : vErrors.concat(validate67.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.question !== void 0) {
                      const _errs10 = errors;
                      if (!validate65(data.question, { instancePath: instancePath + "/question", parentData: data, parentDataProperty: "question", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate65.errors : vErrors.concat(validate65.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs10 === errors;
                    } else {
                      var valid0 = true;
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
    function validate87(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate87.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.engagement === void 0 && (missing0 = "engagement") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.questions === void 0 && (missing0 = "questions") || data.needs === void 0 && (missing0 = "needs") || data.assessments === void 0 && (missing0 = "assessments") || data.criteria === void 0 && (missing0 = "criteria") || data.focus_artifact === void 0 && (missing0 = "focus_artifact")) {
            validate87.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "assessments" || key0 === "criteria" || key0 === "engagement" || key0 === "focus_artifact" || key0 === "needs" || key0 === "questions" || key0 === "request_sha256" || key0 === "schema_version")) {
                validate87.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.assessments !== void 0) {
                let data0 = data.assessments;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 32) {
                      validate87.errors = [{ instancePath: instancePath + "/assessments", schemaPath: "#/properties/assessments/maxItems", keyword: "maxItems", params: { limit: 32 }, message: "must NOT have more than 32 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate80(data0[i0], { instancePath: instancePath + "/assessments/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate80.errors : vErrors.concat(validate80.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate87.errors = [{ instancePath: instancePath + "/assessments", schemaPath: "#/properties/assessments/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.criteria !== void 0) {
                  let data2 = data.criteria;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (Array.isArray(data2)) {
                      if (data2.length > 64) {
                        validate87.errors = [{ instancePath: instancePath + "/criteria", schemaPath: "#/properties/criteria/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                        return false;
                      } else {
                        var valid2 = true;
                        const len1 = data2.length;
                        for (let i1 = 0; i1 < len1; i1++) {
                          const _errs7 = errors;
                          if (!validate89(data2[i1], { instancePath: instancePath + "/criteria/" + i1, parentData: data2, parentDataProperty: i1, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate89.errors : vErrors.concat(validate89.errors);
                            errors = vErrors.length;
                          }
                          var valid2 = _errs7 === errors;
                          if (!valid2) {
                            break;
                          }
                        }
                      }
                    } else {
                      validate87.errors = [{ instancePath: instancePath + "/criteria", schemaPath: "#/properties/criteria/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.engagement !== void 0) {
                    const _errs8 = errors;
                    if (!validate44(data.engagement, { instancePath: instancePath + "/engagement", parentData: data, parentDataProperty: "engagement", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate44.errors : vErrors.concat(validate44.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs8 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.focus_artifact !== void 0) {
                      let data5 = data.focus_artifact;
                      const _errs9 = errors;
                      const _errs10 = errors;
                      let valid3 = false;
                      const _errs11 = errors;
                      if (!validate49(data5, { instancePath: instancePath + "/focus_artifact", parentData: data, parentDataProperty: "focus_artifact", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                        errors = vErrors.length;
                      }
                      var _valid0 = _errs11 === errors;
                      valid3 = valid3 || _valid0;
                      const _errs12 = errors;
                      if (data5 !== null) {
                        const err0 = { instancePath: instancePath + "/focus_artifact", schemaPath: "#/properties/focus_artifact/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      }
                      var _valid0 = _errs12 === errors;
                      valid3 = valid3 || _valid0;
                      if (!valid3) {
                        const err1 = { instancePath: instancePath + "/focus_artifact", schemaPath: "#/properties/focus_artifact/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                        validate87.errors = vErrors;
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
                      if (data.needs !== void 0) {
                        let data6 = data.needs;
                        const _errs14 = errors;
                        if (errors === _errs14) {
                          if (Array.isArray(data6)) {
                            if (data6.length > 64) {
                              validate87.errors = [{ instancePath: instancePath + "/needs", schemaPath: "#/properties/needs/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                              return false;
                            } else {
                              var valid4 = true;
                              const len2 = data6.length;
                              for (let i2 = 0; i2 < len2; i2++) {
                                const _errs16 = errors;
                                if (!validate67(data6[i2], { instancePath: instancePath + "/needs/" + i2, parentData: data6, parentDataProperty: i2, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate67.errors : vErrors.concat(validate67.errors);
                                  errors = vErrors.length;
                                }
                                var valid4 = _errs16 === errors;
                                if (!valid4) {
                                  break;
                                }
                              }
                            }
                          } else {
                            validate87.errors = [{ instancePath: instancePath + "/needs", schemaPath: "#/properties/needs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.questions !== void 0) {
                          let data8 = data.questions;
                          const _errs17 = errors;
                          if (errors === _errs17) {
                            if (Array.isArray(data8)) {
                              if (data8.length > 64) {
                                validate87.errors = [{ instancePath: instancePath + "/questions", schemaPath: "#/properties/questions/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                                return false;
                              } else {
                                var valid5 = true;
                                const len3 = data8.length;
                                for (let i3 = 0; i3 < len3; i3++) {
                                  const _errs19 = errors;
                                  if (!validate65(data8[i3], { instancePath: instancePath + "/questions/" + i3, parentData: data8, parentDataProperty: i3, rootData, dynamicAnchors })) {
                                    vErrors = vErrors === null ? validate65.errors : vErrors.concat(validate65.errors);
                                    errors = vErrors.length;
                                  }
                                  var valid5 = _errs19 === errors;
                                  if (!valid5) {
                                    break;
                                  }
                                }
                              }
                            } else {
                              validate87.errors = [{ instancePath: instancePath + "/questions", schemaPath: "#/properties/questions/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs17 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.request_sha256 !== void 0) {
                            let data10 = data.request_sha256;
                            const _errs20 = errors;
                            if (errors === _errs20) {
                              if (typeof data10 === "string") {
                                if (!pattern4.test(data10)) {
                                  validate87.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate87.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid0 = _errs20 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.schema_version !== void 0) {
                              let data11 = data.schema_version;
                              const _errs22 = errors;
                              if (typeof data11 !== "string") {
                                validate87.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("2" !== data11) {
                                validate87.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "2" }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs22 === errors;
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
          validate87.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate87.errors = vErrors;
      return errors === 0;
    }
    validate87.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.selection === void 0 && (missing0 = "selection") || data.records === void 0 && (missing0 = "records")) {
            validate63.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "records" || key0 === "selection")) {
                validate63.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.records !== void 0) {
                let data0 = data.records;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 160) {
                      validate63.errors = [{ instancePath: instancePath + "/records", schemaPath: "#/properties/records/maxItems", keyword: "maxItems", params: { limit: 160 }, message: "must NOT have more than 160 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate64(data0[i0], { instancePath: instancePath + "/records/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate64.errors : vErrors.concat(validate64.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate63.errors = [{ instancePath: instancePath + "/records", schemaPath: "#/properties/records/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.selection !== void 0) {
                  let data2 = data.selection;
                  const _errs5 = errors;
                  const _errs6 = errors;
                  let valid2 = false;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid3 = false;
                  let passing0 = null;
                  const _errs9 = errors;
                  if (!validate79(data2, { instancePath: instancePath + "/selection", parentData: data, parentDataProperty: "selection", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate79.errors : vErrors.concat(validate79.errors);
                    errors = vErrors.length;
                  }
                  var _valid1 = _errs9 === errors;
                  if (_valid1) {
                    valid3 = true;
                    passing0 = 0;
                    var props0 = true;
                  }
                  const _errs10 = errors;
                  if (!validate87(data2, { instancePath: instancePath + "/selection", parentData: data, parentDataProperty: "selection", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate87.errors : vErrors.concat(validate87.errors);
                    errors = vErrors.length;
                  }
                  var _valid1 = _errs10 === errors;
                  if (_valid1 && valid3) {
                    valid3 = false;
                    passing0 = [passing0, 1];
                  } else {
                    if (_valid1) {
                      valid3 = true;
                      passing0 = 1;
                      if (props0 !== true) {
                        props0 = true;
                      }
                    }
                  }
                  if (!valid3) {
                    const err0 = { instancePath: instancePath + "/selection", schemaPath: "#/properties/selection/anyOf/0/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
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
                  var _valid0 = _errs7 === errors;
                  valid2 = valid2 || _valid0;
                  const _errs12 = errors;
                  if (data2 !== null) {
                    const err1 = { instancePath: instancePath + "/selection", schemaPath: "#/properties/selection/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs12 === errors;
                  valid2 = valid2 || _valid0;
                  if (!valid2) {
                    const err2 = { instancePath: instancePath + "/selection", schemaPath: "#/properties/selection/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                    validate63.errors = vErrors;
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
    var schema81 = { "additionalProperties": false, "properties": { "content_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Content Sha256", "type": "string" }, "kind": { "enum": ["draft_revision", "draft_validation"], "title": "Kind", "type": "string" }, "object_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Object Id", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" } }, "required": ["kind", "object_id", "revision", "content_sha256"], "title": "DraftCommit", "type": "object" };
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
          if (data.command_family === void 0 && (missing0 = "command_family") || data.command_id === void 0 && (missing0 = "command_id") || data.scope === void 0 && (missing0 = "scope") || data.actor_id === void 0 && (missing0 = "actor_id")) {
            validate104.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "actor_id" || key0 === "command_family" || key0 === "command_id" || key0 === "schema_version" || key0 === "scope")) {
                validate104.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.actor_id !== void 0) {
                let data0 = data.actor_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func2(data0) > 128) {
                      validate104.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate104.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate104.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate104.errors = [{ instancePath: instancePath + "/actor_id", schemaPath: "#/properties/actor_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.command_family !== void 0) {
                  let data1 = data.command_family;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func2(data1) > 128) {
                        validate104.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func2(data1) < 1) {
                          validate104.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data1)) {
                            validate104.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate104.errors = [{ instancePath: instancePath + "/command_family", schemaPath: "#/properties/command_family/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.command_id !== void 0) {
                    let data2 = data.command_id;
                    const _errs6 = errors;
                    if (errors === _errs6) {
                      if (typeof data2 === "string") {
                        if (func2(data2) > 128) {
                          validate104.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func2(data2) < 1) {
                            validate104.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern5.test(data2)) {
                              validate104.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate104.errors = [{ instancePath: instancePath + "/command_id", schemaPath: "#/properties/command_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.schema_version !== void 0) {
                      let data3 = data.schema_version;
                      const _errs8 = errors;
                      if (typeof data3 !== "string") {
                        validate104.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data3) {
                        validate104.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.scope !== void 0) {
                        let data4 = data.scope;
                        const _errs10 = errors;
                        const _errs11 = errors;
                        if (errors === _errs11) {
                          if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                            let missing1;
                            if (data4.tenant_id === void 0 && (missing1 = "tenant_id") || data4.project_id === void 0 && (missing1 = "project_id")) {
                              validate104.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate104.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs13 === errors) {
                                if (data4.project_id !== void 0) {
                                  let data5 = data4.project_id;
                                  const _errs14 = errors;
                                  if (errors === _errs14) {
                                    if (typeof data5 === "string") {
                                      if (func2(data5) > 128) {
                                        validate104.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func2(data5) < 1) {
                                          validate104.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data5)) {
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
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                                if (valid2) {
                                  if (data4.tenant_id !== void 0) {
                                    let data6 = data4.tenant_id;
                                    const _errs16 = errors;
                                    if (errors === _errs16) {
                                      if (typeof data6 === "string") {
                                        if (func2(data6) > 128) {
                                          validate104.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func2(data6) < 1) {
                                            validate104.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data6)) {
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
                                    var valid2 = _errs16 === errors;
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
                        var valid0 = _errs10 === errors;
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
          if (data.identity === void 0 && (missing0 = "identity") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.operation_id === void 0 && (missing0 = "operation_id")) {
            validate103.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "identity" || key0 === "operation_id" || key0 === "request_sha256")) {
                validate103.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.identity !== void 0) {
                const _errs2 = errors;
                if (!validate104(data.identity, { instancePath: instancePath + "/identity", parentData: data, parentDataProperty: "identity", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate104.errors : vErrors.concat(validate104.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.operation_id !== void 0) {
                  let data1 = data.operation_id;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (func2(data1) > 128) {
                        validate103.errors = [{ instancePath: instancePath + "/operation_id", schemaPath: "#/properties/operation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func2(data1) < 1) {
                          validate103.errors = [{ instancePath: instancePath + "/operation_id", schemaPath: "#/properties/operation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data1)) {
                            validate103.errors = [{ instancePath: instancePath + "/operation_id", schemaPath: "#/properties/operation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate103.errors = [{ instancePath: instancePath + "/operation_id", schemaPath: "#/properties/operation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.request_sha256 !== void 0) {
                    let data2 = data.request_sha256;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (!pattern4.test(data2)) {
                          validate103.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate103.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          validate103.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate103.errors = vErrors;
      return errors === 0;
    }
    validate103.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate102(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate102.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.status === void 0 && (missing0 = "status") || data.binding === void 0 && (missing0 = "binding") || data.committed === void 0 && (missing0 = "committed")) {
            validate102.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "binding" || key0 === "committed" || key0 === "status")) {
                validate102.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.binding !== void 0) {
                const _errs2 = errors;
                if (!validate103(data.binding, { instancePath: instancePath + "/binding", parentData: data, parentDataProperty: "binding", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate103.errors : vErrors.concat(validate103.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.committed !== void 0) {
                  let data1 = data.committed;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.kind === void 0 && (missing1 = "kind") || data1.object_id === void 0 && (missing1 = "object_id") || data1.revision === void 0 && (missing1 = "revision") || data1.content_sha256 === void 0 && (missing1 = "content_sha256")) {
                        validate102.errors = [{ instancePath: instancePath + "/committed", schemaPath: "#/$defs/DraftCommit/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs6 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "content_sha256" || key1 === "kind" || key1 === "object_id" || key1 === "revision")) {
                            validate102.errors = [{ instancePath: instancePath + "/committed", schemaPath: "#/$defs/DraftCommit/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs6 === errors) {
                          if (data1.content_sha256 !== void 0) {
                            let data2 = data1.content_sha256;
                            const _errs7 = errors;
                            if (errors === _errs7) {
                              if (typeof data2 === "string") {
                                if (!pattern4.test(data2)) {
                                  validate102.errors = [{ instancePath: instancePath + "/committed/content_sha256", schemaPath: "#/$defs/DraftCommit/properties/content_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate102.errors = [{ instancePath: instancePath + "/committed/content_sha256", schemaPath: "#/$defs/DraftCommit/properties/content_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs7 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.kind !== void 0) {
                              let data3 = data1.kind;
                              const _errs9 = errors;
                              if (typeof data3 !== "string") {
                                validate102.errors = [{ instancePath: instancePath + "/committed/kind", schemaPath: "#/$defs/DraftCommit/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if (!(data3 === "draft_revision" || data3 === "draft_validation")) {
                                validate102.errors = [{ instancePath: instancePath + "/committed/kind", schemaPath: "#/$defs/DraftCommit/properties/kind/enum", keyword: "enum", params: { allowedValues: schema81.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
                                return false;
                              }
                              var valid2 = _errs9 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data1.object_id !== void 0) {
                                let data4 = data1.object_id;
                                const _errs11 = errors;
                                if (errors === _errs11) {
                                  if (typeof data4 === "string") {
                                    if (func2(data4) > 128) {
                                      validate102.errors = [{ instancePath: instancePath + "/committed/object_id", schemaPath: "#/$defs/DraftCommit/properties/object_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func2(data4) < 1) {
                                        validate102.errors = [{ instancePath: instancePath + "/committed/object_id", schemaPath: "#/$defs/DraftCommit/properties/object_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data4)) {
                                          validate102.errors = [{ instancePath: instancePath + "/committed/object_id", schemaPath: "#/$defs/DraftCommit/properties/object_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate102.errors = [{ instancePath: instancePath + "/committed/object_id", schemaPath: "#/$defs/DraftCommit/properties/object_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid2 = _errs11 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data1.revision !== void 0) {
                                  let data5 = data1.revision;
                                  const _errs13 = errors;
                                  if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                    validate102.errors = [{ instancePath: instancePath + "/committed/revision", schemaPath: "#/$defs/DraftCommit/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                    return false;
                                  }
                                  if (errors === _errs13) {
                                    if (typeof data5 == "number" && isFinite(data5)) {
                                      if (data5 > 9007199254740991 || isNaN(data5)) {
                                        validate102.errors = [{ instancePath: instancePath + "/committed/revision", schemaPath: "#/$defs/DraftCommit/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                        return false;
                                      } else {
                                        if (data5 < 1 || isNaN(data5)) {
                                          validate102.errors = [{ instancePath: instancePath + "/committed/revision", schemaPath: "#/$defs/DraftCommit/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                          return false;
                                        }
                                      }
                                    }
                                  }
                                  var valid2 = _errs13 === errors;
                                } else {
                                  var valid2 = true;
                                }
                              }
                            }
                          }
                        }
                      }
                    } else {
                      validate102.errors = [{ instancePath: instancePath + "/committed", schemaPath: "#/$defs/DraftCommit/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data6 = data.status;
                    const _errs15 = errors;
                    if (typeof data6 !== "string") {
                      validate102.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("accepted" !== data6) {
                      validate102.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "accepted" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs15 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate102.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate102.errors = vErrors;
      return errors === 0;
    }
    validate102.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate108(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate108.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.status === void 0 && (missing0 = "status") || data.binding === void 0 && (missing0 = "binding") || data.reason_code === void 0 && (missing0 = "reason_code")) {
            validate108.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "binding" || key0 === "reason_code" || key0 === "status")) {
                validate108.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.binding !== void 0) {
                const _errs2 = errors;
                if (!validate103(data.binding, { instancePath: instancePath + "/binding", parentData: data, parentDataProperty: "binding", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate103.errors : vErrors.concat(validate103.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.reason_code !== void 0) {
                  let data1 = data.reason_code;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (func2(data1) > 128) {
                        validate108.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func2(data1) < 1) {
                          validate108.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data1)) {
                            validate108.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate108.errors = [{ instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data2 = data.status;
                    const _errs5 = errors;
                    if (typeof data2 !== "string") {
                      validate108.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("rejected" !== data2) {
                      validate108.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "rejected" }, message: "must be equal to constant" }];
                      return false;
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
          validate108.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate108.errors = vErrors;
      return errors === 0;
    }
    validate108.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate111(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate111.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.status === void 0 && (missing0 = "status") || data.binding === void 0 && (missing0 = "binding")) {
            validate111.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "binding" || key0 === "status")) {
                validate111.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.binding !== void 0) {
                const _errs2 = errors;
                if (!validate103(data.binding, { instancePath: instancePath + "/binding", parentData: data, parentDataProperty: "binding", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate103.errors : vErrors.concat(validate103.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.status !== void 0) {
                  let data1 = data.status;
                  const _errs3 = errors;
                  if (typeof data1 !== "string") {
                    validate111.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("pending" !== data1) {
                    validate111.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "pending" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate111.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate111.errors = vErrors;
      return errors === 0;
    }
    validate111.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate101(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate101.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.outcome === void 0 && (missing0 = "outcome")) {
            validate101.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "outcome" || key0 === "schema_version")) {
                validate101.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.outcome !== void 0) {
                let data0 = data.outcome;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                let passing0 = null;
                const _errs4 = errors;
                if (!validate102(data0, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate102.errors : vErrors.concat(validate102.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                if (_valid0) {
                  valid1 = true;
                  passing0 = 0;
                  var props0 = true;
                }
                const _errs5 = errors;
                if (!validate108(data0, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate108.errors : vErrors.concat(validate108.errors);
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
                  const _errs6 = errors;
                  if (!validate111(data0, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate111.errors : vErrors.concat(validate111.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs6 === errors;
                  if (_valid0 && valid1) {
                    valid1 = false;
                    passing0 = [passing0, 2];
                  } else {
                    if (_valid0) {
                      valid1 = true;
                      passing0 = 2;
                      if (props0 !== true) {
                        props0 = true;
                      }
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
                  validate101.errors = vErrors;
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
                if (data.schema_version !== void 0) {
                  let data1 = data.schema_version;
                  const _errs8 = errors;
                  if (typeof data1 !== "string") {
                    validate101.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("1" !== data1) {
                    validate101.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs8 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate101.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate101.errors = vErrors;
      return errors === 0;
    }
    validate101.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.owner_id === void 0 && (missing0 = "owner_id") || data.selection_id === void 0 && (missing0 = "selection_id") || data.selection_sha256 === void 0 && (missing0 = "selection_sha256") || data.effect_id === void 0 && (missing0 = "effect_id") || data.effect_sha256 === void 0 && (missing0 = "effect_sha256") || data.receipt === void 0 && (missing0 = "receipt") || data.readback_sha256 === void 0 && (missing0 = "readback_sha256")) {
            validate100.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "effect_id" || key0 === "effect_sha256" || key0 === "owner_id" || key0 === "readback_sha256" || key0 === "receipt" || key0 === "selection_id" || key0 === "selection_sha256")) {
                validate100.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.effect_id !== void 0) {
                let data0 = data.effect_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func2(data0) > 128) {
                      validate100.errors = [{ instancePath: instancePath + "/effect_id", schemaPath: "#/properties/effect_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate100.errors = [{ instancePath: instancePath + "/effect_id", schemaPath: "#/properties/effect_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate100.errors = [{ instancePath: instancePath + "/effect_id", schemaPath: "#/properties/effect_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate100.errors = [{ instancePath: instancePath + "/effect_id", schemaPath: "#/properties/effect_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.effect_sha256 !== void 0) {
                  let data1 = data.effect_sha256;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (!pattern4.test(data1)) {
                        validate100.errors = [{ instancePath: instancePath + "/effect_sha256", schemaPath: "#/properties/effect_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate100.errors = [{ instancePath: instancePath + "/effect_sha256", schemaPath: "#/properties/effect_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.owner_id !== void 0) {
                    let data2 = data.owner_id;
                    const _errs6 = errors;
                    if (errors === _errs6) {
                      if (typeof data2 === "string") {
                        if (func2(data2) > 128) {
                          validate100.errors = [{ instancePath: instancePath + "/owner_id", schemaPath: "#/properties/owner_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func2(data2) < 1) {
                            validate100.errors = [{ instancePath: instancePath + "/owner_id", schemaPath: "#/properties/owner_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern5.test(data2)) {
                              validate100.errors = [{ instancePath: instancePath + "/owner_id", schemaPath: "#/properties/owner_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate100.errors = [{ instancePath: instancePath + "/owner_id", schemaPath: "#/properties/owner_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.readback_sha256 !== void 0) {
                      let data3 = data.readback_sha256;
                      const _errs8 = errors;
                      if (errors === _errs8) {
                        if (typeof data3 === "string") {
                          if (!pattern4.test(data3)) {
                            validate100.errors = [{ instancePath: instancePath + "/readback_sha256", schemaPath: "#/properties/readback_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                            return false;
                          }
                        } else {
                          validate100.errors = [{ instancePath: instancePath + "/readback_sha256", schemaPath: "#/properties/readback_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.receipt !== void 0) {
                        const _errs10 = errors;
                        if (!validate101(data.receipt, { instancePath: instancePath + "/receipt", parentData: data, parentDataProperty: "receipt", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate101.errors : vErrors.concat(validate101.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs10 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.selection_id !== void 0) {
                          let data5 = data.selection_id;
                          const _errs11 = errors;
                          if (errors === _errs11) {
                            if (typeof data5 === "string") {
                              if (func2(data5) > 128) {
                                validate100.errors = [{ instancePath: instancePath + "/selection_id", schemaPath: "#/properties/selection_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                return false;
                              } else {
                                if (func2(data5) < 1) {
                                  validate100.errors = [{ instancePath: instancePath + "/selection_id", schemaPath: "#/properties/selection_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                } else {
                                  if (!pattern5.test(data5)) {
                                    validate100.errors = [{ instancePath: instancePath + "/selection_id", schemaPath: "#/properties/selection_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                    return false;
                                  }
                                }
                              }
                            } else {
                              validate100.errors = [{ instancePath: instancePath + "/selection_id", schemaPath: "#/properties/selection_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid0 = _errs11 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.selection_sha256 !== void 0) {
                            let data6 = data.selection_sha256;
                            const _errs13 = errors;
                            if (errors === _errs13) {
                              if (typeof data6 === "string") {
                                if (!pattern4.test(data6)) {
                                  validate100.errors = [{ instancePath: instancePath + "/selection_sha256", schemaPath: "#/properties/selection_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate100.errors = [{ instancePath: instancePath + "/selection_sha256", schemaPath: "#/properties/selection_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
    var pattern96 = new RegExp("^[0-9]+\\.[0-9]+\\.[0-9]+$", "u");
    function validate118(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate118.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.port === void 0 && (missing0 = "port") || data.schema_ref === void 0 && (missing0 = "schema_ref")) {
            validate118.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "port" || key0 === "schema_ref")) {
                validate118.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.port !== void 0) {
                let data0 = data.port;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func2(data0) > 128) {
                      validate118.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate118.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate118.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate118.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.schema_ref !== void 0) {
                  let data1 = data.schema_ref;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.schema_id === void 0 && (missing1 = "schema_id") || data1.version === void 0 && (missing1 = "version") || data1.sha256 === void 0 && (missing1 = "sha256")) {
                        validate118.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                            validate118.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.schema_id !== void 0) {
                            let data2 = data1.schema_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func2(data2) > 128) {
                                  validate118.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func2(data2) < 1) {
                                    validate118.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern5.test(data2)) {
                                      validate118.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate118.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.sha256 !== void 0) {
                              let data3 = data1.sha256;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (!pattern4.test(data3)) {
                                    validate118.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                    return false;
                                  }
                                } else {
                                  validate118.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data1.version !== void 0) {
                                let data4 = data1.version;
                                const _errs12 = errors;
                                if (typeof data4 !== "string") {
                                  validate118.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("1" !== data4) {
                                  validate118.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      validate118.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate118.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate118.errors = vErrors;
      return errors === 0;
    }
    validate118.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.tool === void 0 && (missing0 = "tool") || data.descriptor_sha256 === void 0 && (missing0 = "descriptor_sha256") || data.input_schemas === void 0 && (missing0 = "input_schemas") || data.output_schemas === void 0 && (missing0 = "output_schemas") || data.checkpoint_schema === void 0 && (missing0 = "checkpoint_schema")) {
            validate117.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "checkpoint_schema" || key0 === "descriptor_sha256" || key0 === "input_schemas" || key0 === "output_schemas" || key0 === "schema_version" || key0 === "tool")) {
                validate117.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.checkpoint_schema !== void 0) {
                let data0 = data.checkpoint_schema;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                const _errs5 = errors;
                if (errors === _errs5) {
                  if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                    let missing1;
                    if (data0.schema_id === void 0 && (missing1 = "schema_id") || data0.version === void 0 && (missing1 = "version") || data0.sha256 === void 0 && (missing1 = "sha256")) {
                      const err0 = { instancePath: instancePath + "/checkpoint_schema", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    } else {
                      const _errs7 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                          const err1 = { instancePath: instancePath + "/checkpoint_schema", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                          if (vErrors === null) {
                            vErrors = [err1];
                          } else {
                            vErrors.push(err1);
                          }
                          errors++;
                          break;
                        }
                      }
                      if (_errs7 === errors) {
                        if (data0.schema_id !== void 0) {
                          let data1 = data0.schema_id;
                          const _errs8 = errors;
                          if (errors === _errs8) {
                            if (typeof data1 === "string") {
                              if (func2(data1) > 128) {
                                const err2 = { instancePath: instancePath + "/checkpoint_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              } else {
                                if (func2(data1) < 1) {
                                  const err3 = { instancePath: instancePath + "/checkpoint_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                  if (vErrors === null) {
                                    vErrors = [err3];
                                  } else {
                                    vErrors.push(err3);
                                  }
                                  errors++;
                                } else {
                                  if (!pattern5.test(data1)) {
                                    const err4 = { instancePath: instancePath + "/checkpoint_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                    if (vErrors === null) {
                                      vErrors = [err4];
                                    } else {
                                      vErrors.push(err4);
                                    }
                                    errors++;
                                  }
                                }
                              }
                            } else {
                              const err5 = { instancePath: instancePath + "/checkpoint_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err5];
                              } else {
                                vErrors.push(err5);
                              }
                              errors++;
                            }
                          }
                          var valid3 = _errs8 === errors;
                        } else {
                          var valid3 = true;
                        }
                        if (valid3) {
                          if (data0.sha256 !== void 0) {
                            let data2 = data0.sha256;
                            const _errs10 = errors;
                            if (errors === _errs10) {
                              if (typeof data2 === "string") {
                                if (!pattern4.test(data2)) {
                                  const err6 = { instancePath: instancePath + "/checkpoint_schema/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                  if (vErrors === null) {
                                    vErrors = [err6];
                                  } else {
                                    vErrors.push(err6);
                                  }
                                  errors++;
                                }
                              } else {
                                const err7 = { instancePath: instancePath + "/checkpoint_schema/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err7];
                                } else {
                                  vErrors.push(err7);
                                }
                                errors++;
                              }
                            }
                            var valid3 = _errs10 === errors;
                          } else {
                            var valid3 = true;
                          }
                          if (valid3) {
                            if (data0.version !== void 0) {
                              let data3 = data0.version;
                              const _errs12 = errors;
                              if (typeof data3 !== "string") {
                                const err8 = { instancePath: instancePath + "/checkpoint_schema/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err8];
                                } else {
                                  vErrors.push(err8);
                                }
                                errors++;
                              }
                              if ("1" !== data3) {
                                const err9 = { instancePath: instancePath + "/checkpoint_schema/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" };
                                if (vErrors === null) {
                                  vErrors = [err9];
                                } else {
                                  vErrors.push(err9);
                                }
                                errors++;
                              }
                              var valid3 = _errs12 === errors;
                            } else {
                              var valid3 = true;
                            }
                          }
                        }
                      }
                    }
                  } else {
                    const err10 = { instancePath: instancePath + "/checkpoint_schema", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                    if (vErrors === null) {
                      vErrors = [err10];
                    } else {
                      vErrors.push(err10);
                    }
                    errors++;
                  }
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs14 = errors;
                if (data0 !== null) {
                  const err11 = { instancePath: instancePath + "/checkpoint_schema", schemaPath: "#/properties/checkpoint_schema/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err11];
                  } else {
                    vErrors.push(err11);
                  }
                  errors++;
                }
                var _valid0 = _errs14 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err12 = { instancePath: instancePath + "/checkpoint_schema", schemaPath: "#/properties/checkpoint_schema/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err12];
                  } else {
                    vErrors.push(err12);
                  }
                  errors++;
                  validate117.errors = vErrors;
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
                if (data.descriptor_sha256 !== void 0) {
                  let data4 = data.descriptor_sha256;
                  const _errs16 = errors;
                  if (errors === _errs16) {
                    if (typeof data4 === "string") {
                      if (!pattern4.test(data4)) {
                        validate117.errors = [{ instancePath: instancePath + "/descriptor_sha256", schemaPath: "#/properties/descriptor_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate117.errors = [{ instancePath: instancePath + "/descriptor_sha256", schemaPath: "#/properties/descriptor_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs16 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.input_schemas !== void 0) {
                    let data5 = data.input_schemas;
                    const _errs18 = errors;
                    if (errors === _errs18) {
                      if (Array.isArray(data5)) {
                        if (data5.length > 64) {
                          validate117.errors = [{ instancePath: instancePath + "/input_schemas", schemaPath: "#/properties/input_schemas/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                          return false;
                        } else {
                          var valid4 = true;
                          const len0 = data5.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs20 = errors;
                            if (!validate118(data5[i0], { instancePath: instancePath + "/input_schemas/" + i0, parentData: data5, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate118.errors : vErrors.concat(validate118.errors);
                              errors = vErrors.length;
                            }
                            var valid4 = _errs20 === errors;
                            if (!valid4) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate117.errors = [{ instancePath: instancePath + "/input_schemas", schemaPath: "#/properties/input_schemas/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs18 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.output_schemas !== void 0) {
                      let data7 = data.output_schemas;
                      const _errs21 = errors;
                      if (errors === _errs21) {
                        if (Array.isArray(data7)) {
                          if (data7.length > 64) {
                            validate117.errors = [{ instancePath: instancePath + "/output_schemas", schemaPath: "#/properties/output_schemas/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                            return false;
                          } else {
                            var valid5 = true;
                            const len1 = data7.length;
                            for (let i1 = 0; i1 < len1; i1++) {
                              const _errs23 = errors;
                              if (!validate118(data7[i1], { instancePath: instancePath + "/output_schemas/" + i1, parentData: data7, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate118.errors : vErrors.concat(validate118.errors);
                                errors = vErrors.length;
                              }
                              var valid5 = _errs23 === errors;
                              if (!valid5) {
                                break;
                              }
                            }
                          }
                        } else {
                          validate117.errors = [{ instancePath: instancePath + "/output_schemas", schemaPath: "#/properties/output_schemas/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs21 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.schema_version !== void 0) {
                        let data9 = data.schema_version;
                        const _errs24 = errors;
                        if (typeof data9 !== "string") {
                          validate117.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data9) {
                          validate117.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs24 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.tool !== void 0) {
                          let data10 = data.tool;
                          const _errs26 = errors;
                          const _errs27 = errors;
                          if (errors === _errs27) {
                            if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                              let missing2;
                              if (data10.capability_id === void 0 && (missing2 = "capability_id") || data10.release === void 0 && (missing2 = "release") || data10.image_sha256 === void 0 && (missing2 = "image_sha256") || data10.contract_version === void 0 && (missing2 = "contract_version")) {
                                validate117.errors = [{ instancePath: instancePath + "/tool", schemaPath: "#/$defs/ToolBinding/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                return false;
                              } else {
                                const _errs29 = errors;
                                for (const key2 in data10) {
                                  if (!(key2 === "capability_id" || key2 === "contract_version" || key2 === "image_sha256" || key2 === "release")) {
                                    validate117.errors = [{ instancePath: instancePath + "/tool", schemaPath: "#/$defs/ToolBinding/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs29 === errors) {
                                  if (data10.capability_id !== void 0) {
                                    let data11 = data10.capability_id;
                                    const _errs30 = errors;
                                    if (errors === _errs30) {
                                      if (typeof data11 === "string") {
                                        if (func2(data11) > 128) {
                                          validate117.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func2(data11) < 1) {
                                            validate117.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data11)) {
                                              validate117.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate117.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid7 = _errs30 === errors;
                                  } else {
                                    var valid7 = true;
                                  }
                                  if (valid7) {
                                    if (data10.contract_version !== void 0) {
                                      let data12 = data10.contract_version;
                                      const _errs32 = errors;
                                      if (typeof data12 !== "string") {
                                        validate117.errors = [{ instancePath: instancePath + "/tool/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if ("1" !== data12) {
                                        validate117.errors = [{ instancePath: instancePath + "/tool/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                        return false;
                                      }
                                      var valid7 = _errs32 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                    if (valid7) {
                                      if (data10.image_sha256 !== void 0) {
                                        let data13 = data10.image_sha256;
                                        const _errs34 = errors;
                                        if (errors === _errs34) {
                                          if (typeof data13 === "string") {
                                            if (!pattern4.test(data13)) {
                                              validate117.errors = [{ instancePath: instancePath + "/tool/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                              return false;
                                            }
                                          } else {
                                            validate117.errors = [{ instancePath: instancePath + "/tool/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid7 = _errs34 === errors;
                                      } else {
                                        var valid7 = true;
                                      }
                                      if (valid7) {
                                        if (data10.release !== void 0) {
                                          let data14 = data10.release;
                                          const _errs36 = errors;
                                          if (errors === _errs36) {
                                            if (typeof data14 === "string") {
                                              if (!pattern96.test(data14)) {
                                                validate117.errors = [{ instancePath: instancePath + "/tool/release", schemaPath: "#/$defs/ToolBinding/properties/release/pattern", keyword: "pattern", params: { pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$" }, message: 'must match pattern "^[0-9]+\\.[0-9]+\\.[0-9]+$"' }];
                                                return false;
                                              }
                                            } else {
                                              validate117.errors = [{ instancePath: instancePath + "/tool/release", schemaPath: "#/$defs/ToolBinding/properties/release/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid7 = _errs36 === errors;
                                        } else {
                                          var valid7 = true;
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              validate117.errors = [{ instancePath: instancePath + "/tool", schemaPath: "#/$defs/ToolBinding/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate117.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate117.errors = vErrors;
      return errors === 0;
    }
    validate117.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate116(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate116.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.node === void 0 && (missing0 = "node") || data.release === void 0 && (missing0 = "release")) {
            validate116.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "node" || key0 === "release")) {
                validate116.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.node !== void 0) {
                let data0 = data.node;
                const _errs2 = errors;
                const _errs3 = errors;
                if (errors === _errs3) {
                  if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                    let missing1;
                    if (data0.scope_path === void 0 && (missing1 = "scope_path") || data0.node_id === void 0 && (missing1 = "node_id")) {
                      validate116.errors = [{ instancePath: instancePath + "/node", schemaPath: "#/$defs/CampaignNodeAddress/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                      return false;
                    } else {
                      const _errs5 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "node_id" || key1 === "scope_path")) {
                          validate116.errors = [{ instancePath: instancePath + "/node", schemaPath: "#/$defs/CampaignNodeAddress/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                          return false;
                          break;
                        }
                      }
                      if (_errs5 === errors) {
                        if (data0.node_id !== void 0) {
                          let data1 = data0.node_id;
                          const _errs6 = errors;
                          if (errors === _errs6) {
                            if (typeof data1 === "string") {
                              if (func2(data1) > 128) {
                                validate116.errors = [{ instancePath: instancePath + "/node/node_id", schemaPath: "#/$defs/CampaignNodeAddress/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                return false;
                              } else {
                                if (func2(data1) < 1) {
                                  validate116.errors = [{ instancePath: instancePath + "/node/node_id", schemaPath: "#/$defs/CampaignNodeAddress/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                } else {
                                  if (!pattern5.test(data1)) {
                                    validate116.errors = [{ instancePath: instancePath + "/node/node_id", schemaPath: "#/$defs/CampaignNodeAddress/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                    return false;
                                  }
                                }
                              }
                            } else {
                              validate116.errors = [{ instancePath: instancePath + "/node/node_id", schemaPath: "#/$defs/CampaignNodeAddress/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid2 = _errs6 === errors;
                        } else {
                          var valid2 = true;
                        }
                        if (valid2) {
                          if (data0.scope_path !== void 0) {
                            let data2 = data0.scope_path;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (Array.isArray(data2)) {
                                if (data2.length > 16) {
                                  validate116.errors = [{ instancePath: instancePath + "/node/scope_path", schemaPath: "#/$defs/CampaignNodeAddress/properties/scope_path/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                                  return false;
                                } else {
                                  var valid3 = true;
                                  const len0 = data2.length;
                                  for (let i0 = 0; i0 < len0; i0++) {
                                    let data3 = data2[i0];
                                    const _errs10 = errors;
                                    if (errors === _errs10) {
                                      if (typeof data3 === "string") {
                                        if (func2(data3) > 128) {
                                          validate116.errors = [{ instancePath: instancePath + "/node/scope_path/" + i0, schemaPath: "#/$defs/CampaignNodeAddress/properties/scope_path/items/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func2(data3) < 1) {
                                            validate116.errors = [{ instancePath: instancePath + "/node/scope_path/" + i0, schemaPath: "#/$defs/CampaignNodeAddress/properties/scope_path/items/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data3)) {
                                              validate116.errors = [{ instancePath: instancePath + "/node/scope_path/" + i0, schemaPath: "#/$defs/CampaignNodeAddress/properties/scope_path/items/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate116.errors = [{ instancePath: instancePath + "/node/scope_path/" + i0, schemaPath: "#/$defs/CampaignNodeAddress/properties/scope_path/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid3 = _errs10 === errors;
                                    if (!valid3) {
                                      break;
                                    }
                                  }
                                }
                              } else {
                                validate116.errors = [{ instancePath: instancePath + "/node/scope_path", schemaPath: "#/$defs/CampaignNodeAddress/properties/scope_path/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
                    validate116.errors = [{ instancePath: instancePath + "/node", schemaPath: "#/$defs/CampaignNodeAddress/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.release !== void 0) {
                  const _errs12 = errors;
                  if (!validate117(data.release, { instancePath: instancePath + "/release", parentData: data, parentDataProperty: "release", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate117.errors : vErrors.concat(validate117.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate116.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate116.errors = vErrors;
      return errors === 0;
    }
    validate116.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.authority === void 0 && (missing0 = "authority") || data.draft === void 0 && (missing0 = "draft") || data.proposal === void 0 && (missing0 = "proposal") || data.save === void 0 && (missing0 = "save") || data.research === void 0 && (missing0 = "research") || data.tools === void 0 && (missing0 = "tools") || data.limitations === void 0 && (missing0 = "limitations") || data.knowledge === void 0 && (missing0 = "knowledge")) {
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
              if (data.authority !== void 0) {
                let data0 = data.authority;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate21.errors = [{ instancePath: instancePath + "/authority", schemaPath: "#/properties/authority/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("historical_compiler_provenance" !== data0) {
                  validate21.errors = [{ instancePath: instancePath + "/authority", schemaPath: "#/properties/authority/const", keyword: "const", params: { allowedValue: "historical_compiler_provenance" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.draft !== void 0) {
                  const _errs4 = errors;
                  if (!validate22(data.draft, { instancePath: instancePath + "/draft", parentData: data, parentDataProperty: "draft", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate22.errors : vErrors.concat(validate22.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.knowledge !== void 0) {
                    let data2 = data.knowledge;
                    const _errs5 = errors;
                    const _errs6 = errors;
                    let valid1 = false;
                    const _errs7 = errors;
                    if (!validate24(data2, { instancePath: instancePath + "/knowledge", parentData: data, parentDataProperty: "knowledge", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate24.errors : vErrors.concat(validate24.errors);
                      errors = vErrors.length;
                    }
                    var _valid0 = _errs7 === errors;
                    valid1 = valid1 || _valid0;
                    const _errs8 = errors;
                    if (data2 !== null) {
                      const err0 = { instancePath: instancePath + "/knowledge", schemaPath: "#/properties/knowledge/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    }
                    var _valid0 = _errs8 === errors;
                    valid1 = valid1 || _valid0;
                    if (!valid1) {
                      const err1 = { instancePath: instancePath + "/knowledge", schemaPath: "#/properties/knowledge/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err1];
                      } else {
                        vErrors.push(err1);
                      }
                      errors++;
                      validate21.errors = vErrors;
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
                    if (data.limitations !== void 0) {
                      let data3 = data.limitations;
                      const _errs10 = errors;
                      if (errors === _errs10) {
                        if (Array.isArray(data3)) {
                          if (data3.length > 16) {
                            validate21.errors = [{ instancePath: instancePath + "/limitations", schemaPath: "#/properties/limitations/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                            return false;
                          } else {
                            if (data3.length < 1) {
                              validate21.errors = [{ instancePath: instancePath + "/limitations", schemaPath: "#/properties/limitations/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                              return false;
                            } else {
                              var valid2 = true;
                              const len0 = data3.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                let data4 = data3[i0];
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data4 === "string") {
                                    if (func2(data4) > 128) {
                                      validate21.errors = [{ instancePath: instancePath + "/limitations/" + i0, schemaPath: "#/properties/limitations/items/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func2(data4) < 1) {
                                        validate21.errors = [{ instancePath: instancePath + "/limitations/" + i0, schemaPath: "#/properties/limitations/items/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data4)) {
                                          validate21.errors = [{ instancePath: instancePath + "/limitations/" + i0, schemaPath: "#/properties/limitations/items/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate21.errors = [{ instancePath: instancePath + "/limitations/" + i0, schemaPath: "#/properties/limitations/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid2 = _errs12 === errors;
                                if (!valid2) {
                                  break;
                                }
                              }
                            }
                          }
                        } else {
                          validate21.errors = [{ instancePath: instancePath + "/limitations", schemaPath: "#/properties/limitations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs10 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.proposal !== void 0) {
                        const _errs14 = errors;
                        if (!validate42(data.proposal, { instancePath: instancePath + "/proposal", parentData: data, parentDataProperty: "proposal", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate42.errors : vErrors.concat(validate42.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.research !== void 0) {
                          const _errs15 = errors;
                          if (!validate63(data.research, { instancePath: instancePath + "/research", parentData: data, parentDataProperty: "research", rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate63.errors : vErrors.concat(validate63.errors);
                            errors = vErrors.length;
                          }
                          var valid0 = _errs15 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.save !== void 0) {
                            const _errs16 = errors;
                            if (!validate100(data.save, { instancePath: instancePath + "/save", parentData: data, parentDataProperty: "save", rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate100.errors : vErrors.concat(validate100.errors);
                              errors = vErrors.length;
                            }
                            var valid0 = _errs16 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.schema_version !== void 0) {
                              let data8 = data.schema_version;
                              const _errs17 = errors;
                              if (typeof data8 !== "string") {
                                validate21.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("2" !== data8) {
                                validate21.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "2" }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs17 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.tools !== void 0) {
                                let data9 = data.tools;
                                const _errs19 = errors;
                                if (errors === _errs19) {
                                  if (Array.isArray(data9)) {
                                    if (data9.length > 4096) {
                                      validate21.errors = [{ instancePath: instancePath + "/tools", schemaPath: "#/properties/tools/maxItems", keyword: "maxItems", params: { limit: 4096 }, message: "must NOT have more than 4096 items" }];
                                      return false;
                                    } else {
                                      var valid3 = true;
                                      const len1 = data9.length;
                                      for (let i1 = 0; i1 < len1; i1++) {
                                        const _errs21 = errors;
                                        if (!validate116(data9[i1], { instancePath: instancePath + "/tools/" + i1, parentData: data9, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                          vErrors = vErrors === null ? validate116.errors : vErrors.concat(validate116.errors);
                                          errors = vErrors.length;
                                        }
                                        var valid3 = _errs21 === errors;
                                        if (!valid3) {
                                          break;
                                        }
                                      }
                                    }
                                  } else {
                                    validate21.errors = [{ instancePath: instancePath + "/tools", schemaPath: "#/properties/tools/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                    return false;
                                  }
                                }
                                var valid0 = _errs19 === errors;
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
          if (data.origin_sha256 === void 0 && (missing0 = "origin_sha256") || data.origin === void 0 && (missing0 = "origin")) {
            validate20.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "origin" || key0 === "origin_sha256" || key0 === "schema_version")) {
                validate20.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.origin !== void 0) {
                const _errs2 = errors;
                if (!validate21(data.origin, { instancePath: instancePath + "/origin", parentData: data, parentDataProperty: "origin", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.origin_sha256 !== void 0) {
                  let data1 = data.origin_sha256;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (!pattern4.test(data1)) {
                        validate20.errors = [{ instancePath: instancePath + "/origin_sha256", schemaPath: "#/properties/origin_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate20.errors = [{ instancePath: instancePath + "/origin_sha256", schemaPath: "#/properties/origin_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.schema_version !== void 0) {
                    let data2 = data.schema_version;
                    const _errs5 = errors;
                    if (typeof data2 !== "string") {
                      validate20.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("2" !== data2) {
                      validate20.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "2" }, message: "must be equal to constant" }];
                      return false;
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
