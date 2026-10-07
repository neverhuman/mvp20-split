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
    exports.specimen_request = validate20;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.experiment_id === void 0 && (missing0 = "experiment_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate21.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment_id" || key0 === "revision" || key0 === "scope")) {
                validate21.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment_id !== void 0) {
                let data0 = data.experiment_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate21.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate21.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate21.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate21.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
    var pattern7 = new RegExp("^[0-9a-f]{64}$", "u");
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.experiment === void 0 && (missing0 = "experiment")) {
            validate20.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment" || key0 === "limit" || key0 === "position" || key0 === "wire_version")) {
                validate20.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment !== void 0) {
                const _errs2 = errors;
                if (!validate21(data.experiment, { instancePath: instancePath + "/experiment", parentData: data, parentDataProperty: "experiment", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.limit !== void 0) {
                  let data1 = data.limit;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate20.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 16 || isNaN(data1)) {
                        validate20.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate20.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                  if (data.position !== void 0) {
                    let data2 = data.position;
                    const _errs5 = errors;
                    const _errs6 = errors;
                    let valid1 = false;
                    const _errs7 = errors;
                    const _errs8 = errors;
                    if (errors === _errs8) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.query_sha256 === void 0 && (missing1 = "query_sha256") || data2.offset === void 0 && (missing1 = "offset")) {
                          const err0 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        } else {
                          const _errs10 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "offset" || key1 === "query_sha256")) {
                              const err1 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                            if (data2.offset !== void 0) {
                              let data3 = data2.offset;
                              const _errs11 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                const err2 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              }
                              if (errors === _errs11) {
                                if (typeof data3 == "number" && isFinite(data3)) {
                                  if (data3 > 4096 || isNaN(data3)) {
                                    const err3 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                    if (vErrors === null) {
                                      vErrors = [err3];
                                    } else {
                                      vErrors.push(err3);
                                    }
                                    errors++;
                                  } else {
                                    if (data3 < 0 || isNaN(data3)) {
                                      const err4 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                              var valid3 = _errs11 === errors;
                            } else {
                              var valid3 = true;
                            }
                            if (valid3) {
                              if (data2.query_sha256 !== void 0) {
                                let data4 = data2.query_sha256;
                                const _errs13 = errors;
                                if (errors === _errs13) {
                                  if (typeof data4 === "string") {
                                    if (!pattern7.test(data4)) {
                                      const err5 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                    }
                                  } else {
                                    const err6 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err6];
                                    } else {
                                      vErrors.push(err6);
                                    }
                                    errors++;
                                  }
                                }
                                var valid3 = _errs13 === errors;
                              } else {
                                var valid3 = true;
                              }
                            }
                          }
                        }
                      } else {
                        const err7 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs7 === errors;
                    valid1 = valid1 || _valid0;
                    const _errs15 = errors;
                    if (data2 !== null) {
                      const err8 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err8];
                      } else {
                        vErrors.push(err8);
                      }
                      errors++;
                    }
                    var _valid0 = _errs15 === errors;
                    valid1 = valid1 || _valid0;
                    if (!valid1) {
                      const err9 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err9];
                      } else {
                        vErrors.push(err9);
                      }
                      errors++;
                      validate20.errors = vErrors;
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
                    if (data.wire_version !== void 0) {
                      let data5 = data.wire_version;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        validate20.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data5) {
                        validate20.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs17 === errors;
                    } else {
                      var valid0 = true;
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
    exports.specimen_page = validate23;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.experiment_id === void 0 && (missing0 = "experiment_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate25.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment_id" || key0 === "revision" || key0 === "scope")) {
                validate25.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment_id !== void 0) {
                let data0 = data.experiment_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate25.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate25.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate25.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate25.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate25.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate25.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate25.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate25.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate25.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate25.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate25.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
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
                                      validate25.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate25.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
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
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                            }
                          }
                        }
                      } else {
                        validate25.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.experiment === void 0 && (missing0 = "experiment")) {
            validate24.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment" || key0 === "limit" || key0 === "position" || key0 === "wire_version")) {
                validate24.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment !== void 0) {
                const _errs2 = errors;
                if (!validate25(data.experiment, { instancePath: instancePath + "/experiment", parentData: data, parentDataProperty: "experiment", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.limit !== void 0) {
                  let data1 = data.limit;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate24.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 16 || isNaN(data1)) {
                        validate24.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate24.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                  if (data.position !== void 0) {
                    let data2 = data.position;
                    const _errs5 = errors;
                    const _errs6 = errors;
                    let valid1 = false;
                    const _errs7 = errors;
                    const _errs8 = errors;
                    if (errors === _errs8) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.query_sha256 === void 0 && (missing1 = "query_sha256") || data2.offset === void 0 && (missing1 = "offset")) {
                          const err0 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        } else {
                          const _errs10 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "offset" || key1 === "query_sha256")) {
                              const err1 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                            if (data2.offset !== void 0) {
                              let data3 = data2.offset;
                              const _errs11 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                const err2 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              }
                              if (errors === _errs11) {
                                if (typeof data3 == "number" && isFinite(data3)) {
                                  if (data3 > 4096 || isNaN(data3)) {
                                    const err3 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                    if (vErrors === null) {
                                      vErrors = [err3];
                                    } else {
                                      vErrors.push(err3);
                                    }
                                    errors++;
                                  } else {
                                    if (data3 < 0 || isNaN(data3)) {
                                      const err4 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                              var valid3 = _errs11 === errors;
                            } else {
                              var valid3 = true;
                            }
                            if (valid3) {
                              if (data2.query_sha256 !== void 0) {
                                let data4 = data2.query_sha256;
                                const _errs13 = errors;
                                if (errors === _errs13) {
                                  if (typeof data4 === "string") {
                                    if (!pattern7.test(data4)) {
                                      const err5 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                    }
                                  } else {
                                    const err6 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err6];
                                    } else {
                                      vErrors.push(err6);
                                    }
                                    errors++;
                                  }
                                }
                                var valid3 = _errs13 === errors;
                              } else {
                                var valid3 = true;
                              }
                            }
                          }
                        }
                      } else {
                        const err7 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs7 === errors;
                    valid1 = valid1 || _valid0;
                    const _errs15 = errors;
                    if (data2 !== null) {
                      const err8 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err8];
                      } else {
                        vErrors.push(err8);
                      }
                      errors++;
                    }
                    var _valid0 = _errs15 === errors;
                    valid1 = valid1 || _valid0;
                    if (!valid1) {
                      const err9 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err9];
                      } else {
                        vErrors.push(err9);
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
                    if (data.wire_version !== void 0) {
                      let data5 = data.wire_version;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        validate24.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data5) {
                        validate24.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs17 === errors;
                    } else {
                      var valid0 = true;
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
    function validate30(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
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
          if (data.scope === void 0 && (missing0 = "scope") || data.candidate_id === void 0 && (missing0 = "candidate_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate30.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate_id" || key0 === "revision" || key0 === "scope")) {
                validate30.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate30.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate30.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate30.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate30.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate30.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate30.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate30.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate30.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate30.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate30.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate30.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate30.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate30.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate30.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate30.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate30.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate30.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate30.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate30.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate30.errors = vErrors;
      return errors === 0;
    }
    validate30.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate32(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate32.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.material_state_id === void 0 && (missing0 = "material_state_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate32.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "material_state_id" || key0 === "revision" || key0 === "scope")) {
                validate32.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.material_state_id !== void 0) {
                let data0 = data.material_state_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate32.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate32.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate32.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate32.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate32.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate32.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate32.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate32.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate32.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate32.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate32.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate32.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate32.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate32.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate32.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate32.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate32.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate32.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate32.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate32.errors = vErrors;
      return errors === 0;
    }
    validate32.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.reference === void 0 && (missing0 = "reference") || data.candidate === void 0 && (missing0 = "candidate") || data.supersedes === void 0 && (missing0 = "supersedes") || data.preparation_count === void 0 && (missing0 = "preparation_count") || data.feature_count === void 0 && (missing0 = "feature_count")) {
            validate29.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate" || key0 === "feature_count" || key0 === "preparation_count" || key0 === "reference" || key0 === "supersedes")) {
                validate29.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.candidate !== void 0) {
                const _errs2 = errors;
                if (!validate30(data.candidate, { instancePath: instancePath + "/candidate", parentData: data, parentDataProperty: "candidate", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate30.errors : vErrors.concat(validate30.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.feature_count !== void 0) {
                  let data1 = data.feature_count;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate29.errors = [{ instancePath: instancePath + "/feature_count", schemaPath: "#/properties/feature_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 128 || isNaN(data1)) {
                        validate29.errors = [{ instancePath: instancePath + "/feature_count", schemaPath: "#/properties/feature_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 128 }, message: "must be <= 128" }];
                        return false;
                      } else {
                        if (data1 < 0 || isNaN(data1)) {
                          validate29.errors = [{ instancePath: instancePath + "/feature_count", schemaPath: "#/properties/feature_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                  if (data.preparation_count !== void 0) {
                    let data2 = data.preparation_count;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate29.errors = [{ instancePath: instancePath + "/preparation_count", schemaPath: "#/properties/preparation_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 256 || isNaN(data2)) {
                          validate29.errors = [{ instancePath: instancePath + "/preparation_count", schemaPath: "#/properties/preparation_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 256 }, message: "must be <= 256" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate29.errors = [{ instancePath: instancePath + "/preparation_count", schemaPath: "#/properties/preparation_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                    if (data.reference !== void 0) {
                      const _errs7 = errors;
                      if (!validate32(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate32.errors : vErrors.concat(validate32.errors);
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
                        if (!validate32(data4, { instancePath: instancePath + "/supersedes", parentData: data, parentDataProperty: "supersedes", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate32.errors : vErrors.concat(validate32.errors);
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
                          validate29.errors = vErrors;
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
          validate29.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate29.errors = vErrors;
      return errors === 0;
    }
    validate29.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var pattern21 = new RegExp("^[^\\s/]+/[^\\s/]+$", "u");
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate38.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate38.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate38.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate38.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate38.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate38.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate38.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate38.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern21.test(data1)) {
                            validate38.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate38.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate38.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate38.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate38.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate38.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate38.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate38.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    if (!pattern7.test(data4)) {
                                      validate38.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate38.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate38.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate38.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate38.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate38.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate38.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate38.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate38.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
                                          validate38.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate38.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        validate38.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate38.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
                                            validate38.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate38.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate38.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            if (!pattern7.test(data9)) {
                              validate38.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate38.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate38.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate38.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate38.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate38.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate38.errors = vErrors;
      return errors === 0;
    }
    validate38.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate41(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate41.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.sample_id === void 0 && (missing0 = "sample_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate41.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "revision" || key0 === "sample_id" || key0 === "scope")) {
                validate41.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.revision !== void 0) {
                let data0 = data.revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate41.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate41.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 1 || isNaN(data0)) {
                        validate41.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                if (data.sample_id !== void 0) {
                  let data1 = data.sample_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate41.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate41.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate41.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate41.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
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
                          validate41.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate41.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate41.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate41.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate41.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate41.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate41.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate41.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate41.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate41.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate41.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate41.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate41.errors = vErrors;
      return errors === 0;
    }
    validate41.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.reference === void 0 && (missing0 = "reference") || data.candidate === void 0 && (missing0 = "candidate") || data.material_state === void 0 && (missing0 = "material_state") || data.identity_evidence === void 0 && (missing0 = "identity_evidence") || data.supersedes === void 0 && (missing0 = "supersedes")) {
            validate36.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate" || key0 === "identity_evidence" || key0 === "material_state" || key0 === "reference" || key0 === "supersedes" || key0 === "wire_version")) {
                validate36.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.candidate !== void 0) {
                const _errs2 = errors;
                if (!validate30(data.candidate, { instancePath: instancePath + "/candidate", parentData: data, parentDataProperty: "candidate", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate30.errors : vErrors.concat(validate30.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.identity_evidence !== void 0) {
                  const _errs3 = errors;
                  if (!validate38(data.identity_evidence, { instancePath: instancePath + "/identity_evidence", parentData: data, parentDataProperty: "identity_evidence", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate38.errors : vErrors.concat(validate38.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.material_state !== void 0) {
                    let data2 = data.material_state;
                    const _errs4 = errors;
                    const _errs5 = errors;
                    let valid1 = false;
                    const _errs6 = errors;
                    if (!validate32(data2, { instancePath: instancePath + "/material_state", parentData: data, parentDataProperty: "material_state", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate32.errors : vErrors.concat(validate32.errors);
                      errors = vErrors.length;
                    }
                    var _valid0 = _errs6 === errors;
                    valid1 = valid1 || _valid0;
                    const _errs7 = errors;
                    if (data2 !== null) {
                      const err0 = { instancePath: instancePath + "/material_state", schemaPath: "#/properties/material_state/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                      const err1 = { instancePath: instancePath + "/material_state", schemaPath: "#/properties/material_state/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err1];
                      } else {
                        vErrors.push(err1);
                      }
                      errors++;
                      validate36.errors = vErrors;
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
                    if (data.reference !== void 0) {
                      const _errs9 = errors;
                      if (!validate41(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate41.errors : vErrors.concat(validate41.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs9 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.supersedes !== void 0) {
                        let data4 = data.supersedes;
                        const _errs10 = errors;
                        const _errs11 = errors;
                        let valid2 = false;
                        const _errs12 = errors;
                        if (!validate41(data4, { instancePath: instancePath + "/supersedes", parentData: data, parentDataProperty: "supersedes", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate41.errors : vErrors.concat(validate41.errors);
                          errors = vErrors.length;
                        }
                        var _valid1 = _errs12 === errors;
                        valid2 = valid2 || _valid1;
                        const _errs13 = errors;
                        if (data4 !== null) {
                          const err2 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err2];
                          } else {
                            vErrors.push(err2);
                          }
                          errors++;
                        }
                        var _valid1 = _errs13 === errors;
                        valid2 = valid2 || _valid1;
                        if (!valid2) {
                          const err3 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err3];
                          } else {
                            vErrors.push(err3);
                          }
                          errors++;
                          validate36.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs11;
                          if (vErrors !== null) {
                            if (_errs11) {
                              vErrors.length = _errs11;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs10 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.wire_version !== void 0) {
                          let data5 = data.wire_version;
                          const _errs15 = errors;
                          if (typeof data5 !== "string") {
                            validate36.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("1" !== data5) {
                            validate36.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
          if (data.sample === void 0 && (missing0 = "sample") || data.material === void 0 && (missing0 = "material")) {
            validate28.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "material" || key0 === "sample")) {
                validate28.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.material !== void 0) {
                let data0 = data.material;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate29(data0, { instancePath: instancePath + "/material", parentData: data, parentDataProperty: "material", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate29.errors : vErrors.concat(validate29.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/material", schemaPath: "#/properties/material/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err1 = { instancePath: instancePath + "/material", schemaPath: "#/properties/material/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate28.errors = vErrors;
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
                if (data.sample !== void 0) {
                  const _errs7 = errors;
                  if (!validate36(data.sample, { instancePath: instancePath + "/sample", parentData: data, parentDataProperty: "sample", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate36.errors : vErrors.concat(validate36.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs7 === errors;
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.request === void 0 && (missing0 = "request") || data.query_sha256 === void 0 && (missing0 = "query_sha256") || data.total === void 0 && (missing0 = "total") || data.rows === void 0 && (missing0 = "rows") || data.next_position === void 0 && (missing0 = "next_position")) {
            validate23.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "next_position" || key0 === "query_sha256" || key0 === "request" || key0 === "rows" || key0 === "total" || key0 === "wire_version")) {
                validate23.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.next_position !== void 0) {
                let data0 = data.next_position;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                const _errs5 = errors;
                if (errors === _errs5) {
                  if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                    let missing1;
                    if (data0.query_sha256 === void 0 && (missing1 = "query_sha256") || data0.offset === void 0 && (missing1 = "offset")) {
                      const err0 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/ResearchViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    } else {
                      const _errs7 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "offset" || key1 === "query_sha256")) {
                          const err1 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/ResearchViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                        if (data0.offset !== void 0) {
                          let data1 = data0.offset;
                          const _errs8 = errors;
                          if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                            const err2 = { instancePath: instancePath + "/next_position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                            if (vErrors === null) {
                              vErrors = [err2];
                            } else {
                              vErrors.push(err2);
                            }
                            errors++;
                          }
                          if (errors === _errs8) {
                            if (typeof data1 == "number" && isFinite(data1)) {
                              if (data1 > 4096 || isNaN(data1)) {
                                const err3 = { instancePath: instancePath + "/next_position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                if (vErrors === null) {
                                  vErrors = [err3];
                                } else {
                                  vErrors.push(err3);
                                }
                                errors++;
                              } else {
                                if (data1 < 0 || isNaN(data1)) {
                                  const err4 = { instancePath: instancePath + "/next_position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                          var valid3 = _errs8 === errors;
                        } else {
                          var valid3 = true;
                        }
                        if (valid3) {
                          if (data0.query_sha256 !== void 0) {
                            let data2 = data0.query_sha256;
                            const _errs10 = errors;
                            if (errors === _errs10) {
                              if (typeof data2 === "string") {
                                if (!pattern7.test(data2)) {
                                  const err5 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                  if (vErrors === null) {
                                    vErrors = [err5];
                                  } else {
                                    vErrors.push(err5);
                                  }
                                  errors++;
                                }
                              } else {
                                const err6 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err6];
                                } else {
                                  vErrors.push(err6);
                                }
                                errors++;
                              }
                            }
                            var valid3 = _errs10 === errors;
                          } else {
                            var valid3 = true;
                          }
                        }
                      }
                    }
                  } else {
                    const err7 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/ResearchViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                    if (vErrors === null) {
                      vErrors = [err7];
                    } else {
                      vErrors.push(err7);
                    }
                    errors++;
                  }
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs12 = errors;
                if (data0 !== null) {
                  const err8 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err8];
                  } else {
                    vErrors.push(err8);
                  }
                  errors++;
                }
                var _valid0 = _errs12 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
                  const err9 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err9];
                  } else {
                    vErrors.push(err9);
                  }
                  errors++;
                  validate23.errors = vErrors;
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
                if (data.query_sha256 !== void 0) {
                  let data3 = data.query_sha256;
                  const _errs14 = errors;
                  if (errors === _errs14) {
                    if (typeof data3 === "string") {
                      if (!pattern7.test(data3)) {
                        validate23.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate23.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs14 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.request !== void 0) {
                    const _errs16 = errors;
                    if (!validate24(data.request, { instancePath: instancePath + "/request", parentData: data, parentDataProperty: "request", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate24.errors : vErrors.concat(validate24.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs16 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.rows !== void 0) {
                      let data5 = data.rows;
                      const _errs17 = errors;
                      if (errors === _errs17) {
                        if (Array.isArray(data5)) {
                          if (data5.length > 16) {
                            validate23.errors = [{ instancePath: instancePath + "/rows", schemaPath: "#/properties/rows/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                            return false;
                          } else {
                            var valid4 = true;
                            const len0 = data5.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs19 = errors;
                              if (!validate28(data5[i0], { instancePath: instancePath + "/rows/" + i0, parentData: data5, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate28.errors : vErrors.concat(validate28.errors);
                                errors = vErrors.length;
                              }
                              var valid4 = _errs19 === errors;
                              if (!valid4) {
                                break;
                              }
                            }
                          }
                        } else {
                          validate23.errors = [{ instancePath: instancePath + "/rows", schemaPath: "#/properties/rows/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs17 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.total !== void 0) {
                        let data7 = data.total;
                        const _errs20 = errors;
                        if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                          validate23.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                          return false;
                        }
                        if (errors === _errs20) {
                          if (typeof data7 == "number" && isFinite(data7)) {
                            if (data7 > 256 || isNaN(data7)) {
                              validate23.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 256 }, message: "must be <= 256" }];
                              return false;
                            } else {
                              if (data7 < 1 || isNaN(data7)) {
                                validate23.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                        if (data.wire_version !== void 0) {
                          let data8 = data.wire_version;
                          const _errs22 = errors;
                          if (typeof data8 !== "string") {
                            validate23.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("1" !== data8) {
                            validate23.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
        } else {
          validate23.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate23.errors = vErrors;
      return errors === 0;
    }
    validate23.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.property_request = validate46;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.experiment_id === void 0 && (missing0 = "experiment_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate47.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment_id" || key0 === "revision" || key0 === "scope")) {
                validate47.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment_id !== void 0) {
                let data0 = data.experiment_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate47.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate47.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate47.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate47.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate47.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate47.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate47.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate47.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate47.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate47.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
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
                                      validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate47.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
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
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                            }
                          }
                        }
                      } else {
                        validate47.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate47.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate47.errors = vErrors;
      return errors === 0;
    }
    validate47.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.observation_id === void 0 && (missing0 = "observation_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate49.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "observation_id" || key0 === "revision" || key0 === "scope")) {
                validate49.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.observation_id !== void 0) {
                let data0 = data.observation_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate49.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate49.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate49.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate49.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate49.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate49.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate49.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
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
                                      validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
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
                                var valid2 = _errs12 === errors;
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
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.experiment === void 0 && (missing0 = "experiment") || data.observations === void 0 && (missing0 = "observations")) {
            validate46.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment" || key0 === "limit" || key0 === "observations" || key0 === "position" || key0 === "wire_version")) {
                validate46.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment !== void 0) {
                const _errs2 = errors;
                if (!validate47(data.experiment, { instancePath: instancePath + "/experiment", parentData: data, parentDataProperty: "experiment", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate47.errors : vErrors.concat(validate47.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.limit !== void 0) {
                  let data1 = data.limit;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate46.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 16 || isNaN(data1)) {
                        validate46.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate46.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                  if (data.observations !== void 0) {
                    let data2 = data.observations;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (Array.isArray(data2)) {
                        if (data2.length > 128) {
                          validate46.errors = [{ instancePath: instancePath + "/observations", schemaPath: "#/properties/observations/maxItems", keyword: "maxItems", params: { limit: 128 }, message: "must NOT have more than 128 items" }];
                          return false;
                        } else {
                          if (data2.length < 1) {
                            validate46.errors = [{ instancePath: instancePath + "/observations", schemaPath: "#/properties/observations/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                            return false;
                          } else {
                            var valid1 = true;
                            const len0 = data2.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs7 = errors;
                              if (!validate49(data2[i0], { instancePath: instancePath + "/observations/" + i0, parentData: data2, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate49.errors : vErrors.concat(validate49.errors);
                                errors = vErrors.length;
                              }
                              var valid1 = _errs7 === errors;
                              if (!valid1) {
                                break;
                              }
                            }
                          }
                        }
                      } else {
                        validate46.errors = [{ instancePath: instancePath + "/observations", schemaPath: "#/properties/observations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.position !== void 0) {
                      let data4 = data.position;
                      const _errs8 = errors;
                      const _errs9 = errors;
                      let valid2 = false;
                      const _errs10 = errors;
                      const _errs11 = errors;
                      if (errors === _errs11) {
                        if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                          let missing1;
                          if (data4.query_sha256 === void 0 && (missing1 = "query_sha256") || data4.offset === void 0 && (missing1 = "offset")) {
                            const err0 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                            if (vErrors === null) {
                              vErrors = [err0];
                            } else {
                              vErrors.push(err0);
                            }
                            errors++;
                          } else {
                            const _errs13 = errors;
                            for (const key1 in data4) {
                              if (!(key1 === "offset" || key1 === "query_sha256")) {
                                const err1 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                if (vErrors === null) {
                                  vErrors = [err1];
                                } else {
                                  vErrors.push(err1);
                                }
                                errors++;
                                break;
                              }
                            }
                            if (_errs13 === errors) {
                              if (data4.offset !== void 0) {
                                let data5 = data4.offset;
                                const _errs14 = errors;
                                if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                  const err2 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                  if (vErrors === null) {
                                    vErrors = [err2];
                                  } else {
                                    vErrors.push(err2);
                                  }
                                  errors++;
                                }
                                if (errors === _errs14) {
                                  if (typeof data5 == "number" && isFinite(data5)) {
                                    if (data5 > 4096 || isNaN(data5)) {
                                      const err3 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                      if (vErrors === null) {
                                        vErrors = [err3];
                                      } else {
                                        vErrors.push(err3);
                                      }
                                      errors++;
                                    } else {
                                      if (data5 < 0 || isNaN(data5)) {
                                        const err4 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                                var valid4 = _errs14 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data4.query_sha256 !== void 0) {
                                  let data6 = data4.query_sha256;
                                  const _errs16 = errors;
                                  if (errors === _errs16) {
                                    if (typeof data6 === "string") {
                                      if (!pattern7.test(data6)) {
                                        const err5 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                        if (vErrors === null) {
                                          vErrors = [err5];
                                        } else {
                                          vErrors.push(err5);
                                        }
                                        errors++;
                                      }
                                    } else {
                                      const err6 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err6];
                                      } else {
                                        vErrors.push(err6);
                                      }
                                      errors++;
                                    }
                                  }
                                  var valid4 = _errs16 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          const err7 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                          if (vErrors === null) {
                            vErrors = [err7];
                          } else {
                            vErrors.push(err7);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs10 === errors;
                      valid2 = valid2 || _valid0;
                      const _errs18 = errors;
                      if (data4 !== null) {
                        const err8 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                      }
                      var _valid0 = _errs18 === errors;
                      valid2 = valid2 || _valid0;
                      if (!valid2) {
                        const err9 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err9];
                        } else {
                          vErrors.push(err9);
                        }
                        errors++;
                        validate46.errors = vErrors;
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
                      if (data.wire_version !== void 0) {
                        let data7 = data.wire_version;
                        const _errs20 = errors;
                        if (typeof data7 !== "string") {
                          validate46.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data7) {
                          validate46.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
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
        } else {
          validate46.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate46.errors = vErrors;
      return errors === 0;
    }
    validate46.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.property_page = validate51;
    var schema59 = { "$defs": { "ArtifactRef": { "additionalProperties": false, "properties": { "artifact_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Artifact Id", "type": "string" }, "media_type": { "maxLength": 128, "minLength": 3, "pattern": "^[^\\s/]+/[^\\s/]+$", "title": "Media Type", "type": "string" }, "schema_ref": { "$ref": "#/$defs/SchemaRef" }, "scope": { "$ref": "#/$defs/Scope" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "size_bytes": { "maximum": 9007199254740991, "minimum": 0, "title": "Size Bytes", "type": "integer" } }, "required": ["artifact_id", "scope", "sha256", "media_type", "schema_ref", "size_bytes"], "title": "ArtifactRef", "type": "object" }, "CategoricalMeasurement": { "additionalProperties": false, "properties": { "kind": { "const": "categorical", "title": "Kind", "type": "string" }, "label": { "maxLength": 256, "minLength": 1, "title": "Label", "type": "string" } }, "required": ["kind", "label"], "title": "CategoricalMeasurement", "type": "object" }, "CensorBound": { "additionalProperties": false, "properties": { "inclusive": { "title": "Inclusive", "type": "boolean" }, "quantity": { "$ref": "#/$defs/MeasurementQuantity" } }, "required": ["quantity", "inclusive"], "title": "CensorBound", "type": "object" }, "CensoredMeasurement": { "additionalProperties": false, "properties": { "kind": { "const": "censored", "title": "Kind", "type": "string" }, "lower": { "anyOf": [{ "$ref": "#/$defs/CensorBound" }, { "type": "null" }] }, "upper": { "anyOf": [{ "$ref": "#/$defs/CensorBound" }, { "type": "null" }] } }, "required": ["kind", "lower", "upper"], "title": "CensoredMeasurement", "type": "object" }, "ExperimentExpectation": { "additionalProperties": false, "properties": { "expectation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Expectation Id", "type": "string" }, "readout": { "$ref": "#/$defs/ExperimentReadout" }, "replicate": { "$ref": "#/$defs/ExperimentReplicate" }, "sample": { "$ref": "#/$defs/SampleRevisionRef" } }, "required": ["expectation_id", "sample", "readout", "replicate"], "title": "ExperimentExpectation", "type": "object" }, "ExperimentProtocol": { "additionalProperties": false, "properties": { "applicability": { "$ref": "#/$defs/ArtifactRef" }, "method": { "$ref": "#/$defs/SchemaRef" }, "source": { "$ref": "#/$defs/ArtifactRef" } }, "required": ["method", "applicability", "source"], "title": "ExperimentProtocol", "type": "object" }, "ExperimentReadout": { "additionalProperties": false, "properties": { "criterion_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Criterion Id", "type": "string" }, "kind": { "enum": ["numeric", "categorical", "series"], "title": "Kind", "type": "string" }, "unit": { "anyOf": [{ "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "type": "string" }, { "type": "null" }], "title": "Unit" }, "x_unit": { "anyOf": [{ "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "type": "string" }, { "type": "null" }], "title": "X Unit" } }, "required": ["criterion_id", "kind", "unit", "x_unit"], "title": "ExperimentReadout", "type": "object" }, "ExperimentReplicate": { "additionalProperties": false, "properties": { "replicate_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Replicate Id", "type": "string" }, "role": { "enum": ["sample", "positive_control", "negative_control", "blank"], "title": "Role", "type": "string" } }, "required": ["replicate_id", "role"], "title": "ExperimentReplicate", "type": "object" }, "ExperimentRevisionRef": { "additionalProperties": false, "properties": { "experiment_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Experiment Id", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "experiment_id", "revision"], "title": "ExperimentRevisionRef", "type": "object" }, "MaterialStateRevisionRef": { "additionalProperties": false, "properties": { "material_state_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Material State Id", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "material_state_id", "revision"], "title": "MaterialStateRevisionRef", "type": "object" }, "MeasurementInterval": { "additionalProperties": false, "properties": { "description": { "maxLength": 512, "minLength": 1, "title": "Description", "type": "string" }, "lower": { "$ref": "#/$defs/MeasurementQuantity" }, "upper": { "$ref": "#/$defs/MeasurementQuantity" } }, "required": ["lower", "upper", "description"], "title": "MeasurementInterval", "type": "object" }, "MeasurementQuantity": { "additionalProperties": false, "properties": { "unit": { "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "title": "Unit", "type": "string" }, "value": { "maxLength": 128, "minLength": 1, "pattern": "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])", "title": "Value", "type": "string" } }, "required": ["value", "unit"], "title": "MeasurementQuantity", "type": "object" }, "MissingMeasurement": { "additionalProperties": false, "properties": { "kind": { "const": "missing", "title": "Kind", "type": "string" }, "reason": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Reason", "type": "string" } }, "required": ["kind", "reason"], "title": "MissingMeasurement", "type": "object" }, "NumericMeasurement": { "additionalProperties": false, "properties": { "kind": { "const": "numeric", "title": "Kind", "type": "string" }, "quantity": { "$ref": "#/$defs/MeasurementQuantity" }, "uncertainty": { "anyOf": [{ "$ref": "#/$defs/MeasurementInterval" }, { "type": "null" }] } }, "required": ["kind", "quantity", "uncertainty"], "title": "NumericMeasurement", "type": "object" }, "ObservationBindingRecord": { "additionalProperties": false, "properties": { "measurement": { "$ref": "#/$defs/ObservationMethod" }, "role": { "anyOf": [{ "enum": ["sample", "positive_control", "negative_control", "blank"], "type": "string" }, { "type": "null" }], "title": "Role" }, "specimen": { "$ref": "#/$defs/ObservationSpecimen" }, "target": { "$ref": "#/$defs/ObservationTarget" } }, "required": ["target", "specimen", "measurement", "role"], "title": "ObservationBindingRecord", "type": "object" }, "ObservationMethod": { "additionalProperties": false, "properties": { "context": { "anyOf": [{ "$ref": "#/$defs/ArtifactRef" }, { "type": "null" }] }, "method": { "anyOf": [{ "$ref": "#/$defs/SchemaRef" }, { "type": "null" }] } }, "required": ["method", "context"], "title": "ObservationMethod", "type": "object" }, "ObservationQuality": { "additionalProperties": false, "properties": { "controls": { "enum": ["passed", "failed", "unknown"], "title": "Controls", "type": "string" }, "flags": { "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 64, "title": "Flags", "type": "array" } }, "required": ["controls", "flags"], "title": "ObservationQuality", "type": "object" }, "ObservationRevisionRef": { "additionalProperties": false, "properties": { "observation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Observation Id", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "observation_id", "revision"], "title": "ObservationRevisionRef", "type": "object" }, "ObservationSpecimen": { "additionalProperties": false, "properties": { "material_state": { "anyOf": [{ "$ref": "#/$defs/MaterialStateRevisionRef" }, { "type": "null" }] }, "sample": { "anyOf": [{ "$ref": "#/$defs/SampleRevisionRef" }, { "type": "null" }] } }, "required": ["sample", "material_state"], "title": "ObservationSpecimen", "type": "object" }, "ObservationTarget": { "additionalProperties": false, "properties": { "expectation_id": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Expectation Id" }, "experiment": { "anyOf": [{ "$ref": "#/$defs/ExperimentRevisionRef" }, { "type": "null" }] }, "replicate_id": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Replicate Id" } }, "required": ["experiment", "expectation_id", "replicate_id"], "title": "ObservationTarget", "type": "object" }, "PropertyViewRequest": { "additionalProperties": false, "properties": { "experiment": { "$ref": "#/$defs/ExperimentRevisionRef" }, "limit": { "default": 16, "maximum": 16, "minimum": 1, "title": "Limit", "type": "integer" }, "observations": { "items": { "$ref": "#/$defs/ObservationRevisionRef" }, "maxItems": 128, "minItems": 1, "title": "Observations", "type": "array" }, "position": { "anyOf": [{ "$ref": "#/$defs/ResearchViewPosition" }, { "type": "null" }], "default": null }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" } }, "required": ["wire_version", "experiment", "observations"], "title": "PropertyViewRequest", "type": "object" }, "PropertyViewRow": { "additionalProperties": false, "properties": { "binding": { "$ref": "#/$defs/ObservationBindingRecord" }, "context_link": { "enum": ["declared_expectation", "unbound", "different_experiment", "unknown_expectation"], "title": "Context Link", "type": "string" }, "expectation": { "anyOf": [{ "$ref": "#/$defs/ExperimentExpectation" }, { "type": "null" }] }, "quality": { "$ref": "#/$defs/ObservationQuality" }, "reference": { "$ref": "#/$defs/ObservationRevisionRef" }, "source": { "$ref": "#/$defs/ArtifactRef" }, "supersedes": { "anyOf": [{ "$ref": "#/$defs/ObservationRevisionRef" }, { "type": "null" }] }, "value": { "discriminator": { "mapping": { "categorical": "#/$defs/CategoricalMeasurement", "censored": "#/$defs/CensoredMeasurement", "missing": "#/$defs/MissingMeasurement", "numeric": "#/$defs/NumericMeasurement", "series": "#/$defs/SeriesDescriptor" }, "propertyName": "kind" }, "oneOf": [{ "$ref": "#/$defs/NumericMeasurement" }, { "$ref": "#/$defs/CensoredMeasurement" }, { "$ref": "#/$defs/CategoricalMeasurement" }, { "$ref": "#/$defs/MissingMeasurement" }, { "$ref": "#/$defs/SeriesDescriptor" }], "title": "Value" } }, "required": ["reference", "supersedes", "source", "binding", "quality", "value", "context_link", "expectation"], "title": "PropertyViewRow", "type": "object" }, "ResearchViewPosition": { "additionalProperties": false, "properties": { "offset": { "maximum": 4096, "minimum": 0, "title": "Offset", "type": "integer" }, "query_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Query Sha256", "type": "string" } }, "required": ["query_sha256", "offset"], "title": "ResearchViewPosition", "type": "object" }, "SampleRevisionRef": { "additionalProperties": false, "properties": { "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "sample_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Sample Id", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "sample_id", "revision"], "title": "SampleRevisionRef", "type": "object" }, "SchemaRef": { "additionalProperties": false, "properties": { "schema_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Schema Id", "type": "string" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "version": { "const": "1", "title": "Version", "type": "string" } }, "required": ["schema_id", "version", "sha256"], "title": "SchemaRef", "type": "object" }, "Scope": { "additionalProperties": false, "properties": { "project_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Project Id", "type": "string" }, "tenant_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Tenant Id", "type": "string" } }, "required": ["tenant_id", "project_id"], "title": "Scope", "type": "object" }, "SeriesDescriptor": { "additionalProperties": false, "properties": { "kind": { "const": "series", "title": "Kind", "type": "string" }, "point_count": { "maximum": 4096, "minimum": 1, "title": "Point Count", "type": "integer" }, "x_unit": { "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "title": "X Unit", "type": "string" }, "y_unit": { "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "title": "Y Unit", "type": "string" } }, "required": ["kind", "x_unit", "y_unit", "point_count"], "title": "SeriesDescriptor", "type": "object" } }, "$id": "urn:amphora:research-views.property-view-page:1:serialization", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": { "authority": { "const": "reported_evidence_only", "title": "Authority", "type": "string" }, "next_position": { "anyOf": [{ "$ref": "#/$defs/ResearchViewPosition" }, { "type": "null" }] }, "protocol": { "$ref": "#/$defs/ExperimentProtocol" }, "query_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Query Sha256", "type": "string" }, "request": { "$ref": "#/$defs/PropertyViewRequest" }, "rows": { "items": { "$ref": "#/$defs/PropertyViewRow" }, "maxItems": 16, "title": "Rows", "type": "array" }, "selection_scope": { "const": "explicit_observation_revisions", "title": "Selection Scope", "type": "string" }, "total": { "maximum": 128, "minimum": 1, "title": "Total", "type": "integer" }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" } }, "required": ["wire_version", "request", "query_sha256", "total", "protocol", "authority", "selection_scope", "rows", "next_position"], "title": "PropertyViewPage", "type": "object" };
    var func53 = Object.prototype.hasOwnProperty;
    function validate53(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate53.evaluated;
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
            validate53.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate53.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate53.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate53.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate53.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate53.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate53.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate53.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern21.test(data1)) {
                            validate53.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate53.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate53.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate53.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate53.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate53.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate53.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate53.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    if (!pattern7.test(data4)) {
                                      validate53.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate53.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate53.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate53.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate53.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate53.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate53.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate53.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate53.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
                                          validate53.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate53.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        validate53.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate53.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
                                            validate53.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate53.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate53.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            if (!pattern7.test(data9)) {
                              validate53.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate53.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate53.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate53.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate53.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate53.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate53.errors = vErrors;
      return errors === 0;
    }
    validate53.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.method === void 0 && (missing0 = "method") || data.applicability === void 0 && (missing0 = "applicability") || data.source === void 0 && (missing0 = "source")) {
            validate52.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "applicability" || key0 === "method" || key0 === "source")) {
                validate52.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.applicability !== void 0) {
                const _errs2 = errors;
                if (!validate53(data.applicability, { instancePath: instancePath + "/applicability", parentData: data, parentDataProperty: "applicability", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate53.errors : vErrors.concat(validate53.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.method !== void 0) {
                  let data1 = data.method;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.schema_id === void 0 && (missing1 = "schema_id") || data1.version === void 0 && (missing1 = "version") || data1.sha256 === void 0 && (missing1 = "sha256")) {
                        validate52.errors = [{ instancePath: instancePath + "/method", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs6 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                            validate52.errors = [{ instancePath: instancePath + "/method", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs6 === errors) {
                          if (data1.schema_id !== void 0) {
                            let data2 = data1.schema_id;
                            const _errs7 = errors;
                            if (errors === _errs7) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate52.errors = [{ instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate52.errors = [{ instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate52.errors = [{ instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate52.errors = [{ instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs7 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.sha256 !== void 0) {
                              let data3 = data1.sha256;
                              const _errs9 = errors;
                              if (errors === _errs9) {
                                if (typeof data3 === "string") {
                                  if (!pattern7.test(data3)) {
                                    validate52.errors = [{ instancePath: instancePath + "/method/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                    return false;
                                  }
                                } else {
                                  validate52.errors = [{ instancePath: instancePath + "/method/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs9 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data1.version !== void 0) {
                                let data4 = data1.version;
                                const _errs11 = errors;
                                if (typeof data4 !== "string") {
                                  validate52.errors = [{ instancePath: instancePath + "/method/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("1" !== data4) {
                                  validate52.errors = [{ instancePath: instancePath + "/method/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid2 = _errs11 === errors;
                              } else {
                                var valid2 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      validate52.errors = [{ instancePath: instancePath + "/method", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.source !== void 0) {
                    const _errs13 = errors;
                    if (!validate53(data.source, { instancePath: instancePath + "/source", parentData: data, parentDataProperty: "source", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate53.errors : vErrors.concat(validate53.errors);
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
        } else {
          validate52.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate52.errors = vErrors;
      return errors === 0;
    }
    validate52.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate58(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate58.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.experiment_id === void 0 && (missing0 = "experiment_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate58.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment_id" || key0 === "revision" || key0 === "scope")) {
                validate58.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment_id !== void 0) {
                let data0 = data.experiment_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate58.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate58.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate58.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate58.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate58.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate58.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate58.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate58.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate58.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate58.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate58.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate58.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate58.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate58.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate58.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate58.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate58.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate58.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate58.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate58.errors = vErrors;
      return errors === 0;
    }
    validate58.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate60(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate60.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.observation_id === void 0 && (missing0 = "observation_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate60.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "observation_id" || key0 === "revision" || key0 === "scope")) {
                validate60.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.observation_id !== void 0) {
                let data0 = data.observation_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate60.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate60.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate60.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate60.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate60.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate60.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate60.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate60.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate60.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate60.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate60.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate60.errors = vErrors;
      return errors === 0;
    }
    validate60.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.experiment === void 0 && (missing0 = "experiment") || data.observations === void 0 && (missing0 = "observations")) {
            validate57.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment" || key0 === "limit" || key0 === "observations" || key0 === "position" || key0 === "wire_version")) {
                validate57.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment !== void 0) {
                const _errs2 = errors;
                if (!validate58(data.experiment, { instancePath: instancePath + "/experiment", parentData: data, parentDataProperty: "experiment", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate58.errors : vErrors.concat(validate58.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.limit !== void 0) {
                  let data1 = data.limit;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate57.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 16 || isNaN(data1)) {
                        validate57.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate57.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                  if (data.observations !== void 0) {
                    let data2 = data.observations;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (Array.isArray(data2)) {
                        if (data2.length > 128) {
                          validate57.errors = [{ instancePath: instancePath + "/observations", schemaPath: "#/properties/observations/maxItems", keyword: "maxItems", params: { limit: 128 }, message: "must NOT have more than 128 items" }];
                          return false;
                        } else {
                          if (data2.length < 1) {
                            validate57.errors = [{ instancePath: instancePath + "/observations", schemaPath: "#/properties/observations/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                            return false;
                          } else {
                            var valid1 = true;
                            const len0 = data2.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs7 = errors;
                              if (!validate60(data2[i0], { instancePath: instancePath + "/observations/" + i0, parentData: data2, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate60.errors : vErrors.concat(validate60.errors);
                                errors = vErrors.length;
                              }
                              var valid1 = _errs7 === errors;
                              if (!valid1) {
                                break;
                              }
                            }
                          }
                        }
                      } else {
                        validate57.errors = [{ instancePath: instancePath + "/observations", schemaPath: "#/properties/observations/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.position !== void 0) {
                      let data4 = data.position;
                      const _errs8 = errors;
                      const _errs9 = errors;
                      let valid2 = false;
                      const _errs10 = errors;
                      const _errs11 = errors;
                      if (errors === _errs11) {
                        if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                          let missing1;
                          if (data4.query_sha256 === void 0 && (missing1 = "query_sha256") || data4.offset === void 0 && (missing1 = "offset")) {
                            const err0 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                            if (vErrors === null) {
                              vErrors = [err0];
                            } else {
                              vErrors.push(err0);
                            }
                            errors++;
                          } else {
                            const _errs13 = errors;
                            for (const key1 in data4) {
                              if (!(key1 === "offset" || key1 === "query_sha256")) {
                                const err1 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                if (vErrors === null) {
                                  vErrors = [err1];
                                } else {
                                  vErrors.push(err1);
                                }
                                errors++;
                                break;
                              }
                            }
                            if (_errs13 === errors) {
                              if (data4.offset !== void 0) {
                                let data5 = data4.offset;
                                const _errs14 = errors;
                                if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                  const err2 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                  if (vErrors === null) {
                                    vErrors = [err2];
                                  } else {
                                    vErrors.push(err2);
                                  }
                                  errors++;
                                }
                                if (errors === _errs14) {
                                  if (typeof data5 == "number" && isFinite(data5)) {
                                    if (data5 > 4096 || isNaN(data5)) {
                                      const err3 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                      if (vErrors === null) {
                                        vErrors = [err3];
                                      } else {
                                        vErrors.push(err3);
                                      }
                                      errors++;
                                    } else {
                                      if (data5 < 0 || isNaN(data5)) {
                                        const err4 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                                var valid4 = _errs14 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data4.query_sha256 !== void 0) {
                                  let data6 = data4.query_sha256;
                                  const _errs16 = errors;
                                  if (errors === _errs16) {
                                    if (typeof data6 === "string") {
                                      if (!pattern7.test(data6)) {
                                        const err5 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                        if (vErrors === null) {
                                          vErrors = [err5];
                                        } else {
                                          vErrors.push(err5);
                                        }
                                        errors++;
                                      }
                                    } else {
                                      const err6 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err6];
                                      } else {
                                        vErrors.push(err6);
                                      }
                                      errors++;
                                    }
                                  }
                                  var valid4 = _errs16 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          const err7 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                          if (vErrors === null) {
                            vErrors = [err7];
                          } else {
                            vErrors.push(err7);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs10 === errors;
                      valid2 = valid2 || _valid0;
                      const _errs18 = errors;
                      if (data4 !== null) {
                        const err8 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                      }
                      var _valid0 = _errs18 === errors;
                      valid2 = valid2 || _valid0;
                      if (!valid2) {
                        const err9 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err9];
                        } else {
                          vErrors.push(err9);
                        }
                        errors++;
                        validate57.errors = vErrors;
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
                      if (data.wire_version !== void 0) {
                        let data7 = data.wire_version;
                        const _errs20 = errors;
                        if (typeof data7 !== "string") {
                          validate57.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data7) {
                          validate57.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
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
        } else {
          validate57.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate57.errors = vErrors;
      return errors === 0;
    }
    validate57.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema72 = { "additionalProperties": false, "properties": { "binding": { "$ref": "#/$defs/ObservationBindingRecord" }, "context_link": { "enum": ["declared_expectation", "unbound", "different_experiment", "unknown_expectation"], "title": "Context Link", "type": "string" }, "expectation": { "anyOf": [{ "$ref": "#/$defs/ExperimentExpectation" }, { "type": "null" }] }, "quality": { "$ref": "#/$defs/ObservationQuality" }, "reference": { "$ref": "#/$defs/ObservationRevisionRef" }, "source": { "$ref": "#/$defs/ArtifactRef" }, "supersedes": { "anyOf": [{ "$ref": "#/$defs/ObservationRevisionRef" }, { "type": "null" }] }, "value": { "discriminator": { "mapping": { "categorical": "#/$defs/CategoricalMeasurement", "censored": "#/$defs/CensoredMeasurement", "missing": "#/$defs/MissingMeasurement", "numeric": "#/$defs/NumericMeasurement", "series": "#/$defs/SeriesDescriptor" }, "propertyName": "kind" }, "oneOf": [{ "$ref": "#/$defs/NumericMeasurement" }, { "$ref": "#/$defs/CensoredMeasurement" }, { "$ref": "#/$defs/CategoricalMeasurement" }, { "$ref": "#/$defs/MissingMeasurement" }, { "$ref": "#/$defs/SeriesDescriptor" }], "title": "Value" } }, "required": ["reference", "supersedes", "source", "binding", "quality", "value", "context_link", "expectation"], "title": "PropertyViewRow", "type": "object" };
    var schema85 = { "additionalProperties": false, "properties": { "controls": { "enum": ["passed", "failed", "unknown"], "title": "Controls", "type": "string" }, "flags": { "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 64, "title": "Flags", "type": "array" } }, "required": ["controls", "flags"], "title": "ObservationQuality", "type": "object" };
    var schema73 = { "additionalProperties": false, "properties": { "measurement": { "$ref": "#/$defs/ObservationMethod" }, "role": { "anyOf": [{ "enum": ["sample", "positive_control", "negative_control", "blank"], "type": "string" }, { "type": "null" }], "title": "Role" }, "specimen": { "$ref": "#/$defs/ObservationSpecimen" }, "target": { "$ref": "#/$defs/ObservationTarget" } }, "required": ["target", "specimen", "measurement", "role"], "title": "ObservationBindingRecord", "type": "object" };
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
          if (data.method === void 0 && (missing0 = "method") || data.context === void 0 && (missing0 = "context")) {
            validate65.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "context" || key0 === "method")) {
                validate65.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.context !== void 0) {
                let data0 = data.context;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate53(data0, { instancePath: instancePath + "/context", parentData: data, parentDataProperty: "context", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate53.errors : vErrors.concat(validate53.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/context", schemaPath: "#/properties/context/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err1 = { instancePath: instancePath + "/context", schemaPath: "#/properties/context/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate65.errors = vErrors;
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
                if (data.method !== void 0) {
                  let data1 = data.method;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid2 = false;
                  const _errs9 = errors;
                  const _errs10 = errors;
                  if (errors === _errs10) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.schema_id === void 0 && (missing1 = "schema_id") || data1.version === void 0 && (missing1 = "version") || data1.sha256 === void 0 && (missing1 = "sha256")) {
                        const err2 = { instancePath: instancePath + "/method", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                      } else {
                        const _errs12 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                            const err3 = { instancePath: instancePath + "/method", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                            if (vErrors === null) {
                              vErrors = [err3];
                            } else {
                              vErrors.push(err3);
                            }
                            errors++;
                            break;
                          }
                        }
                        if (_errs12 === errors) {
                          if (data1.schema_id !== void 0) {
                            let data2 = data1.schema_id;
                            const _errs13 = errors;
                            if (errors === _errs13) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  const err4 = { instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                  if (vErrors === null) {
                                    vErrors = [err4];
                                  } else {
                                    vErrors.push(err4);
                                  }
                                  errors++;
                                } else {
                                  if (func1(data2) < 1) {
                                    const err5 = { instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                    if (vErrors === null) {
                                      vErrors = [err5];
                                    } else {
                                      vErrors.push(err5);
                                    }
                                    errors++;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      const err6 = { instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                const err7 = { instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err7];
                                } else {
                                  vErrors.push(err7);
                                }
                                errors++;
                              }
                            }
                            var valid4 = _errs13 === errors;
                          } else {
                            var valid4 = true;
                          }
                          if (valid4) {
                            if (data1.sha256 !== void 0) {
                              let data3 = data1.sha256;
                              const _errs15 = errors;
                              if (errors === _errs15) {
                                if (typeof data3 === "string") {
                                  if (!pattern7.test(data3)) {
                                    const err8 = { instancePath: instancePath + "/method/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                    if (vErrors === null) {
                                      vErrors = [err8];
                                    } else {
                                      vErrors.push(err8);
                                    }
                                    errors++;
                                  }
                                } else {
                                  const err9 = { instancePath: instancePath + "/method/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                            if (valid4) {
                              if (data1.version !== void 0) {
                                let data4 = data1.version;
                                const _errs17 = errors;
                                if (typeof data4 !== "string") {
                                  const err10 = { instancePath: instancePath + "/method/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err10];
                                  } else {
                                    vErrors.push(err10);
                                  }
                                  errors++;
                                }
                                if ("1" !== data4) {
                                  const err11 = { instancePath: instancePath + "/method/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" };
                                  if (vErrors === null) {
                                    vErrors = [err11];
                                  } else {
                                    vErrors.push(err11);
                                  }
                                  errors++;
                                }
                                var valid4 = _errs17 === errors;
                              } else {
                                var valid4 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      const err12 = { instancePath: instancePath + "/method", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err12];
                      } else {
                        vErrors.push(err12);
                      }
                      errors++;
                    }
                  }
                  var _valid1 = _errs9 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs19 = errors;
                  if (data1 !== null) {
                    const err13 = { instancePath: instancePath + "/method", schemaPath: "#/properties/method/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err13];
                    } else {
                      vErrors.push(err13);
                    }
                    errors++;
                  }
                  var _valid1 = _errs19 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err14 = { instancePath: instancePath + "/method", schemaPath: "#/properties/method/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err14];
                    } else {
                      vErrors.push(err14);
                    }
                    errors++;
                    validate65.errors = vErrors;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.material_state_id === void 0 && (missing0 = "material_state_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate69.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "material_state_id" || key0 === "revision" || key0 === "scope")) {
                validate69.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.material_state_id !== void 0) {
                let data0 = data.material_state_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate69.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate69.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate69.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate69.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate69.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
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
                          validate69.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate69.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate69.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate69.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate69.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate69.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate69.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate69.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate69.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate69.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate69.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate69.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate69.errors = vErrors;
      return errors === 0;
    }
    validate69.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate71(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate71.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.sample_id === void 0 && (missing0 = "sample_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate71.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "revision" || key0 === "sample_id" || key0 === "scope")) {
                validate71.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.revision !== void 0) {
                let data0 = data.revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate71.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate71.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 1 || isNaN(data0)) {
                        validate71.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                if (data.sample_id !== void 0) {
                  let data1 = data.sample_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate71.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate71.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate71.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate71.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
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
                          validate71.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate71.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate71.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate71.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate71.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate71.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate71.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate71.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate71.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate71.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate71.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate71.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate71.errors = vErrors;
      return errors === 0;
    }
    validate71.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate68(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
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
          if (data.sample === void 0 && (missing0 = "sample") || data.material_state === void 0 && (missing0 = "material_state")) {
            validate68.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "material_state" || key0 === "sample")) {
                validate68.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.material_state !== void 0) {
                let data0 = data.material_state;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate69(data0, { instancePath: instancePath + "/material_state", parentData: data, parentDataProperty: "material_state", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate69.errors : vErrors.concat(validate69.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/material_state", schemaPath: "#/properties/material_state/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err1 = { instancePath: instancePath + "/material_state", schemaPath: "#/properties/material_state/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate68.errors = vErrors;
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
                if (data.sample !== void 0) {
                  let data1 = data.sample;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid2 = false;
                  const _errs9 = errors;
                  if (!validate71(data1, { instancePath: instancePath + "/sample", parentData: data, parentDataProperty: "sample", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate71.errors : vErrors.concat(validate71.errors);
                    errors = vErrors.length;
                  }
                  var _valid1 = _errs9 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs10 = errors;
                  if (data1 !== null) {
                    const err2 = { instancePath: instancePath + "/sample", schemaPath: "#/properties/sample/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err3 = { instancePath: instancePath + "/sample", schemaPath: "#/properties/sample/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                    validate68.errors = vErrors;
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
          if (data.experiment === void 0 && (missing0 = "experiment") || data.expectation_id === void 0 && (missing0 = "expectation_id") || data.replicate_id === void 0 && (missing0 = "replicate_id")) {
            validate74.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "expectation_id" || key0 === "experiment" || key0 === "replicate_id")) {
                validate74.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.expectation_id !== void 0) {
                let data0 = data.expectation_id;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (errors === _errs4) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      const err0 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    } else {
                      if (func1(data0) < 1) {
                        const err1 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      } else {
                        if (!pattern4.test(data0)) {
                          const err2 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                    const err3 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                  const err4 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err5 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err5];
                  } else {
                    vErrors.push(err5);
                  }
                  errors++;
                  validate74.errors = vErrors;
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
                if (data.experiment !== void 0) {
                  let data1 = data.experiment;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid2 = false;
                  const _errs10 = errors;
                  if (!validate58(data1, { instancePath: instancePath + "/experiment", parentData: data, parentDataProperty: "experiment", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate58.errors : vErrors.concat(validate58.errors);
                    errors = vErrors.length;
                  }
                  var _valid1 = _errs10 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs11 = errors;
                  if (data1 !== null) {
                    const err6 = { instancePath: instancePath + "/experiment", schemaPath: "#/properties/experiment/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err6];
                    } else {
                      vErrors.push(err6);
                    }
                    errors++;
                  }
                  var _valid1 = _errs11 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err7 = { instancePath: instancePath + "/experiment", schemaPath: "#/properties/experiment/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err7];
                    } else {
                      vErrors.push(err7);
                    }
                    errors++;
                    validate74.errors = vErrors;
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
                  if (data.replicate_id !== void 0) {
                    let data2 = data.replicate_id;
                    const _errs13 = errors;
                    const _errs14 = errors;
                    let valid3 = false;
                    const _errs15 = errors;
                    if (errors === _errs15) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 128) {
                          const err8 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                          if (vErrors === null) {
                            vErrors = [err8];
                          } else {
                            vErrors.push(err8);
                          }
                          errors++;
                        } else {
                          if (func1(data2) < 1) {
                            const err9 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                            if (vErrors === null) {
                              vErrors = [err9];
                            } else {
                              vErrors.push(err9);
                            }
                            errors++;
                          } else {
                            if (!pattern4.test(data2)) {
                              const err10 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                        const err11 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err11];
                        } else {
                          vErrors.push(err11);
                        }
                        errors++;
                      }
                    }
                    var _valid2 = _errs15 === errors;
                    valid3 = valid3 || _valid2;
                    const _errs17 = errors;
                    if (data2 !== null) {
                      const err12 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err12];
                      } else {
                        vErrors.push(err12);
                      }
                      errors++;
                    }
                    var _valid2 = _errs17 === errors;
                    valid3 = valid3 || _valid2;
                    if (!valid3) {
                      const err13 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err13];
                      } else {
                        vErrors.push(err13);
                      }
                      errors++;
                      validate74.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs14;
                      if (vErrors !== null) {
                        if (_errs14) {
                          vErrors.length = _errs14;
                        } else {
                          vErrors = null;
                        }
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
        } else {
          validate74.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate74.errors = vErrors;
      return errors === 0;
    }
    validate74.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.target === void 0 && (missing0 = "target") || data.specimen === void 0 && (missing0 = "specimen") || data.measurement === void 0 && (missing0 = "measurement") || data.role === void 0 && (missing0 = "role")) {
            validate64.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "measurement" || key0 === "role" || key0 === "specimen" || key0 === "target")) {
                validate64.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.measurement !== void 0) {
                const _errs2 = errors;
                if (!validate65(data.measurement, { instancePath: instancePath + "/measurement", parentData: data, parentDataProperty: "measurement", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate65.errors : vErrors.concat(validate65.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.role !== void 0) {
                  let data1 = data.role;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  let valid1 = false;
                  const _errs5 = errors;
                  if (typeof data1 !== "string") {
                    const err0 = { instancePath: instancePath + "/role", schemaPath: "#/properties/role/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  if (!(data1 === "sample" || data1 === "positive_control" || data1 === "negative_control" || data1 === "blank")) {
                    const err1 = { instancePath: instancePath + "/role", schemaPath: "#/properties/role/anyOf/0/enum", keyword: "enum", params: { allowedValues: schema73.properties.role.anyOf[0].enum }, message: "must be equal to one of the allowed values" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs5 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs7 = errors;
                  if (data1 !== null) {
                    const err2 = { instancePath: instancePath + "/role", schemaPath: "#/properties/role/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                  }
                  var _valid0 = _errs7 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err3 = { instancePath: instancePath + "/role", schemaPath: "#/properties/role/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                    validate64.errors = vErrors;
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
                  if (data.specimen !== void 0) {
                    const _errs9 = errors;
                    if (!validate68(data.specimen, { instancePath: instancePath + "/specimen", parentData: data, parentDataProperty: "specimen", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate68.errors : vErrors.concat(validate68.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.target !== void 0) {
                      const _errs10 = errors;
                      if (!validate74(data.target, { instancePath: instancePath + "/target", parentData: data, parentDataProperty: "target", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate74.errors : vErrors.concat(validate74.errors);
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
          validate64.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate64.errors = vErrors;
      return errors === 0;
    }
    validate64.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema83 = { "additionalProperties": false, "properties": { "criterion_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Criterion Id", "type": "string" }, "kind": { "enum": ["numeric", "categorical", "series"], "title": "Kind", "type": "string" }, "unit": { "anyOf": [{ "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "type": "string" }, { "type": "null" }], "title": "Unit" }, "x_unit": { "anyOf": [{ "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "type": "string" }, { "type": "null" }], "title": "X Unit" } }, "required": ["criterion_id", "kind", "unit", "x_unit"], "title": "ExperimentReadout", "type": "object" };
    var schema84 = { "additionalProperties": false, "properties": { "replicate_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Replicate Id", "type": "string" }, "role": { "enum": ["sample", "positive_control", "negative_control", "blank"], "title": "Role", "type": "string" } }, "required": ["replicate_id", "role"], "title": "ExperimentReplicate", "type": "object" };
    var pattern67 = new RegExp("^\\S+$(?![\\s\\S])", "u");
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
          if (data.expectation_id === void 0 && (missing0 = "expectation_id") || data.sample === void 0 && (missing0 = "sample") || data.readout === void 0 && (missing0 = "readout") || data.replicate === void 0 && (missing0 = "replicate")) {
            validate78.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "expectation_id" || key0 === "readout" || key0 === "replicate" || key0 === "sample")) {
                validate78.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.expectation_id !== void 0) {
                let data0 = data.expectation_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate78.errors = [{ instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate78.errors = [{ instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate78.errors = [{ instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate78.errors = [{ instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.readout !== void 0) {
                  let data1 = data.readout;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.criterion_id === void 0 && (missing1 = "criterion_id") || data1.kind === void 0 && (missing1 = "kind") || data1.unit === void 0 && (missing1 = "unit") || data1.x_unit === void 0 && (missing1 = "x_unit")) {
                        validate78.errors = [{ instancePath: instancePath + "/readout", schemaPath: "#/$defs/ExperimentReadout/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "criterion_id" || key1 === "kind" || key1 === "unit" || key1 === "x_unit")) {
                            validate78.errors = [{ instancePath: instancePath + "/readout", schemaPath: "#/$defs/ExperimentReadout/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.criterion_id !== void 0) {
                            let data2 = data1.criterion_id;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate78.errors = [{ instancePath: instancePath + "/readout/criterion_id", schemaPath: "#/$defs/ExperimentReadout/properties/criterion_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate78.errors = [{ instancePath: instancePath + "/readout/criterion_id", schemaPath: "#/$defs/ExperimentReadout/properties/criterion_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      validate78.errors = [{ instancePath: instancePath + "/readout/criterion_id", schemaPath: "#/$defs/ExperimentReadout/properties/criterion_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate78.errors = [{ instancePath: instancePath + "/readout/criterion_id", schemaPath: "#/$defs/ExperimentReadout/properties/criterion_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.kind !== void 0) {
                              let data3 = data1.kind;
                              const _errs10 = errors;
                              if (typeof data3 !== "string") {
                                validate78.errors = [{ instancePath: instancePath + "/readout/kind", schemaPath: "#/$defs/ExperimentReadout/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if (!(data3 === "numeric" || data3 === "categorical" || data3 === "series")) {
                                validate78.errors = [{ instancePath: instancePath + "/readout/kind", schemaPath: "#/$defs/ExperimentReadout/properties/kind/enum", keyword: "enum", params: { allowedValues: schema83.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
                                return false;
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data1.unit !== void 0) {
                                let data4 = data1.unit;
                                const _errs12 = errors;
                                const _errs13 = errors;
                                let valid3 = false;
                                const _errs14 = errors;
                                if (errors === _errs14) {
                                  if (typeof data4 === "string") {
                                    if (func1(data4) > 32) {
                                      const err0 = { instancePath: instancePath + "/readout/unit", schemaPath: "#/$defs/ExperimentReadout/properties/unit/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err0];
                                      } else {
                                        vErrors.push(err0);
                                      }
                                      errors++;
                                    } else {
                                      if (func1(data4) < 1) {
                                        const err1 = { instancePath: instancePath + "/readout/unit", schemaPath: "#/$defs/ExperimentReadout/properties/unit/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err1];
                                        } else {
                                          vErrors.push(err1);
                                        }
                                        errors++;
                                      } else {
                                        if (!pattern67.test(data4)) {
                                          const err2 = { instancePath: instancePath + "/readout/unit", schemaPath: "#/$defs/ExperimentReadout/properties/unit/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' };
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
                                    const err3 = { instancePath: instancePath + "/readout/unit", schemaPath: "#/$defs/ExperimentReadout/properties/unit/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err3];
                                    } else {
                                      vErrors.push(err3);
                                    }
                                    errors++;
                                  }
                                }
                                var _valid0 = _errs14 === errors;
                                valid3 = valid3 || _valid0;
                                const _errs16 = errors;
                                if (data4 !== null) {
                                  const err4 = { instancePath: instancePath + "/readout/unit", schemaPath: "#/$defs/ExperimentReadout/properties/unit/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                  if (vErrors === null) {
                                    vErrors = [err4];
                                  } else {
                                    vErrors.push(err4);
                                  }
                                  errors++;
                                }
                                var _valid0 = _errs16 === errors;
                                valid3 = valid3 || _valid0;
                                if (!valid3) {
                                  const err5 = { instancePath: instancePath + "/readout/unit", schemaPath: "#/$defs/ExperimentReadout/properties/unit/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                  if (vErrors === null) {
                                    vErrors = [err5];
                                  } else {
                                    vErrors.push(err5);
                                  }
                                  errors++;
                                  validate78.errors = vErrors;
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
                              if (valid2) {
                                if (data1.x_unit !== void 0) {
                                  let data5 = data1.x_unit;
                                  const _errs18 = errors;
                                  const _errs19 = errors;
                                  let valid4 = false;
                                  const _errs20 = errors;
                                  if (errors === _errs20) {
                                    if (typeof data5 === "string") {
                                      if (func1(data5) > 32) {
                                        const err6 = { instancePath: instancePath + "/readout/x_unit", schemaPath: "#/$defs/ExperimentReadout/properties/x_unit/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err6];
                                        } else {
                                          vErrors.push(err6);
                                        }
                                        errors++;
                                      } else {
                                        if (func1(data5) < 1) {
                                          const err7 = { instancePath: instancePath + "/readout/x_unit", schemaPath: "#/$defs/ExperimentReadout/properties/x_unit/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err7];
                                          } else {
                                            vErrors.push(err7);
                                          }
                                          errors++;
                                        } else {
                                          if (!pattern67.test(data5)) {
                                            const err8 = { instancePath: instancePath + "/readout/x_unit", schemaPath: "#/$defs/ExperimentReadout/properties/x_unit/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' };
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
                                      const err9 = { instancePath: instancePath + "/readout/x_unit", schemaPath: "#/$defs/ExperimentReadout/properties/x_unit/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err9];
                                      } else {
                                        vErrors.push(err9);
                                      }
                                      errors++;
                                    }
                                  }
                                  var _valid1 = _errs20 === errors;
                                  valid4 = valid4 || _valid1;
                                  const _errs22 = errors;
                                  if (data5 !== null) {
                                    const err10 = { instancePath: instancePath + "/readout/x_unit", schemaPath: "#/$defs/ExperimentReadout/properties/x_unit/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                    if (vErrors === null) {
                                      vErrors = [err10];
                                    } else {
                                      vErrors.push(err10);
                                    }
                                    errors++;
                                  }
                                  var _valid1 = _errs22 === errors;
                                  valid4 = valid4 || _valid1;
                                  if (!valid4) {
                                    const err11 = { instancePath: instancePath + "/readout/x_unit", schemaPath: "#/$defs/ExperimentReadout/properties/x_unit/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                    if (vErrors === null) {
                                      vErrors = [err11];
                                    } else {
                                      vErrors.push(err11);
                                    }
                                    errors++;
                                    validate78.errors = vErrors;
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
                                  var valid2 = _errs18 === errors;
                                } else {
                                  var valid2 = true;
                                }
                              }
                            }
                          }
                        }
                      }
                    } else {
                      validate78.errors = [{ instancePath: instancePath + "/readout", schemaPath: "#/$defs/ExperimentReadout/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.replicate !== void 0) {
                    let data6 = data.replicate;
                    const _errs24 = errors;
                    const _errs25 = errors;
                    if (errors === _errs25) {
                      if (data6 && typeof data6 == "object" && !Array.isArray(data6)) {
                        let missing2;
                        if (data6.replicate_id === void 0 && (missing2 = "replicate_id") || data6.role === void 0 && (missing2 = "role")) {
                          validate78.errors = [{ instancePath: instancePath + "/replicate", schemaPath: "#/$defs/ExperimentReplicate/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                          return false;
                        } else {
                          const _errs27 = errors;
                          for (const key2 in data6) {
                            if (!(key2 === "replicate_id" || key2 === "role")) {
                              validate78.errors = [{ instancePath: instancePath + "/replicate", schemaPath: "#/$defs/ExperimentReplicate/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs27 === errors) {
                            if (data6.replicate_id !== void 0) {
                              let data7 = data6.replicate_id;
                              const _errs28 = errors;
                              if (errors === _errs28) {
                                if (typeof data7 === "string") {
                                  if (func1(data7) > 128) {
                                    validate78.errors = [{ instancePath: instancePath + "/replicate/replicate_id", schemaPath: "#/$defs/ExperimentReplicate/properties/replicate_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data7) < 1) {
                                      validate78.errors = [{ instancePath: instancePath + "/replicate/replicate_id", schemaPath: "#/$defs/ExperimentReplicate/properties/replicate_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data7)) {
                                        validate78.errors = [{ instancePath: instancePath + "/replicate/replicate_id", schemaPath: "#/$defs/ExperimentReplicate/properties/replicate_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate78.errors = [{ instancePath: instancePath + "/replicate/replicate_id", schemaPath: "#/$defs/ExperimentReplicate/properties/replicate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid6 = _errs28 === errors;
                            } else {
                              var valid6 = true;
                            }
                            if (valid6) {
                              if (data6.role !== void 0) {
                                let data8 = data6.role;
                                const _errs30 = errors;
                                if (typeof data8 !== "string") {
                                  validate78.errors = [{ instancePath: instancePath + "/replicate/role", schemaPath: "#/$defs/ExperimentReplicate/properties/role/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if (!(data8 === "sample" || data8 === "positive_control" || data8 === "negative_control" || data8 === "blank")) {
                                  validate78.errors = [{ instancePath: instancePath + "/replicate/role", schemaPath: "#/$defs/ExperimentReplicate/properties/role/enum", keyword: "enum", params: { allowedValues: schema84.properties.role.enum }, message: "must be equal to one of the allowed values" }];
                                  return false;
                                }
                                var valid6 = _errs30 === errors;
                              } else {
                                var valid6 = true;
                              }
                            }
                          }
                        }
                      } else {
                        validate78.errors = [{ instancePath: instancePath + "/replicate", schemaPath: "#/$defs/ExperimentReplicate/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs24 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.sample !== void 0) {
                      const _errs32 = errors;
                      if (!validate71(data.sample, { instancePath: instancePath + "/sample", parentData: data, parentDataProperty: "sample", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate71.errors : vErrors.concat(validate71.errors);
                        errors = vErrors.length;
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
        } else {
          validate78.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate78.errors = vErrors;
      return errors === 0;
    }
    validate78.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var pattern72 = new RegExp("^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])", "u");
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
          if (data.lower === void 0 && (missing0 = "lower") || data.upper === void 0 && (missing0 = "upper") || data.description === void 0 && (missing0 = "description")) {
            validate85.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "description" || key0 === "lower" || key0 === "upper")) {
                validate85.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.description !== void 0) {
                let data0 = data.description;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 512) {
                      validate85.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/maxLength", keyword: "maxLength", params: { limit: 512 }, message: "must NOT have more than 512 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate85.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      }
                    }
                  } else {
                    validate85.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.lower !== void 0) {
                  let data1 = data.lower;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.value === void 0 && (missing1 = "value") || data1.unit === void 0 && (missing1 = "unit")) {
                        validate85.errors = [{ instancePath: instancePath + "/lower", schemaPath: "#/$defs/MeasurementQuantity/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "unit" || key1 === "value")) {
                            validate85.errors = [{ instancePath: instancePath + "/lower", schemaPath: "#/$defs/MeasurementQuantity/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.unit !== void 0) {
                            let data2 = data1.unit;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 32) {
                                  validate85.errors = [{ instancePath: instancePath + "/lower/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate85.errors = [{ instancePath: instancePath + "/lower/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern67.test(data2)) {
                                      validate85.errors = [{ instancePath: instancePath + "/lower/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate85.errors = [{ instancePath: instancePath + "/lower/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.value !== void 0) {
                              let data3 = data1.value;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate85.errors = [{ instancePath: instancePath + "/lower/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate85.errors = [{ instancePath: instancePath + "/lower/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern72.test(data3)) {
                                        validate85.errors = [{ instancePath: instancePath + "/lower/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])" }, message: 'must match pattern "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate85.errors = [{ instancePath: instancePath + "/lower/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate85.errors = [{ instancePath: instancePath + "/lower", schemaPath: "#/$defs/MeasurementQuantity/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.upper !== void 0) {
                    let data4 = data.upper;
                    const _errs12 = errors;
                    const _errs13 = errors;
                    if (errors === _errs13) {
                      if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                        let missing2;
                        if (data4.value === void 0 && (missing2 = "value") || data4.unit === void 0 && (missing2 = "unit")) {
                          validate85.errors = [{ instancePath: instancePath + "/upper", schemaPath: "#/$defs/MeasurementQuantity/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                          return false;
                        } else {
                          const _errs15 = errors;
                          for (const key2 in data4) {
                            if (!(key2 === "unit" || key2 === "value")) {
                              validate85.errors = [{ instancePath: instancePath + "/upper", schemaPath: "#/$defs/MeasurementQuantity/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs15 === errors) {
                            if (data4.unit !== void 0) {
                              let data5 = data4.unit;
                              const _errs16 = errors;
                              if (errors === _errs16) {
                                if (typeof data5 === "string") {
                                  if (func1(data5) > 32) {
                                    validate85.errors = [{ instancePath: instancePath + "/upper/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data5) < 1) {
                                      validate85.errors = [{ instancePath: instancePath + "/upper/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern67.test(data5)) {
                                        validate85.errors = [{ instancePath: instancePath + "/upper/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate85.errors = [{ instancePath: instancePath + "/upper/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid4 = _errs16 === errors;
                            } else {
                              var valid4 = true;
                            }
                            if (valid4) {
                              if (data4.value !== void 0) {
                                let data6 = data4.value;
                                const _errs18 = errors;
                                if (errors === _errs18) {
                                  if (typeof data6 === "string") {
                                    if (func1(data6) > 128) {
                                      validate85.errors = [{ instancePath: instancePath + "/upper/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data6) < 1) {
                                        validate85.errors = [{ instancePath: instancePath + "/upper/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern72.test(data6)) {
                                          validate85.errors = [{ instancePath: instancePath + "/upper/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])" }, message: 'must match pattern "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate85.errors = [{ instancePath: instancePath + "/upper/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid4 = _errs18 === errors;
                              } else {
                                var valid4 = true;
                              }
                            }
                          }
                        }
                      } else {
                        validate85.errors = [{ instancePath: instancePath + "/upper", schemaPath: "#/$defs/MeasurementQuantity/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate85.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate85.errors = vErrors;
      return errors === 0;
    }
    validate85.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.kind === void 0 && (missing0 = "kind") || data.quantity === void 0 && (missing0 = "quantity") || data.uncertainty === void 0 && (missing0 = "uncertainty")) {
            validate84.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "kind" || key0 === "quantity" || key0 === "uncertainty")) {
                validate84.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.kind !== void 0) {
                let data0 = data.kind;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate84.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("numeric" !== data0) {
                  validate84.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "numeric" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.quantity !== void 0) {
                  let data1 = data.quantity;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.value === void 0 && (missing1 = "value") || data1.unit === void 0 && (missing1 = "unit")) {
                        validate84.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "unit" || key1 === "value")) {
                            validate84.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.unit !== void 0) {
                            let data2 = data1.unit;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 32) {
                                  validate84.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate84.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern67.test(data2)) {
                                      validate84.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate84.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.value !== void 0) {
                              let data3 = data1.value;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate84.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate84.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern72.test(data3)) {
                                        validate84.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])" }, message: 'must match pattern "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate84.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate84.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.uncertainty !== void 0) {
                    let data4 = data.uncertainty;
                    const _errs12 = errors;
                    const _errs13 = errors;
                    let valid3 = false;
                    const _errs14 = errors;
                    if (!validate85(data4, { instancePath: instancePath + "/uncertainty", parentData: data, parentDataProperty: "uncertainty", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate85.errors : vErrors.concat(validate85.errors);
                      errors = vErrors.length;
                    }
                    var _valid0 = _errs14 === errors;
                    valid3 = valid3 || _valid0;
                    const _errs15 = errors;
                    if (data4 !== null) {
                      const err0 = { instancePath: instancePath + "/uncertainty", schemaPath: "#/properties/uncertainty/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    }
                    var _valid0 = _errs15 === errors;
                    valid3 = valid3 || _valid0;
                    if (!valid3) {
                      const err1 = { instancePath: instancePath + "/uncertainty", schemaPath: "#/properties/uncertainty/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err1];
                      } else {
                        vErrors.push(err1);
                      }
                      errors++;
                      validate84.errors = vErrors;
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
          if (data.quantity === void 0 && (missing0 = "quantity") || data.inclusive === void 0 && (missing0 = "inclusive")) {
            validate89.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "inclusive" || key0 === "quantity")) {
                validate89.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.inclusive !== void 0) {
                const _errs2 = errors;
                if (typeof data.inclusive !== "boolean") {
                  validate89.errors = [{ instancePath: instancePath + "/inclusive", schemaPath: "#/properties/inclusive/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.quantity !== void 0) {
                  let data1 = data.quantity;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.value === void 0 && (missing1 = "value") || data1.unit === void 0 && (missing1 = "unit")) {
                        validate89.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "unit" || key1 === "value")) {
                            validate89.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.unit !== void 0) {
                            let data2 = data1.unit;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 32) {
                                  validate89.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate89.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern67.test(data2)) {
                                      validate89.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate89.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.value !== void 0) {
                              let data3 = data1.value;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate89.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate89.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern72.test(data3)) {
                                        validate89.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])" }, message: 'must match pattern "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate89.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate89.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate89.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate89.errors = vErrors;
      return errors === 0;
    }
    validate89.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate88(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate88.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.lower === void 0 && (missing0 = "lower") || data.upper === void 0 && (missing0 = "upper")) {
            validate88.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "kind" || key0 === "lower" || key0 === "upper")) {
                validate88.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.kind !== void 0) {
                let data0 = data.kind;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate88.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("censored" !== data0) {
                  validate88.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "censored" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.lower !== void 0) {
                  let data1 = data.lower;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  const _errs6 = errors;
                  if (!validate89(data1, { instancePath: instancePath + "/lower", parentData: data, parentDataProperty: "lower", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate89.errors : vErrors.concat(validate89.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs6 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs7 = errors;
                  if (data1 !== null) {
                    const err0 = { instancePath: instancePath + "/lower", schemaPath: "#/properties/lower/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err1 = { instancePath: instancePath + "/lower", schemaPath: "#/properties/lower/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                    validate88.errors = vErrors;
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
                  if (data.upper !== void 0) {
                    let data2 = data.upper;
                    const _errs9 = errors;
                    const _errs10 = errors;
                    let valid2 = false;
                    const _errs11 = errors;
                    if (!validate89(data2, { instancePath: instancePath + "/upper", parentData: data, parentDataProperty: "upper", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate89.errors : vErrors.concat(validate89.errors);
                      errors = vErrors.length;
                    }
                    var _valid1 = _errs11 === errors;
                    valid2 = valid2 || _valid1;
                    const _errs12 = errors;
                    if (data2 !== null) {
                      const err2 = { instancePath: instancePath + "/upper", schemaPath: "#/properties/upper/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err2];
                      } else {
                        vErrors.push(err2);
                      }
                      errors++;
                    }
                    var _valid1 = _errs12 === errors;
                    valid2 = valid2 || _valid1;
                    if (!valid2) {
                      const err3 = { instancePath: instancePath + "/upper", schemaPath: "#/properties/upper/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err3];
                      } else {
                        vErrors.push(err3);
                      }
                      errors++;
                      validate88.errors = vErrors;
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
                }
              }
            }
          }
        } else {
          validate88.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate88.errors = vErrors;
      return errors === 0;
    }
    validate88.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.reference === void 0 && (missing0 = "reference") || data.supersedes === void 0 && (missing0 = "supersedes") || data.source === void 0 && (missing0 = "source") || data.binding === void 0 && (missing0 = "binding") || data.quality === void 0 && (missing0 = "quality") || data.value === void 0 && (missing0 = "value") || data.context_link === void 0 && (missing0 = "context_link") || data.expectation === void 0 && (missing0 = "expectation")) {
            validate63.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "binding" || key0 === "context_link" || key0 === "expectation" || key0 === "quality" || key0 === "reference" || key0 === "source" || key0 === "supersedes" || key0 === "value")) {
                validate63.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.binding !== void 0) {
                const _errs2 = errors;
                if (!validate64(data.binding, { instancePath: instancePath + "/binding", parentData: data, parentDataProperty: "binding", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate64.errors : vErrors.concat(validate64.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.context_link !== void 0) {
                  let data1 = data.context_link;
                  const _errs3 = errors;
                  if (typeof data1 !== "string") {
                    validate63.errors = [{ instancePath: instancePath + "/context_link", schemaPath: "#/properties/context_link/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "declared_expectation" || data1 === "unbound" || data1 === "different_experiment" || data1 === "unknown_expectation")) {
                    validate63.errors = [{ instancePath: instancePath + "/context_link", schemaPath: "#/properties/context_link/enum", keyword: "enum", params: { allowedValues: schema72.properties.context_link.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.expectation !== void 0) {
                    let data2 = data.expectation;
                    const _errs5 = errors;
                    const _errs6 = errors;
                    let valid1 = false;
                    const _errs7 = errors;
                    if (!validate78(data2, { instancePath: instancePath + "/expectation", parentData: data, parentDataProperty: "expectation", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate78.errors : vErrors.concat(validate78.errors);
                      errors = vErrors.length;
                    }
                    var _valid0 = _errs7 === errors;
                    valid1 = valid1 || _valid0;
                    const _errs8 = errors;
                    if (data2 !== null) {
                      const err0 = { instancePath: instancePath + "/expectation", schemaPath: "#/properties/expectation/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                      const err1 = { instancePath: instancePath + "/expectation", schemaPath: "#/properties/expectation/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err1];
                      } else {
                        vErrors.push(err1);
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
                  if (valid0) {
                    if (data.quality !== void 0) {
                      let data3 = data.quality;
                      const _errs10 = errors;
                      const _errs11 = errors;
                      if (errors === _errs11) {
                        if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                          let missing1;
                          if (data3.controls === void 0 && (missing1 = "controls") || data3.flags === void 0 && (missing1 = "flags")) {
                            validate63.errors = [{ instancePath: instancePath + "/quality", schemaPath: "#/$defs/ObservationQuality/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                            return false;
                          } else {
                            const _errs13 = errors;
                            for (const key1 in data3) {
                              if (!(key1 === "controls" || key1 === "flags")) {
                                validate63.errors = [{ instancePath: instancePath + "/quality", schemaPath: "#/$defs/ObservationQuality/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs13 === errors) {
                              if (data3.controls !== void 0) {
                                let data4 = data3.controls;
                                const _errs14 = errors;
                                if (typeof data4 !== "string") {
                                  validate63.errors = [{ instancePath: instancePath + "/quality/controls", schemaPath: "#/$defs/ObservationQuality/properties/controls/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if (!(data4 === "passed" || data4 === "failed" || data4 === "unknown")) {
                                  validate63.errors = [{ instancePath: instancePath + "/quality/controls", schemaPath: "#/$defs/ObservationQuality/properties/controls/enum", keyword: "enum", params: { allowedValues: schema85.properties.controls.enum }, message: "must be equal to one of the allowed values" }];
                                  return false;
                                }
                                var valid3 = _errs14 === errors;
                              } else {
                                var valid3 = true;
                              }
                              if (valid3) {
                                if (data3.flags !== void 0) {
                                  let data5 = data3.flags;
                                  const _errs16 = errors;
                                  if (errors === _errs16) {
                                    if (Array.isArray(data5)) {
                                      if (data5.length > 64) {
                                        validate63.errors = [{ instancePath: instancePath + "/quality/flags", schemaPath: "#/$defs/ObservationQuality/properties/flags/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                                        return false;
                                      } else {
                                        var valid4 = true;
                                        const len0 = data5.length;
                                        for (let i0 = 0; i0 < len0; i0++) {
                                          let data6 = data5[i0];
                                          const _errs18 = errors;
                                          if (errors === _errs18) {
                                            if (typeof data6 === "string") {
                                              if (func1(data6) > 128) {
                                                validate63.errors = [{ instancePath: instancePath + "/quality/flags/" + i0, schemaPath: "#/$defs/ObservationQuality/properties/flags/items/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                return false;
                                              } else {
                                                if (func1(data6) < 1) {
                                                  validate63.errors = [{ instancePath: instancePath + "/quality/flags/" + i0, schemaPath: "#/$defs/ObservationQuality/properties/flags/items/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                  return false;
                                                } else {
                                                  if (!pattern4.test(data6)) {
                                                    validate63.errors = [{ instancePath: instancePath + "/quality/flags/" + i0, schemaPath: "#/$defs/ObservationQuality/properties/flags/items/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            } else {
                                              validate63.errors = [{ instancePath: instancePath + "/quality/flags/" + i0, schemaPath: "#/$defs/ObservationQuality/properties/flags/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid4 = _errs18 === errors;
                                          if (!valid4) {
                                            break;
                                          }
                                        }
                                      }
                                    } else {
                                      validate63.errors = [{ instancePath: instancePath + "/quality/flags", schemaPath: "#/$defs/ObservationQuality/properties/flags/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                      return false;
                                    }
                                  }
                                  var valid3 = _errs16 === errors;
                                } else {
                                  var valid3 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate63.errors = [{ instancePath: instancePath + "/quality", schemaPath: "#/$defs/ObservationQuality/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs10 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.reference !== void 0) {
                        const _errs20 = errors;
                        if (!validate60(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate60.errors : vErrors.concat(validate60.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs20 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.source !== void 0) {
                          const _errs21 = errors;
                          if (!validate53(data.source, { instancePath: instancePath + "/source", parentData: data, parentDataProperty: "source", rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate53.errors : vErrors.concat(validate53.errors);
                            errors = vErrors.length;
                          }
                          var valid0 = _errs21 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.supersedes !== void 0) {
                            let data9 = data.supersedes;
                            const _errs22 = errors;
                            const _errs23 = errors;
                            let valid5 = false;
                            const _errs24 = errors;
                            if (!validate60(data9, { instancePath: instancePath + "/supersedes", parentData: data, parentDataProperty: "supersedes", rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate60.errors : vErrors.concat(validate60.errors);
                              errors = vErrors.length;
                            }
                            var _valid1 = _errs24 === errors;
                            valid5 = valid5 || _valid1;
                            const _errs25 = errors;
                            if (data9 !== null) {
                              const err2 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                            }
                            var _valid1 = _errs25 === errors;
                            valid5 = valid5 || _valid1;
                            if (!valid5) {
                              const err3 = { instancePath: instancePath + "/supersedes", schemaPath: "#/properties/supersedes/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err3];
                              } else {
                                vErrors.push(err3);
                              }
                              errors++;
                              validate63.errors = vErrors;
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
                            var valid0 = _errs22 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.value !== void 0) {
                              let data10 = data.value;
                              const _errs27 = errors;
                              const _errs28 = errors;
                              let valid6 = false;
                              let passing0 = null;
                              const _errs29 = errors;
                              if (!validate84(data10, { instancePath: instancePath + "/value", parentData: data, parentDataProperty: "value", rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate84.errors : vErrors.concat(validate84.errors);
                                errors = vErrors.length;
                              }
                              var _valid2 = _errs29 === errors;
                              if (_valid2) {
                                valid6 = true;
                                passing0 = 0;
                                var props2 = true;
                              }
                              const _errs30 = errors;
                              if (!validate88(data10, { instancePath: instancePath + "/value", parentData: data, parentDataProperty: "value", rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate88.errors : vErrors.concat(validate88.errors);
                                errors = vErrors.length;
                              }
                              var _valid2 = _errs30 === errors;
                              if (_valid2 && valid6) {
                                valid6 = false;
                                passing0 = [passing0, 1];
                              } else {
                                if (_valid2) {
                                  valid6 = true;
                                  passing0 = 1;
                                  if (props2 !== true) {
                                    props2 = true;
                                  }
                                }
                                const _errs31 = errors;
                                const _errs32 = errors;
                                if (errors === _errs32) {
                                  if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                                    let missing2;
                                    if (data10.kind === void 0 && (missing2 = "kind") || data10.label === void 0 && (missing2 = "label")) {
                                      const err4 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/CategoricalMeasurement/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                                      if (vErrors === null) {
                                        vErrors = [err4];
                                      } else {
                                        vErrors.push(err4);
                                      }
                                      errors++;
                                    } else {
                                      const _errs34 = errors;
                                      for (const key2 in data10) {
                                        if (!(key2 === "kind" || key2 === "label")) {
                                          const err5 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/CategoricalMeasurement/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                                          if (vErrors === null) {
                                            vErrors = [err5];
                                          } else {
                                            vErrors.push(err5);
                                          }
                                          errors++;
                                          break;
                                        }
                                      }
                                      if (_errs34 === errors) {
                                        if (data10.kind !== void 0) {
                                          let data11 = data10.kind;
                                          const _errs35 = errors;
                                          if (typeof data11 !== "string") {
                                            const err6 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/CategoricalMeasurement/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                            if (vErrors === null) {
                                              vErrors = [err6];
                                            } else {
                                              vErrors.push(err6);
                                            }
                                            errors++;
                                          }
                                          if ("categorical" !== data11) {
                                            const err7 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/CategoricalMeasurement/properties/kind/const", keyword: "const", params: { allowedValue: "categorical" }, message: "must be equal to constant" };
                                            if (vErrors === null) {
                                              vErrors = [err7];
                                            } else {
                                              vErrors.push(err7);
                                            }
                                            errors++;
                                          }
                                          var valid8 = _errs35 === errors;
                                        } else {
                                          var valid8 = true;
                                        }
                                        if (valid8) {
                                          if (data10.label !== void 0) {
                                            let data12 = data10.label;
                                            const _errs37 = errors;
                                            if (errors === _errs37) {
                                              if (typeof data12 === "string") {
                                                if (func1(data12) > 256) {
                                                  const err8 = { instancePath: instancePath + "/value/label", schemaPath: "#/$defs/CategoricalMeasurement/properties/label/maxLength", keyword: "maxLength", params: { limit: 256 }, message: "must NOT have more than 256 characters" };
                                                  if (vErrors === null) {
                                                    vErrors = [err8];
                                                  } else {
                                                    vErrors.push(err8);
                                                  }
                                                  errors++;
                                                } else {
                                                  if (func1(data12) < 1) {
                                                    const err9 = { instancePath: instancePath + "/value/label", schemaPath: "#/$defs/CategoricalMeasurement/properties/label/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                    if (vErrors === null) {
                                                      vErrors = [err9];
                                                    } else {
                                                      vErrors.push(err9);
                                                    }
                                                    errors++;
                                                  }
                                                }
                                              } else {
                                                const err10 = { instancePath: instancePath + "/value/label", schemaPath: "#/$defs/CategoricalMeasurement/properties/label/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                if (vErrors === null) {
                                                  vErrors = [err10];
                                                } else {
                                                  vErrors.push(err10);
                                                }
                                                errors++;
                                              }
                                            }
                                            var valid8 = _errs37 === errors;
                                          } else {
                                            var valid8 = true;
                                          }
                                        }
                                      }
                                    }
                                  } else {
                                    const err11 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/CategoricalMeasurement/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                    if (vErrors === null) {
                                      vErrors = [err11];
                                    } else {
                                      vErrors.push(err11);
                                    }
                                    errors++;
                                  }
                                }
                                var _valid2 = _errs31 === errors;
                                if (_valid2 && valid6) {
                                  valid6 = false;
                                  passing0 = [passing0, 2];
                                } else {
                                  if (_valid2) {
                                    valid6 = true;
                                    passing0 = 2;
                                    if (props2 !== true) {
                                      props2 = true;
                                    }
                                  }
                                  const _errs39 = errors;
                                  const _errs40 = errors;
                                  if (errors === _errs40) {
                                    if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                                      let missing3;
                                      if (data10.kind === void 0 && (missing3 = "kind") || data10.reason === void 0 && (missing3 = "reason")) {
                                        const err12 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/MissingMeasurement/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" };
                                        if (vErrors === null) {
                                          vErrors = [err12];
                                        } else {
                                          vErrors.push(err12);
                                        }
                                        errors++;
                                      } else {
                                        const _errs42 = errors;
                                        for (const key3 in data10) {
                                          if (!(key3 === "kind" || key3 === "reason")) {
                                            const err13 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/MissingMeasurement/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" };
                                            if (vErrors === null) {
                                              vErrors = [err13];
                                            } else {
                                              vErrors.push(err13);
                                            }
                                            errors++;
                                            break;
                                          }
                                        }
                                        if (_errs42 === errors) {
                                          if (data10.kind !== void 0) {
                                            let data13 = data10.kind;
                                            const _errs43 = errors;
                                            if (typeof data13 !== "string") {
                                              const err14 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/MissingMeasurement/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                              if (vErrors === null) {
                                                vErrors = [err14];
                                              } else {
                                                vErrors.push(err14);
                                              }
                                              errors++;
                                            }
                                            if ("missing" !== data13) {
                                              const err15 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/MissingMeasurement/properties/kind/const", keyword: "const", params: { allowedValue: "missing" }, message: "must be equal to constant" };
                                              if (vErrors === null) {
                                                vErrors = [err15];
                                              } else {
                                                vErrors.push(err15);
                                              }
                                              errors++;
                                            }
                                            var valid10 = _errs43 === errors;
                                          } else {
                                            var valid10 = true;
                                          }
                                          if (valid10) {
                                            if (data10.reason !== void 0) {
                                              let data14 = data10.reason;
                                              const _errs45 = errors;
                                              if (errors === _errs45) {
                                                if (typeof data14 === "string") {
                                                  if (func1(data14) > 128) {
                                                    const err16 = { instancePath: instancePath + "/value/reason", schemaPath: "#/$defs/MissingMeasurement/properties/reason/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                                    if (vErrors === null) {
                                                      vErrors = [err16];
                                                    } else {
                                                      vErrors.push(err16);
                                                    }
                                                    errors++;
                                                  } else {
                                                    if (func1(data14) < 1) {
                                                      const err17 = { instancePath: instancePath + "/value/reason", schemaPath: "#/$defs/MissingMeasurement/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                      if (vErrors === null) {
                                                        vErrors = [err17];
                                                      } else {
                                                        vErrors.push(err17);
                                                      }
                                                      errors++;
                                                    } else {
                                                      if (!pattern4.test(data14)) {
                                                        const err18 = { instancePath: instancePath + "/value/reason", schemaPath: "#/$defs/MissingMeasurement/properties/reason/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                                        if (vErrors === null) {
                                                          vErrors = [err18];
                                                        } else {
                                                          vErrors.push(err18);
                                                        }
                                                        errors++;
                                                      }
                                                    }
                                                  }
                                                } else {
                                                  const err19 = { instancePath: instancePath + "/value/reason", schemaPath: "#/$defs/MissingMeasurement/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                  if (vErrors === null) {
                                                    vErrors = [err19];
                                                  } else {
                                                    vErrors.push(err19);
                                                  }
                                                  errors++;
                                                }
                                              }
                                              var valid10 = _errs45 === errors;
                                            } else {
                                              var valid10 = true;
                                            }
                                          }
                                        }
                                      }
                                    } else {
                                      const err20 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/MissingMeasurement/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                      if (vErrors === null) {
                                        vErrors = [err20];
                                      } else {
                                        vErrors.push(err20);
                                      }
                                      errors++;
                                    }
                                  }
                                  var _valid2 = _errs39 === errors;
                                  if (_valid2 && valid6) {
                                    valid6 = false;
                                    passing0 = [passing0, 3];
                                  } else {
                                    if (_valid2) {
                                      valid6 = true;
                                      passing0 = 3;
                                      if (props2 !== true) {
                                        props2 = true;
                                      }
                                    }
                                    const _errs47 = errors;
                                    const _errs48 = errors;
                                    if (errors === _errs48) {
                                      if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                                        let missing4;
                                        if (data10.kind === void 0 && (missing4 = "kind") || data10.x_unit === void 0 && (missing4 = "x_unit") || data10.y_unit === void 0 && (missing4 = "y_unit") || data10.point_count === void 0 && (missing4 = "point_count")) {
                                          const err21 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/SeriesDescriptor/required", keyword: "required", params: { missingProperty: missing4 }, message: "must have required property '" + missing4 + "'" };
                                          if (vErrors === null) {
                                            vErrors = [err21];
                                          } else {
                                            vErrors.push(err21);
                                          }
                                          errors++;
                                        } else {
                                          const _errs50 = errors;
                                          for (const key4 in data10) {
                                            if (!(key4 === "kind" || key4 === "point_count" || key4 === "x_unit" || key4 === "y_unit")) {
                                              const err22 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/SeriesDescriptor/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key4 }, message: "must NOT have additional properties" };
                                              if (vErrors === null) {
                                                vErrors = [err22];
                                              } else {
                                                vErrors.push(err22);
                                              }
                                              errors++;
                                              break;
                                            }
                                          }
                                          if (_errs50 === errors) {
                                            if (data10.kind !== void 0) {
                                              let data15 = data10.kind;
                                              const _errs51 = errors;
                                              if (typeof data15 !== "string") {
                                                const err23 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/SeriesDescriptor/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                if (vErrors === null) {
                                                  vErrors = [err23];
                                                } else {
                                                  vErrors.push(err23);
                                                }
                                                errors++;
                                              }
                                              if ("series" !== data15) {
                                                const err24 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/SeriesDescriptor/properties/kind/const", keyword: "const", params: { allowedValue: "series" }, message: "must be equal to constant" };
                                                if (vErrors === null) {
                                                  vErrors = [err24];
                                                } else {
                                                  vErrors.push(err24);
                                                }
                                                errors++;
                                              }
                                              var valid12 = _errs51 === errors;
                                            } else {
                                              var valid12 = true;
                                            }
                                            if (valid12) {
                                              if (data10.point_count !== void 0) {
                                                let data16 = data10.point_count;
                                                const _errs53 = errors;
                                                if (!(typeof data16 == "number" && (!(data16 % 1) && !isNaN(data16)) && isFinite(data16))) {
                                                  const err25 = { instancePath: instancePath + "/value/point_count", schemaPath: "#/$defs/SeriesDescriptor/properties/point_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                                  if (vErrors === null) {
                                                    vErrors = [err25];
                                                  } else {
                                                    vErrors.push(err25);
                                                  }
                                                  errors++;
                                                }
                                                if (errors === _errs53) {
                                                  if (typeof data16 == "number" && isFinite(data16)) {
                                                    if (data16 > 4096 || isNaN(data16)) {
                                                      const err26 = { instancePath: instancePath + "/value/point_count", schemaPath: "#/$defs/SeriesDescriptor/properties/point_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                                      if (vErrors === null) {
                                                        vErrors = [err26];
                                                      } else {
                                                        vErrors.push(err26);
                                                      }
                                                      errors++;
                                                    } else {
                                                      if (data16 < 1 || isNaN(data16)) {
                                                        const err27 = { instancePath: instancePath + "/value/point_count", schemaPath: "#/$defs/SeriesDescriptor/properties/point_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" };
                                                        if (vErrors === null) {
                                                          vErrors = [err27];
                                                        } else {
                                                          vErrors.push(err27);
                                                        }
                                                        errors++;
                                                      }
                                                    }
                                                  }
                                                }
                                                var valid12 = _errs53 === errors;
                                              } else {
                                                var valid12 = true;
                                              }
                                              if (valid12) {
                                                if (data10.x_unit !== void 0) {
                                                  let data17 = data10.x_unit;
                                                  const _errs55 = errors;
                                                  if (errors === _errs55) {
                                                    if (typeof data17 === "string") {
                                                      if (func1(data17) > 32) {
                                                        const err28 = { instancePath: instancePath + "/value/x_unit", schemaPath: "#/$defs/SeriesDescriptor/properties/x_unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" };
                                                        if (vErrors === null) {
                                                          vErrors = [err28];
                                                        } else {
                                                          vErrors.push(err28);
                                                        }
                                                        errors++;
                                                      } else {
                                                        if (func1(data17) < 1) {
                                                          const err29 = { instancePath: instancePath + "/value/x_unit", schemaPath: "#/$defs/SeriesDescriptor/properties/x_unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                          if (vErrors === null) {
                                                            vErrors = [err29];
                                                          } else {
                                                            vErrors.push(err29);
                                                          }
                                                          errors++;
                                                        } else {
                                                          if (!pattern67.test(data17)) {
                                                            const err30 = { instancePath: instancePath + "/value/x_unit", schemaPath: "#/$defs/SeriesDescriptor/properties/x_unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' };
                                                            if (vErrors === null) {
                                                              vErrors = [err30];
                                                            } else {
                                                              vErrors.push(err30);
                                                            }
                                                            errors++;
                                                          }
                                                        }
                                                      }
                                                    } else {
                                                      const err31 = { instancePath: instancePath + "/value/x_unit", schemaPath: "#/$defs/SeriesDescriptor/properties/x_unit/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                      if (vErrors === null) {
                                                        vErrors = [err31];
                                                      } else {
                                                        vErrors.push(err31);
                                                      }
                                                      errors++;
                                                    }
                                                  }
                                                  var valid12 = _errs55 === errors;
                                                } else {
                                                  var valid12 = true;
                                                }
                                                if (valid12) {
                                                  if (data10.y_unit !== void 0) {
                                                    let data18 = data10.y_unit;
                                                    const _errs57 = errors;
                                                    if (errors === _errs57) {
                                                      if (typeof data18 === "string") {
                                                        if (func1(data18) > 32) {
                                                          const err32 = { instancePath: instancePath + "/value/y_unit", schemaPath: "#/$defs/SeriesDescriptor/properties/y_unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" };
                                                          if (vErrors === null) {
                                                            vErrors = [err32];
                                                          } else {
                                                            vErrors.push(err32);
                                                          }
                                                          errors++;
                                                        } else {
                                                          if (func1(data18) < 1) {
                                                            const err33 = { instancePath: instancePath + "/value/y_unit", schemaPath: "#/$defs/SeriesDescriptor/properties/y_unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                            if (vErrors === null) {
                                                              vErrors = [err33];
                                                            } else {
                                                              vErrors.push(err33);
                                                            }
                                                            errors++;
                                                          } else {
                                                            if (!pattern67.test(data18)) {
                                                              const err34 = { instancePath: instancePath + "/value/y_unit", schemaPath: "#/$defs/SeriesDescriptor/properties/y_unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' };
                                                              if (vErrors === null) {
                                                                vErrors = [err34];
                                                              } else {
                                                                vErrors.push(err34);
                                                              }
                                                              errors++;
                                                            }
                                                          }
                                                        }
                                                      } else {
                                                        const err35 = { instancePath: instancePath + "/value/y_unit", schemaPath: "#/$defs/SeriesDescriptor/properties/y_unit/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                        if (vErrors === null) {
                                                          vErrors = [err35];
                                                        } else {
                                                          vErrors.push(err35);
                                                        }
                                                        errors++;
                                                      }
                                                    }
                                                    var valid12 = _errs57 === errors;
                                                  } else {
                                                    var valid12 = true;
                                                  }
                                                }
                                              }
                                            }
                                          }
                                        }
                                      } else {
                                        const err36 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/SeriesDescriptor/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                        if (vErrors === null) {
                                          vErrors = [err36];
                                        } else {
                                          vErrors.push(err36);
                                        }
                                        errors++;
                                      }
                                    }
                                    var _valid2 = _errs47 === errors;
                                    if (_valid2 && valid6) {
                                      valid6 = false;
                                      passing0 = [passing0, 4];
                                    } else {
                                      if (_valid2) {
                                        valid6 = true;
                                        passing0 = 4;
                                        if (props2 !== true) {
                                          props2 = true;
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                              if (!valid6) {
                                const err37 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                                if (vErrors === null) {
                                  vErrors = [err37];
                                } else {
                                  vErrors.push(err37);
                                }
                                errors++;
                                validate63.errors = vErrors;
                                return false;
                              } else {
                                errors = _errs28;
                                if (vErrors !== null) {
                                  if (_errs28) {
                                    vErrors.length = _errs28;
                                  } else {
                                    vErrors = null;
                                  }
                                }
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
    function validate51(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate51.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.request === void 0 && (missing0 = "request") || data.query_sha256 === void 0 && (missing0 = "query_sha256") || data.total === void 0 && (missing0 = "total") || data.protocol === void 0 && (missing0 = "protocol") || data.authority === void 0 && (missing0 = "authority") || data.selection_scope === void 0 && (missing0 = "selection_scope") || data.rows === void 0 && (missing0 = "rows") || data.next_position === void 0 && (missing0 = "next_position")) {
            validate51.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func53.call(schema59.properties, key0)) {
                validate51.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.authority !== void 0) {
                let data0 = data.authority;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate51.errors = [{ instancePath: instancePath + "/authority", schemaPath: "#/properties/authority/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("reported_evidence_only" !== data0) {
                  validate51.errors = [{ instancePath: instancePath + "/authority", schemaPath: "#/properties/authority/const", keyword: "const", params: { allowedValue: "reported_evidence_only" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.next_position !== void 0) {
                  let data1 = data.next_position;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  const _errs6 = errors;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.query_sha256 === void 0 && (missing1 = "query_sha256") || data1.offset === void 0 && (missing1 = "offset")) {
                        const err0 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/ResearchViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        const _errs9 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "offset" || key1 === "query_sha256")) {
                            const err1 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/ResearchViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                            if (vErrors === null) {
                              vErrors = [err1];
                            } else {
                              vErrors.push(err1);
                            }
                            errors++;
                            break;
                          }
                        }
                        if (_errs9 === errors) {
                          if (data1.offset !== void 0) {
                            let data2 = data1.offset;
                            const _errs10 = errors;
                            if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                              const err2 = { instancePath: instancePath + "/next_position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                            }
                            if (errors === _errs10) {
                              if (typeof data2 == "number" && isFinite(data2)) {
                                if (data2 > 4096 || isNaN(data2)) {
                                  const err3 = { instancePath: instancePath + "/next_position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                  if (vErrors === null) {
                                    vErrors = [err3];
                                  } else {
                                    vErrors.push(err3);
                                  }
                                  errors++;
                                } else {
                                  if (data2 < 0 || isNaN(data2)) {
                                    const err4 = { instancePath: instancePath + "/next_position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                            var valid3 = _errs10 === errors;
                          } else {
                            var valid3 = true;
                          }
                          if (valid3) {
                            if (data1.query_sha256 !== void 0) {
                              let data3 = data1.query_sha256;
                              const _errs12 = errors;
                              if (errors === _errs12) {
                                if (typeof data3 === "string") {
                                  if (!pattern7.test(data3)) {
                                    const err5 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                    if (vErrors === null) {
                                      vErrors = [err5];
                                    } else {
                                      vErrors.push(err5);
                                    }
                                    errors++;
                                  }
                                } else {
                                  const err6 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err6];
                                  } else {
                                    vErrors.push(err6);
                                  }
                                  errors++;
                                }
                              }
                              var valid3 = _errs12 === errors;
                            } else {
                              var valid3 = true;
                            }
                          }
                        }
                      }
                    } else {
                      const err7 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/ResearchViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err7];
                      } else {
                        vErrors.push(err7);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs6 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs14 = errors;
                  if (data1 !== null) {
                    const err8 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err8];
                    } else {
                      vErrors.push(err8);
                    }
                    errors++;
                  }
                  var _valid0 = _errs14 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err9 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err9];
                    } else {
                      vErrors.push(err9);
                    }
                    errors++;
                    validate51.errors = vErrors;
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
                  if (data.protocol !== void 0) {
                    const _errs16 = errors;
                    if (!validate52(data.protocol, { instancePath: instancePath + "/protocol", parentData: data, parentDataProperty: "protocol", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate52.errors : vErrors.concat(validate52.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs16 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.query_sha256 !== void 0) {
                      let data5 = data.query_sha256;
                      const _errs17 = errors;
                      if (errors === _errs17) {
                        if (typeof data5 === "string") {
                          if (!pattern7.test(data5)) {
                            validate51.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                            return false;
                          }
                        } else {
                          validate51.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs17 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.request !== void 0) {
                        const _errs19 = errors;
                        if (!validate57(data.request, { instancePath: instancePath + "/request", parentData: data, parentDataProperty: "request", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate57.errors : vErrors.concat(validate57.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs19 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.rows !== void 0) {
                          let data7 = data.rows;
                          const _errs20 = errors;
                          if (errors === _errs20) {
                            if (Array.isArray(data7)) {
                              if (data7.length > 16) {
                                validate51.errors = [{ instancePath: instancePath + "/rows", schemaPath: "#/properties/rows/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                                return false;
                              } else {
                                var valid4 = true;
                                const len0 = data7.length;
                                for (let i0 = 0; i0 < len0; i0++) {
                                  const _errs22 = errors;
                                  if (!validate63(data7[i0], { instancePath: instancePath + "/rows/" + i0, parentData: data7, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                    vErrors = vErrors === null ? validate63.errors : vErrors.concat(validate63.errors);
                                    errors = vErrors.length;
                                  }
                                  var valid4 = _errs22 === errors;
                                  if (!valid4) {
                                    break;
                                  }
                                }
                              }
                            } else {
                              validate51.errors = [{ instancePath: instancePath + "/rows", schemaPath: "#/properties/rows/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs20 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.selection_scope !== void 0) {
                            let data9 = data.selection_scope;
                            const _errs23 = errors;
                            if (typeof data9 !== "string") {
                              validate51.errors = [{ instancePath: instancePath + "/selection_scope", schemaPath: "#/properties/selection_scope/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("explicit_observation_revisions" !== data9) {
                              validate51.errors = [{ instancePath: instancePath + "/selection_scope", schemaPath: "#/properties/selection_scope/const", keyword: "const", params: { allowedValue: "explicit_observation_revisions" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs23 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.total !== void 0) {
                              let data10 = data.total;
                              const _errs25 = errors;
                              if (!(typeof data10 == "number" && (!(data10 % 1) && !isNaN(data10)) && isFinite(data10))) {
                                validate51.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (errors === _errs25) {
                                if (typeof data10 == "number" && isFinite(data10)) {
                                  if (data10 > 128 || isNaN(data10)) {
                                    validate51.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 128 }, message: "must be <= 128" }];
                                    return false;
                                  } else {
                                    if (data10 < 1 || isNaN(data10)) {
                                      validate51.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                      return false;
                                    }
                                  }
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
                                  validate51.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("1" !== data11) {
                                  validate51.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
            }
          }
        } else {
          validate51.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate51.errors = vErrors;
      return errors === 0;
    }
    validate51.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.series_request = validate94;
    function validate95(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate95.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.observation_id === void 0 && (missing0 = "observation_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate95.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "observation_id" || key0 === "revision" || key0 === "scope")) {
                validate95.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.observation_id !== void 0) {
                let data0 = data.observation_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate95.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate95.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate95.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate95.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate95.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate95.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate95.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate95.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate95.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate95.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate95.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate95.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate95.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate95.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate95.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate95.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate95.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate95.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate95.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate95.errors = vErrors;
      return errors === 0;
    }
    validate95.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate94(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate94.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.observation === void 0 && (missing0 = "observation")) {
            validate94.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "limit" || key0 === "observation" || key0 === "position" || key0 === "wire_version")) {
                validate94.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.limit !== void 0) {
                let data0 = data.limit;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate94.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 256 || isNaN(data0)) {
                      validate94.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 256 }, message: "must be <= 256" }];
                      return false;
                    } else {
                      if (data0 < 1 || isNaN(data0)) {
                        validate94.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                if (data.observation !== void 0) {
                  const _errs4 = errors;
                  if (!validate95(data.observation, { instancePath: instancePath + "/observation", parentData: data, parentDataProperty: "observation", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate95.errors : vErrors.concat(validate95.errors);
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
                    const _errs6 = errors;
                    let valid1 = false;
                    const _errs7 = errors;
                    const _errs8 = errors;
                    if (errors === _errs8) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.query_sha256 === void 0 && (missing1 = "query_sha256") || data2.offset === void 0 && (missing1 = "offset")) {
                          const err0 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        } else {
                          const _errs10 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "offset" || key1 === "query_sha256")) {
                              const err1 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                            if (data2.offset !== void 0) {
                              let data3 = data2.offset;
                              const _errs11 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                const err2 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              }
                              if (errors === _errs11) {
                                if (typeof data3 == "number" && isFinite(data3)) {
                                  if (data3 > 4096 || isNaN(data3)) {
                                    const err3 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                    if (vErrors === null) {
                                      vErrors = [err3];
                                    } else {
                                      vErrors.push(err3);
                                    }
                                    errors++;
                                  } else {
                                    if (data3 < 0 || isNaN(data3)) {
                                      const err4 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                              var valid3 = _errs11 === errors;
                            } else {
                              var valid3 = true;
                            }
                            if (valid3) {
                              if (data2.query_sha256 !== void 0) {
                                let data4 = data2.query_sha256;
                                const _errs13 = errors;
                                if (errors === _errs13) {
                                  if (typeof data4 === "string") {
                                    if (!pattern7.test(data4)) {
                                      const err5 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                    }
                                  } else {
                                    const err6 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err6];
                                    } else {
                                      vErrors.push(err6);
                                    }
                                    errors++;
                                  }
                                }
                                var valid3 = _errs13 === errors;
                              } else {
                                var valid3 = true;
                              }
                            }
                          }
                        }
                      } else {
                        const err7 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs7 === errors;
                    valid1 = valid1 || _valid0;
                    const _errs15 = errors;
                    if (data2 !== null) {
                      const err8 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err8];
                      } else {
                        vErrors.push(err8);
                      }
                      errors++;
                    }
                    var _valid0 = _errs15 === errors;
                    valid1 = valid1 || _valid0;
                    if (!valid1) {
                      const err9 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err9];
                      } else {
                        vErrors.push(err9);
                      }
                      errors++;
                      validate94.errors = vErrors;
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
                    if (data.wire_version !== void 0) {
                      let data5 = data.wire_version;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        validate94.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data5) {
                        validate94.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs17 === errors;
                    } else {
                      var valid0 = true;
                    }
                  }
                }
              }
            }
          }
        } else {
          validate94.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate94.errors = vErrors;
      return errors === 0;
    }
    validate94.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.series_page = validate97;
    var schema101 = { "$defs": { "ArtifactRef": { "additionalProperties": false, "properties": { "artifact_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Artifact Id", "type": "string" }, "media_type": { "maxLength": 128, "minLength": 3, "pattern": "^[^\\s/]+/[^\\s/]+$", "title": "Media Type", "type": "string" }, "schema_ref": { "$ref": "#/$defs/SchemaRef" }, "scope": { "$ref": "#/$defs/Scope" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "size_bytes": { "maximum": 9007199254740991, "minimum": 0, "title": "Size Bytes", "type": "integer" } }, "required": ["artifact_id", "scope", "sha256", "media_type", "schema_ref", "size_bytes"], "title": "ArtifactRef", "type": "object" }, "CensorBound": { "additionalProperties": false, "properties": { "inclusive": { "title": "Inclusive", "type": "boolean" }, "quantity": { "$ref": "#/$defs/MeasurementQuantity" } }, "required": ["quantity", "inclusive"], "title": "CensorBound", "type": "object" }, "CensoredMeasurement": { "additionalProperties": false, "properties": { "kind": { "const": "censored", "title": "Kind", "type": "string" }, "lower": { "anyOf": [{ "$ref": "#/$defs/CensorBound" }, { "type": "null" }] }, "upper": { "anyOf": [{ "$ref": "#/$defs/CensorBound" }, { "type": "null" }] } }, "required": ["kind", "lower", "upper"], "title": "CensoredMeasurement", "type": "object" }, "ExperimentRevisionRef": { "additionalProperties": false, "properties": { "experiment_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Experiment Id", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "experiment_id", "revision"], "title": "ExperimentRevisionRef", "type": "object" }, "MaterialStateRevisionRef": { "additionalProperties": false, "properties": { "material_state_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Material State Id", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "material_state_id", "revision"], "title": "MaterialStateRevisionRef", "type": "object" }, "MeasurementInterval": { "additionalProperties": false, "properties": { "description": { "maxLength": 512, "minLength": 1, "title": "Description", "type": "string" }, "lower": { "$ref": "#/$defs/MeasurementQuantity" }, "upper": { "$ref": "#/$defs/MeasurementQuantity" } }, "required": ["lower", "upper", "description"], "title": "MeasurementInterval", "type": "object" }, "MeasurementQuantity": { "additionalProperties": false, "properties": { "unit": { "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "title": "Unit", "type": "string" }, "value": { "maxLength": 128, "minLength": 1, "pattern": "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])", "title": "Value", "type": "string" } }, "required": ["value", "unit"], "title": "MeasurementQuantity", "type": "object" }, "MissingMeasurement": { "additionalProperties": false, "properties": { "kind": { "const": "missing", "title": "Kind", "type": "string" }, "reason": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Reason", "type": "string" } }, "required": ["kind", "reason"], "title": "MissingMeasurement", "type": "object" }, "NumericMeasurement": { "additionalProperties": false, "properties": { "kind": { "const": "numeric", "title": "Kind", "type": "string" }, "quantity": { "$ref": "#/$defs/MeasurementQuantity" }, "uncertainty": { "anyOf": [{ "$ref": "#/$defs/MeasurementInterval" }, { "type": "null" }] } }, "required": ["kind", "quantity", "uncertainty"], "title": "NumericMeasurement", "type": "object" }, "ObservationBindingRecord": { "additionalProperties": false, "properties": { "measurement": { "$ref": "#/$defs/ObservationMethod" }, "role": { "anyOf": [{ "enum": ["sample", "positive_control", "negative_control", "blank"], "type": "string" }, { "type": "null" }], "title": "Role" }, "specimen": { "$ref": "#/$defs/ObservationSpecimen" }, "target": { "$ref": "#/$defs/ObservationTarget" } }, "required": ["target", "specimen", "measurement", "role"], "title": "ObservationBindingRecord", "type": "object" }, "ObservationMethod": { "additionalProperties": false, "properties": { "context": { "anyOf": [{ "$ref": "#/$defs/ArtifactRef" }, { "type": "null" }] }, "method": { "anyOf": [{ "$ref": "#/$defs/SchemaRef" }, { "type": "null" }] } }, "required": ["method", "context"], "title": "ObservationMethod", "type": "object" }, "ObservationQuality": { "additionalProperties": false, "properties": { "controls": { "enum": ["passed", "failed", "unknown"], "title": "Controls", "type": "string" }, "flags": { "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 64, "title": "Flags", "type": "array" } }, "required": ["controls", "flags"], "title": "ObservationQuality", "type": "object" }, "ObservationRevisionRef": { "additionalProperties": false, "properties": { "observation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Observation Id", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "observation_id", "revision"], "title": "ObservationRevisionRef", "type": "object" }, "ObservationSeriesRequest": { "additionalProperties": false, "properties": { "limit": { "default": 256, "maximum": 256, "minimum": 1, "title": "Limit", "type": "integer" }, "observation": { "$ref": "#/$defs/ObservationRevisionRef" }, "position": { "anyOf": [{ "$ref": "#/$defs/ResearchViewPosition" }, { "type": "null" }], "default": null }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" } }, "required": ["wire_version", "observation"], "title": "ObservationSeriesRequest", "type": "object" }, "ObservationSpecimen": { "additionalProperties": false, "properties": { "material_state": { "anyOf": [{ "$ref": "#/$defs/MaterialStateRevisionRef" }, { "type": "null" }] }, "sample": { "anyOf": [{ "$ref": "#/$defs/SampleRevisionRef" }, { "type": "null" }] } }, "required": ["sample", "material_state"], "title": "ObservationSpecimen", "type": "object" }, "ObservationTarget": { "additionalProperties": false, "properties": { "expectation_id": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Expectation Id" }, "experiment": { "anyOf": [{ "$ref": "#/$defs/ExperimentRevisionRef" }, { "type": "null" }] }, "replicate_id": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Replicate Id" } }, "required": ["experiment", "expectation_id", "replicate_id"], "title": "ObservationTarget", "type": "object" }, "ResearchViewPosition": { "additionalProperties": false, "properties": { "offset": { "maximum": 4096, "minimum": 0, "title": "Offset", "type": "integer" }, "query_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Query Sha256", "type": "string" } }, "required": ["query_sha256", "offset"], "title": "ResearchViewPosition", "type": "object" }, "SampleRevisionRef": { "additionalProperties": false, "properties": { "revision": { "maximum": 9007199254740991, "minimum": 1, "title": "Revision", "type": "integer" }, "sample_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Sample Id", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "sample_id", "revision"], "title": "SampleRevisionRef", "type": "object" }, "SchemaRef": { "additionalProperties": false, "properties": { "schema_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Schema Id", "type": "string" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "version": { "const": "1", "title": "Version", "type": "string" } }, "required": ["schema_id", "version", "sha256"], "title": "SchemaRef", "type": "object" }, "Scope": { "additionalProperties": false, "properties": { "project_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Project Id", "type": "string" }, "tenant_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Tenant Id", "type": "string" } }, "required": ["tenant_id", "project_id"], "title": "Scope", "type": "object" }, "SeriesMeasurementPoint": { "additionalProperties": false, "properties": { "x": { "$ref": "#/$defs/MeasurementQuantity" }, "y": { "discriminator": { "mapping": { "censored": "#/$defs/CensoredMeasurement", "missing": "#/$defs/MissingMeasurement", "numeric": "#/$defs/NumericMeasurement" }, "propertyName": "kind" }, "oneOf": [{ "$ref": "#/$defs/NumericMeasurement" }, { "$ref": "#/$defs/CensoredMeasurement" }, { "$ref": "#/$defs/MissingMeasurement" }], "title": "Y" } }, "required": ["x", "y"], "title": "SeriesMeasurementPoint", "type": "object" } }, "$id": "urn:amphora:research-views.observation-series-page:1:serialization", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": { "binding": { "$ref": "#/$defs/ObservationBindingRecord" }, "next_position": { "anyOf": [{ "$ref": "#/$defs/ResearchViewPosition" }, { "type": "null" }] }, "points": { "items": { "$ref": "#/$defs/SeriesMeasurementPoint" }, "maxItems": 256, "title": "Points", "type": "array" }, "quality": { "$ref": "#/$defs/ObservationQuality" }, "query_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Query Sha256", "type": "string" }, "request": { "$ref": "#/$defs/ObservationSeriesRequest" }, "source": { "$ref": "#/$defs/ArtifactRef" }, "total": { "maximum": 4096, "minimum": 1, "title": "Total", "type": "integer" }, "wire_version": { "const": "1", "title": "Wire Version", "type": "string" }, "x_unit": { "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "title": "X Unit", "type": "string" }, "y_unit": { "maxLength": 32, "minLength": 1, "pattern": "^\\S+$(?![\\s\\S])", "title": "Y Unit", "type": "string" } }, "required": ["wire_version", "request", "query_sha256", "total", "x_unit", "y_unit", "source", "binding", "quality", "points", "next_position"], "title": "ObservationSeriesPage", "type": "object" };
    var schema128 = { "additionalProperties": false, "properties": { "controls": { "enum": ["passed", "failed", "unknown"], "title": "Controls", "type": "string" }, "flags": { "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 64, "title": "Flags", "type": "array" } }, "required": ["controls", "flags"], "title": "ObservationQuality", "type": "object" };
    var schema102 = { "additionalProperties": false, "properties": { "measurement": { "$ref": "#/$defs/ObservationMethod" }, "role": { "anyOf": [{ "enum": ["sample", "positive_control", "negative_control", "blank"], "type": "string" }, { "type": "null" }], "title": "Role" }, "specimen": { "$ref": "#/$defs/ObservationSpecimen" }, "target": { "$ref": "#/$defs/ObservationTarget" } }, "required": ["target", "specimen", "measurement", "role"], "title": "ObservationBindingRecord", "type": "object" };
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate100.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate100.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate100.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate100.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate100.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate100.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate100.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate100.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern21.test(data1)) {
                            validate100.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate100.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate100.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate100.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate100.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate100.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate100.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate100.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    if (!pattern7.test(data4)) {
                                      validate100.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate100.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate100.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate100.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate100.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate100.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate100.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate100.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate100.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
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
                                        validate100.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate100.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
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
                                  var valid4 = _errs22 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate100.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            if (!pattern7.test(data9)) {
                              validate100.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate100.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate100.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate100.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate100.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate100.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate100.errors = vErrors;
      return errors === 0;
    }
    validate100.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.method === void 0 && (missing0 = "method") || data.context === void 0 && (missing0 = "context")) {
            validate99.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "context" || key0 === "method")) {
                validate99.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.context !== void 0) {
                let data0 = data.context;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate100(data0, { instancePath: instancePath + "/context", parentData: data, parentDataProperty: "context", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate100.errors : vErrors.concat(validate100.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/context", schemaPath: "#/properties/context/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err1 = { instancePath: instancePath + "/context", schemaPath: "#/properties/context/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate99.errors = vErrors;
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
                if (data.method !== void 0) {
                  let data1 = data.method;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid2 = false;
                  const _errs9 = errors;
                  const _errs10 = errors;
                  if (errors === _errs10) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.schema_id === void 0 && (missing1 = "schema_id") || data1.version === void 0 && (missing1 = "version") || data1.sha256 === void 0 && (missing1 = "sha256")) {
                        const err2 = { instancePath: instancePath + "/method", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                      } else {
                        const _errs12 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                            const err3 = { instancePath: instancePath + "/method", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                            if (vErrors === null) {
                              vErrors = [err3];
                            } else {
                              vErrors.push(err3);
                            }
                            errors++;
                            break;
                          }
                        }
                        if (_errs12 === errors) {
                          if (data1.schema_id !== void 0) {
                            let data2 = data1.schema_id;
                            const _errs13 = errors;
                            if (errors === _errs13) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  const err4 = { instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                  if (vErrors === null) {
                                    vErrors = [err4];
                                  } else {
                                    vErrors.push(err4);
                                  }
                                  errors++;
                                } else {
                                  if (func1(data2) < 1) {
                                    const err5 = { instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                    if (vErrors === null) {
                                      vErrors = [err5];
                                    } else {
                                      vErrors.push(err5);
                                    }
                                    errors++;
                                  } else {
                                    if (!pattern4.test(data2)) {
                                      const err6 = { instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                const err7 = { instancePath: instancePath + "/method/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err7];
                                } else {
                                  vErrors.push(err7);
                                }
                                errors++;
                              }
                            }
                            var valid4 = _errs13 === errors;
                          } else {
                            var valid4 = true;
                          }
                          if (valid4) {
                            if (data1.sha256 !== void 0) {
                              let data3 = data1.sha256;
                              const _errs15 = errors;
                              if (errors === _errs15) {
                                if (typeof data3 === "string") {
                                  if (!pattern7.test(data3)) {
                                    const err8 = { instancePath: instancePath + "/method/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                    if (vErrors === null) {
                                      vErrors = [err8];
                                    } else {
                                      vErrors.push(err8);
                                    }
                                    errors++;
                                  }
                                } else {
                                  const err9 = { instancePath: instancePath + "/method/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                            if (valid4) {
                              if (data1.version !== void 0) {
                                let data4 = data1.version;
                                const _errs17 = errors;
                                if (typeof data4 !== "string") {
                                  const err10 = { instancePath: instancePath + "/method/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err10];
                                  } else {
                                    vErrors.push(err10);
                                  }
                                  errors++;
                                }
                                if ("1" !== data4) {
                                  const err11 = { instancePath: instancePath + "/method/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" };
                                  if (vErrors === null) {
                                    vErrors = [err11];
                                  } else {
                                    vErrors.push(err11);
                                  }
                                  errors++;
                                }
                                var valid4 = _errs17 === errors;
                              } else {
                                var valid4 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      const err12 = { instancePath: instancePath + "/method", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err12];
                      } else {
                        vErrors.push(err12);
                      }
                      errors++;
                    }
                  }
                  var _valid1 = _errs9 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs19 = errors;
                  if (data1 !== null) {
                    const err13 = { instancePath: instancePath + "/method", schemaPath: "#/properties/method/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err13];
                    } else {
                      vErrors.push(err13);
                    }
                    errors++;
                  }
                  var _valid1 = _errs19 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err14 = { instancePath: instancePath + "/method", schemaPath: "#/properties/method/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err14];
                    } else {
                      vErrors.push(err14);
                    }
                    errors++;
                    validate99.errors = vErrors;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.material_state_id === void 0 && (missing0 = "material_state_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate104.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "material_state_id" || key0 === "revision" || key0 === "scope")) {
                validate104.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.material_state_id !== void 0) {
                let data0 = data.material_state_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate104.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate104.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate104.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate104.errors = [{ instancePath: instancePath + "/material_state_id", schemaPath: "#/properties/material_state_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate104.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate104.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate104.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate104.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate104.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                var valid2 = _errs12 === errors;
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
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
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
    function validate106(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate106.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.sample_id === void 0 && (missing0 = "sample_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate106.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "revision" || key0 === "sample_id" || key0 === "scope")) {
                validate106.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.revision !== void 0) {
                let data0 = data.revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate106.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate106.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 1 || isNaN(data0)) {
                        validate106.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                if (data.sample_id !== void 0) {
                  let data1 = data.sample_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate106.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate106.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate106.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate106.errors = [{ instancePath: instancePath + "/sample_id", schemaPath: "#/properties/sample_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
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
                          validate106.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate106.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate106.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate106.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate106.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate106.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate106.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate106.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate106.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate106.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate106.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate106.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate106.errors = vErrors;
      return errors === 0;
    }
    validate106.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.sample === void 0 && (missing0 = "sample") || data.material_state === void 0 && (missing0 = "material_state")) {
            validate103.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "material_state" || key0 === "sample")) {
                validate103.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.material_state !== void 0) {
                let data0 = data.material_state;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate104(data0, { instancePath: instancePath + "/material_state", parentData: data, parentDataProperty: "material_state", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate104.errors : vErrors.concat(validate104.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/material_state", schemaPath: "#/properties/material_state/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err1 = { instancePath: instancePath + "/material_state", schemaPath: "#/properties/material_state/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate103.errors = vErrors;
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
                if (data.sample !== void 0) {
                  let data1 = data.sample;
                  const _errs7 = errors;
                  const _errs8 = errors;
                  let valid2 = false;
                  const _errs9 = errors;
                  if (!validate106(data1, { instancePath: instancePath + "/sample", parentData: data, parentDataProperty: "sample", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate106.errors : vErrors.concat(validate106.errors);
                    errors = vErrors.length;
                  }
                  var _valid1 = _errs9 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs10 = errors;
                  if (data1 !== null) {
                    const err2 = { instancePath: instancePath + "/sample", schemaPath: "#/properties/sample/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err3 = { instancePath: instancePath + "/sample", schemaPath: "#/properties/sample/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                    validate103.errors = vErrors;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.experiment_id === void 0 && (missing0 = "experiment_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate110.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment_id" || key0 === "revision" || key0 === "scope")) {
                validate110.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment_id !== void 0) {
                let data0 = data.experiment_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate110.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate110.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate110.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate110.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate110.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate110.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate110.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate110.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate110.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate110.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate110.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate110.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate110.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate110.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate110.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate110.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate110.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate110.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate110.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate110.errors = vErrors;
      return errors === 0;
    }
    validate110.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate109(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate109.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.experiment === void 0 && (missing0 = "experiment") || data.expectation_id === void 0 && (missing0 = "expectation_id") || data.replicate_id === void 0 && (missing0 = "replicate_id")) {
            validate109.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "expectation_id" || key0 === "experiment" || key0 === "replicate_id")) {
                validate109.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.expectation_id !== void 0) {
                let data0 = data.expectation_id;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (errors === _errs4) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      const err0 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    } else {
                      if (func1(data0) < 1) {
                        const err1 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      } else {
                        if (!pattern4.test(data0)) {
                          const err2 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                    const err3 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
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
                  const err4 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err5 = { instancePath: instancePath + "/expectation_id", schemaPath: "#/properties/expectation_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err5];
                  } else {
                    vErrors.push(err5);
                  }
                  errors++;
                  validate109.errors = vErrors;
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
                if (data.experiment !== void 0) {
                  let data1 = data.experiment;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  let valid2 = false;
                  const _errs10 = errors;
                  if (!validate110(data1, { instancePath: instancePath + "/experiment", parentData: data, parentDataProperty: "experiment", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate110.errors : vErrors.concat(validate110.errors);
                    errors = vErrors.length;
                  }
                  var _valid1 = _errs10 === errors;
                  valid2 = valid2 || _valid1;
                  const _errs11 = errors;
                  if (data1 !== null) {
                    const err6 = { instancePath: instancePath + "/experiment", schemaPath: "#/properties/experiment/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err6];
                    } else {
                      vErrors.push(err6);
                    }
                    errors++;
                  }
                  var _valid1 = _errs11 === errors;
                  valid2 = valid2 || _valid1;
                  if (!valid2) {
                    const err7 = { instancePath: instancePath + "/experiment", schemaPath: "#/properties/experiment/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err7];
                    } else {
                      vErrors.push(err7);
                    }
                    errors++;
                    validate109.errors = vErrors;
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
                  if (data.replicate_id !== void 0) {
                    let data2 = data.replicate_id;
                    const _errs13 = errors;
                    const _errs14 = errors;
                    let valid3 = false;
                    const _errs15 = errors;
                    if (errors === _errs15) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 128) {
                          const err8 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                          if (vErrors === null) {
                            vErrors = [err8];
                          } else {
                            vErrors.push(err8);
                          }
                          errors++;
                        } else {
                          if (func1(data2) < 1) {
                            const err9 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                            if (vErrors === null) {
                              vErrors = [err9];
                            } else {
                              vErrors.push(err9);
                            }
                            errors++;
                          } else {
                            if (!pattern4.test(data2)) {
                              const err10 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                        const err11 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err11];
                        } else {
                          vErrors.push(err11);
                        }
                        errors++;
                      }
                    }
                    var _valid2 = _errs15 === errors;
                    valid3 = valid3 || _valid2;
                    const _errs17 = errors;
                    if (data2 !== null) {
                      const err12 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err12];
                      } else {
                        vErrors.push(err12);
                      }
                      errors++;
                    }
                    var _valid2 = _errs17 === errors;
                    valid3 = valid3 || _valid2;
                    if (!valid3) {
                      const err13 = { instancePath: instancePath + "/replicate_id", schemaPath: "#/properties/replicate_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err13];
                      } else {
                        vErrors.push(err13);
                      }
                      errors++;
                      validate109.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs14;
                      if (vErrors !== null) {
                        if (_errs14) {
                          vErrors.length = _errs14;
                        } else {
                          vErrors = null;
                        }
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
        } else {
          validate109.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate109.errors = vErrors;
      return errors === 0;
    }
    validate109.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate98(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate98.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.target === void 0 && (missing0 = "target") || data.specimen === void 0 && (missing0 = "specimen") || data.measurement === void 0 && (missing0 = "measurement") || data.role === void 0 && (missing0 = "role")) {
            validate98.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "measurement" || key0 === "role" || key0 === "specimen" || key0 === "target")) {
                validate98.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.measurement !== void 0) {
                const _errs2 = errors;
                if (!validate99(data.measurement, { instancePath: instancePath + "/measurement", parentData: data, parentDataProperty: "measurement", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate99.errors : vErrors.concat(validate99.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.role !== void 0) {
                  let data1 = data.role;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  let valid1 = false;
                  const _errs5 = errors;
                  if (typeof data1 !== "string") {
                    const err0 = { instancePath: instancePath + "/role", schemaPath: "#/properties/role/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                    if (vErrors === null) {
                      vErrors = [err0];
                    } else {
                      vErrors.push(err0);
                    }
                    errors++;
                  }
                  if (!(data1 === "sample" || data1 === "positive_control" || data1 === "negative_control" || data1 === "blank")) {
                    const err1 = { instancePath: instancePath + "/role", schemaPath: "#/properties/role/anyOf/0/enum", keyword: "enum", params: { allowedValues: schema102.properties.role.anyOf[0].enum }, message: "must be equal to one of the allowed values" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                  }
                  var _valid0 = _errs5 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs7 = errors;
                  if (data1 !== null) {
                    const err2 = { instancePath: instancePath + "/role", schemaPath: "#/properties/role/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err2];
                    } else {
                      vErrors.push(err2);
                    }
                    errors++;
                  }
                  var _valid0 = _errs7 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err3 = { instancePath: instancePath + "/role", schemaPath: "#/properties/role/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                    validate98.errors = vErrors;
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
                  if (data.specimen !== void 0) {
                    const _errs9 = errors;
                    if (!validate103(data.specimen, { instancePath: instancePath + "/specimen", parentData: data, parentDataProperty: "specimen", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate103.errors : vErrors.concat(validate103.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.target !== void 0) {
                      const _errs10 = errors;
                      if (!validate109(data.target, { instancePath: instancePath + "/target", parentData: data, parentDataProperty: "target", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate109.errors : vErrors.concat(validate109.errors);
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
          validate98.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate98.errors = vErrors;
      return errors === 0;
    }
    validate98.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.lower === void 0 && (missing0 = "lower") || data.upper === void 0 && (missing0 = "upper") || data.description === void 0 && (missing0 = "description")) {
            validate116.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "description" || key0 === "lower" || key0 === "upper")) {
                validate116.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.description !== void 0) {
                let data0 = data.description;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 512) {
                      validate116.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/maxLength", keyword: "maxLength", params: { limit: 512 }, message: "must NOT have more than 512 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate116.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      }
                    }
                  } else {
                    validate116.errors = [{ instancePath: instancePath + "/description", schemaPath: "#/properties/description/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.lower !== void 0) {
                  let data1 = data.lower;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.value === void 0 && (missing1 = "value") || data1.unit === void 0 && (missing1 = "unit")) {
                        validate116.errors = [{ instancePath: instancePath + "/lower", schemaPath: "#/$defs/MeasurementQuantity/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "unit" || key1 === "value")) {
                            validate116.errors = [{ instancePath: instancePath + "/lower", schemaPath: "#/$defs/MeasurementQuantity/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.unit !== void 0) {
                            let data2 = data1.unit;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 32) {
                                  validate116.errors = [{ instancePath: instancePath + "/lower/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate116.errors = [{ instancePath: instancePath + "/lower/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern67.test(data2)) {
                                      validate116.errors = [{ instancePath: instancePath + "/lower/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate116.errors = [{ instancePath: instancePath + "/lower/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.value !== void 0) {
                              let data3 = data1.value;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate116.errors = [{ instancePath: instancePath + "/lower/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate116.errors = [{ instancePath: instancePath + "/lower/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern72.test(data3)) {
                                        validate116.errors = [{ instancePath: instancePath + "/lower/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])" }, message: 'must match pattern "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate116.errors = [{ instancePath: instancePath + "/lower/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate116.errors = [{ instancePath: instancePath + "/lower", schemaPath: "#/$defs/MeasurementQuantity/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.upper !== void 0) {
                    let data4 = data.upper;
                    const _errs12 = errors;
                    const _errs13 = errors;
                    if (errors === _errs13) {
                      if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                        let missing2;
                        if (data4.value === void 0 && (missing2 = "value") || data4.unit === void 0 && (missing2 = "unit")) {
                          validate116.errors = [{ instancePath: instancePath + "/upper", schemaPath: "#/$defs/MeasurementQuantity/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                          return false;
                        } else {
                          const _errs15 = errors;
                          for (const key2 in data4) {
                            if (!(key2 === "unit" || key2 === "value")) {
                              validate116.errors = [{ instancePath: instancePath + "/upper", schemaPath: "#/$defs/MeasurementQuantity/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs15 === errors) {
                            if (data4.unit !== void 0) {
                              let data5 = data4.unit;
                              const _errs16 = errors;
                              if (errors === _errs16) {
                                if (typeof data5 === "string") {
                                  if (func1(data5) > 32) {
                                    validate116.errors = [{ instancePath: instancePath + "/upper/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data5) < 1) {
                                      validate116.errors = [{ instancePath: instancePath + "/upper/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern67.test(data5)) {
                                        validate116.errors = [{ instancePath: instancePath + "/upper/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate116.errors = [{ instancePath: instancePath + "/upper/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid4 = _errs16 === errors;
                            } else {
                              var valid4 = true;
                            }
                            if (valid4) {
                              if (data4.value !== void 0) {
                                let data6 = data4.value;
                                const _errs18 = errors;
                                if (errors === _errs18) {
                                  if (typeof data6 === "string") {
                                    if (func1(data6) > 128) {
                                      validate116.errors = [{ instancePath: instancePath + "/upper/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data6) < 1) {
                                        validate116.errors = [{ instancePath: instancePath + "/upper/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern72.test(data6)) {
                                          validate116.errors = [{ instancePath: instancePath + "/upper/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])" }, message: 'must match pattern "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate116.errors = [{ instancePath: instancePath + "/upper/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid4 = _errs18 === errors;
                              } else {
                                var valid4 = true;
                              }
                            }
                          }
                        }
                      } else {
                        validate116.errors = [{ instancePath: instancePath + "/upper", schemaPath: "#/$defs/MeasurementQuantity/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate116.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate116.errors = vErrors;
      return errors === 0;
    }
    validate116.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.kind === void 0 && (missing0 = "kind") || data.quantity === void 0 && (missing0 = "quantity") || data.uncertainty === void 0 && (missing0 = "uncertainty")) {
            validate115.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "kind" || key0 === "quantity" || key0 === "uncertainty")) {
                validate115.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.kind !== void 0) {
                let data0 = data.kind;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate115.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("numeric" !== data0) {
                  validate115.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "numeric" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.quantity !== void 0) {
                  let data1 = data.quantity;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.value === void 0 && (missing1 = "value") || data1.unit === void 0 && (missing1 = "unit")) {
                        validate115.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "unit" || key1 === "value")) {
                            validate115.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.unit !== void 0) {
                            let data2 = data1.unit;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 32) {
                                  validate115.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate115.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern67.test(data2)) {
                                      validate115.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate115.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.value !== void 0) {
                              let data3 = data1.value;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate115.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate115.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern72.test(data3)) {
                                        validate115.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])" }, message: 'must match pattern "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate115.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate115.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.uncertainty !== void 0) {
                    let data4 = data.uncertainty;
                    const _errs12 = errors;
                    const _errs13 = errors;
                    let valid3 = false;
                    const _errs14 = errors;
                    if (!validate116(data4, { instancePath: instancePath + "/uncertainty", parentData: data, parentDataProperty: "uncertainty", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate116.errors : vErrors.concat(validate116.errors);
                      errors = vErrors.length;
                    }
                    var _valid0 = _errs14 === errors;
                    valid3 = valid3 || _valid0;
                    const _errs15 = errors;
                    if (data4 !== null) {
                      const err0 = { instancePath: instancePath + "/uncertainty", schemaPath: "#/properties/uncertainty/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    }
                    var _valid0 = _errs15 === errors;
                    valid3 = valid3 || _valid0;
                    if (!valid3) {
                      const err1 = { instancePath: instancePath + "/uncertainty", schemaPath: "#/properties/uncertainty/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err1];
                      } else {
                        vErrors.push(err1);
                      }
                      errors++;
                      validate115.errors = vErrors;
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
    function validate120(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate120.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.quantity === void 0 && (missing0 = "quantity") || data.inclusive === void 0 && (missing0 = "inclusive")) {
            validate120.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "inclusive" || key0 === "quantity")) {
                validate120.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.inclusive !== void 0) {
                const _errs2 = errors;
                if (typeof data.inclusive !== "boolean") {
                  validate120.errors = [{ instancePath: instancePath + "/inclusive", schemaPath: "#/properties/inclusive/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.quantity !== void 0) {
                  let data1 = data.quantity;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.value === void 0 && (missing1 = "value") || data1.unit === void 0 && (missing1 = "unit")) {
                        validate120.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "unit" || key1 === "value")) {
                            validate120.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs7 === errors) {
                          if (data1.unit !== void 0) {
                            let data2 = data1.unit;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 32) {
                                  validate120.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate120.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern67.test(data2)) {
                                      validate120.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate120.errors = [{ instancePath: instancePath + "/quantity/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid2 = _errs8 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.value !== void 0) {
                              let data3 = data1.value;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    validate120.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate120.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern72.test(data3)) {
                                        validate120.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])" }, message: 'must match pattern "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate120.errors = [{ instancePath: instancePath + "/quantity/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate120.errors = [{ instancePath: instancePath + "/quantity", schemaPath: "#/$defs/MeasurementQuantity/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate120.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate120.errors = vErrors;
      return errors === 0;
    }
    validate120.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate119(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate119.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.lower === void 0 && (missing0 = "lower") || data.upper === void 0 && (missing0 = "upper")) {
            validate119.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "kind" || key0 === "lower" || key0 === "upper")) {
                validate119.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.kind !== void 0) {
                let data0 = data.kind;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate119.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("censored" !== data0) {
                  validate119.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "censored" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.lower !== void 0) {
                  let data1 = data.lower;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  const _errs6 = errors;
                  if (!validate120(data1, { instancePath: instancePath + "/lower", parentData: data, parentDataProperty: "lower", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate120.errors : vErrors.concat(validate120.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs6 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs7 = errors;
                  if (data1 !== null) {
                    const err0 = { instancePath: instancePath + "/lower", schemaPath: "#/properties/lower/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err1 = { instancePath: instancePath + "/lower", schemaPath: "#/properties/lower/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                    validate119.errors = vErrors;
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
                  if (data.upper !== void 0) {
                    let data2 = data.upper;
                    const _errs9 = errors;
                    const _errs10 = errors;
                    let valid2 = false;
                    const _errs11 = errors;
                    if (!validate120(data2, { instancePath: instancePath + "/upper", parentData: data, parentDataProperty: "upper", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate120.errors : vErrors.concat(validate120.errors);
                      errors = vErrors.length;
                    }
                    var _valid1 = _errs11 === errors;
                    valid2 = valid2 || _valid1;
                    const _errs12 = errors;
                    if (data2 !== null) {
                      const err2 = { instancePath: instancePath + "/upper", schemaPath: "#/properties/upper/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err2];
                      } else {
                        vErrors.push(err2);
                      }
                      errors++;
                    }
                    var _valid1 = _errs12 === errors;
                    valid2 = valid2 || _valid1;
                    if (!valid2) {
                      const err3 = { instancePath: instancePath + "/upper", schemaPath: "#/properties/upper/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err3];
                      } else {
                        vErrors.push(err3);
                      }
                      errors++;
                      validate119.errors = vErrors;
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
                }
              }
            }
          }
        } else {
          validate119.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate119.errors = vErrors;
      return errors === 0;
    }
    validate119.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate114(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate114.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.x === void 0 && (missing0 = "x") || data.y === void 0 && (missing0 = "y")) {
            validate114.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "x" || key0 === "y")) {
                validate114.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.x !== void 0) {
                let data0 = data.x;
                const _errs2 = errors;
                const _errs3 = errors;
                if (errors === _errs3) {
                  if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                    let missing1;
                    if (data0.value === void 0 && (missing1 = "value") || data0.unit === void 0 && (missing1 = "unit")) {
                      validate114.errors = [{ instancePath: instancePath + "/x", schemaPath: "#/$defs/MeasurementQuantity/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                      return false;
                    } else {
                      const _errs5 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "unit" || key1 === "value")) {
                          validate114.errors = [{ instancePath: instancePath + "/x", schemaPath: "#/$defs/MeasurementQuantity/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                          return false;
                          break;
                        }
                      }
                      if (_errs5 === errors) {
                        if (data0.unit !== void 0) {
                          let data1 = data0.unit;
                          const _errs6 = errors;
                          if (errors === _errs6) {
                            if (typeof data1 === "string") {
                              if (func1(data1) > 32) {
                                validate114.errors = [{ instancePath: instancePath + "/x/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                return false;
                              } else {
                                if (func1(data1) < 1) {
                                  validate114.errors = [{ instancePath: instancePath + "/x/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                } else {
                                  if (!pattern67.test(data1)) {
                                    validate114.errors = [{ instancePath: instancePath + "/x/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                    return false;
                                  }
                                }
                              }
                            } else {
                              validate114.errors = [{ instancePath: instancePath + "/x/unit", schemaPath: "#/$defs/MeasurementQuantity/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid2 = _errs6 === errors;
                        } else {
                          var valid2 = true;
                        }
                        if (valid2) {
                          if (data0.value !== void 0) {
                            let data2 = data0.value;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (typeof data2 === "string") {
                                if (func1(data2) > 128) {
                                  validate114.errors = [{ instancePath: instancePath + "/x/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate114.errors = [{ instancePath: instancePath + "/x/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern72.test(data2)) {
                                      validate114.errors = [{ instancePath: instancePath + "/x/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])" }, message: 'must match pattern "^-?(0|[1-9][0-9]*)(\\.[0-9]+)?([eE][+-]?[0-9]+)?$(?![\\s\\S])"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate114.errors = [{ instancePath: instancePath + "/x/value", schemaPath: "#/$defs/MeasurementQuantity/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate114.errors = [{ instancePath: instancePath + "/x", schemaPath: "#/$defs/MeasurementQuantity/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.y !== void 0) {
                  let data3 = data.y;
                  const _errs10 = errors;
                  const _errs11 = errors;
                  let valid3 = false;
                  let passing0 = null;
                  const _errs12 = errors;
                  if (!validate115(data3, { instancePath: instancePath + "/y", parentData: data, parentDataProperty: "y", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate115.errors : vErrors.concat(validate115.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs12 === errors;
                  if (_valid0) {
                    valid3 = true;
                    passing0 = 0;
                    var props0 = true;
                  }
                  const _errs13 = errors;
                  if (!validate119(data3, { instancePath: instancePath + "/y", parentData: data, parentDataProperty: "y", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate119.errors : vErrors.concat(validate119.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs13 === errors;
                  if (_valid0 && valid3) {
                    valid3 = false;
                    passing0 = [passing0, 1];
                  } else {
                    if (_valid0) {
                      valid3 = true;
                      passing0 = 1;
                      if (props0 !== true) {
                        props0 = true;
                      }
                    }
                    const _errs14 = errors;
                    const _errs15 = errors;
                    if (errors === _errs15) {
                      if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                        let missing2;
                        if (data3.kind === void 0 && (missing2 = "kind") || data3.reason === void 0 && (missing2 = "reason")) {
                          const err0 = { instancePath: instancePath + "/y", schemaPath: "#/$defs/MissingMeasurement/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        } else {
                          const _errs17 = errors;
                          for (const key2 in data3) {
                            if (!(key2 === "kind" || key2 === "reason")) {
                              const err1 = { instancePath: instancePath + "/y", schemaPath: "#/$defs/MissingMeasurement/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
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
                            if (data3.kind !== void 0) {
                              let data4 = data3.kind;
                              const _errs18 = errors;
                              if (typeof data4 !== "string") {
                                const err2 = { instancePath: instancePath + "/y/kind", schemaPath: "#/$defs/MissingMeasurement/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              }
                              if ("missing" !== data4) {
                                const err3 = { instancePath: instancePath + "/y/kind", schemaPath: "#/$defs/MissingMeasurement/properties/kind/const", keyword: "const", params: { allowedValue: "missing" }, message: "must be equal to constant" };
                                if (vErrors === null) {
                                  vErrors = [err3];
                                } else {
                                  vErrors.push(err3);
                                }
                                errors++;
                              }
                              var valid5 = _errs18 === errors;
                            } else {
                              var valid5 = true;
                            }
                            if (valid5) {
                              if (data3.reason !== void 0) {
                                let data5 = data3.reason;
                                const _errs20 = errors;
                                if (errors === _errs20) {
                                  if (typeof data5 === "string") {
                                    if (func1(data5) > 128) {
                                      const err4 = { instancePath: instancePath + "/y/reason", schemaPath: "#/$defs/MissingMeasurement/properties/reason/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err4];
                                      } else {
                                        vErrors.push(err4);
                                      }
                                      errors++;
                                    } else {
                                      if (func1(data5) < 1) {
                                        const err5 = { instancePath: instancePath + "/y/reason", schemaPath: "#/$defs/MissingMeasurement/properties/reason/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err5];
                                        } else {
                                          vErrors.push(err5);
                                        }
                                        errors++;
                                      } else {
                                        if (!pattern4.test(data5)) {
                                          const err6 = { instancePath: instancePath + "/y/reason", schemaPath: "#/$defs/MissingMeasurement/properties/reason/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                    const err7 = { instancePath: instancePath + "/y/reason", schemaPath: "#/$defs/MissingMeasurement/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err7];
                                    } else {
                                      vErrors.push(err7);
                                    }
                                    errors++;
                                  }
                                }
                                var valid5 = _errs20 === errors;
                              } else {
                                var valid5 = true;
                              }
                            }
                          }
                        }
                      } else {
                        const err8 = { instancePath: instancePath + "/y", schemaPath: "#/$defs/MissingMeasurement/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs14 === errors;
                    if (_valid0 && valid3) {
                      valid3 = false;
                      passing0 = [passing0, 2];
                    } else {
                      if (_valid0) {
                        valid3 = true;
                        passing0 = 2;
                        if (props0 !== true) {
                          props0 = true;
                        }
                      }
                    }
                  }
                  if (!valid3) {
                    const err9 = { instancePath: instancePath + "/y", schemaPath: "#/properties/y/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                    if (vErrors === null) {
                      vErrors = [err9];
                    } else {
                      vErrors.push(err9);
                    }
                    errors++;
                    validate114.errors = vErrors;
                    return false;
                  } else {
                    errors = _errs11;
                    if (vErrors !== null) {
                      if (_errs11) {
                        vErrors.length = _errs11;
                      } else {
                        vErrors = null;
                      }
                    }
                  }
                  var valid0 = _errs10 === errors;
                } else {
                  var valid0 = true;
                }
              }
            }
          }
        } else {
          validate114.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate114.errors = vErrors;
      return errors === 0;
    }
    validate114.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate126(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate126.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.scope === void 0 && (missing0 = "scope") || data.observation_id === void 0 && (missing0 = "observation_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate126.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "observation_id" || key0 === "revision" || key0 === "scope")) {
                validate126.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.observation_id !== void 0) {
                let data0 = data.observation_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate126.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate126.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate126.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate126.errors = [{ instancePath: instancePath + "/observation_id", schemaPath: "#/properties/observation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate126.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate126.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate126.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate126.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate126.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate126.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate126.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate126.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate126.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate126.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate126.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate126.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate126.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate126.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate126.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate126.errors = vErrors;
      return errors === 0;
    }
    validate126.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.observation === void 0 && (missing0 = "observation")) {
            validate125.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "limit" || key0 === "observation" || key0 === "position" || key0 === "wire_version")) {
                validate125.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.limit !== void 0) {
                let data0 = data.limit;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate125.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 256 || isNaN(data0)) {
                      validate125.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 256 }, message: "must be <= 256" }];
                      return false;
                    } else {
                      if (data0 < 1 || isNaN(data0)) {
                        validate125.errors = [{ instancePath: instancePath + "/limit", schemaPath: "#/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                if (data.observation !== void 0) {
                  const _errs4 = errors;
                  if (!validate126(data.observation, { instancePath: instancePath + "/observation", parentData: data, parentDataProperty: "observation", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate126.errors : vErrors.concat(validate126.errors);
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
                    const _errs6 = errors;
                    let valid1 = false;
                    const _errs7 = errors;
                    const _errs8 = errors;
                    if (errors === _errs8) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.query_sha256 === void 0 && (missing1 = "query_sha256") || data2.offset === void 0 && (missing1 = "offset")) {
                          const err0 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        } else {
                          const _errs10 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "offset" || key1 === "query_sha256")) {
                              const err1 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                            if (data2.offset !== void 0) {
                              let data3 = data2.offset;
                              const _errs11 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                const err2 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              }
                              if (errors === _errs11) {
                                if (typeof data3 == "number" && isFinite(data3)) {
                                  if (data3 > 4096 || isNaN(data3)) {
                                    const err3 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                    if (vErrors === null) {
                                      vErrors = [err3];
                                    } else {
                                      vErrors.push(err3);
                                    }
                                    errors++;
                                  } else {
                                    if (data3 < 0 || isNaN(data3)) {
                                      const err4 = { instancePath: instancePath + "/position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                              var valid3 = _errs11 === errors;
                            } else {
                              var valid3 = true;
                            }
                            if (valid3) {
                              if (data2.query_sha256 !== void 0) {
                                let data4 = data2.query_sha256;
                                const _errs13 = errors;
                                if (errors === _errs13) {
                                  if (typeof data4 === "string") {
                                    if (!pattern7.test(data4)) {
                                      const err5 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                    }
                                  } else {
                                    const err6 = { instancePath: instancePath + "/position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err6];
                                    } else {
                                      vErrors.push(err6);
                                    }
                                    errors++;
                                  }
                                }
                                var valid3 = _errs13 === errors;
                              } else {
                                var valid3 = true;
                              }
                            }
                          }
                        }
                      } else {
                        const err7 = { instancePath: instancePath + "/position", schemaPath: "#/$defs/ResearchViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err7];
                        } else {
                          vErrors.push(err7);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs7 === errors;
                    valid1 = valid1 || _valid0;
                    const _errs15 = errors;
                    if (data2 !== null) {
                      const err8 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err8];
                      } else {
                        vErrors.push(err8);
                      }
                      errors++;
                    }
                    var _valid0 = _errs15 === errors;
                    valid1 = valid1 || _valid0;
                    if (!valid1) {
                      const err9 = { instancePath: instancePath + "/position", schemaPath: "#/properties/position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err9];
                      } else {
                        vErrors.push(err9);
                      }
                      errors++;
                      validate125.errors = vErrors;
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
                    if (data.wire_version !== void 0) {
                      let data5 = data.wire_version;
                      const _errs17 = errors;
                      if (typeof data5 !== "string") {
                        validate125.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data5) {
                        validate125.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs17 === errors;
                    } else {
                      var valid0 = true;
                    }
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
    function validate97(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.request === void 0 && (missing0 = "request") || data.query_sha256 === void 0 && (missing0 = "query_sha256") || data.total === void 0 && (missing0 = "total") || data.x_unit === void 0 && (missing0 = "x_unit") || data.y_unit === void 0 && (missing0 = "y_unit") || data.source === void 0 && (missing0 = "source") || data.binding === void 0 && (missing0 = "binding") || data.quality === void 0 && (missing0 = "quality") || data.points === void 0 && (missing0 = "points") || data.next_position === void 0 && (missing0 = "next_position")) {
            validate97.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func53.call(schema101.properties, key0)) {
                validate97.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.binding !== void 0) {
                const _errs2 = errors;
                if (!validate98(data.binding, { instancePath: instancePath + "/binding", parentData: data, parentDataProperty: "binding", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate98.errors : vErrors.concat(validate98.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.next_position !== void 0) {
                  let data1 = data.next_position;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  let valid1 = false;
                  const _errs5 = errors;
                  const _errs6 = errors;
                  if (errors === _errs6) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.query_sha256 === void 0 && (missing1 = "query_sha256") || data1.offset === void 0 && (missing1 = "offset")) {
                        const err0 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/ResearchViewPosition/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        const _errs8 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "offset" || key1 === "query_sha256")) {
                            const err1 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/ResearchViewPosition/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                            if (vErrors === null) {
                              vErrors = [err1];
                            } else {
                              vErrors.push(err1);
                            }
                            errors++;
                            break;
                          }
                        }
                        if (_errs8 === errors) {
                          if (data1.offset !== void 0) {
                            let data2 = data1.offset;
                            const _errs9 = errors;
                            if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                              const err2 = { instancePath: instancePath + "/next_position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                            }
                            if (errors === _errs9) {
                              if (typeof data2 == "number" && isFinite(data2)) {
                                if (data2 > 4096 || isNaN(data2)) {
                                  const err3 = { instancePath: instancePath + "/next_position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" };
                                  if (vErrors === null) {
                                    vErrors = [err3];
                                  } else {
                                    vErrors.push(err3);
                                  }
                                  errors++;
                                } else {
                                  if (data2 < 0 || isNaN(data2)) {
                                    const err4 = { instancePath: instancePath + "/next_position/offset", schemaPath: "#/$defs/ResearchViewPosition/properties/offset/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                            var valid3 = _errs9 === errors;
                          } else {
                            var valid3 = true;
                          }
                          if (valid3) {
                            if (data1.query_sha256 !== void 0) {
                              let data3 = data1.query_sha256;
                              const _errs11 = errors;
                              if (errors === _errs11) {
                                if (typeof data3 === "string") {
                                  if (!pattern7.test(data3)) {
                                    const err5 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                    if (vErrors === null) {
                                      vErrors = [err5];
                                    } else {
                                      vErrors.push(err5);
                                    }
                                    errors++;
                                  }
                                } else {
                                  const err6 = { instancePath: instancePath + "/next_position/query_sha256", schemaPath: "#/$defs/ResearchViewPosition/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err6];
                                  } else {
                                    vErrors.push(err6);
                                  }
                                  errors++;
                                }
                              }
                              var valid3 = _errs11 === errors;
                            } else {
                              var valid3 = true;
                            }
                          }
                        }
                      }
                    } else {
                      const err7 = { instancePath: instancePath + "/next_position", schemaPath: "#/$defs/ResearchViewPosition/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err7];
                      } else {
                        vErrors.push(err7);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs5 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs13 = errors;
                  if (data1 !== null) {
                    const err8 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err8];
                    } else {
                      vErrors.push(err8);
                    }
                    errors++;
                  }
                  var _valid0 = _errs13 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err9 = { instancePath: instancePath + "/next_position", schemaPath: "#/properties/next_position/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err9];
                    } else {
                      vErrors.push(err9);
                    }
                    errors++;
                    validate97.errors = vErrors;
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
                  if (data.points !== void 0) {
                    let data4 = data.points;
                    const _errs15 = errors;
                    if (errors === _errs15) {
                      if (Array.isArray(data4)) {
                        if (data4.length > 256) {
                          validate97.errors = [{ instancePath: instancePath + "/points", schemaPath: "#/properties/points/maxItems", keyword: "maxItems", params: { limit: 256 }, message: "must NOT have more than 256 items" }];
                          return false;
                        } else {
                          var valid4 = true;
                          const len0 = data4.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs17 = errors;
                            if (!validate114(data4[i0], { instancePath: instancePath + "/points/" + i0, parentData: data4, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate114.errors : vErrors.concat(validate114.errors);
                              errors = vErrors.length;
                            }
                            var valid4 = _errs17 === errors;
                            if (!valid4) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate97.errors = [{ instancePath: instancePath + "/points", schemaPath: "#/properties/points/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs15 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.quality !== void 0) {
                      let data6 = data.quality;
                      const _errs18 = errors;
                      const _errs19 = errors;
                      if (errors === _errs19) {
                        if (data6 && typeof data6 == "object" && !Array.isArray(data6)) {
                          let missing2;
                          if (data6.controls === void 0 && (missing2 = "controls") || data6.flags === void 0 && (missing2 = "flags")) {
                            validate97.errors = [{ instancePath: instancePath + "/quality", schemaPath: "#/$defs/ObservationQuality/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs21 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "controls" || key2 === "flags")) {
                                validate97.errors = [{ instancePath: instancePath + "/quality", schemaPath: "#/$defs/ObservationQuality/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs21 === errors) {
                              if (data6.controls !== void 0) {
                                let data7 = data6.controls;
                                const _errs22 = errors;
                                if (typeof data7 !== "string") {
                                  validate97.errors = [{ instancePath: instancePath + "/quality/controls", schemaPath: "#/$defs/ObservationQuality/properties/controls/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if (!(data7 === "passed" || data7 === "failed" || data7 === "unknown")) {
                                  validate97.errors = [{ instancePath: instancePath + "/quality/controls", schemaPath: "#/$defs/ObservationQuality/properties/controls/enum", keyword: "enum", params: { allowedValues: schema128.properties.controls.enum }, message: "must be equal to one of the allowed values" }];
                                  return false;
                                }
                                var valid6 = _errs22 === errors;
                              } else {
                                var valid6 = true;
                              }
                              if (valid6) {
                                if (data6.flags !== void 0) {
                                  let data8 = data6.flags;
                                  const _errs24 = errors;
                                  if (errors === _errs24) {
                                    if (Array.isArray(data8)) {
                                      if (data8.length > 64) {
                                        validate97.errors = [{ instancePath: instancePath + "/quality/flags", schemaPath: "#/$defs/ObservationQuality/properties/flags/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                                        return false;
                                      } else {
                                        var valid7 = true;
                                        const len1 = data8.length;
                                        for (let i1 = 0; i1 < len1; i1++) {
                                          let data9 = data8[i1];
                                          const _errs26 = errors;
                                          if (errors === _errs26) {
                                            if (typeof data9 === "string") {
                                              if (func1(data9) > 128) {
                                                validate97.errors = [{ instancePath: instancePath + "/quality/flags/" + i1, schemaPath: "#/$defs/ObservationQuality/properties/flags/items/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                return false;
                                              } else {
                                                if (func1(data9) < 1) {
                                                  validate97.errors = [{ instancePath: instancePath + "/quality/flags/" + i1, schemaPath: "#/$defs/ObservationQuality/properties/flags/items/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                  return false;
                                                } else {
                                                  if (!pattern4.test(data9)) {
                                                    validate97.errors = [{ instancePath: instancePath + "/quality/flags/" + i1, schemaPath: "#/$defs/ObservationQuality/properties/flags/items/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            } else {
                                              validate97.errors = [{ instancePath: instancePath + "/quality/flags/" + i1, schemaPath: "#/$defs/ObservationQuality/properties/flags/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid7 = _errs26 === errors;
                                          if (!valid7) {
                                            break;
                                          }
                                        }
                                      }
                                    } else {
                                      validate97.errors = [{ instancePath: instancePath + "/quality/flags", schemaPath: "#/$defs/ObservationQuality/properties/flags/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                      return false;
                                    }
                                  }
                                  var valid6 = _errs24 === errors;
                                } else {
                                  var valid6 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate97.errors = [{ instancePath: instancePath + "/quality", schemaPath: "#/$defs/ObservationQuality/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs18 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.query_sha256 !== void 0) {
                        let data10 = data.query_sha256;
                        const _errs28 = errors;
                        if (errors === _errs28) {
                          if (typeof data10 === "string") {
                            if (!pattern7.test(data10)) {
                              validate97.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate97.errors = [{ instancePath: instancePath + "/query_sha256", schemaPath: "#/properties/query_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs28 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.request !== void 0) {
                          const _errs30 = errors;
                          if (!validate125(data.request, { instancePath: instancePath + "/request", parentData: data, parentDataProperty: "request", rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate125.errors : vErrors.concat(validate125.errors);
                            errors = vErrors.length;
                          }
                          var valid0 = _errs30 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.source !== void 0) {
                            const _errs31 = errors;
                            if (!validate100(data.source, { instancePath: instancePath + "/source", parentData: data, parentDataProperty: "source", rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate100.errors : vErrors.concat(validate100.errors);
                              errors = vErrors.length;
                            }
                            var valid0 = _errs31 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.total !== void 0) {
                              let data13 = data.total;
                              const _errs32 = errors;
                              if (!(typeof data13 == "number" && (!(data13 % 1) && !isNaN(data13)) && isFinite(data13))) {
                                validate97.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (errors === _errs32) {
                                if (typeof data13 == "number" && isFinite(data13)) {
                                  if (data13 > 4096 || isNaN(data13)) {
                                    validate97.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 4096 }, message: "must be <= 4096" }];
                                    return false;
                                  } else {
                                    if (data13 < 1 || isNaN(data13)) {
                                      validate97.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                      return false;
                                    }
                                  }
                                }
                              }
                              var valid0 = _errs32 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.wire_version !== void 0) {
                                let data14 = data.wire_version;
                                const _errs34 = errors;
                                if (typeof data14 !== "string") {
                                  validate97.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("1" !== data14) {
                                  validate97.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid0 = _errs34 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.x_unit !== void 0) {
                                  let data15 = data.x_unit;
                                  const _errs36 = errors;
                                  if (errors === _errs36) {
                                    if (typeof data15 === "string") {
                                      if (func1(data15) > 32) {
                                        validate97.errors = [{ instancePath: instancePath + "/x_unit", schemaPath: "#/properties/x_unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data15) < 1) {
                                          validate97.errors = [{ instancePath: instancePath + "/x_unit", schemaPath: "#/properties/x_unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern67.test(data15)) {
                                            validate97.errors = [{ instancePath: instancePath + "/x_unit", schemaPath: "#/properties/x_unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate97.errors = [{ instancePath: instancePath + "/x_unit", schemaPath: "#/properties/x_unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid0 = _errs36 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.y_unit !== void 0) {
                                    let data16 = data.y_unit;
                                    const _errs38 = errors;
                                    if (errors === _errs38) {
                                      if (typeof data16 === "string") {
                                        if (func1(data16) > 32) {
                                          validate97.errors = [{ instancePath: instancePath + "/y_unit", schemaPath: "#/properties/y_unit/maxLength", keyword: "maxLength", params: { limit: 32 }, message: "must NOT have more than 32 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data16) < 1) {
                                            validate97.errors = [{ instancePath: instancePath + "/y_unit", schemaPath: "#/properties/y_unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern67.test(data16)) {
                                              validate97.errors = [{ instancePath: instancePath + "/y_unit", schemaPath: "#/properties/y_unit/pattern", keyword: "pattern", params: { pattern: "^\\S+$(?![\\s\\S])" }, message: 'must match pattern "^\\S+$(?![\\s\\S])"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate97.errors = [{ instancePath: instancePath + "/y_unit", schemaPath: "#/properties/y_unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                    }
                                    var valid0 = _errs38 === errors;
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
    exports.catalog = validate130;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.experiment_id === void 0 && (missing0 = "experiment_id") || data.revision === void 0 && (missing0 = "revision")) {
            validate131.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment_id" || key0 === "revision" || key0 === "scope")) {
                validate131.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment_id !== void 0) {
                let data0 = data.experiment_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate131.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate131.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate131.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate131.errors = [{ instancePath: instancePath + "/experiment_id", schemaPath: "#/properties/experiment_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate131.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate131.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate131.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate131.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate131.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate131.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate131.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate131.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate131.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate131.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate131.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate131.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate131.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate131.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate131.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate131.errors = vErrors;
      return errors === 0;
    }
    validate131.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema137 = { "additionalProperties": false, "properties": { "result_schema": { "$ref": "#/$defs/SchemaRef" }, "version": { "const": "1", "title": "Version", "type": "string" }, "view_id": { "enum": ["specimens", "properties", "observation_series"], "title": "View Id", "type": "string" } }, "required": ["view_id", "version", "result_schema"], "title": "ResearchViewCapability", "type": "object" };
    function validate133(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate133.evaluated;
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
            validate133.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "result_schema" || key0 === "version" || key0 === "view_id")) {
                validate133.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate133.errors = [{ instancePath: instancePath + "/result_schema", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                      return false;
                    } else {
                      const _errs5 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                          validate133.errors = [{ instancePath: instancePath + "/result_schema", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                validate133.errors = [{ instancePath: instancePath + "/result_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                return false;
                              } else {
                                if (func1(data1) < 1) {
                                  validate133.errors = [{ instancePath: instancePath + "/result_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                } else {
                                  if (!pattern4.test(data1)) {
                                    validate133.errors = [{ instancePath: instancePath + "/result_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                    return false;
                                  }
                                }
                              }
                            } else {
                              validate133.errors = [{ instancePath: instancePath + "/result_schema/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                if (!pattern7.test(data2)) {
                                  validate133.errors = [{ instancePath: instancePath + "/result_schema/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate133.errors = [{ instancePath: instancePath + "/result_schema/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                validate133.errors = [{ instancePath: instancePath + "/result_schema/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("1" !== data3) {
                                validate133.errors = [{ instancePath: instancePath + "/result_schema/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                    validate133.errors = [{ instancePath: instancePath + "/result_schema", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                    validate133.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("1" !== data4) {
                    validate133.errors = [{ instancePath: instancePath + "/version", schemaPath: "#/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                      validate133.errors = [{ instancePath: instancePath + "/view_id", schemaPath: "#/properties/view_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data5 === "specimens" || data5 === "properties" || data5 === "observation_series")) {
                      validate133.errors = [{ instancePath: instancePath + "/view_id", schemaPath: "#/properties/view_id/enum", keyword: "enum", params: { allowedValues: schema137.properties.view_id.enum }, message: "must be equal to one of the allowed values" }];
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
          validate133.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate133.errors = vErrors;
      return errors === 0;
    }
    validate133.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate130(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate130.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.wire_version === void 0 && (missing0 = "wire_version") || data.owner === void 0 && (missing0 = "owner") || data.experiment === void 0 && (missing0 = "experiment") || data.views === void 0 && (missing0 = "views") || data.limits === void 0 && (missing0 = "limits")) {
            validate130.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "experiment" || key0 === "limits" || key0 === "owner" || key0 === "views" || key0 === "wire_version")) {
                validate130.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.experiment !== void 0) {
                const _errs2 = errors;
                if (!validate131(data.experiment, { instancePath: instancePath + "/experiment", parentData: data, parentDataProperty: "experiment", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate131.errors : vErrors.concat(validate131.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.limits !== void 0) {
                  let data1 = data.limits;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.rows === void 0 && (missing1 = "rows") || data1.selected_observations === void 0 && (missing1 = "selected_observations") || data1.series_points === void 0 && (missing1 = "series_points") || data1.response_bytes === void 0 && (missing1 = "response_bytes") || data1.source_fetch === void 0 && (missing1 = "source_fetch")) {
                        validate130.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/ResearchViewLimits/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs6 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "response_bytes" || key1 === "rows" || key1 === "selected_observations" || key1 === "series_points" || key1 === "source_fetch")) {
                            validate130.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/ResearchViewLimits/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                            return false;
                            break;
                          }
                        }
                        if (_errs6 === errors) {
                          if (data1.response_bytes !== void 0) {
                            let data2 = data1.response_bytes;
                            const _errs7 = errors;
                            if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                              validate130.errors = [{ instancePath: instancePath + "/limits/response_bytes", schemaPath: "#/$defs/ResearchViewLimits/properties/response_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            if (1048576 !== data2) {
                              validate130.errors = [{ instancePath: instancePath + "/limits/response_bytes", schemaPath: "#/$defs/ResearchViewLimits/properties/response_bytes/const", keyword: "const", params: { allowedValue: 1048576 }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid2 = _errs7 === errors;
                          } else {
                            var valid2 = true;
                          }
                          if (valid2) {
                            if (data1.rows !== void 0) {
                              let data3 = data1.rows;
                              const _errs9 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                validate130.errors = [{ instancePath: instancePath + "/limits/rows", schemaPath: "#/$defs/ResearchViewLimits/properties/rows/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (16 !== data3) {
                                validate130.errors = [{ instancePath: instancePath + "/limits/rows", schemaPath: "#/$defs/ResearchViewLimits/properties/rows/const", keyword: "const", params: { allowedValue: 16 }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid2 = _errs9 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data1.selected_observations !== void 0) {
                                let data4 = data1.selected_observations;
                                const _errs11 = errors;
                                if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                                  validate130.errors = [{ instancePath: instancePath + "/limits/selected_observations", schemaPath: "#/$defs/ResearchViewLimits/properties/selected_observations/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                if (128 !== data4) {
                                  validate130.errors = [{ instancePath: instancePath + "/limits/selected_observations", schemaPath: "#/$defs/ResearchViewLimits/properties/selected_observations/const", keyword: "const", params: { allowedValue: 128 }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid2 = _errs11 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data1.series_points !== void 0) {
                                  let data5 = data1.series_points;
                                  const _errs13 = errors;
                                  if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                    validate130.errors = [{ instancePath: instancePath + "/limits/series_points", schemaPath: "#/$defs/ResearchViewLimits/properties/series_points/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                    return false;
                                  }
                                  if (256 !== data5) {
                                    validate130.errors = [{ instancePath: instancePath + "/limits/series_points", schemaPath: "#/$defs/ResearchViewLimits/properties/series_points/const", keyword: "const", params: { allowedValue: 256 }, message: "must be equal to constant" }];
                                    return false;
                                  }
                                  var valid2 = _errs13 === errors;
                                } else {
                                  var valid2 = true;
                                }
                                if (valid2) {
                                  if (data1.source_fetch !== void 0) {
                                    let data6 = data1.source_fetch;
                                    const _errs15 = errors;
                                    if (typeof data6 !== "string") {
                                      validate130.errors = [{ instancePath: instancePath + "/limits/source_fetch", schemaPath: "#/$defs/ResearchViewLimits/properties/source_fetch/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                    if ("separate_data_authority" !== data6) {
                                      validate130.errors = [{ instancePath: instancePath + "/limits/source_fetch", schemaPath: "#/$defs/ResearchViewLimits/properties/source_fetch/const", keyword: "const", params: { allowedValue: "separate_data_authority" }, message: "must be equal to constant" }];
                                      return false;
                                    }
                                    var valid2 = _errs15 === errors;
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
                      validate130.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/ResearchViewLimits/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.owner !== void 0) {
                    let data7 = data.owner;
                    const _errs17 = errors;
                    if (typeof data7 !== "string") {
                      validate130.errors = [{ instancePath: instancePath + "/owner", schemaPath: "#/properties/owner/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("research" !== data7) {
                      validate130.errors = [{ instancePath: instancePath + "/owner", schemaPath: "#/properties/owner/const", keyword: "const", params: { allowedValue: "research" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs17 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.views !== void 0) {
                      let data8 = data.views;
                      const _errs19 = errors;
                      if (errors === _errs19) {
                        if (Array.isArray(data8)) {
                          if (data8.length > 3) {
                            validate130.errors = [{ instancePath: instancePath + "/views", schemaPath: "#/properties/views/maxItems", keyword: "maxItems", params: { limit: 3 }, message: "must NOT have more than 3 items" }];
                            return false;
                          } else {
                            if (data8.length < 3) {
                              validate130.errors = [{ instancePath: instancePath + "/views", schemaPath: "#/properties/views/minItems", keyword: "minItems", params: { limit: 3 }, message: "must NOT have fewer than 3 items" }];
                              return false;
                            } else {
                              var valid3 = true;
                              const len0 = data8.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                const _errs21 = errors;
                                if (!validate133(data8[i0], { instancePath: instancePath + "/views/" + i0, parentData: data8, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate133.errors : vErrors.concat(validate133.errors);
                                  errors = vErrors.length;
                                }
                                var valid3 = _errs21 === errors;
                                if (!valid3) {
                                  break;
                                }
                              }
                            }
                          }
                        } else {
                          validate130.errors = [{ instancePath: instancePath + "/views", schemaPath: "#/properties/views/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs19 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.wire_version !== void 0) {
                        let data10 = data.wire_version;
                        const _errs22 = errors;
                        if (typeof data10 !== "string") {
                          validate130.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data10) {
                          validate130.errors = [{ instancePath: instancePath + "/wire_version", schemaPath: "#/properties/wire_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
        } else {
          validate130.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate130.errors = vErrors;
      return errors === 0;
    }
    validate130.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
  }
});
export default require_reviewed_validators();
