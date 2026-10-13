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
    exports.request = validate20;
    var func1 = require_ucs2length().default;
    var pattern4 = new RegExp("^[A-Za-z0-9][A-Za-z0-9._:-]*$", "u");
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
          if (data.scope === void 0 && (missing0 = "scope") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate21.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate_id" || key0 === "revision" || key0 === "scope")) {
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
                    if (func1(data0) > 128) {
                      validate21.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate21.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate21.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
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
                if (data.revision !== void 0) {
                  let data1 = data.revision;
                  const _errs4 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate21.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
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
                          validate21.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate21.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate21.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate21.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate21.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate21.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate21.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate21.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate21.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate21.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate21.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate21.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate21.errors = vErrors;
      return errors === 0;
    }
    validate21.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var pattern10 = new RegExp("^[0-9a-f]{64}$", "u");
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
          if (data.scope === void 0 && (missing0 = "scope") || data.candidate === void 0 && (missing0 = "candidate") || data.semantic_profile === void 0 && (missing0 = "semantic_profile") || data.origin === void 0 && (missing0 = "origin") || data.representation_kind === void 0 && (missing0 = "representation_kind") || data.wire_version === void 0 && (missing0 = "wire_version") || data.smiles === void 0 && (missing0 = "smiles")) {
            validate20.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate" || key0 === "origin" || key0 === "representation_kind" || key0 === "scope" || key0 === "semantic_profile" || key0 === "smiles" || key0 === "wire_version")) {
                validate20.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.candidate !== void 0) {
                const _errs2 = errors;
                if (!validate21(data.candidate, { instancePath: instancePath + "/candidate", parentData: data, parentDataProperty: "candidate", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.origin !== void 0) {
                  let data1 = data.origin;
                  const _errs3 = errors;
                  if (typeof data1 !== "string") {
                    validate20.errors = [{ instancePath: instancePath + "/origin", schemaPath: "#/properties/origin/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("supplied" !== data1) {
                    validate20.errors = [{ instancePath: instancePath + "/origin", schemaPath: "#/properties/origin/const", keyword: "const", params: { allowedValue: "supplied" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.representation_kind !== void 0) {
                    let data2 = data.representation_kind;
                    const _errs5 = errors;
                    if (typeof data2 !== "string") {
                      validate20.errors = [{ instancePath: instancePath + "/representation_kind", schemaPath: "#/properties/representation_kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("finite_molecule" !== data2) {
                      validate20.errors = [{ instancePath: instancePath + "/representation_kind", schemaPath: "#/properties/representation_kind/const", keyword: "const", params: { allowedValue: "finite_molecule" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.scope !== void 0) {
                      let data3 = data.scope;
                      const _errs7 = errors;
                      const _errs8 = errors;
                      if (errors === _errs8) {
                        if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                          let missing1;
                          if (data3.tenant_id === void 0 && (missing1 = "tenant_id") || data3.project_id === void 0 && (missing1 = "project_id")) {
                            validate20.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                            return false;
                          } else {
                            const _errs10 = errors;
                            for (const key1 in data3) {
                              if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                validate20.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs10 === errors) {
                              if (data3.project_id !== void 0) {
                                let data4 = data3.project_id;
                                const _errs11 = errors;
                                if (errors === _errs11) {
                                  if (typeof data4 === "string") {
                                    if (func1(data4) > 128) {
                                      validate20.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate20.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate20.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate20.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid2 = _errs11 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data3.tenant_id !== void 0) {
                                  let data5 = data3.tenant_id;
                                  const _errs13 = errors;
                                  if (errors === _errs13) {
                                    if (typeof data5 === "string") {
                                      if (func1(data5) > 128) {
                                        validate20.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate20.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data5)) {
                                            validate20.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate20.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid2 = _errs13 === errors;
                                } else {
                                  var valid2 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate20.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.semantic_profile !== void 0) {
                        let data6 = data.semantic_profile;
                        const _errs15 = errors;
                        const _errs16 = errors;
                        if (errors === _errs16) {
                          if (data6 && typeof data6 == "object" && !Array.isArray(data6)) {
                            let missing2;
                            if (data6.schema_id === void 0 && (missing2 = "schema_id") || data6.version === void 0 && (missing2 = "version") || data6.sha256 === void 0 && (missing2 = "sha256")) {
                              validate20.errors = [{ instancePath: instancePath + "/semantic_profile", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                              return false;
                            } else {
                              const _errs18 = errors;
                              for (const key2 in data6) {
                                if (!(key2 === "schema_id" || key2 === "sha256" || key2 === "version")) {
                                  validate20.errors = [{ instancePath: instancePath + "/semantic_profile", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs18 === errors) {
                                if (data6.schema_id !== void 0) {
                                  let data7 = data6.schema_id;
                                  const _errs19 = errors;
                                  if (errors === _errs19) {
                                    if (typeof data7 === "string") {
                                      if (func1(data7) > 128) {
                                        validate20.errors = [{ instancePath: instancePath + "/semantic_profile/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data7) < 1) {
                                          validate20.errors = [{ instancePath: instancePath + "/semantic_profile/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data7)) {
                                            validate20.errors = [{ instancePath: instancePath + "/semantic_profile/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate20.errors = [{ instancePath: instancePath + "/semantic_profile/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid4 = _errs19 === errors;
                                } else {
                                  var valid4 = true;
                                }
                                if (valid4) {
                                  if (data6.sha256 !== void 0) {
                                    let data8 = data6.sha256;
                                    const _errs21 = errors;
                                    if (errors === _errs21) {
                                      if (typeof data8 === "string") {
                                        if (!pattern10.test(data8)) {
                                          validate20.errors = [{ instancePath: instancePath + "/semantic_profile/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                          return false;
                                        }
                                      } else {
                                        validate20.errors = [{ instancePath: instancePath + "/semantic_profile/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid4 = _errs21 === errors;
                                  } else {
                                    var valid4 = true;
                                  }
                                  if (valid4) {
                                    if (data6.version !== void 0) {
                                      let data9 = data6.version;
                                      const _errs23 = errors;
                                      if (typeof data9 !== "string") {
                                        validate20.errors = [{ instancePath: instancePath + "/semantic_profile/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if ("1" !== data9) {
                                        validate20.errors = [{ instancePath: instancePath + "/semantic_profile/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                        return false;
                                      }
                                      var valid4 = _errs23 === errors;
                                    } else {
                                      var valid4 = true;
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            validate20.errors = [{ instancePath: instancePath + "/semantic_profile", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                            return false;
                          }
                        }
                        var valid0 = _errs15 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.smiles !== void 0) {
                          let data10 = data.smiles;
                          const _errs25 = errors;
                          if (errors === _errs25) {
                            if (typeof data10 === "string") {
                              if (func1(data10) > 4096) {
                                validate20.errors = [{ instancePath: instancePath + "/smiles", schemaPath: "#/properties/smiles/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                                return false;
                              } else {
                                if (func1(data10) < 1) {
                                  validate20.errors = [{ instancePath: instancePath + "/smiles", schemaPath: "#/properties/smiles/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                }
                              }
                            } else {
                              validate20.errors = [{ instancePath: instancePath + "/smiles", schemaPath: "#/properties/smiles/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid0 = _errs25 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.wire_version !== void 0) {
                            let data11 = data.wire_version;
                            const _errs27 = errors;
                            if (typeof data11 !== "string") {
                              validate20.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("1" !== data11) {
                              validate20.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs27 === errors;
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
    exports.result = validate23;
    var schema46 = { "additionalProperties": false, "properties": { "code": { "enum": ["invalid_smiles", "unsupported_representation", "unsupported_feature", "profile_mismatch", "size_limit", "derivation_failed"], "title": "Code", "type": "string" }, "status": { "enum": ["invalid", "unsupported", "error"], "title": "Status", "type": "string" } }, "required": ["status", "code"], "title": "StructureFailure", "type": "object" };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate24.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate_id" || key0 === "revision" || key0 === "scope")) {
                validate24.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func1(data0) > 128) {
                      validate24.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate24.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate24.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate24.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate24.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate24.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate24.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate24.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate24.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate24.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate24.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate24.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate24.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate24.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate24.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate24.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate24.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate24.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate24.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate24.errors = vErrors;
      return errors === 0;
    }
    validate24.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var pattern14 = new RegExp("^[A-Za-z0-9+/]*={0,2}$", "u");
    var schema43 = { "additionalProperties": false, "properties": { "aromatic": { "title": "Aromatic", "type": "boolean" }, "atomic_number": { "maximum": 118, "minimum": 1, "title": "Atomic Number", "type": "integer" }, "chiral_tag": { "enum": ["CHI_UNSPECIFIED", "CHI_TETRAHEDRAL_CW", "CHI_TETRAHEDRAL_CCW"], "title": "Chiral Tag", "type": "string" }, "explicit_hydrogens": { "maximum": 16, "minimum": 0, "title": "Explicit Hydrogens", "type": "integer" }, "formal_charge": { "maximum": 16, "minimum": -16, "title": "Formal Charge", "type": "integer" }, "implicit_hydrogens": { "maximum": 16, "minimum": 0, "title": "Implicit Hydrogens", "type": "integer" }, "index": { "maximum": 511, "minimum": 0, "title": "Index", "type": "integer" }, "isotope": { "maximum": 999, "minimum": 0, "title": "Isotope", "type": "integer" } }, "required": ["index", "atomic_number", "isotope", "formal_charge", "explicit_hydrogens", "implicit_hydrogens", "aromatic", "chiral_tag"], "title": "Atom", "type": "object" };
    var schema44 = { "additionalProperties": false, "properties": { "begin": { "maximum": 511, "minimum": 0, "title": "Begin", "type": "integer" }, "end": { "maximum": 511, "minimum": 0, "title": "End", "type": "integer" }, "order": { "enum": ["single", "double", "triple", "aromatic"], "title": "Order", "type": "string" }, "stereo": { "enum": ["STEREONONE", "STEREOZ", "STEREOE", "STEREOCIS", "STEREOTRANS"], "title": "Stereo", "type": "string" }, "stereo_atoms": { "items": { "maximum": 511, "minimum": 0, "type": "integer" }, "maxItems": 2, "title": "Stereo Atoms", "type": "array" } }, "required": ["begin", "end", "order", "stereo", "stereo_atoms"], "title": "Bond", "type": "object" };
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
          if (data.atoms === void 0 && (missing0 = "atoms") || data.bonds === void 0 && (missing0 = "bonds")) {
            validate27.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "atoms" || key0 === "bonds")) {
                validate27.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.atoms !== void 0) {
                let data0 = data.atoms;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 512) {
                      validate27.errors = [{ instancePath: instancePath + "/atoms", schemaPath: "#/properties/atoms/maxItems", keyword: "maxItems", params: { limit: 512 }, message: "must NOT have more than 512 items" }];
                      return false;
                    } else {
                      if (data0.length < 1) {
                        validate27.errors = [{ instancePath: instancePath + "/atoms", schemaPath: "#/properties/atoms/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                        return false;
                      } else {
                        var valid1 = true;
                        const len0 = data0.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          let data1 = data0[i0];
                          const _errs4 = errors;
                          const _errs5 = errors;
                          if (errors === _errs5) {
                            if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                              let missing1;
                              if (data1.index === void 0 && (missing1 = "index") || data1.atomic_number === void 0 && (missing1 = "atomic_number") || data1.isotope === void 0 && (missing1 = "isotope") || data1.formal_charge === void 0 && (missing1 = "formal_charge") || data1.explicit_hydrogens === void 0 && (missing1 = "explicit_hydrogens") || data1.implicit_hydrogens === void 0 && (missing1 = "implicit_hydrogens") || data1.aromatic === void 0 && (missing1 = "aromatic") || data1.chiral_tag === void 0 && (missing1 = "chiral_tag")) {
                                validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0, schemaPath: "#/$defs/Atom/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                return false;
                              } else {
                                const _errs7 = errors;
                                for (const key1 in data1) {
                                  if (!(key1 === "aromatic" || key1 === "atomic_number" || key1 === "chiral_tag" || key1 === "explicit_hydrogens" || key1 === "formal_charge" || key1 === "implicit_hydrogens" || key1 === "index" || key1 === "isotope")) {
                                    validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0, schemaPath: "#/$defs/Atom/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs7 === errors) {
                                  if (data1.aromatic !== void 0) {
                                    const _errs8 = errors;
                                    if (typeof data1.aromatic !== "boolean") {
                                      validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/aromatic", schemaPath: "#/$defs/Atom/properties/aromatic/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                      return false;
                                    }
                                    var valid3 = _errs8 === errors;
                                  } else {
                                    var valid3 = true;
                                  }
                                  if (valid3) {
                                    if (data1.atomic_number !== void 0) {
                                      let data3 = data1.atomic_number;
                                      const _errs10 = errors;
                                      if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                        validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/atomic_number", schemaPath: "#/$defs/Atom/properties/atomic_number/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                        return false;
                                      }
                                      if (errors === _errs10) {
                                        if (typeof data3 == "number" && isFinite(data3)) {
                                          if (data3 > 118 || isNaN(data3)) {
                                            validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/atomic_number", schemaPath: "#/$defs/Atom/properties/atomic_number/maximum", keyword: "maximum", params: { comparison: "<=", limit: 118 }, message: "must be <= 118" }];
                                            return false;
                                          } else {
                                            if (data3 < 1 || isNaN(data3)) {
                                              validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/atomic_number", schemaPath: "#/$defs/Atom/properties/atomic_number/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                              return false;
                                            }
                                          }
                                        }
                                      }
                                      var valid3 = _errs10 === errors;
                                    } else {
                                      var valid3 = true;
                                    }
                                    if (valid3) {
                                      if (data1.chiral_tag !== void 0) {
                                        let data4 = data1.chiral_tag;
                                        const _errs12 = errors;
                                        if (typeof data4 !== "string") {
                                          validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/chiral_tag", schemaPath: "#/$defs/Atom/properties/chiral_tag/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        if (!(data4 === "CHI_UNSPECIFIED" || data4 === "CHI_TETRAHEDRAL_CW" || data4 === "CHI_TETRAHEDRAL_CCW")) {
                                          validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/chiral_tag", schemaPath: "#/$defs/Atom/properties/chiral_tag/enum", keyword: "enum", params: { allowedValues: schema43.properties.chiral_tag.enum }, message: "must be equal to one of the allowed values" }];
                                          return false;
                                        }
                                        var valid3 = _errs12 === errors;
                                      } else {
                                        var valid3 = true;
                                      }
                                      if (valid3) {
                                        if (data1.explicit_hydrogens !== void 0) {
                                          let data5 = data1.explicit_hydrogens;
                                          const _errs14 = errors;
                                          if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                            validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/explicit_hydrogens", schemaPath: "#/$defs/Atom/properties/explicit_hydrogens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                            return false;
                                          }
                                          if (errors === _errs14) {
                                            if (typeof data5 == "number" && isFinite(data5)) {
                                              if (data5 > 16 || isNaN(data5)) {
                                                validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/explicit_hydrogens", schemaPath: "#/$defs/Atom/properties/explicit_hydrogens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                                                return false;
                                              } else {
                                                if (data5 < 0 || isNaN(data5)) {
                                                  validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/explicit_hydrogens", schemaPath: "#/$defs/Atom/properties/explicit_hydrogens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                  return false;
                                                }
                                              }
                                            }
                                          }
                                          var valid3 = _errs14 === errors;
                                        } else {
                                          var valid3 = true;
                                        }
                                        if (valid3) {
                                          if (data1.formal_charge !== void 0) {
                                            let data6 = data1.formal_charge;
                                            const _errs16 = errors;
                                            if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                                              validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/formal_charge", schemaPath: "#/$defs/Atom/properties/formal_charge/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                              return false;
                                            }
                                            if (errors === _errs16) {
                                              if (typeof data6 == "number" && isFinite(data6)) {
                                                if (data6 > 16 || isNaN(data6)) {
                                                  validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/formal_charge", schemaPath: "#/$defs/Atom/properties/formal_charge/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                                                  return false;
                                                } else {
                                                  if (data6 < -16 || isNaN(data6)) {
                                                    validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/formal_charge", schemaPath: "#/$defs/Atom/properties/formal_charge/minimum", keyword: "minimum", params: { comparison: ">=", limit: -16 }, message: "must be >= -16" }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            }
                                            var valid3 = _errs16 === errors;
                                          } else {
                                            var valid3 = true;
                                          }
                                          if (valid3) {
                                            if (data1.implicit_hydrogens !== void 0) {
                                              let data7 = data1.implicit_hydrogens;
                                              const _errs18 = errors;
                                              if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                                                validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/implicit_hydrogens", schemaPath: "#/$defs/Atom/properties/implicit_hydrogens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                return false;
                                              }
                                              if (errors === _errs18) {
                                                if (typeof data7 == "number" && isFinite(data7)) {
                                                  if (data7 > 16 || isNaN(data7)) {
                                                    validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/implicit_hydrogens", schemaPath: "#/$defs/Atom/properties/implicit_hydrogens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                                                    return false;
                                                  } else {
                                                    if (data7 < 0 || isNaN(data7)) {
                                                      validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/implicit_hydrogens", schemaPath: "#/$defs/Atom/properties/implicit_hydrogens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                      return false;
                                                    }
                                                  }
                                                }
                                              }
                                              var valid3 = _errs18 === errors;
                                            } else {
                                              var valid3 = true;
                                            }
                                            if (valid3) {
                                              if (data1.index !== void 0) {
                                                let data8 = data1.index;
                                                const _errs20 = errors;
                                                if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)) && isFinite(data8))) {
                                                  validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/index", schemaPath: "#/$defs/Atom/properties/index/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                  return false;
                                                }
                                                if (errors === _errs20) {
                                                  if (typeof data8 == "number" && isFinite(data8)) {
                                                    if (data8 > 511 || isNaN(data8)) {
                                                      validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/index", schemaPath: "#/$defs/Atom/properties/index/maximum", keyword: "maximum", params: { comparison: "<=", limit: 511 }, message: "must be <= 511" }];
                                                      return false;
                                                    } else {
                                                      if (data8 < 0 || isNaN(data8)) {
                                                        validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/index", schemaPath: "#/$defs/Atom/properties/index/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                        return false;
                                                      }
                                                    }
                                                  }
                                                }
                                                var valid3 = _errs20 === errors;
                                              } else {
                                                var valid3 = true;
                                              }
                                              if (valid3) {
                                                if (data1.isotope !== void 0) {
                                                  let data9 = data1.isotope;
                                                  const _errs22 = errors;
                                                  if (!(typeof data9 == "number" && (!(data9 % 1) && !isNaN(data9)) && isFinite(data9))) {
                                                    validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/isotope", schemaPath: "#/$defs/Atom/properties/isotope/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                    return false;
                                                  }
                                                  if (errors === _errs22) {
                                                    if (typeof data9 == "number" && isFinite(data9)) {
                                                      if (data9 > 999 || isNaN(data9)) {
                                                        validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/isotope", schemaPath: "#/$defs/Atom/properties/isotope/maximum", keyword: "maximum", params: { comparison: "<=", limit: 999 }, message: "must be <= 999" }];
                                                        return false;
                                                      } else {
                                                        if (data9 < 0 || isNaN(data9)) {
                                                          validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0 + "/isotope", schemaPath: "#/$defs/Atom/properties/isotope/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                                  }
                                }
                              }
                            } else {
                              validate27.errors = [{ instancePath: instancePath + "/atoms/" + i0, schemaPath: "#/$defs/Atom/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid1 = _errs4 === errors;
                          if (!valid1) {
                            break;
                          }
                        }
                      }
                    }
                  } else {
                    validate27.errors = [{ instancePath: instancePath + "/atoms", schemaPath: "#/properties/atoms/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.bonds !== void 0) {
                  let data10 = data.bonds;
                  const _errs24 = errors;
                  if (errors === _errs24) {
                    if (Array.isArray(data10)) {
                      if (data10.length > 1024) {
                        validate27.errors = [{ instancePath: instancePath + "/bonds", schemaPath: "#/properties/bonds/maxItems", keyword: "maxItems", params: { limit: 1024 }, message: "must NOT have more than 1024 items" }];
                        return false;
                      } else {
                        var valid4 = true;
                        const len1 = data10.length;
                        for (let i1 = 0; i1 < len1; i1++) {
                          let data11 = data10[i1];
                          const _errs26 = errors;
                          const _errs27 = errors;
                          if (errors === _errs27) {
                            if (data11 && typeof data11 == "object" && !Array.isArray(data11)) {
                              let missing2;
                              if (data11.begin === void 0 && (missing2 = "begin") || data11.end === void 0 && (missing2 = "end") || data11.order === void 0 && (missing2 = "order") || data11.stereo === void 0 && (missing2 = "stereo") || data11.stereo_atoms === void 0 && (missing2 = "stereo_atoms")) {
                                validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1, schemaPath: "#/$defs/Bond/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                return false;
                              } else {
                                const _errs29 = errors;
                                for (const key2 in data11) {
                                  if (!(key2 === "begin" || key2 === "end" || key2 === "order" || key2 === "stereo" || key2 === "stereo_atoms")) {
                                    validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1, schemaPath: "#/$defs/Bond/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs29 === errors) {
                                  if (data11.begin !== void 0) {
                                    let data12 = data11.begin;
                                    const _errs30 = errors;
                                    if (!(typeof data12 == "number" && (!(data12 % 1) && !isNaN(data12)) && isFinite(data12))) {
                                      validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/begin", schemaPath: "#/$defs/Bond/properties/begin/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                      return false;
                                    }
                                    if (errors === _errs30) {
                                      if (typeof data12 == "number" && isFinite(data12)) {
                                        if (data12 > 511 || isNaN(data12)) {
                                          validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/begin", schemaPath: "#/$defs/Bond/properties/begin/maximum", keyword: "maximum", params: { comparison: "<=", limit: 511 }, message: "must be <= 511" }];
                                          return false;
                                        } else {
                                          if (data12 < 0 || isNaN(data12)) {
                                            validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/begin", schemaPath: "#/$defs/Bond/properties/begin/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                            return false;
                                          }
                                        }
                                      }
                                    }
                                    var valid6 = _errs30 === errors;
                                  } else {
                                    var valid6 = true;
                                  }
                                  if (valid6) {
                                    if (data11.end !== void 0) {
                                      let data13 = data11.end;
                                      const _errs32 = errors;
                                      if (!(typeof data13 == "number" && (!(data13 % 1) && !isNaN(data13)) && isFinite(data13))) {
                                        validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/end", schemaPath: "#/$defs/Bond/properties/end/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                        return false;
                                      }
                                      if (errors === _errs32) {
                                        if (typeof data13 == "number" && isFinite(data13)) {
                                          if (data13 > 511 || isNaN(data13)) {
                                            validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/end", schemaPath: "#/$defs/Bond/properties/end/maximum", keyword: "maximum", params: { comparison: "<=", limit: 511 }, message: "must be <= 511" }];
                                            return false;
                                          } else {
                                            if (data13 < 0 || isNaN(data13)) {
                                              validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/end", schemaPath: "#/$defs/Bond/properties/end/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                              return false;
                                            }
                                          }
                                        }
                                      }
                                      var valid6 = _errs32 === errors;
                                    } else {
                                      var valid6 = true;
                                    }
                                    if (valid6) {
                                      if (data11.order !== void 0) {
                                        let data14 = data11.order;
                                        const _errs34 = errors;
                                        if (typeof data14 !== "string") {
                                          validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/order", schemaPath: "#/$defs/Bond/properties/order/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        if (!(data14 === "single" || data14 === "double" || data14 === "triple" || data14 === "aromatic")) {
                                          validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/order", schemaPath: "#/$defs/Bond/properties/order/enum", keyword: "enum", params: { allowedValues: schema44.properties.order.enum }, message: "must be equal to one of the allowed values" }];
                                          return false;
                                        }
                                        var valid6 = _errs34 === errors;
                                      } else {
                                        var valid6 = true;
                                      }
                                      if (valid6) {
                                        if (data11.stereo !== void 0) {
                                          let data15 = data11.stereo;
                                          const _errs36 = errors;
                                          if (typeof data15 !== "string") {
                                            validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/stereo", schemaPath: "#/$defs/Bond/properties/stereo/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                          if (!(data15 === "STEREONONE" || data15 === "STEREOZ" || data15 === "STEREOE" || data15 === "STEREOCIS" || data15 === "STEREOTRANS")) {
                                            validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/stereo", schemaPath: "#/$defs/Bond/properties/stereo/enum", keyword: "enum", params: { allowedValues: schema44.properties.stereo.enum }, message: "must be equal to one of the allowed values" }];
                                            return false;
                                          }
                                          var valid6 = _errs36 === errors;
                                        } else {
                                          var valid6 = true;
                                        }
                                        if (valid6) {
                                          if (data11.stereo_atoms !== void 0) {
                                            let data16 = data11.stereo_atoms;
                                            const _errs38 = errors;
                                            if (errors === _errs38) {
                                              if (Array.isArray(data16)) {
                                                if (data16.length > 2) {
                                                  validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/stereo_atoms", schemaPath: "#/$defs/Bond/properties/stereo_atoms/maxItems", keyword: "maxItems", params: { limit: 2 }, message: "must NOT have more than 2 items" }];
                                                  return false;
                                                } else {
                                                  var valid7 = true;
                                                  const len2 = data16.length;
                                                  for (let i2 = 0; i2 < len2; i2++) {
                                                    let data17 = data16[i2];
                                                    const _errs40 = errors;
                                                    if (!(typeof data17 == "number" && (!(data17 % 1) && !isNaN(data17)) && isFinite(data17))) {
                                                      validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/stereo_atoms/" + i2, schemaPath: "#/$defs/Bond/properties/stereo_atoms/items/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                      return false;
                                                    }
                                                    if (errors === _errs40) {
                                                      if (typeof data17 == "number" && isFinite(data17)) {
                                                        if (data17 > 511 || isNaN(data17)) {
                                                          validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/stereo_atoms/" + i2, schemaPath: "#/$defs/Bond/properties/stereo_atoms/items/maximum", keyword: "maximum", params: { comparison: "<=", limit: 511 }, message: "must be <= 511" }];
                                                          return false;
                                                        } else {
                                                          if (data17 < 0 || isNaN(data17)) {
                                                            validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/stereo_atoms/" + i2, schemaPath: "#/$defs/Bond/properties/stereo_atoms/items/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                            return false;
                                                          }
                                                        }
                                                      }
                                                    }
                                                    var valid7 = _errs40 === errors;
                                                    if (!valid7) {
                                                      break;
                                                    }
                                                  }
                                                }
                                              } else {
                                                validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1 + "/stereo_atoms", schemaPath: "#/$defs/Bond/properties/stereo_atoms/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                                return false;
                                              }
                                            }
                                            var valid6 = _errs38 === errors;
                                          } else {
                                            var valid6 = true;
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              validate27.errors = [{ instancePath: instancePath + "/bonds/" + i1, schemaPath: "#/$defs/Bond/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid4 = _errs26 === errors;
                          if (!valid4) {
                            break;
                          }
                        }
                      }
                    } else {
                      validate27.errors = [{ instancePath: instancePath + "/bonds", schemaPath: "#/properties/bonds/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs24 === errors;
                } else {
                  var valid0 = true;
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
          if (data.status === void 0 && (missing0 = "status") || data.authority === void 0 && (missing0 = "authority") || data.method === void 0 && (missing0 = "method") || data.canonical_isomeric_smiles === void 0 && (missing0 = "canonical_isomeric_smiles") || data.graph === void 0 && (missing0 = "graph") || data.formula === void 0 && (missing0 = "formula") || data.depiction === void 0 && (missing0 = "depiction") || data.warnings === void 0 && (missing0 = "warnings")) {
            validate26.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "authority" || key0 === "canonical_isomeric_smiles" || key0 === "depiction" || key0 === "formula" || key0 === "graph" || key0 === "method" || key0 === "status" || key0 === "warnings")) {
                validate26.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.authority !== void 0) {
                let data0 = data.authority;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate26.errors = [{ instancePath: instancePath + "/authority", schemaPath: "#/properties/authority/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("structural_derivation" !== data0) {
                  validate26.errors = [{ instancePath: instancePath + "/authority", schemaPath: "#/properties/authority/const", keyword: "const", params: { allowedValue: "structural_derivation" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.canonical_isomeric_smiles !== void 0) {
                  let data1 = data.canonical_isomeric_smiles;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 8192) {
                        validate26.errors = [{ instancePath: instancePath + "/canonical_isomeric_smiles", schemaPath: "#/properties/canonical_isomeric_smiles/maxLength", keyword: "maxLength", params: { limit: 8192 }, message: "must NOT have more than 8192 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate26.errors = [{ instancePath: instancePath + "/canonical_isomeric_smiles", schemaPath: "#/properties/canonical_isomeric_smiles/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        }
                      }
                    } else {
                      validate26.errors = [{ instancePath: instancePath + "/canonical_isomeric_smiles", schemaPath: "#/properties/canonical_isomeric_smiles/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.depiction !== void 0) {
                    let data2 = data.depiction;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.media_type === void 0 && (missing1 = "media_type") || data2.width === void 0 && (missing1 = "width") || data2.height === void 0 && (missing1 = "height") || data2.sha256 === void 0 && (missing1 = "sha256") || data2.png_base64 === void 0 && (missing1 = "png_base64")) {
                          validate26.errors = [{ instancePath: instancePath + "/depiction", schemaPath: "#/$defs/Depiction/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "height" || key1 === "media_type" || key1 === "png_base64" || key1 === "sha256" || key1 === "width")) {
                              validate26.errors = [{ instancePath: instancePath + "/depiction", schemaPath: "#/$defs/Depiction/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs9 === errors) {
                            if (data2.height !== void 0) {
                              let data3 = data2.height;
                              const _errs10 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                validate26.errors = [{ instancePath: instancePath + "/depiction/height", schemaPath: "#/$defs/Depiction/properties/height/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (errors === _errs10) {
                                if (typeof data3 == "number" && isFinite(data3)) {
                                  if (data3 > 768 || isNaN(data3)) {
                                    validate26.errors = [{ instancePath: instancePath + "/depiction/height", schemaPath: "#/$defs/Depiction/properties/height/maximum", keyword: "maximum", params: { comparison: "<=", limit: 768 }, message: "must be <= 768" }];
                                    return false;
                                  } else {
                                    if (data3 < 1 || isNaN(data3)) {
                                      validate26.errors = [{ instancePath: instancePath + "/depiction/height", schemaPath: "#/$defs/Depiction/properties/height/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                              if (data2.media_type !== void 0) {
                                let data4 = data2.media_type;
                                const _errs12 = errors;
                                if (typeof data4 !== "string") {
                                  validate26.errors = [{ instancePath: instancePath + "/depiction/media_type", schemaPath: "#/$defs/Depiction/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("image/png" !== data4) {
                                  validate26.errors = [{ instancePath: instancePath + "/depiction/media_type", schemaPath: "#/$defs/Depiction/properties/media_type/const", keyword: "const", params: { allowedValue: "image/png" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data2.png_base64 !== void 0) {
                                  let data5 = data2.png_base64;
                                  const _errs14 = errors;
                                  if (errors === _errs14) {
                                    if (typeof data5 === "string") {
                                      if (func1(data5) > 174764) {
                                        validate26.errors = [{ instancePath: instancePath + "/depiction/png_base64", schemaPath: "#/$defs/Depiction/properties/png_base64/maxLength", keyword: "maxLength", params: { limit: 174764 }, message: "must NOT have more than 174764 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 4) {
                                          validate26.errors = [{ instancePath: instancePath + "/depiction/png_base64", schemaPath: "#/$defs/Depiction/properties/png_base64/minLength", keyword: "minLength", params: { limit: 4 }, message: "must NOT have fewer than 4 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern14.test(data5)) {
                                            validate26.errors = [{ instancePath: instancePath + "/depiction/png_base64", schemaPath: "#/$defs/Depiction/properties/png_base64/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9+/]*={0,2}$" }, message: 'must match pattern "^[A-Za-z0-9+/]*={0,2}$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate26.errors = [{ instancePath: instancePath + "/depiction/png_base64", schemaPath: "#/$defs/Depiction/properties/png_base64/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                                if (valid2) {
                                  if (data2.sha256 !== void 0) {
                                    let data6 = data2.sha256;
                                    const _errs16 = errors;
                                    if (errors === _errs16) {
                                      if (typeof data6 === "string") {
                                        if (!pattern10.test(data6)) {
                                          validate26.errors = [{ instancePath: instancePath + "/depiction/sha256", schemaPath: "#/$defs/Depiction/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                          return false;
                                        }
                                      } else {
                                        validate26.errors = [{ instancePath: instancePath + "/depiction/sha256", schemaPath: "#/$defs/Depiction/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid2 = _errs16 === errors;
                                  } else {
                                    var valid2 = true;
                                  }
                                  if (valid2) {
                                    if (data2.width !== void 0) {
                                      let data7 = data2.width;
                                      const _errs18 = errors;
                                      if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                                        validate26.errors = [{ instancePath: instancePath + "/depiction/width", schemaPath: "#/$defs/Depiction/properties/width/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                        return false;
                                      }
                                      if (errors === _errs18) {
                                        if (typeof data7 == "number" && isFinite(data7)) {
                                          if (data7 > 1024 || isNaN(data7)) {
                                            validate26.errors = [{ instancePath: instancePath + "/depiction/width", schemaPath: "#/$defs/Depiction/properties/width/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1024 }, message: "must be <= 1024" }];
                                            return false;
                                          } else {
                                            if (data7 < 1 || isNaN(data7)) {
                                              validate26.errors = [{ instancePath: instancePath + "/depiction/width", schemaPath: "#/$defs/Depiction/properties/width/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                              return false;
                                            }
                                          }
                                        }
                                      }
                                      var valid2 = _errs18 === errors;
                                    } else {
                                      var valid2 = true;
                                    }
                                  }
                                }
                              }
                            }
                          }
                        }
                      } else {
                        validate26.errors = [{ instancePath: instancePath + "/depiction", schemaPath: "#/$defs/Depiction/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.formula !== void 0) {
                      let data8 = data.formula;
                      const _errs20 = errors;
                      const _errs21 = errors;
                      if (errors === _errs21) {
                        if (data8 && typeof data8 == "object" && !Array.isArray(data8)) {
                          let missing2;
                          if (data8.text === void 0 && (missing2 = "text") || data8.isotope_policy === void 0 && (missing2 = "isotope_policy") || data8.charge_policy === void 0 && (missing2 = "charge_policy") || data8.net_formal_charge === void 0 && (missing2 = "net_formal_charge")) {
                            validate26.errors = [{ instancePath: instancePath + "/formula", schemaPath: "#/$defs/Formula/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs23 = errors;
                            for (const key2 in data8) {
                              if (!(key2 === "charge_policy" || key2 === "isotope_policy" || key2 === "net_formal_charge" || key2 === "text")) {
                                validate26.errors = [{ instancePath: instancePath + "/formula", schemaPath: "#/$defs/Formula/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs23 === errors) {
                              if (data8.charge_policy !== void 0) {
                                let data9 = data8.charge_policy;
                                const _errs24 = errors;
                                if (typeof data9 !== "string") {
                                  validate26.errors = [{ instancePath: instancePath + "/formula/charge_policy", schemaPath: "#/$defs/Formula/properties/charge_policy/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("explicit_net_formal_charge" !== data9) {
                                  validate26.errors = [{ instancePath: instancePath + "/formula/charge_policy", schemaPath: "#/$defs/Formula/properties/charge_policy/const", keyword: "const", params: { allowedValue: "explicit_net_formal_charge" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid4 = _errs24 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data8.isotope_policy !== void 0) {
                                  let data10 = data8.isotope_policy;
                                  const _errs26 = errors;
                                  if (typeof data10 !== "string") {
                                    validate26.errors = [{ instancePath: instancePath + "/formula/isotope_policy", schemaPath: "#/$defs/Formula/properties/isotope_policy/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("separate_isotopes" !== data10) {
                                    validate26.errors = [{ instancePath: instancePath + "/formula/isotope_policy", schemaPath: "#/$defs/Formula/properties/isotope_policy/const", keyword: "const", params: { allowedValue: "separate_isotopes" }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid4 = _errs26 === errors;
                                } else {
                                  var valid4 = true;
                                }
                                if (valid4) {
                                  if (data8.net_formal_charge !== void 0) {
                                    let data11 = data8.net_formal_charge;
                                    const _errs28 = errors;
                                    if (!(typeof data11 == "number" && (!(data11 % 1) && !isNaN(data11)) && isFinite(data11))) {
                                      validate26.errors = [{ instancePath: instancePath + "/formula/net_formal_charge", schemaPath: "#/$defs/Formula/properties/net_formal_charge/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                      return false;
                                    }
                                    if (errors === _errs28) {
                                      if (typeof data11 == "number" && isFinite(data11)) {
                                        if (data11 > 2048 || isNaN(data11)) {
                                          validate26.errors = [{ instancePath: instancePath + "/formula/net_formal_charge", schemaPath: "#/$defs/Formula/properties/net_formal_charge/maximum", keyword: "maximum", params: { comparison: "<=", limit: 2048 }, message: "must be <= 2048" }];
                                          return false;
                                        } else {
                                          if (data11 < -2048 || isNaN(data11)) {
                                            validate26.errors = [{ instancePath: instancePath + "/formula/net_formal_charge", schemaPath: "#/$defs/Formula/properties/net_formal_charge/minimum", keyword: "minimum", params: { comparison: ">=", limit: -2048 }, message: "must be >= -2048" }];
                                            return false;
                                          }
                                        }
                                      }
                                    }
                                    var valid4 = _errs28 === errors;
                                  } else {
                                    var valid4 = true;
                                  }
                                  if (valid4) {
                                    if (data8.text !== void 0) {
                                      let data12 = data8.text;
                                      const _errs30 = errors;
                                      if (errors === _errs30) {
                                        if (typeof data12 === "string") {
                                          if (func1(data12) > 256) {
                                            validate26.errors = [{ instancePath: instancePath + "/formula/text", schemaPath: "#/$defs/Formula/properties/text/maxLength", keyword: "maxLength", params: { limit: 256 }, message: "must NOT have more than 256 characters" }];
                                            return false;
                                          } else {
                                            if (func1(data12) < 1) {
                                              validate26.errors = [{ instancePath: instancePath + "/formula/text", schemaPath: "#/$defs/Formula/properties/text/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                              return false;
                                            }
                                          }
                                        } else {
                                          validate26.errors = [{ instancePath: instancePath + "/formula/text", schemaPath: "#/$defs/Formula/properties/text/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                      }
                                      var valid4 = _errs30 === errors;
                                    } else {
                                      var valid4 = true;
                                    }
                                  }
                                }
                              }
                            }
                          }
                        } else {
                          validate26.errors = [{ instancePath: instancePath + "/formula", schemaPath: "#/$defs/Formula/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs20 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.graph !== void 0) {
                        const _errs32 = errors;
                        if (!validate27(data.graph, { instancePath: instancePath + "/graph", parentData: data, parentDataProperty: "graph", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate27.errors : vErrors.concat(validate27.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs32 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.method !== void 0) {
                          let data14 = data.method;
                          const _errs33 = errors;
                          const _errs34 = errors;
                          if (errors === _errs34) {
                            if (data14 && typeof data14 == "object" && !Array.isArray(data14)) {
                              let missing3;
                              if (data14.toolkit === void 0 && (missing3 = "toolkit") || data14.toolkit_version === void 0 && (missing3 = "toolkit_version") || data14.method === void 0 && (missing3 = "method") || data14.environment_sha256 === void 0 && (missing3 = "environment_sha256")) {
                                validate26.errors = [{ instancePath: instancePath + "/method", schemaPath: "#/$defs/DerivationMethod/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" }];
                                return false;
                              } else {
                                const _errs36 = errors;
                                for (const key3 in data14) {
                                  if (!(key3 === "environment_sha256" || key3 === "method" || key3 === "toolkit" || key3 === "toolkit_version")) {
                                    validate26.errors = [{ instancePath: instancePath + "/method", schemaPath: "#/$defs/DerivationMethod/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs36 === errors) {
                                  if (data14.environment_sha256 !== void 0) {
                                    let data15 = data14.environment_sha256;
                                    const _errs37 = errors;
                                    if (errors === _errs37) {
                                      if (typeof data15 === "string") {
                                        if (!pattern10.test(data15)) {
                                          validate26.errors = [{ instancePath: instancePath + "/method/environment_sha256", schemaPath: "#/$defs/DerivationMethod/properties/environment_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                          return false;
                                        }
                                      } else {
                                        validate26.errors = [{ instancePath: instancePath + "/method/environment_sha256", schemaPath: "#/$defs/DerivationMethod/properties/environment_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid6 = _errs37 === errors;
                                  } else {
                                    var valid6 = true;
                                  }
                                  if (valid6) {
                                    if (data14.method !== void 0) {
                                      let data16 = data14.method;
                                      const _errs39 = errors;
                                      if (typeof data16 !== "string") {
                                        validate26.errors = [{ instancePath: instancePath + "/method/method", schemaPath: "#/$defs/DerivationMethod/properties/method/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if ("finite-smiles-2d-v1" !== data16) {
                                        validate26.errors = [{ instancePath: instancePath + "/method/method", schemaPath: "#/$defs/DerivationMethod/properties/method/const", keyword: "const", params: { allowedValue: "finite-smiles-2d-v1" }, message: "must be equal to constant" }];
                                        return false;
                                      }
                                      var valid6 = _errs39 === errors;
                                    } else {
                                      var valid6 = true;
                                    }
                                    if (valid6) {
                                      if (data14.toolkit !== void 0) {
                                        let data17 = data14.toolkit;
                                        const _errs41 = errors;
                                        if (typeof data17 !== "string") {
                                          validate26.errors = [{ instancePath: instancePath + "/method/toolkit", schemaPath: "#/$defs/DerivationMethod/properties/toolkit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        if ("rdkit" !== data17) {
                                          validate26.errors = [{ instancePath: instancePath + "/method/toolkit", schemaPath: "#/$defs/DerivationMethod/properties/toolkit/const", keyword: "const", params: { allowedValue: "rdkit" }, message: "must be equal to constant" }];
                                          return false;
                                        }
                                        var valid6 = _errs41 === errors;
                                      } else {
                                        var valid6 = true;
                                      }
                                      if (valid6) {
                                        if (data14.toolkit_version !== void 0) {
                                          let data18 = data14.toolkit_version;
                                          const _errs43 = errors;
                                          if (errors === _errs43) {
                                            if (typeof data18 === "string") {
                                              if (func1(data18) > 256) {
                                                validate26.errors = [{ instancePath: instancePath + "/method/toolkit_version", schemaPath: "#/$defs/DerivationMethod/properties/toolkit_version/maxLength", keyword: "maxLength", params: { limit: 256 }, message: "must NOT have more than 256 characters" }];
                                                return false;
                                              } else {
                                                if (func1(data18) < 1) {
                                                  validate26.errors = [{ instancePath: instancePath + "/method/toolkit_version", schemaPath: "#/$defs/DerivationMethod/properties/toolkit_version/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                  return false;
                                                }
                                              }
                                            } else {
                                              validate26.errors = [{ instancePath: instancePath + "/method/toolkit_version", schemaPath: "#/$defs/DerivationMethod/properties/toolkit_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid6 = _errs43 === errors;
                                        } else {
                                          var valid6 = true;
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              validate26.errors = [{ instancePath: instancePath + "/method", schemaPath: "#/$defs/DerivationMethod/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid0 = _errs33 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.status !== void 0) {
                            let data19 = data.status;
                            const _errs45 = errors;
                            if (typeof data19 !== "string") {
                              validate26.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("derived" !== data19) {
                              validate26.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "derived" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs45 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.warnings !== void 0) {
                              let data20 = data.warnings;
                              const _errs47 = errors;
                              if (errors === _errs47) {
                                if (Array.isArray(data20)) {
                                  if (data20.length > 1) {
                                    validate26.errors = [{ instancePath: instancePath + "/warnings", schemaPath: "#/properties/warnings/maxItems", keyword: "maxItems", params: { limit: 1 }, message: "must NOT have more than 1 items" }];
                                    return false;
                                  } else {
                                    var valid7 = true;
                                    const len0 = data20.length;
                                    for (let i0 = 0; i0 < len0; i0++) {
                                      let data21 = data20[i0];
                                      const _errs49 = errors;
                                      if (typeof data21 !== "string") {
                                        validate26.errors = [{ instancePath: instancePath + "/warnings/" + i0, schemaPath: "#/properties/warnings/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if ("unspecified_stereochemistry" !== data21) {
                                        validate26.errors = [{ instancePath: instancePath + "/warnings/" + i0, schemaPath: "#/properties/warnings/items/const", keyword: "const", params: { allowedValue: "unspecified_stereochemistry" }, message: "must be equal to constant" }];
                                        return false;
                                      }
                                      var valid7 = _errs49 === errors;
                                      if (!valid7) {
                                        break;
                                      }
                                    }
                                  }
                                } else {
                                  validate26.errors = [{ instancePath: instancePath + "/warnings", schemaPath: "#/properties/warnings/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs47 === errors;
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
          validate26.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate26.errors = vErrors;
      return errors === 0;
    }
    validate26.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate23(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.candidate === void 0 && (missing0 = "candidate") || data.semantic_profile === void 0 && (missing0 = "semantic_profile") || data.origin === void 0 && (missing0 = "origin") || data.representation_kind === void 0 && (missing0 = "representation_kind") || data.wire_version === void 0 && (missing0 = "wire_version") || data.source_sha256 === void 0 && (missing0 = "source_sha256") || data.outcome === void 0 && (missing0 = "outcome")) {
            validate23.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate" || key0 === "origin" || key0 === "outcome" || key0 === "representation_kind" || key0 === "scope" || key0 === "semantic_profile" || key0 === "source_sha256" || key0 === "wire_version")) {
                validate23.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.candidate !== void 0) {
                const _errs2 = errors;
                if (!validate24(data.candidate, { instancePath: instancePath + "/candidate", parentData: data, parentDataProperty: "candidate", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate24.errors : vErrors.concat(validate24.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.origin !== void 0) {
                  let data1 = data.origin;
                  const _errs3 = errors;
                  if (typeof data1 !== "string") {
                    validate23.errors = [{ instancePath: instancePath + "/origin", schemaPath: "#/properties/origin/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("supplied" !== data1) {
                    validate23.errors = [{ instancePath: instancePath + "/origin", schemaPath: "#/properties/origin/const", keyword: "const", params: { allowedValue: "supplied" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.outcome !== void 0) {
                    let data2 = data.outcome;
                    const _errs5 = errors;
                    const _errs6 = errors;
                    let valid1 = false;
                    let passing0 = null;
                    const _errs7 = errors;
                    if (!validate26(data2, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
                      errors = vErrors.length;
                    }
                    var _valid0 = _errs7 === errors;
                    if (_valid0) {
                      valid1 = true;
                      passing0 = 0;
                      var props0 = true;
                    }
                    const _errs8 = errors;
                    const _errs9 = errors;
                    if (errors === _errs9) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.status === void 0 && (missing1 = "status") || data2.code === void 0 && (missing1 = "code")) {
                          const err0 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/StructureFailure/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        } else {
                          const _errs11 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "code" || key1 === "status")) {
                              const err1 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/StructureFailure/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                              if (vErrors === null) {
                                vErrors = [err1];
                              } else {
                                vErrors.push(err1);
                              }
                              errors++;
                              break;
                            }
                          }
                          if (_errs11 === errors) {
                            if (data2.code !== void 0) {
                              let data3 = data2.code;
                              const _errs12 = errors;
                              if (typeof data3 !== "string") {
                                const err2 = { instancePath: instancePath + "/outcome/code", schemaPath: "#/$defs/StructureFailure/properties/code/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              }
                              if (!(data3 === "invalid_smiles" || data3 === "unsupported_representation" || data3 === "unsupported_feature" || data3 === "profile_mismatch" || data3 === "size_limit" || data3 === "derivation_failed")) {
                                const err3 = { instancePath: instancePath + "/outcome/code", schemaPath: "#/$defs/StructureFailure/properties/code/enum", keyword: "enum", params: { allowedValues: schema46.properties.code.enum }, message: "must be equal to one of the allowed values" };
                                if (vErrors === null) {
                                  vErrors = [err3];
                                } else {
                                  vErrors.push(err3);
                                }
                                errors++;
                              }
                              var valid3 = _errs12 === errors;
                            } else {
                              var valid3 = true;
                            }
                            if (valid3) {
                              if (data2.status !== void 0) {
                                let data4 = data2.status;
                                const _errs14 = errors;
                                if (typeof data4 !== "string") {
                                  const err4 = { instancePath: instancePath + "/outcome/status", schemaPath: "#/$defs/StructureFailure/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err4];
                                  } else {
                                    vErrors.push(err4);
                                  }
                                  errors++;
                                }
                                if (!(data4 === "invalid" || data4 === "unsupported" || data4 === "error")) {
                                  const err5 = { instancePath: instancePath + "/outcome/status", schemaPath: "#/$defs/StructureFailure/properties/status/enum", keyword: "enum", params: { allowedValues: schema46.properties.status.enum }, message: "must be equal to one of the allowed values" };
                                  if (vErrors === null) {
                                    vErrors = [err5];
                                  } else {
                                    vErrors.push(err5);
                                  }
                                  errors++;
                                }
                                var valid3 = _errs14 === errors;
                              } else {
                                var valid3 = true;
                              }
                            }
                          }
                        }
                      } else {
                        const err6 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/StructureFailure/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs8 === errors;
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
                      const err7 = { instancePath: instancePath + "/outcome", schemaPath: "#/properties/outcome/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                      if (vErrors === null) {
                        vErrors = [err7];
                      } else {
                        vErrors.push(err7);
                      }
                      errors++;
                      validate23.errors = vErrors;
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
                    if (data.representation_kind !== void 0) {
                      let data5 = data.representation_kind;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        validate23.errors = [{ instancePath: instancePath + "/representation_kind", schemaPath: "#/properties/representation_kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("finite_molecule" !== data5) {
                        validate23.errors = [{ instancePath: instancePath + "/representation_kind", schemaPath: "#/properties/representation_kind/const", keyword: "const", params: { allowedValue: "finite_molecule" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs17 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.scope !== void 0) {
                        let data6 = data.scope;
                        const _errs19 = errors;
                        const _errs20 = errors;
                        if (errors === _errs20) {
                          if (data6 && typeof data6 == "object" && !Array.isArray(data6)) {
                            let missing2;
                            if (data6.tenant_id === void 0 && (missing2 = "tenant_id") || data6.project_id === void 0 && (missing2 = "project_id")) {
                              validate23.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                              return false;
                            } else {
                              const _errs22 = errors;
                              for (const key2 in data6) {
                                if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                  validate23.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs22 === errors) {
                                if (data6.project_id !== void 0) {
                                  let data7 = data6.project_id;
                                  const _errs23 = errors;
                                  if (errors === _errs23) {
                                    if (typeof data7 === "string") {
                                      if (func1(data7) > 128) {
                                        validate23.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data7) < 1) {
                                          validate23.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data7)) {
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
                                  var valid5 = _errs23 === errors;
                                } else {
                                  var valid5 = true;
                                }
                                if (valid5) {
                                  if (data6.tenant_id !== void 0) {
                                    let data8 = data6.tenant_id;
                                    const _errs25 = errors;
                                    if (errors === _errs25) {
                                      if (typeof data8 === "string") {
                                        if (func1(data8) > 128) {
                                          validate23.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data8) < 1) {
                                            validate23.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data8)) {
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
                                    var valid5 = _errs25 === errors;
                                  } else {
                                    var valid5 = true;
                                  }
                                }
                              }
                            }
                          } else {
                            validate23.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                            return false;
                          }
                        }
                        var valid0 = _errs19 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.semantic_profile !== void 0) {
                          let data9 = data.semantic_profile;
                          const _errs27 = errors;
                          const _errs28 = errors;
                          if (errors === _errs28) {
                            if (data9 && typeof data9 == "object" && !Array.isArray(data9)) {
                              let missing3;
                              if (data9.schema_id === void 0 && (missing3 = "schema_id") || data9.version === void 0 && (missing3 = "version") || data9.sha256 === void 0 && (missing3 = "sha256")) {
                                validate23.errors = [{ instancePath: instancePath + "/semantic_profile", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" }];
                                return false;
                              } else {
                                const _errs30 = errors;
                                for (const key3 in data9) {
                                  if (!(key3 === "schema_id" || key3 === "sha256" || key3 === "version")) {
                                    validate23.errors = [{ instancePath: instancePath + "/semantic_profile", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs30 === errors) {
                                  if (data9.schema_id !== void 0) {
                                    let data10 = data9.schema_id;
                                    const _errs31 = errors;
                                    if (errors === _errs31) {
                                      if (typeof data10 === "string") {
                                        if (func1(data10) > 128) {
                                          validate23.errors = [{ instancePath: instancePath + "/semantic_profile/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data10) < 1) {
                                            validate23.errors = [{ instancePath: instancePath + "/semantic_profile/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data10)) {
                                              validate23.errors = [{ instancePath: instancePath + "/semantic_profile/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate23.errors = [{ instancePath: instancePath + "/semantic_profile/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid7 = _errs31 === errors;
                                  } else {
                                    var valid7 = true;
                                  }
                                  if (valid7) {
                                    if (data9.sha256 !== void 0) {
                                      let data11 = data9.sha256;
                                      const _errs33 = errors;
                                      if (errors === _errs33) {
                                        if (typeof data11 === "string") {
                                          if (!pattern10.test(data11)) {
                                            validate23.errors = [{ instancePath: instancePath + "/semantic_profile/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                            return false;
                                          }
                                        } else {
                                          validate23.errors = [{ instancePath: instancePath + "/semantic_profile/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                      }
                                      var valid7 = _errs33 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                    if (valid7) {
                                      if (data9.version !== void 0) {
                                        let data12 = data9.version;
                                        const _errs35 = errors;
                                        if (typeof data12 !== "string") {
                                          validate23.errors = [{ instancePath: instancePath + "/semantic_profile/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        if ("1" !== data12) {
                                          validate23.errors = [{ instancePath: instancePath + "/semantic_profile/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                          return false;
                                        }
                                        var valid7 = _errs35 === errors;
                                      } else {
                                        var valid7 = true;
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              validate23.errors = [{ instancePath: instancePath + "/semantic_profile", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid0 = _errs27 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.source_sha256 !== void 0) {
                            let data13 = data.source_sha256;
                            const _errs37 = errors;
                            if (errors === _errs37) {
                              if (typeof data13 === "string") {
                                if (!pattern10.test(data13)) {
                                  validate23.errors = [{ instancePath: instancePath + "/source_sha256", schemaPath: "#/properties/source_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate23.errors = [{ instancePath: instancePath + "/source_sha256", schemaPath: "#/properties/source_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid0 = _errs37 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.wire_version !== void 0) {
                              let data14 = data.wire_version;
                              const _errs39 = errors;
                              if (typeof data14 !== "string") {
                                validate23.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("1" !== data14) {
                                validate23.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs39 === errors;
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
          validate23.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate23.errors = vErrors;
      return errors === 0;
    }
    validate23.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.candidate = validate30;
    function validate31(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate31.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate31.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate_id" || key0 === "revision" || key0 === "scope")) {
                validate31.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func1(data0) > 128) {
                      validate31.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate31.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate31.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate31.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate31.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate31.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate31.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate31.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate31.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate31.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate31.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate31.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate31.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate31.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate31.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate31.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate31.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate31.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate31.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate31.errors = vErrors;
      return errors === 0;
    }
    validate31.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var pattern26 = new RegExp("^[^\\s/]+/[^\\s/]+$", "u");
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate33.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate33.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate33.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate33.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate33.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate33.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate33.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate33.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern26.test(data1)) {
                            validate33.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate33.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate33.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate33.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate33.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate33.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate33.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate33.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    if (!pattern10.test(data4)) {
                                      validate33.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate33.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate33.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate33.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate33.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate33.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate33.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate33.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate33.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
                                          validate33.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate33.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        validate33.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate33.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
                                            validate33.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate33.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate33.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            if (!pattern10.test(data9)) {
                              validate33.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate33.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate33.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate33.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate33.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate33.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate33.errors = vErrors;
      return errors === 0;
    }
    validate33.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate30(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate30.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.reference === void 0 && (missing0 = "reference") || data.representation === void 0 && (missing0 = "representation") || data.supersedes === void 0 && (missing0 = "supersedes")) {
            validate30.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "reference" || key0 === "representation" || key0 === "supersedes" || key0 === "wire_version")) {
                validate30.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.reference !== void 0) {
                const _errs2 = errors;
                if (!validate31(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate31.errors : vErrors.concat(validate31.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.representation !== void 0) {
                  const _errs3 = errors;
                  if (!validate33(data.representation, { instancePath: instancePath + "/representation", parentData: data, parentDataProperty: "representation", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate33.errors : vErrors.concat(validate33.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.supersedes !== void 0) {
                    let data2 = data.supersedes;
                    const _errs4 = errors;
                    const _errs5 = errors;
                    let valid1 = false;
                    const _errs6 = errors;
                    if (!validate31(data2, { instancePath: instancePath + "/supersedes", parentData: data, parentDataProperty: "supersedes", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate31.errors : vErrors.concat(validate31.errors);
                      errors = vErrors.length;
                    }
                    var _valid0 = _errs6 === errors;
                    valid1 = valid1 || _valid0;
                    const _errs7 = errors;
                    if (data2 !== null) {
                      const err0 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    }
                    var _valid0 = _errs7 === errors;
                    valid1 = valid1 || _valid0;
                    if (!valid1) {
                      const err1 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err1];
                      } else {
                        vErrors.push(err1);
                      }
                      errors++;
                      validate30.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs5;
                      if (vErrors !== null) {
                        if (_errs5) {
                          vErrors.length = _errs5;
                        } else {
                          vErrors = null;
                        }
                      }
                    }
                    var valid0 = _errs4 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.wire_version !== void 0) {
                      let data3 = data.wire_version;
                      const _errs9 = errors;
                      if (typeof data3 !== "string") {
                        validate30.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data3) {
                        validate30.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
        } else {
          validate30.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate30.errors = vErrors;
      return errors === 0;
    }
    validate30.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.producer = validate36;
    var schema56 = { "additionalProperties": false, "properties": { "accepted_run_revision": { "maximum": 9007199254740991, "minimum": 0, "title": "Accepted Run Revision", "type": "integer" }, "activation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Activation Id", "type": "string" }, "canonical_result": { "title": "Canonical Result", "type": "boolean" }, "completion_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Completion Id", "type": "string" }, "result": { "$ref": "#/$defs/Completion" }, "retention_reservation_ids": { "default": [], "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 65, "title": "Retention Reservation Ids", "type": "array" }, "run_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Run Id", "type": "string" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "run_id", "completion_id", "activation_id", "accepted_run_revision", "canonical_result", "result"], "title": "CompletionRecord", "type": "object" };
    var func51 = Object.prototype.hasOwnProperty;
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate40.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate40.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate40.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate40.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate40.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate40.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate40.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate40.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern26.test(data1)) {
                            validate40.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate40.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate40.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate40.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate40.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate40.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate40.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate40.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    if (!pattern10.test(data4)) {
                                      validate40.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate40.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate40.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate40.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate40.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate40.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate40.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate40.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate40.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
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
                                        validate40.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate40.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
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
                                  var valid4 = _errs22 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate40.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            if (!pattern10.test(data9)) {
                              validate40.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate40.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate40.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate40.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate40.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate40.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate40.errors = vErrors;
      return errors === 0;
    }
    validate40.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.port === void 0 && (missing0 = "port") || data.artifact === void 0 && (missing0 = "artifact")) {
            validate42.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "port")) {
                validate42.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                const _errs2 = errors;
                if (!validate40(data.artifact, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.port !== void 0) {
                  let data1 = data.port;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate42.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate42.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate42.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate42.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          validate42.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate42.errors = vErrors;
      return errors === 0;
    }
    validate42.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.status === void 0 && (missing0 = "status") || data.outputs === void 0 && (missing0 = "outputs")) {
            validate39.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "checkpoint" || key0 === "outputs" || key0 === "status")) {
                validate39.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.checkpoint !== void 0) {
                let data0 = data.checkpoint;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate40(data0, { instancePath: instancePath + "/checkpoint", parentData: data, parentDataProperty: "checkpoint", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/checkpoint", schemaPath: "#/properties/checkpoint/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err1 = { instancePath: instancePath + "/checkpoint", schemaPath: "#/properties/checkpoint/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate39.errors = vErrors;
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
                if (data.outputs !== void 0) {
                  let data1 = data.outputs;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (Array.isArray(data1)) {
                      if (data1.length > 64) {
                        validate39.errors = [{ instancePath: instancePath + "/outputs", schemaPath: "#/properties/outputs/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                        return false;
                      } else {
                        if (data1.length < 1) {
                          validate39.errors = [{ instancePath: instancePath + "/outputs", schemaPath: "#/properties/outputs/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                          return false;
                        } else {
                          var valid2 = true;
                          const len0 = data1.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs9 = errors;
                            if (!validate42(data1[i0], { instancePath: instancePath + "/outputs/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate42.errors : vErrors.concat(validate42.errors);
                              errors = vErrors.length;
                            }
                            var valid2 = _errs9 === errors;
                            if (!valid2) {
                              break;
                            }
                          }
                        }
                      }
                    } else {
                      validate39.errors = [{ instancePath: instancePath + "/outputs", schemaPath: "#/properties/outputs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs7 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.status !== void 0) {
                    let data3 = data.status;
                    const _errs10 = errors;
                    if (typeof data3 !== "string") {
                      validate39.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("succeeded" !== data3) {
                      validate39.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "succeeded" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs10 === errors;
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
    function validate38(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
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
          if (data.schema_version === void 0 && (missing0 = "schema_version") || data.invocation_id === void 0 && (missing0 = "invocation_id") || data.attempt_id === void 0 && (missing0 = "attempt_id") || data.fence === void 0 && (missing0 = "fence") || data.outcome === void 0 && (missing0 = "outcome")) {
            validate38.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "attempt_id" || key0 === "fence" || key0 === "invocation_id" || key0 === "outcome" || key0 === "schema_version")) {
                validate38.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.attempt_id !== void 0) {
                let data0 = data.attempt_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate38.errors = [{ instancePath: instancePath + "/attempt_id", schemaPath: "#/properties/attempt_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate38.errors = [{ instancePath: instancePath + "/attempt_id", schemaPath: "#/properties/attempt_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate38.errors = [{ instancePath: instancePath + "/attempt_id", schemaPath: "#/properties/attempt_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate38.errors = [{ instancePath: instancePath + "/attempt_id", schemaPath: "#/properties/attempt_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.fence !== void 0) {
                  let data1 = data.fence;
                  const _errs4 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate38.errors = [{ instancePath: instancePath + "/fence", schemaPath: "#/properties/fence/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate38.errors = [{ instancePath: instancePath + "/fence", schemaPath: "#/properties/fence/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate38.errors = [{ instancePath: instancePath + "/fence", schemaPath: "#/properties/fence/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                  if (data.invocation_id !== void 0) {
                    let data2 = data.invocation_id;
                    const _errs6 = errors;
                    if (errors === _errs6) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 128) {
                          validate38.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate38.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern4.test(data2)) {
                              validate38.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate38.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.outcome !== void 0) {
                      let data3 = data.outcome;
                      const _errs8 = errors;
                      const _errs9 = errors;
                      let valid1 = false;
                      let passing0 = null;
                      const _errs10 = errors;
                      if (!validate39(data3, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate39.errors : vErrors.concat(validate39.errors);
                        errors = vErrors.length;
                      }
                      var _valid0 = _errs10 === errors;
                      if (_valid0) {
                        valid1 = true;
                        passing0 = 0;
                        var props0 = true;
                      }
                      const _errs11 = errors;
                      const _errs12 = errors;
                      if (errors === _errs12) {
                        if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                          let missing1;
                          if (data3.status === void 0 && (missing1 = "status") || data3.reason_code === void 0 && (missing1 = "reason_code")) {
                            const err0 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/Abstained/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                            if (vErrors === null) {
                              vErrors = [err0];
                            } else {
                              vErrors.push(err0);
                            }
                            errors++;
                          } else {
                            const _errs14 = errors;
                            for (const key1 in data3) {
                              if (!(key1 === "reason_code" || key1 === "status")) {
                                const err1 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/Abstained/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                              if (data3.reason_code !== void 0) {
                                let data4 = data3.reason_code;
                                const _errs15 = errors;
                                if (errors === _errs15) {
                                  if (typeof data4 === "string") {
                                    if (func1(data4) > 128) {
                                      const err2 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Abstained/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err2];
                                      } else {
                                        vErrors.push(err2);
                                      }
                                      errors++;
                                    } else {
                                      if (func1(data4) < 1) {
                                        const err3 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Abstained/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err3];
                                        } else {
                                          vErrors.push(err3);
                                        }
                                        errors++;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          const err4 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Abstained/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                    const err5 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Abstained/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err5];
                                    } else {
                                      vErrors.push(err5);
                                    }
                                    errors++;
                                  }
                                }
                                var valid3 = _errs15 === errors;
                              } else {
                                var valid3 = true;
                              }
                              if (valid3) {
                                if (data3.status !== void 0) {
                                  let data5 = data3.status;
                                  const _errs17 = errors;
                                  if (typeof data5 !== "string") {
                                    const err6 = { instancePath: instancePath + "/outcome/status", schemaPath: "#/$defs/Abstained/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err6];
                                    } else {
                                      vErrors.push(err6);
                                    }
                                    errors++;
                                  }
                                  if ("abstained" !== data5) {
                                    const err7 = { instancePath: instancePath + "/outcome/status", schemaPath: "#/$defs/Abstained/properties/status/const", keyword: "const", params: { allowedValue: "abstained" }, message: "must be equal to constant" };
                                    if (vErrors === null) {
                                      vErrors = [err7];
                                    } else {
                                      vErrors.push(err7);
                                    }
                                    errors++;
                                  }
                                  var valid3 = _errs17 === errors;
                                } else {
                                  var valid3 = true;
                                }
                              }
                            }
                          }
                        } else {
                          const err8 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/Abstained/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                          if (vErrors === null) {
                            vErrors = [err8];
                          } else {
                            vErrors.push(err8);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs11 === errors;
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
                        const _errs19 = errors;
                        const _errs20 = errors;
                        if (errors === _errs20) {
                          if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                            let missing2;
                            if (data3.status === void 0 && (missing2 = "status") || data3.reason_code === void 0 && (missing2 = "reason_code") || data3.retryable === void 0 && (missing2 = "retryable")) {
                              const err9 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/Failed/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                              if (vErrors === null) {
                                vErrors = [err9];
                              } else {
                                vErrors.push(err9);
                              }
                              errors++;
                            } else {
                              const _errs22 = errors;
                              for (const key2 in data3) {
                                if (!(key2 === "reason_code" || key2 === "retryable" || key2 === "status")) {
                                  const err10 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/Failed/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                                  if (vErrors === null) {
                                    vErrors = [err10];
                                  } else {
                                    vErrors.push(err10);
                                  }
                                  errors++;
                                  break;
                                }
                              }
                              if (_errs22 === errors) {
                                if (data3.reason_code !== void 0) {
                                  let data6 = data3.reason_code;
                                  const _errs23 = errors;
                                  if (errors === _errs23) {
                                    if (typeof data6 === "string") {
                                      if (func1(data6) > 128) {
                                        const err11 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Failed/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err11];
                                        } else {
                                          vErrors.push(err11);
                                        }
                                        errors++;
                                      } else {
                                        if (func1(data6) < 1) {
                                          const err12 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Failed/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err12];
                                          } else {
                                            vErrors.push(err12);
                                          }
                                          errors++;
                                        } else {
                                          if (!pattern4.test(data6)) {
                                            const err13 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Failed/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                            if (vErrors === null) {
                                              vErrors = [err13];
                                            } else {
                                              vErrors.push(err13);
                                            }
                                            errors++;
                                          }
                                        }
                                      }
                                    } else {
                                      const err14 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Failed/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err14];
                                      } else {
                                        vErrors.push(err14);
                                      }
                                      errors++;
                                    }
                                  }
                                  var valid5 = _errs23 === errors;
                                } else {
                                  var valid5 = true;
                                }
                                if (valid5) {
                                  if (data3.retryable !== void 0) {
                                    const _errs25 = errors;
                                    if (typeof data3.retryable !== "boolean") {
                                      const err15 = { instancePath: instancePath + "/outcome/retryable", schemaPath: "#/$defs/Failed/properties/retryable/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" };
                                      if (vErrors === null) {
                                        vErrors = [err15];
                                      } else {
                                        vErrors.push(err15);
                                      }
                                      errors++;
                                    }
                                    var valid5 = _errs25 === errors;
                                  } else {
                                    var valid5 = true;
                                  }
                                  if (valid5) {
                                    if (data3.status !== void 0) {
                                      let data8 = data3.status;
                                      const _errs27 = errors;
                                      if (typeof data8 !== "string") {
                                        const err16 = { instancePath: instancePath + "/outcome/status", schemaPath: "#/$defs/Failed/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err16];
                                        } else {
                                          vErrors.push(err16);
                                        }
                                        errors++;
                                      }
                                      if ("failed" !== data8) {
                                        const err17 = { instancePath: instancePath + "/outcome/status", schemaPath: "#/$defs/Failed/properties/status/const", keyword: "const", params: { allowedValue: "failed" }, message: "must be equal to constant" };
                                        if (vErrors === null) {
                                          vErrors = [err17];
                                        } else {
                                          vErrors.push(err17);
                                        }
                                        errors++;
                                      }
                                      var valid5 = _errs27 === errors;
                                    } else {
                                      var valid5 = true;
                                    }
                                  }
                                }
                              }
                            }
                          } else {
                            const err18 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/Failed/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err18];
                            } else {
                              vErrors.push(err18);
                            }
                            errors++;
                          }
                        }
                        var _valid0 = _errs19 === errors;
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
                          const _errs29 = errors;
                          const _errs30 = errors;
                          if (errors === _errs30) {
                            if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                              let missing3;
                              if (data3.status === void 0 && (missing3 = "status") || data3.operation_id === void 0 && (missing3 = "operation_id") || data3.reason_code === void 0 && (missing3 = "reason_code")) {
                                const err19 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/Uncertain/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" };
                                if (vErrors === null) {
                                  vErrors = [err19];
                                } else {
                                  vErrors.push(err19);
                                }
                                errors++;
                              } else {
                                const _errs32 = errors;
                                for (const key3 in data3) {
                                  if (!(key3 === "operation_id" || key3 === "reason_code" || key3 === "status")) {
                                    const err20 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/Uncertain/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" };
                                    if (vErrors === null) {
                                      vErrors = [err20];
                                    } else {
                                      vErrors.push(err20);
                                    }
                                    errors++;
                                    break;
                                  }
                                }
                                if (_errs32 === errors) {
                                  if (data3.operation_id !== void 0) {
                                    let data9 = data3.operation_id;
                                    const _errs33 = errors;
                                    if (errors === _errs33) {
                                      if (typeof data9 === "string") {
                                        if (func1(data9) > 128) {
                                          const err21 = { instancePath: instancePath + "/outcome/operation_id", schemaPath: "#/$defs/Uncertain/properties/operation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err21];
                                          } else {
                                            vErrors.push(err21);
                                          }
                                          errors++;
                                        } else {
                                          if (func1(data9) < 1) {
                                            const err22 = { instancePath: instancePath + "/outcome/operation_id", schemaPath: "#/$defs/Uncertain/properties/operation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                            if (vErrors === null) {
                                              vErrors = [err22];
                                            } else {
                                              vErrors.push(err22);
                                            }
                                            errors++;
                                          } else {
                                            if (!pattern4.test(data9)) {
                                              const err23 = { instancePath: instancePath + "/outcome/operation_id", schemaPath: "#/$defs/Uncertain/properties/operation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                        const err24 = { instancePath: instancePath + "/outcome/operation_id", schemaPath: "#/$defs/Uncertain/properties/operation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err24];
                                        } else {
                                          vErrors.push(err24);
                                        }
                                        errors++;
                                      }
                                    }
                                    var valid7 = _errs33 === errors;
                                  } else {
                                    var valid7 = true;
                                  }
                                  if (valid7) {
                                    if (data3.reason_code !== void 0) {
                                      let data10 = data3.reason_code;
                                      const _errs35 = errors;
                                      if (errors === _errs35) {
                                        if (typeof data10 === "string") {
                                          if (func1(data10) > 128) {
                                            const err25 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Uncertain/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                            if (vErrors === null) {
                                              vErrors = [err25];
                                            } else {
                                              vErrors.push(err25);
                                            }
                                            errors++;
                                          } else {
                                            if (func1(data10) < 1) {
                                              const err26 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Uncertain/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                              if (vErrors === null) {
                                                vErrors = [err26];
                                              } else {
                                                vErrors.push(err26);
                                              }
                                              errors++;
                                            } else {
                                              if (!pattern4.test(data10)) {
                                                const err27 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Uncertain/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                                if (vErrors === null) {
                                                  vErrors = [err27];
                                                } else {
                                                  vErrors.push(err27);
                                                }
                                                errors++;
                                              }
                                            }
                                          }
                                        } else {
                                          const err28 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/Uncertain/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err28];
                                          } else {
                                            vErrors.push(err28);
                                          }
                                          errors++;
                                        }
                                      }
                                      var valid7 = _errs35 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                    if (valid7) {
                                      if (data3.status !== void 0) {
                                        let data11 = data3.status;
                                        const _errs37 = errors;
                                        if (typeof data11 !== "string") {
                                          const err29 = { instancePath: instancePath + "/outcome/status", schemaPath: "#/$defs/Uncertain/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err29];
                                          } else {
                                            vErrors.push(err29);
                                          }
                                          errors++;
                                        }
                                        if ("uncertain_external_effect" !== data11) {
                                          const err30 = { instancePath: instancePath + "/outcome/status", schemaPath: "#/$defs/Uncertain/properties/status/const", keyword: "const", params: { allowedValue: "uncertain_external_effect" }, message: "must be equal to constant" };
                                          if (vErrors === null) {
                                            vErrors = [err30];
                                          } else {
                                            vErrors.push(err30);
                                          }
                                          errors++;
                                        }
                                        var valid7 = _errs37 === errors;
                                      } else {
                                        var valid7 = true;
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              const err31 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/Uncertain/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                              if (vErrors === null) {
                                vErrors = [err31];
                              } else {
                                vErrors.push(err31);
                              }
                              errors++;
                            }
                          }
                          var _valid0 = _errs29 === errors;
                          if (_valid0 && valid1) {
                            valid1 = false;
                            passing0 = [passing0, 3];
                          } else {
                            if (_valid0) {
                              valid1 = true;
                              passing0 = 3;
                              if (props0 !== true) {
                                props0 = true;
                              }
                            }
                          }
                        }
                      }
                      if (!valid1) {
                        const err32 = { instancePath: instancePath + "/outcome", schemaPath: "#/properties/outcome/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                        if (vErrors === null) {
                          vErrors = [err32];
                        } else {
                          vErrors.push(err32);
                        }
                        errors++;
                        validate38.errors = vErrors;
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
                      if (data.schema_version !== void 0) {
                        let data12 = data.schema_version;
                        const _errs40 = errors;
                        if (typeof data12 !== "string") {
                          validate38.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data12) {
                          validate38.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs40 === errors;
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
          validate38.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate38.errors = vErrors;
      return errors === 0;
    }
    validate38.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.completion_id === void 0 && (missing0 = "completion_id") || data.activation_id === void 0 && (missing0 = "activation_id") || data.accepted_run_revision === void 0 && (missing0 = "accepted_run_revision") || data.canonical_result === void 0 && (missing0 = "canonical_result") || data.result === void 0 && (missing0 = "result")) {
            validate37.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func51.call(schema56.properties, key0)) {
                validate37.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.accepted_run_revision !== void 0) {
                let data0 = data.accepted_run_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate37.errors = [{ instancePath: instancePath + "/accepted_run_revision", schemaPath: "#/properties/accepted_run_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate37.errors = [{ instancePath: instancePath + "/accepted_run_revision", schemaPath: "#/properties/accepted_run_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate37.errors = [{ instancePath: instancePath + "/accepted_run_revision", schemaPath: "#/properties/accepted_run_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                if (data.activation_id !== void 0) {
                  let data1 = data.activation_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate37.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate37.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate37.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate37.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.canonical_result !== void 0) {
                    const _errs6 = errors;
                    if (typeof data.canonical_result !== "boolean") {
                      validate37.errors = [{ instancePath: instancePath + "/canonical_result", schemaPath: "#/properties/canonical_result/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                      return false;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.completion_id !== void 0) {
                      let data3 = data.completion_id;
                      const _errs8 = errors;
                      if (errors === _errs8) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 128) {
                            validate37.errors = [{ instancePath: instancePath + "/completion_id", schemaPath: "#/properties/completion_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate37.errors = [{ instancePath: instancePath + "/completion_id", schemaPath: "#/properties/completion_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern4.test(data3)) {
                                validate37.errors = [{ instancePath: instancePath + "/completion_id", schemaPath: "#/properties/completion_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate37.errors = [{ instancePath: instancePath + "/completion_id", schemaPath: "#/properties/completion_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.result !== void 0) {
                        const _errs10 = errors;
                        if (!validate38(data.result, { instancePath: instancePath + "/result", parentData: data, parentDataProperty: "result", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate38.errors : vErrors.concat(validate38.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs10 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.retention_reservation_ids !== void 0) {
                          let data5 = data.retention_reservation_ids;
                          const _errs11 = errors;
                          if (errors === _errs11) {
                            if (Array.isArray(data5)) {
                              if (data5.length > 65) {
                                validate37.errors = [{ instancePath: instancePath + "/retention_reservation_ids", schemaPath: "#/properties/retention_reservation_ids/maxItems", keyword: "maxItems", params: { limit: 65 }, message: "must NOT have more than 65 items" }];
                                return false;
                              } else {
                                var valid1 = true;
                                const len0 = data5.length;
                                for (let i0 = 0; i0 < len0; i0++) {
                                  let data6 = data5[i0];
                                  const _errs13 = errors;
                                  if (errors === _errs13) {
                                    if (typeof data6 === "string") {
                                      if (func1(data6) > 128) {
                                        validate37.errors = [{ instancePath: instancePath + "/retention_reservation_ids/" + i0, schemaPath: "#/properties/retention_reservation_ids/items/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data6) < 1) {
                                          validate37.errors = [{ instancePath: instancePath + "/retention_reservation_ids/" + i0, schemaPath: "#/properties/retention_reservation_ids/items/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data6)) {
                                            validate37.errors = [{ instancePath: instancePath + "/retention_reservation_ids/" + i0, schemaPath: "#/properties/retention_reservation_ids/items/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate37.errors = [{ instancePath: instancePath + "/retention_reservation_ids/" + i0, schemaPath: "#/properties/retention_reservation_ids/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid1 = _errs13 === errors;
                                  if (!valid1) {
                                    break;
                                  }
                                }
                              }
                            } else {
                              validate37.errors = [{ instancePath: instancePath + "/retention_reservation_ids", schemaPath: "#/properties/retention_reservation_ids/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs11 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.run_id !== void 0) {
                            let data7 = data.run_id;
                            const _errs15 = errors;
                            if (errors === _errs15) {
                              if (typeof data7 === "string") {
                                if (func1(data7) > 128) {
                                  validate37.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data7) < 1) {
                                    validate37.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data7)) {
                                      validate37.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate37.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid0 = _errs15 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.schema_version !== void 0) {
                              let data8 = data.schema_version;
                              const _errs17 = errors;
                              if (typeof data8 !== "string") {
                                validate37.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("1" !== data8) {
                                validate37.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs17 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.scope !== void 0) {
                                let data9 = data.scope;
                                const _errs19 = errors;
                                const _errs20 = errors;
                                if (errors === _errs20) {
                                  if (data9 && typeof data9 == "object" && !Array.isArray(data9)) {
                                    let missing1;
                                    if (data9.tenant_id === void 0 && (missing1 = "tenant_id") || data9.project_id === void 0 && (missing1 = "project_id")) {
                                      validate37.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                      return false;
                                    } else {
                                      const _errs22 = errors;
                                      for (const key1 in data9) {
                                        if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                          validate37.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                          return false;
                                          break;
                                        }
                                      }
                                      if (_errs22 === errors) {
                                        if (data9.project_id !== void 0) {
                                          let data10 = data9.project_id;
                                          const _errs23 = errors;
                                          if (errors === _errs23) {
                                            if (typeof data10 === "string") {
                                              if (func1(data10) > 128) {
                                                validate37.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                return false;
                                              } else {
                                                if (func1(data10) < 1) {
                                                  validate37.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                  return false;
                                                } else {
                                                  if (!pattern4.test(data10)) {
                                                    validate37.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            } else {
                                              validate37.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid3 = _errs23 === errors;
                                        } else {
                                          var valid3 = true;
                                        }
                                        if (valid3) {
                                          if (data9.tenant_id !== void 0) {
                                            let data11 = data9.tenant_id;
                                            const _errs25 = errors;
                                            if (errors === _errs25) {
                                              if (typeof data11 === "string") {
                                                if (func1(data11) > 128) {
                                                  validate37.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                  return false;
                                                } else {
                                                  if (func1(data11) < 1) {
                                                    validate37.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                    return false;
                                                  } else {
                                                    if (!pattern4.test(data11)) {
                                                      validate37.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                      return false;
                                                    }
                                                  }
                                                }
                                              } else {
                                                validate37.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                            }
                                            var valid3 = _errs25 === errors;
                                          } else {
                                            var valid3 = true;
                                          }
                                        }
                                      }
                                    }
                                  } else {
                                    validate37.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate37.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate37.errors = vErrors;
      return errors === 0;
    }
    validate37.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var pattern57 = new RegExp("^[0-9]+\\.[0-9]+\\.[0-9]+$", "u");
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
          if (data.node_id === void 0 && (missing0 = "node_id") || data.activation_id === void 0 && (missing0 = "activation_id") || data.invocation_id === void 0 && (missing0 = "invocation_id") || data.tool === void 0 && (missing0 = "tool") || data.inputs === void 0 && (missing0 = "inputs") || data.timeout_seconds === void 0 && (missing0 = "timeout_seconds")) {
            validate48.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "activation_id" || key0 === "checkpoint" || key0 === "inputs" || key0 === "invocation_id" || key0 === "node_id" || key0 === "side_effects" || key0 === "timeout_seconds" || key0 === "tool")) {
                validate48.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.activation_id !== void 0) {
                let data0 = data.activation_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate48.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate48.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate48.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate48.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.checkpoint !== void 0) {
                  let data1 = data.checkpoint;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  const _errs6 = errors;
                  if (!validate40(data1, { instancePath: instancePath + "/checkpoint", parentData: data, parentDataProperty: "checkpoint", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate40.errors : vErrors.concat(validate40.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs6 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs7 = errors;
                  if (data1 !== null) {
                    const err0 = { instancePath: instancePath + "/checkpoint", schemaPath: "#/properties/checkpoint/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  var _valid0 = _errs7 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err1 = { instancePath: instancePath + "/checkpoint", schemaPath: "#/properties/checkpoint/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                    validate48.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs5;
                    if (vErrors !== null) {
                      if (_errs5) {
                        vErrors.length = _errs5;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.inputs !== void 0) {
                    let data2 = data.inputs;
                    const _errs9 = errors;
                    if (errors === _errs9) {
                      if (Array.isArray(data2)) {
                        if (data2.length > 64) {
                          validate48.errors = [{ instancePath: instancePath + "/inputs", schemaPath: "#/properties/inputs/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                          return false;
                        } else {
                          var valid2 = true;
                          const len0 = data2.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs11 = errors;
                            if (!validate42(data2[i0], { instancePath: instancePath + "/inputs/" + i0, parentData: data2, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate42.errors : vErrors.concat(validate42.errors);
                              errors = vErrors.length;
                            }
                            var valid2 = _errs11 === errors;
                            if (!valid2) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate48.errors = [{ instancePath: instancePath + "/inputs", schemaPath: "#/properties/inputs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.invocation_id !== void 0) {
                      let data4 = data.invocation_id;
                      const _errs12 = errors;
                      if (errors === _errs12) {
                        if (typeof data4 === "string") {
                          if (func1(data4) > 128) {
                            validate48.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data4) < 1) {
                              validate48.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern4.test(data4)) {
                                validate48.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate48.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.node_id !== void 0) {
                        let data5 = data.node_id;
                        const _errs14 = errors;
                        if (errors === _errs14) {
                          if (typeof data5 === "string") {
                            if (func1(data5) > 128) {
                              validate48.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func1(data5) < 1) {
                                validate48.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern4.test(data5)) {
                                  validate48.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate48.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.side_effects !== void 0) {
                          let data6 = data.side_effects;
                          const _errs16 = errors;
                          if (typeof data6 !== "string") {
                            validate48.errors = [{ instancePath: instancePath + "/side_effects", schemaPath: "#/properties/side_effects/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("pure" !== data6) {
                            validate48.errors = [{ instancePath: instancePath + "/side_effects", schemaPath: "#/properties/side_effects/const", keyword: "const", params: { allowedValue: "pure" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.timeout_seconds !== void 0) {
                            let data7 = data.timeout_seconds;
                            const _errs18 = errors;
                            if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                              validate48.errors = [{ instancePath: instancePath + "/timeout_seconds", schemaPath: "#/properties/timeout_seconds/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            if (errors === _errs18) {
                              if (typeof data7 == "number" && isFinite(data7)) {
                                if (data7 > 86400 || isNaN(data7)) {
                                  validate48.errors = [{ instancePath: instancePath + "/timeout_seconds", schemaPath: "#/properties/timeout_seconds/maximum", keyword: "maximum", params: { comparison: "<=", limit: 86400 }, message: "must be <= 86400" }];
                                  return false;
                                } else {
                                  if (data7 < 1 || isNaN(data7)) {
                                    validate48.errors = [{ instancePath: instancePath + "/timeout_seconds", schemaPath: "#/properties/timeout_seconds/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                    return false;
                                  }
                                }
                              }
                            }
                            var valid0 = _errs18 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.tool !== void 0) {
                              let data8 = data.tool;
                              const _errs20 = errors;
                              const _errs21 = errors;
                              if (errors === _errs21) {
                                if (data8 && typeof data8 == "object" && !Array.isArray(data8)) {
                                  let missing1;
                                  if (data8.capability_id === void 0 && (missing1 = "capability_id") || data8.release === void 0 && (missing1 = "release") || data8.image_sha256 === void 0 && (missing1 = "image_sha256") || data8.contract_version === void 0 && (missing1 = "contract_version")) {
                                    validate48.errors = [{ instancePath: instancePath + "/tool", schemaPath: "#/$defs/ToolBinding/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                    return false;
                                  } else {
                                    const _errs23 = errors;
                                    for (const key1 in data8) {
                                      if (!(key1 === "capability_id" || key1 === "contract_version" || key1 === "image_sha256" || key1 === "release")) {
                                        validate48.errors = [{ instancePath: instancePath + "/tool", schemaPath: "#/$defs/ToolBinding/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                        return false;
                                        break;
                                      }
                                    }
                                    if (_errs23 === errors) {
                                      if (data8.capability_id !== void 0) {
                                        let data9 = data8.capability_id;
                                        const _errs24 = errors;
                                        if (errors === _errs24) {
                                          if (typeof data9 === "string") {
                                            if (func1(data9) > 128) {
                                              validate48.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                              return false;
                                            } else {
                                              if (func1(data9) < 1) {
                                                validate48.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                return false;
                                              } else {
                                                if (!pattern4.test(data9)) {
                                                  validate48.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                  return false;
                                                }
                                              }
                                            }
                                          } else {
                                            validate48.errors = [{ instancePath: instancePath + "/tool/capability_id", schemaPath: "#/$defs/ToolBinding/properties/capability_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid4 = _errs24 === errors;
                                      } else {
                                        var valid4 = true;
                                      }
                                      if (valid4) {
                                        if (data8.contract_version !== void 0) {
                                          let data10 = data8.contract_version;
                                          const _errs26 = errors;
                                          if (typeof data10 !== "string") {
                                            validate48.errors = [{ instancePath: instancePath + "/tool/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                          if ("1" !== data10) {
                                            validate48.errors = [{ instancePath: instancePath + "/tool/contract_version", schemaPath: "#/$defs/ToolBinding/properties/contract_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                            return false;
                                          }
                                          var valid4 = _errs26 === errors;
                                        } else {
                                          var valid4 = true;
                                        }
                                        if (valid4) {
                                          if (data8.image_sha256 !== void 0) {
                                            let data11 = data8.image_sha256;
                                            const _errs28 = errors;
                                            if (errors === _errs28) {
                                              if (typeof data11 === "string") {
                                                if (!pattern10.test(data11)) {
                                                  validate48.errors = [{ instancePath: instancePath + "/tool/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                                  return false;
                                                }
                                              } else {
                                                validate48.errors = [{ instancePath: instancePath + "/tool/image_sha256", schemaPath: "#/$defs/ToolBinding/properties/image_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                            }
                                            var valid4 = _errs28 === errors;
                                          } else {
                                            var valid4 = true;
                                          }
                                          if (valid4) {
                                            if (data8.release !== void 0) {
                                              let data12 = data8.release;
                                              const _errs30 = errors;
                                              if (errors === _errs30) {
                                                if (typeof data12 === "string") {
                                                  if (!pattern57.test(data12)) {
                                                    validate48.errors = [{ instancePath: instancePath + "/tool/release", schemaPath: "#/$defs/ToolBinding/properties/release/pattern", keyword: "pattern", params: { pattern: "^[0-9]+\\.[0-9]+\\.[0-9]+$" }, message: 'must match pattern "^[0-9]+\\.[0-9]+\\.[0-9]+$"' }];
                                                    return false;
                                                  }
                                                } else {
                                                  validate48.errors = [{ instancePath: instancePath + "/tool/release", schemaPath: "#/$defs/ToolBinding/properties/release/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                  return false;
                                                }
                                              }
                                              var valid4 = _errs30 === errors;
                                            } else {
                                              var valid4 = true;
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                } else {
                                  validate48.errors = [{ instancePath: instancePath + "/tool", schemaPath: "#/$defs/ToolBinding/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs20 === errors;
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
          validate48.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate48.errors = vErrors;
      return errors === 0;
    }
    validate48.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate36(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.authority === void 0 && (missing0 = "authority") || data.worker_id === void 0 && (missing0 = "worker_id") || data.invocation === void 0 && (missing0 = "invocation") || data.completion === void 0 && (missing0 = "completion")) {
            validate36.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "authority" || key0 === "completion" || key0 === "invocation" || key0 === "wire_version" || key0 === "worker_id")) {
                validate36.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.authority !== void 0) {
                let data0 = data.authority;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate36.errors = [{ instancePath: instancePath + "/authority", schemaPath: "#/properties/authority/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("accepted_execution" !== data0) {
                  validate36.errors = [{ instancePath: instancePath + "/authority", schemaPath: "#/properties/authority/const", keyword: "const", params: { allowedValue: "accepted_execution" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.completion !== void 0) {
                  const _errs4 = errors;
                  if (!validate37(data.completion, { instancePath: instancePath + "/completion", parentData: data, parentDataProperty: "completion", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate37.errors : vErrors.concat(validate37.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.invocation !== void 0) {
                    const _errs5 = errors;
                    if (!validate48(data.invocation, { instancePath: instancePath + "/invocation", parentData: data, parentDataProperty: "invocation", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.wire_version !== void 0) {
                      let data3 = data.wire_version;
                      const _errs6 = errors;
                      if (typeof data3 !== "string") {
                        validate36.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data3) {
                        validate36.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs6 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.worker_id !== void 0) {
                        let data4 = data.worker_id;
                        const _errs8 = errors;
                        if (errors === _errs8) {
                          if (typeof data4 === "string") {
                            if (func1(data4) > 128) {
                              validate36.errors = [{ instancePath: instancePath + "/worker_id", schemaPath: "#/properties/worker_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func1(data4) < 1) {
                                validate36.errors = [{ instancePath: instancePath + "/worker_id", schemaPath: "#/properties/worker_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern4.test(data4)) {
                                  validate36.errors = [{ instancePath: instancePath + "/worker_id", schemaPath: "#/properties/worker_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate36.errors = [{ instancePath: instancePath + "/worker_id", schemaPath: "#/properties/worker_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
  }
});
export default require_reviewed_validators();
