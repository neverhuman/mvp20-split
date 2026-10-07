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
    exports.checkpoints = validate20;
    var schema32 = { "additionalProperties": false, "properties": { "checkpoint_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Checkpoint Id", "type": "string" }, "eligibility_reason": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Eligibility Reason" }, "reference": { "$ref": "#/$defs/SupervisionRef" }, "requests": { "maximum": 9007199254740991, "minimum": 0, "title": "Requests", "type": "integer" }, "targets": { "items": { "pattern": "^[0-9a-f]{64}$", "type": "string" }, "maxItems": 64, "minItems": 1, "title": "Targets", "type": "array" }, "winner_kind": { "anyOf": [{ "enum": ["model_accepted", "fallback", "cancelled"], "type": "string" }, { "type": "null" }], "title": "Winner Kind" }, "winner_reason": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Winner Reason" } }, "required": ["reference", "checkpoint_id", "targets", "eligibility_reason", "requests", "winner_kind", "winner_reason"], "title": "CheckpointInspectionItem", "type": "object" };
    var func1 = require_ucs2length().default;
    var pattern4 = new RegExp("^[A-Za-z0-9][A-Za-z0-9._:-]*$", "u");
    var pattern10 = new RegExp("^[0-9a-f]{64}$", "u");
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.decision_id === void 0 && (missing0 = "decision_id")) {
            validate22.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "decision_id" || key0 === "run_id" || key0 === "scope")) {
                validate22.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.decision_id !== void 0) {
                let data0 = data.decision_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate22.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate22.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate22.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate22.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data1 = data.run_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate22.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate22.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate22.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate22.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate22.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate22.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate22.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate22.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
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
                                      validate22.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate22.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
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
                                var valid2 = _errs12 === errors;
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
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
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
          if (data.reference === void 0 && (missing0 = "reference") || data.checkpoint_id === void 0 && (missing0 = "checkpoint_id") || data.targets === void 0 && (missing0 = "targets") || data.eligibility_reason === void 0 && (missing0 = "eligibility_reason") || data.requests === void 0 && (missing0 = "requests") || data.winner_kind === void 0 && (missing0 = "winner_kind") || data.winner_reason === void 0 && (missing0 = "winner_reason")) {
            validate21.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "checkpoint_id" || key0 === "eligibility_reason" || key0 === "reference" || key0 === "requests" || key0 === "targets" || key0 === "winner_kind" || key0 === "winner_reason")) {
                validate21.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.checkpoint_id !== void 0) {
                let data0 = data.checkpoint_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate21.errors = [{ instancePath: instancePath + "/checkpoint_id", schemaPath: "#/properties/checkpoint_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate21.errors = [{ instancePath: instancePath + "/checkpoint_id", schemaPath: "#/properties/checkpoint_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate21.errors = [{ instancePath: instancePath + "/checkpoint_id", schemaPath: "#/properties/checkpoint_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate21.errors = [{ instancePath: instancePath + "/checkpoint_id", schemaPath: "#/properties/checkpoint_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.eligibility_reason !== void 0) {
                  let data1 = data.eligibility_reason;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  const _errs6 = errors;
                  if (errors === _errs6) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        const err0 = { instancePath: instancePath + "/eligibility_reason", schemaPath: "#/properties/eligibility_reason/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        if (func1(data1) < 1) {
                          const err1 = { instancePath: instancePath + "/eligibility_reason", schemaPath: "#/properties/eligibility_reason/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                          if (vErrors === null) {
                            vErrors = [err1];
                          } else {
                            vErrors.push(err1);
                          }
                          errors++;
                        } else {
                          if (!pattern4.test(data1)) {
                            const err2 = { instancePath: instancePath + "/eligibility_reason", schemaPath: "#/properties/eligibility_reason/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                      const err3 = { instancePath: instancePath + "/eligibility_reason", schemaPath: "#/properties/eligibility_reason/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err3];
                      } else {
                        vErrors.push(err3);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs6 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs8 = errors;
                  if (data1 !== null) {
                    const err4 = { instancePath: instancePath + "/eligibility_reason", schemaPath: "#/properties/eligibility_reason/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                  }
                  var _valid0 = _errs8 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err5 = { instancePath: instancePath + "/eligibility_reason", schemaPath: "#/properties/eligibility_reason/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err5];
                    } else {
                      vErrors.push(err5);
                    }
                    errors++;
                    validate21.errors = vErrors;
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
                    const _errs10 = errors;
                    if (!validate22(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate22.errors : vErrors.concat(validate22.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs10 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.requests !== void 0) {
                      let data3 = data.requests;
                      const _errs11 = errors;
                      if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                        validate21.errors = [{ instancePath: instancePath + "/requests", schemaPath: "#/properties/requests/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      if (errors === _errs11) {
                        if (typeof data3 == "number" && isFinite(data3)) {
                          if (data3 > 9007199254740991 || isNaN(data3)) {
                            validate21.errors = [{ instancePath: instancePath + "/requests", schemaPath: "#/properties/requests/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                            return false;
                          } else {
                            if (data3 < 0 || isNaN(data3)) {
                              validate21.errors = [{ instancePath: instancePath + "/requests", schemaPath: "#/properties/requests/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                              return false;
                            }
                          }
                        }
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.targets !== void 0) {
                        let data4 = data.targets;
                        const _errs13 = errors;
                        if (errors === _errs13) {
                          if (Array.isArray(data4)) {
                            if (data4.length > 64) {
                              validate21.errors = [{ instancePath: instancePath + "/targets", schemaPath: "#/properties/targets/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                              return false;
                            } else {
                              if (data4.length < 1) {
                                validate21.errors = [{ instancePath: instancePath + "/targets", schemaPath: "#/properties/targets/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                                return false;
                              } else {
                                var valid2 = true;
                                const len0 = data4.length;
                                for (let i0 = 0; i0 < len0; i0++) {
                                  let data5 = data4[i0];
                                  const _errs15 = errors;
                                  if (errors === _errs15) {
                                    if (typeof data5 === "string") {
                                      if (!pattern10.test(data5)) {
                                        validate21.errors = [{ instancePath: instancePath + "/targets/" + i0, schemaPath: "#/properties/targets/items/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                        return false;
                                      }
                                    } else {
                                      validate21.errors = [{ instancePath: instancePath + "/targets/" + i0, schemaPath: "#/properties/targets/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid2 = _errs15 === errors;
                                  if (!valid2) {
                                    break;
                                  }
                                }
                              }
                            }
                          } else {
                            validate21.errors = [{ instancePath: instancePath + "/targets", schemaPath: "#/properties/targets/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs13 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.winner_kind !== void 0) {
                          let data6 = data.winner_kind;
                          const _errs17 = errors;
                          const _errs18 = errors;
                          let valid3 = false;
                          const _errs19 = errors;
                          if (typeof data6 !== "string") {
                            const err6 = { instancePath: instancePath + "/winner_kind", schemaPath: "#/properties/winner_kind/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err6];
                            } else {
                              vErrors.push(err6);
                            }
                            errors++;
                          }
                          if (!(data6 === "model_accepted" || data6 === "fallback" || data6 === "cancelled")) {
                            const err7 = { instancePath: instancePath + "/winner_kind", schemaPath: "#/properties/winner_kind/anyOf/0/enum", keyword: "enum", params: { allowedValues: schema32.properties.winner_kind.anyOf[0].enum }, message: "must be equal to one of the allowed values" };
                            if (vErrors === null) {
                              vErrors = [err7];
                            } else {
                              vErrors.push(err7);
                            }
                            errors++;
                          }
                          var _valid1 = _errs19 === errors;
                          valid3 = valid3 || _valid1;
                          const _errs21 = errors;
                          if (data6 !== null) {
                            const err8 = { instancePath: instancePath + "/winner_kind", schemaPath: "#/properties/winner_kind/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err8];
                            } else {
                              vErrors.push(err8);
                            }
                            errors++;
                          }
                          var _valid1 = _errs21 === errors;
                          valid3 = valid3 || _valid1;
                          if (!valid3) {
                            const err9 = { instancePath: instancePath + "/winner_kind", schemaPath: "#/properties/winner_kind/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err9];
                            } else {
                              vErrors.push(err9);
                            }
                            errors++;
                            validate21.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs18;
                            if (vErrors !== null) {
                              if (_errs18) {
                                vErrors.length = _errs18;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs17 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.winner_reason !== void 0) {
                            let data7 = data.winner_reason;
                            const _errs23 = errors;
                            const _errs24 = errors;
                            let valid4 = false;
                            const _errs25 = errors;
                            if (errors === _errs25) {
                              if (typeof data7 === "string") {
                                if (func1(data7) > 128) {
                                  const err10 = { instancePath: instancePath + "/winner_reason", schemaPath: "#/properties/winner_reason/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                  if (vErrors === null) {
                                    vErrors = [err10];
                                  } else {
                                    vErrors.push(err10);
                                  }
                                  errors++;
                                } else {
                                  if (func1(data7) < 1) {
                                    const err11 = { instancePath: instancePath + "/winner_reason", schemaPath: "#/properties/winner_reason/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                    if (vErrors === null) {
                                      vErrors = [err11];
                                    } else {
                                      vErrors.push(err11);
                                    }
                                    errors++;
                                  } else {
                                    if (!pattern4.test(data7)) {
                                      const err12 = { instancePath: instancePath + "/winner_reason", schemaPath: "#/properties/winner_reason/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                      if (vErrors === null) {
                                        vErrors = [err12];
                                      } else {
                                        vErrors.push(err12);
                                      }
                                      errors++;
                                    }
                                  }
                                }
                              } else {
                                const err13 = { instancePath: instancePath + "/winner_reason", schemaPath: "#/properties/winner_reason/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err13];
                                } else {
                                  vErrors.push(err13);
                                }
                                errors++;
                              }
                            }
                            var _valid2 = _errs25 === errors;
                            valid4 = valid4 || _valid2;
                            const _errs27 = errors;
                            if (data7 !== null) {
                              const err14 = { instancePath: instancePath + "/winner_reason", schemaPath: "#/properties/winner_reason/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                              if (vErrors === null) {
                                vErrors = [err14];
                              } else {
                                vErrors.push(err14);
                              }
                              errors++;
                            }
                            var _valid2 = _errs27 === errors;
                            valid4 = valid4 || _valid2;
                            if (!valid4) {
                              const err15 = { instancePath: instancePath + "/winner_reason", schemaPath: "#/properties/winner_reason/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                              if (vErrors === null) {
                                vErrors = [err15];
                              } else {
                                vErrors.push(err15);
                              }
                              errors++;
                              validate21.errors = vErrors;
                              return false;
                            } else {
                              errors = _errs24;
                              if (vErrors !== null) {
                                if (_errs24) {
                                  vErrors.length = _errs24;
                                } else {
                                  vErrors = null;
                                }
                              }
                            }
                            var valid0 = _errs23 === errors;
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
          validate21.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate21.errors = vErrors;
      return errors === 0;
    }
    validate21.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.revision === void 0 && (missing0 = "revision") || data.frontier_revision === void 0 && (missing0 = "frontier_revision")) {
            validate26.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "frontier_revision" || key0 === "plan_sha256" || key0 === "revision" || key0 === "run_id" || key0 === "scope")) {
                validate26.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.frontier_revision !== void 0) {
                let data0 = data.frontier_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate26.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate26.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate26.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                if (data.plan_sha256 !== void 0) {
                  let data1 = data.plan_sha256;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (!pattern10.test(data1)) {
                        validate26.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate26.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate26.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate26.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate26.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                    if (data.run_id !== void 0) {
                      let data3 = data.run_id;
                      const _errs8 = errors;
                      if (errors === _errs8) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 128) {
                            validate26.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate26.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern4.test(data3)) {
                                validate26.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate26.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
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
                              validate26.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate26.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                      if (func1(data5) > 128) {
                                        validate26.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate26.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data5)) {
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
                                        if (func1(data6) > 128) {
                                          validate26.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate26.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data6)) {
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
                                    var valid2 = _errs16 === errors;
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
          if (data.cut === void 0 && (missing0 = "cut") || data.epoch === void 0 && (missing0 = "epoch") || data.snapshot_token === void 0 && (missing0 = "snapshot_token")) {
            validate25.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "cut" || key0 === "epoch" || key0 === "snapshot_token")) {
                validate25.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.cut !== void 0) {
                const _errs2 = errors;
                if (!validate26(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.epoch !== void 0) {
                  let data1 = data.epoch;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (!pattern10.test(data1)) {
                        validate25.errors = [{ instancePath: instancePath + "/epoch", schemaPath: "#/properties/epoch/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate25.errors = [{ instancePath: instancePath + "/epoch", schemaPath: "#/properties/epoch/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.snapshot_token !== void 0) {
                    let data2 = data.snapshot_token;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 4096) {
                          validate25.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate25.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          }
                        }
                      } else {
                        validate25.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          validate25.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate25.errors = vErrors;
      return errors === 0;
    }
    validate25.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.snapshot === void 0 && (missing0 = "snapshot") || data.total === void 0 && (missing0 = "total") || data.items === void 0 && (missing0 = "items") || data.next_cursor === void 0 && (missing0 = "next_cursor")) {
            validate20.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "items" || key0 === "next_cursor" || key0 === "schema_version" || key0 === "snapshot" || key0 === "total")) {
                validate20.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.items !== void 0) {
                let data0 = data.items;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 10) {
                      validate20.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/maxItems", keyword: "maxItems", params: { limit: 10 }, message: "must NOT have more than 10 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate21(data0[i0], { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate20.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.next_cursor !== void 0) {
                  let data2 = data.next_cursor;
                  const _errs5 = errors;
                  const _errs6 = errors;
                  let valid2 = false;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (typeof data2 === "string") {
                      if (func1(data2) > 4096) {
                        const err0 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        if (func1(data2) < 1) {
                          const err1 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                          if (vErrors === null) {
                            vErrors = [err1];
                          } else {
                            vErrors.push(err1);
                          }
                          errors++;
                        }
                      }
                    } else {
                      const err2 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err2];
                      } else {
                        vErrors.push(err2);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs7 === errors;
                  valid2 = valid2 || _valid0;
                  const _errs9 = errors;
                  if (data2 !== null) {
                    const err3 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid2 = valid2 || _valid0;
                  if (!valid2) {
                    const err4 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
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
                  if (data.schema_version !== void 0) {
                    let data3 = data.schema_version;
                    const _errs11 = errors;
                    if (typeof data3 !== "string") {
                      validate20.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("1" !== data3) {
                      validate20.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs11 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.snapshot !== void 0) {
                      const _errs13 = errors;
                      if (!validate25(data.snapshot, { instancePath: instancePath + "/snapshot", parentData: data, parentDataProperty: "snapshot", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate25.errors : vErrors.concat(validate25.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs13 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.total !== void 0) {
                        let data5 = data.total;
                        const _errs14 = errors;
                        if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                          validate20.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                          return false;
                        }
                        if (errors === _errs14) {
                          if (typeof data5 == "number" && isFinite(data5)) {
                            if (data5 > 9007199254740991 || isNaN(data5)) {
                              validate20.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                              return false;
                            } else {
                              if (data5 < 0 || isNaN(data5)) {
                                validate20.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                return false;
                              }
                            }
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
    exports.requests = validate29;
    var schema39 = { "additionalProperties": false, "properties": { "attempts": { "items": { "$ref": "#/$defs/CheckpointInspectionAttempt" }, "maxItems": 16, "title": "Attempts", "type": "array" }, "context_entries": { "maximum": 128, "minimum": 0, "title": "Context Entries", "type": "integer" }, "context_omissions": { "maximum": 128, "minimum": 0, "title": "Context Omissions", "type": "integer" }, "disposition": { "anyOf": [{ "enum": ["repair", "fallback"], "type": "string" }, { "type": "null" }], "title": "Disposition" }, "disposition_reason": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Disposition Reason" }, "engagement": { "$ref": "#/$defs/EngagementRef" }, "limits": { "$ref": "#/$defs/CallLimits" }, "lineage": { "$ref": "#/$defs/SupervisionLineage" }, "model": { "$ref": "#/$defs/ModelBinding" }, "planning_request_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Planning Request Sha256", "type": "string" }, "prompt": { "$ref": "#/$defs/ArtifactRef" }, "report_stop_reason": { "anyOf": [{ "enum": ["proposed", "abstained", "policy_rejected", "attempt_limit", "checkpoint_deadline", "execution_processing_unavailable", "required_artifact_unavailable", "required_packet_size", "required_input_limit", "budget_template_unavailable", "provider_unconfigured", "token_budget_exhausted", "accounting_budget_exhausted", "provider_usage_overage", "repair_attempt_budget_exhausted", "repair_token_budget_exhausted", "repair_accounting_budget_exhausted"], "type": "string" }, { "type": "null" }], "title": "Report Stop Reason" }, "request_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Request Sha256", "type": "string" }, "responses": { "maximum": 9007199254740991, "minimum": 0, "title": "Responses", "type": "integer" } }, "required": ["request_sha256", "lineage", "engagement", "planning_request_sha256", "model", "prompt", "limits", "context_entries", "context_omissions", "report_stop_reason", "attempts", "responses", "disposition", "disposition_reason"], "title": "CheckpointRequestItem", "type": "object" };
    var schema40 = { "additionalProperties": false, "properties": { "observation_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Observation Sha256", "type": "string" }, "ordinal": { "maximum": 16, "minimum": 1, "title": "Ordinal", "type": "integer" }, "status": { "enum": ["proposed", "abstained", "invalid", "unavailable", "policy_rejected", "unknown"], "title": "Status", "type": "string" } }, "required": ["ordinal", "status", "observation_sha256"], "title": "CheckpointInspectionAttempt", "type": "object" };
    var func25 = Object.prototype.hasOwnProperty;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.engagement_id === void 0 && (missing0 = "engagement_id")) {
            validate31.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "engagement_id" || key0 === "scope")) {
                validate31.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (func1(data0) > 128) {
                      validate31.errors = [{ instancePath: instancePath + "/engagement_id", schemaPath: "#/properties/engagement_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate31.errors = [{ instancePath: instancePath + "/engagement_id", schemaPath: "#/properties/engagement_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate31.errors = [{ instancePath: instancePath + "/engagement_id", schemaPath: "#/properties/engagement_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate31.errors = [{ instancePath: instancePath + "/engagement_id", schemaPath: "#/properties/engagement_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate31.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                        return false;
                      } else {
                        const _errs7 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "project_id" || key1 === "tenant_id")) {
                            validate31.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                  validate31.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data2) < 1) {
                                    validate31.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data2)) {
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
                                    validate31.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate31.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
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
                              var valid2 = _errs10 === errors;
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
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate34.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate34.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate34.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate34.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate34.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate34.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate34.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate34.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern26.test(data1)) {
                            validate34.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate34.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate34.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate34.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate34.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate34.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate34.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate34.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate34.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate34.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate34.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate34.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate34.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate34.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate34.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate34.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate34.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
                                          validate34.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate34.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        validate34.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate34.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
                                            validate34.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate34.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate34.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                              validate34.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate34.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate34.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate34.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate34.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          if (data.provider_id === void 0 && (missing0 = "provider_id") || data.model_id === void 0 && (missing0 = "model_id") || data.model_revision === void 0 && (missing0 = "model_revision") || data.configuration === void 0 && (missing0 = "configuration") || data.tokenizer === void 0 && (missing0 = "tokenizer") || data.context_window_tokens === void 0 && (missing0 = "context_window_tokens")) {
            validate33.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "configuration" || key0 === "context_window_tokens" || key0 === "model_id" || key0 === "model_revision" || key0 === "provider_id" || key0 === "tokenizer")) {
                validate33.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.configuration !== void 0) {
                const _errs2 = errors;
                if (!validate34(data.configuration, { instancePath: instancePath + "/configuration", parentData: data, parentDataProperty: "configuration", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate34.errors : vErrors.concat(validate34.errors);
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
                    validate33.errors = [{ instancePath: instancePath + "/context_window_tokens", schemaPath: "#/properties/context_window_tokens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 16777216 || isNaN(data1)) {
                        validate33.errors = [{ instancePath: instancePath + "/context_window_tokens", schemaPath: "#/properties/context_window_tokens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16777216 }, message: "must be <= 16777216" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate33.errors = [{ instancePath: instancePath + "/context_window_tokens", schemaPath: "#/properties/context_window_tokens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                        if (func1(data2) > 128) {
                          validate33.errors = [{ instancePath: instancePath + "/model_id", schemaPath: "#/properties/model_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate33.errors = [{ instancePath: instancePath + "/model_id", schemaPath: "#/properties/model_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern4.test(data2)) {
                              validate33.errors = [{ instancePath: instancePath + "/model_id", schemaPath: "#/properties/model_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate33.errors = [{ instancePath: instancePath + "/model_id", schemaPath: "#/properties/model_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          if (func1(data3) > 128) {
                            validate33.errors = [{ instancePath: instancePath + "/model_revision", schemaPath: "#/properties/model_revision/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate33.errors = [{ instancePath: instancePath + "/model_revision", schemaPath: "#/properties/model_revision/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern4.test(data3)) {
                                validate33.errors = [{ instancePath: instancePath + "/model_revision", schemaPath: "#/properties/model_revision/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate33.errors = [{ instancePath: instancePath + "/model_revision", schemaPath: "#/properties/model_revision/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            if (func1(data4) > 128) {
                              validate33.errors = [{ instancePath: instancePath + "/provider_id", schemaPath: "#/properties/provider_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func1(data4) < 1) {
                                validate33.errors = [{ instancePath: instancePath + "/provider_id", schemaPath: "#/properties/provider_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern4.test(data4)) {
                                  validate33.errors = [{ instancePath: instancePath + "/provider_id", schemaPath: "#/properties/provider_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate33.errors = [{ instancePath: instancePath + "/provider_id", schemaPath: "#/properties/provider_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                validate33.errors = [{ instancePath: instancePath + "/tokenizer", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                return false;
                              } else {
                                const _errs14 = errors;
                                for (const key1 in data5) {
                                  if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                                    validate33.errors = [{ instancePath: instancePath + "/tokenizer", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                        if (func1(data6) > 128) {
                                          validate33.errors = [{ instancePath: instancePath + "/tokenizer/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate33.errors = [{ instancePath: instancePath + "/tokenizer/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data6)) {
                                              validate33.errors = [{ instancePath: instancePath + "/tokenizer/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate33.errors = [{ instancePath: instancePath + "/tokenizer/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                          if (!pattern10.test(data7)) {
                                            validate33.errors = [{ instancePath: instancePath + "/tokenizer/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                            return false;
                                          }
                                        } else {
                                          validate33.errors = [{ instancePath: instancePath + "/tokenizer/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                          validate33.errors = [{ instancePath: instancePath + "/tokenizer/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        if ("1" !== data8) {
                                          validate33.errors = [{ instancePath: instancePath + "/tokenizer/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                              validate33.errors = [{ instancePath: instancePath + "/tokenizer", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate33.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate33.errors = vErrors;
      return errors === 0;
    }
    validate33.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.lineage === void 0 && (missing0 = "lineage") || data.engagement === void 0 && (missing0 = "engagement") || data.planning_request_sha256 === void 0 && (missing0 = "planning_request_sha256") || data.model === void 0 && (missing0 = "model") || data.prompt === void 0 && (missing0 = "prompt") || data.limits === void 0 && (missing0 = "limits") || data.context_entries === void 0 && (missing0 = "context_entries") || data.context_omissions === void 0 && (missing0 = "context_omissions") || data.report_stop_reason === void 0 && (missing0 = "report_stop_reason") || data.attempts === void 0 && (missing0 = "attempts") || data.responses === void 0 && (missing0 = "responses") || data.disposition === void 0 && (missing0 = "disposition") || data.disposition_reason === void 0 && (missing0 = "disposition_reason")) {
            validate30.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func25.call(schema39.properties, key0)) {
                validate30.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (data0.length > 16) {
                      validate30.errors = [{ instancePath: instancePath + "/attempts", schemaPath: "#/properties/attempts/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
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
                            if (data1.ordinal === void 0 && (missing1 = "ordinal") || data1.status === void 0 && (missing1 = "status") || data1.observation_sha256 === void 0 && (missing1 = "observation_sha256")) {
                              validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0, schemaPath: "#/$defs/CheckpointInspectionAttempt/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs7 = errors;
                              for (const key1 in data1) {
                                if (!(key1 === "observation_sha256" || key1 === "ordinal" || key1 === "status")) {
                                  validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0, schemaPath: "#/$defs/CheckpointInspectionAttempt/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs7 === errors) {
                                if (data1.observation_sha256 !== void 0) {
                                  let data2 = data1.observation_sha256;
                                  const _errs8 = errors;
                                  if (errors === _errs8) {
                                    if (typeof data2 === "string") {
                                      if (!pattern10.test(data2)) {
                                        validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/observation_sha256", schemaPath: "#/$defs/CheckpointInspectionAttempt/properties/observation_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                        return false;
                                      }
                                    } else {
                                      validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/observation_sha256", schemaPath: "#/$defs/CheckpointInspectionAttempt/properties/observation_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid3 = _errs8 === errors;
                                } else {
                                  var valid3 = true;
                                }
                                if (valid3) {
                                  if (data1.ordinal !== void 0) {
                                    let data3 = data1.ordinal;
                                    const _errs10 = errors;
                                    if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                      validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/ordinal", schemaPath: "#/$defs/CheckpointInspectionAttempt/properties/ordinal/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                      return false;
                                    }
                                    if (errors === _errs10) {
                                      if (typeof data3 == "number" && isFinite(data3)) {
                                        if (data3 > 16 || isNaN(data3)) {
                                          validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/ordinal", schemaPath: "#/$defs/CheckpointInspectionAttempt/properties/ordinal/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                                          return false;
                                        } else {
                                          if (data3 < 1 || isNaN(data3)) {
                                            validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/ordinal", schemaPath: "#/$defs/CheckpointInspectionAttempt/properties/ordinal/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                                    if (data1.status !== void 0) {
                                      let data4 = data1.status;
                                      const _errs12 = errors;
                                      if (typeof data4 !== "string") {
                                        validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/status", schemaPath: "#/$defs/CheckpointInspectionAttempt/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if (!(data4 === "proposed" || data4 === "abstained" || data4 === "invalid" || data4 === "unavailable" || data4 === "policy_rejected" || data4 === "unknown")) {
                                        validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/status", schemaPath: "#/$defs/CheckpointInspectionAttempt/properties/status/enum", keyword: "enum", params: { allowedValues: schema40.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                                        return false;
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
                            validate30.errors = [{ instancePath: instancePath + "/attempts/" + i0, schemaPath: "#/$defs/CheckpointInspectionAttempt/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                    validate30.errors = [{ instancePath: instancePath + "/attempts", schemaPath: "#/properties/attempts/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.context_entries !== void 0) {
                  let data5 = data.context_entries;
                  const _errs14 = errors;
                  if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                    validate30.errors = [{ instancePath: instancePath + "/context_entries", schemaPath: "#/properties/context_entries/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs14) {
                    if (typeof data5 == "number" && isFinite(data5)) {
                      if (data5 > 128 || isNaN(data5)) {
                        validate30.errors = [{ instancePath: instancePath + "/context_entries", schemaPath: "#/properties/context_entries/maximum", keyword: "maximum", params: { comparison: "<=", limit: 128 }, message: "must be <= 128" }];
                        return false;
                      } else {
                        if (data5 < 0 || isNaN(data5)) {
                          validate30.errors = [{ instancePath: instancePath + "/context_entries", schemaPath: "#/properties/context_entries/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                          return false;
                        }
                      }
                    }
                  }
                  var valid0 = _errs14 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.context_omissions !== void 0) {
                    let data6 = data.context_omissions;
                    const _errs16 = errors;
                    if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                      validate30.errors = [{ instancePath: instancePath + "/context_omissions", schemaPath: "#/properties/context_omissions/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs16) {
                      if (typeof data6 == "number" && isFinite(data6)) {
                        if (data6 > 128 || isNaN(data6)) {
                          validate30.errors = [{ instancePath: instancePath + "/context_omissions", schemaPath: "#/properties/context_omissions/maximum", keyword: "maximum", params: { comparison: "<=", limit: 128 }, message: "must be <= 128" }];
                          return false;
                        } else {
                          if (data6 < 0 || isNaN(data6)) {
                            validate30.errors = [{ instancePath: instancePath + "/context_omissions", schemaPath: "#/properties/context_omissions/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs16 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.disposition !== void 0) {
                      let data7 = data.disposition;
                      const _errs18 = errors;
                      const _errs19 = errors;
                      let valid4 = false;
                      const _errs20 = errors;
                      if (typeof data7 !== "string") {
                        const err0 = { instancePath: instancePath + "/disposition", schemaPath: "#/properties/disposition/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      }
                      if (!(data7 === "repair" || data7 === "fallback")) {
                        const err1 = { instancePath: instancePath + "/disposition", schemaPath: "#/properties/disposition/anyOf/0/enum", keyword: "enum", params: { allowedValues: schema39.properties.disposition.anyOf[0].enum }, message: "must be equal to one of the allowed values" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      }
                      var _valid0 = _errs20 === errors;
                      valid4 = valid4 || _valid0;
                      const _errs22 = errors;
                      if (data7 !== null) {
                        const err2 = { instancePath: instancePath + "/disposition", schemaPath: "#/properties/disposition/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err2];
                        } else {
                          vErrors.push(err2);
                        }
                        errors++;
                      }
                      var _valid0 = _errs22 === errors;
                      valid4 = valid4 || _valid0;
                      if (!valid4) {
                        const err3 = { instancePath: instancePath + "/disposition", schemaPath: "#/properties/disposition/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err3];
                        } else {
                          vErrors.push(err3);
                        }
                        errors++;
                        validate30.errors = vErrors;
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
                    if (valid0) {
                      if (data.disposition_reason !== void 0) {
                        let data8 = data.disposition_reason;
                        const _errs24 = errors;
                        const _errs25 = errors;
                        let valid5 = false;
                        const _errs26 = errors;
                        if (errors === _errs26) {
                          if (typeof data8 === "string") {
                            if (func1(data8) > 128) {
                              const err4 = { instancePath: instancePath + "/disposition_reason", schemaPath: "#/properties/disposition_reason/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                              if (vErrors === null) {
                                vErrors = [err4];
                              } else {
                                vErrors.push(err4);
                              }
                              errors++;
                            } else {
                              if (func1(data8) < 1) {
                                const err5 = { instancePath: instancePath + "/disposition_reason", schemaPath: "#/properties/disposition_reason/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                if (vErrors === null) {
                                  vErrors = [err5];
                                } else {
                                  vErrors.push(err5);
                                }
                                errors++;
                              } else {
                                if (!pattern4.test(data8)) {
                                  const err6 = { instancePath: instancePath + "/disposition_reason", schemaPath: "#/properties/disposition_reason/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                            const err7 = { instancePath: instancePath + "/disposition_reason", schemaPath: "#/properties/disposition_reason/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                            if (vErrors === null) {
                              vErrors = [err7];
                            } else {
                              vErrors.push(err7);
                            }
                            errors++;
                          }
                        }
                        var _valid1 = _errs26 === errors;
                        valid5 = valid5 || _valid1;
                        const _errs28 = errors;
                        if (data8 !== null) {
                          const err8 = { instancePath: instancePath + "/disposition_reason", schemaPath: "#/properties/disposition_reason/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err8];
                          } else {
                            vErrors.push(err8);
                          }
                          errors++;
                        }
                        var _valid1 = _errs28 === errors;
                        valid5 = valid5 || _valid1;
                        if (!valid5) {
                          const err9 = { instancePath: instancePath + "/disposition_reason", schemaPath: "#/properties/disposition_reason/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err9];
                          } else {
                            vErrors.push(err9);
                          }
                          errors++;
                          validate30.errors = vErrors;
                          return false;
                        } else {
                          errors = _errs25;
                          if (vErrors !== null) {
                            if (_errs25) {
                              vErrors.length = _errs25;
                            } else {
                              vErrors = null;
                            }
                          }
                        }
                        var valid0 = _errs24 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.engagement !== void 0) {
                          const _errs30 = errors;
                          if (!validate31(data.engagement, { instancePath: instancePath + "/engagement", parentData: data, parentDataProperty: "engagement", rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate31.errors : vErrors.concat(validate31.errors);
                            errors = vErrors.length;
                          }
                          var valid0 = _errs30 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.limits !== void 0) {
                            let data10 = data.limits;
                            const _errs31 = errors;
                            const _errs32 = errors;
                            if (errors === _errs32) {
                              if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                                let missing2;
                                if (data10.max_input_tokens === void 0 && (missing2 = "max_input_tokens") || data10.max_output_tokens === void 0 && (missing2 = "max_output_tokens") || data10.max_attempts === void 0 && (missing2 = "max_attempts") || data10.total_tokens === void 0 && (missing2 = "total_tokens") || data10.total_accounting_units === void 0 && (missing2 = "total_accounting_units") || data10.accounting_unit === void 0 && (missing2 = "accounting_unit")) {
                                  validate30.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/CallLimits/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                  return false;
                                } else {
                                  const _errs34 = errors;
                                  for (const key2 in data10) {
                                    if (!(key2 === "accounting_unit" || key2 === "max_attempts" || key2 === "max_input_tokens" || key2 === "max_output_tokens" || key2 === "total_accounting_units" || key2 === "total_tokens")) {
                                      validate30.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/CallLimits/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                      return false;
                                      break;
                                    }
                                  }
                                  if (_errs34 === errors) {
                                    if (data10.accounting_unit !== void 0) {
                                      let data11 = data10.accounting_unit;
                                      const _errs35 = errors;
                                      if (errors === _errs35) {
                                        if (typeof data11 === "string") {
                                          if (func1(data11) > 128) {
                                            validate30.errors = [{ instancePath: instancePath + "/limits/accounting_unit", schemaPath: "#/$defs/CallLimits/properties/accounting_unit/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                            return false;
                                          } else {
                                            if (func1(data11) < 1) {
                                              validate30.errors = [{ instancePath: instancePath + "/limits/accounting_unit", schemaPath: "#/$defs/CallLimits/properties/accounting_unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                              return false;
                                            } else {
                                              if (!pattern4.test(data11)) {
                                                validate30.errors = [{ instancePath: instancePath + "/limits/accounting_unit", schemaPath: "#/$defs/CallLimits/properties/accounting_unit/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                return false;
                                              }
                                            }
                                          }
                                        } else {
                                          validate30.errors = [{ instancePath: instancePath + "/limits/accounting_unit", schemaPath: "#/$defs/CallLimits/properties/accounting_unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                      }
                                      var valid7 = _errs35 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                    if (valid7) {
                                      if (data10.max_attempts !== void 0) {
                                        let data12 = data10.max_attempts;
                                        const _errs37 = errors;
                                        if (!(typeof data12 == "number" && (!(data12 % 1) && !isNaN(data12)) && isFinite(data12))) {
                                          validate30.errors = [{ instancePath: instancePath + "/limits/max_attempts", schemaPath: "#/$defs/CallLimits/properties/max_attempts/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                          return false;
                                        }
                                        if (errors === _errs37) {
                                          if (typeof data12 == "number" && isFinite(data12)) {
                                            if (data12 > 16 || isNaN(data12)) {
                                              validate30.errors = [{ instancePath: instancePath + "/limits/max_attempts", schemaPath: "#/$defs/CallLimits/properties/max_attempts/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                                              return false;
                                            } else {
                                              if (data12 < 1 || isNaN(data12)) {
                                                validate30.errors = [{ instancePath: instancePath + "/limits/max_attempts", schemaPath: "#/$defs/CallLimits/properties/max_attempts/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                                return false;
                                              }
                                            }
                                          }
                                        }
                                        var valid7 = _errs37 === errors;
                                      } else {
                                        var valid7 = true;
                                      }
                                      if (valid7) {
                                        if (data10.max_input_tokens !== void 0) {
                                          let data13 = data10.max_input_tokens;
                                          const _errs39 = errors;
                                          if (!(typeof data13 == "number" && (!(data13 % 1) && !isNaN(data13)) && isFinite(data13))) {
                                            validate30.errors = [{ instancePath: instancePath + "/limits/max_input_tokens", schemaPath: "#/$defs/CallLimits/properties/max_input_tokens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                            return false;
                                          }
                                          if (errors === _errs39) {
                                            if (typeof data13 == "number" && isFinite(data13)) {
                                              if (data13 > 16777216 || isNaN(data13)) {
                                                validate30.errors = [{ instancePath: instancePath + "/limits/max_input_tokens", schemaPath: "#/$defs/CallLimits/properties/max_input_tokens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16777216 }, message: "must be <= 16777216" }];
                                                return false;
                                              } else {
                                                if (data13 < 1 || isNaN(data13)) {
                                                  validate30.errors = [{ instancePath: instancePath + "/limits/max_input_tokens", schemaPath: "#/$defs/CallLimits/properties/max_input_tokens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                                  return false;
                                                }
                                              }
                                            }
                                          }
                                          var valid7 = _errs39 === errors;
                                        } else {
                                          var valid7 = true;
                                        }
                                        if (valid7) {
                                          if (data10.max_output_tokens !== void 0) {
                                            let data14 = data10.max_output_tokens;
                                            const _errs41 = errors;
                                            if (!(typeof data14 == "number" && (!(data14 % 1) && !isNaN(data14)) && isFinite(data14))) {
                                              validate30.errors = [{ instancePath: instancePath + "/limits/max_output_tokens", schemaPath: "#/$defs/CallLimits/properties/max_output_tokens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                              return false;
                                            }
                                            if (errors === _errs41) {
                                              if (typeof data14 == "number" && isFinite(data14)) {
                                                if (data14 > 16777216 || isNaN(data14)) {
                                                  validate30.errors = [{ instancePath: instancePath + "/limits/max_output_tokens", schemaPath: "#/$defs/CallLimits/properties/max_output_tokens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16777216 }, message: "must be <= 16777216" }];
                                                  return false;
                                                } else {
                                                  if (data14 < 1 || isNaN(data14)) {
                                                    validate30.errors = [{ instancePath: instancePath + "/limits/max_output_tokens", schemaPath: "#/$defs/CallLimits/properties/max_output_tokens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            }
                                            var valid7 = _errs41 === errors;
                                          } else {
                                            var valid7 = true;
                                          }
                                          if (valid7) {
                                            if (data10.total_accounting_units !== void 0) {
                                              let data15 = data10.total_accounting_units;
                                              const _errs43 = errors;
                                              if (!(typeof data15 == "number" && (!(data15 % 1) && !isNaN(data15)) && isFinite(data15))) {
                                                validate30.errors = [{ instancePath: instancePath + "/limits/total_accounting_units", schemaPath: "#/$defs/CallLimits/properties/total_accounting_units/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                return false;
                                              }
                                              if (errors === _errs43) {
                                                if (typeof data15 == "number" && isFinite(data15)) {
                                                  if (data15 > 9007199254740991 || isNaN(data15)) {
                                                    validate30.errors = [{ instancePath: instancePath + "/limits/total_accounting_units", schemaPath: "#/$defs/CallLimits/properties/total_accounting_units/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                                    return false;
                                                  } else {
                                                    if (data15 < 1 || isNaN(data15)) {
                                                      validate30.errors = [{ instancePath: instancePath + "/limits/total_accounting_units", schemaPath: "#/$defs/CallLimits/properties/total_accounting_units/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                                      return false;
                                                    }
                                                  }
                                                }
                                              }
                                              var valid7 = _errs43 === errors;
                                            } else {
                                              var valid7 = true;
                                            }
                                            if (valid7) {
                                              if (data10.total_tokens !== void 0) {
                                                let data16 = data10.total_tokens;
                                                const _errs45 = errors;
                                                if (!(typeof data16 == "number" && (!(data16 % 1) && !isNaN(data16)) && isFinite(data16))) {
                                                  validate30.errors = [{ instancePath: instancePath + "/limits/total_tokens", schemaPath: "#/$defs/CallLimits/properties/total_tokens/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                                  return false;
                                                }
                                                if (errors === _errs45) {
                                                  if (typeof data16 == "number" && isFinite(data16)) {
                                                    if (data16 > 268435456 || isNaN(data16)) {
                                                      validate30.errors = [{ instancePath: instancePath + "/limits/total_tokens", schemaPath: "#/$defs/CallLimits/properties/total_tokens/maximum", keyword: "maximum", params: { comparison: "<=", limit: 268435456 }, message: "must be <= 268435456" }];
                                                      return false;
                                                    } else {
                                                      if (data16 < 1 || isNaN(data16)) {
                                                        validate30.errors = [{ instancePath: instancePath + "/limits/total_tokens", schemaPath: "#/$defs/CallLimits/properties/total_tokens/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                                        return false;
                                                      }
                                                    }
                                                  }
                                                }
                                                var valid7 = _errs45 === errors;
                                              } else {
                                                var valid7 = true;
                                              }
                                            }
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              } else {
                                validate30.errors = [{ instancePath: instancePath + "/limits", schemaPath: "#/$defs/CallLimits/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                return false;
                              }
                            }
                            var valid0 = _errs31 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.lineage !== void 0) {
                              let data17 = data.lineage;
                              const _errs47 = errors;
                              const _errs48 = errors;
                              if (errors === _errs48) {
                                if (data17 && typeof data17 == "object" && !Array.isArray(data17)) {
                                  let missing3;
                                  if (data17.ordinal === void 0 && (missing3 = "ordinal") || data17.root_request_sha256 === void 0 && (missing3 = "root_request_sha256") || data17.parent_request_sha256 === void 0 && (missing3 = "parent_request_sha256")) {
                                    validate30.errors = [{ instancePath: instancePath + "/lineage", schemaPath: "#/$defs/SupervisionLineage/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" }];
                                    return false;
                                  } else {
                                    const _errs50 = errors;
                                    for (const key3 in data17) {
                                      if (!(key3 === "ordinal" || key3 === "parent_request_sha256" || key3 === "root_request_sha256")) {
                                        validate30.errors = [{ instancePath: instancePath + "/lineage", schemaPath: "#/$defs/SupervisionLineage/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" }];
                                        return false;
                                        break;
                                      }
                                    }
                                    if (_errs50 === errors) {
                                      if (data17.ordinal !== void 0) {
                                        let data18 = data17.ordinal;
                                        const _errs51 = errors;
                                        if (!(typeof data18 == "number" && (!(data18 % 1) && !isNaN(data18)) && isFinite(data18))) {
                                          validate30.errors = [{ instancePath: instancePath + "/lineage/ordinal", schemaPath: "#/$defs/SupervisionLineage/properties/ordinal/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                          return false;
                                        }
                                        if (errors === _errs51) {
                                          if (typeof data18 == "number" && isFinite(data18)) {
                                            if (data18 > 16 || isNaN(data18)) {
                                              validate30.errors = [{ instancePath: instancePath + "/lineage/ordinal", schemaPath: "#/$defs/SupervisionLineage/properties/ordinal/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                                              return false;
                                            } else {
                                              if (data18 < 1 || isNaN(data18)) {
                                                validate30.errors = [{ instancePath: instancePath + "/lineage/ordinal", schemaPath: "#/$defs/SupervisionLineage/properties/ordinal/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                                return false;
                                              }
                                            }
                                          }
                                        }
                                        var valid9 = _errs51 === errors;
                                      } else {
                                        var valid9 = true;
                                      }
                                      if (valid9) {
                                        if (data17.parent_request_sha256 !== void 0) {
                                          let data19 = data17.parent_request_sha256;
                                          const _errs53 = errors;
                                          const _errs54 = errors;
                                          let valid10 = false;
                                          const _errs55 = errors;
                                          if (errors === _errs55) {
                                            if (typeof data19 === "string") {
                                              if (!pattern10.test(data19)) {
                                                const err10 = { instancePath: instancePath + "/lineage/parent_request_sha256", schemaPath: "#/$defs/SupervisionLineage/properties/parent_request_sha256/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                                if (vErrors === null) {
                                                  vErrors = [err10];
                                                } else {
                                                  vErrors.push(err10);
                                                }
                                                errors++;
                                              }
                                            } else {
                                              const err11 = { instancePath: instancePath + "/lineage/parent_request_sha256", schemaPath: "#/$defs/SupervisionLineage/properties/parent_request_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                              if (vErrors === null) {
                                                vErrors = [err11];
                                              } else {
                                                vErrors.push(err11);
                                              }
                                              errors++;
                                            }
                                          }
                                          var _valid2 = _errs55 === errors;
                                          valid10 = valid10 || _valid2;
                                          const _errs57 = errors;
                                          if (data19 !== null) {
                                            const err12 = { instancePath: instancePath + "/lineage/parent_request_sha256", schemaPath: "#/$defs/SupervisionLineage/properties/parent_request_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                            if (vErrors === null) {
                                              vErrors = [err12];
                                            } else {
                                              vErrors.push(err12);
                                            }
                                            errors++;
                                          }
                                          var _valid2 = _errs57 === errors;
                                          valid10 = valid10 || _valid2;
                                          if (!valid10) {
                                            const err13 = { instancePath: instancePath + "/lineage/parent_request_sha256", schemaPath: "#/$defs/SupervisionLineage/properties/parent_request_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                            if (vErrors === null) {
                                              vErrors = [err13];
                                            } else {
                                              vErrors.push(err13);
                                            }
                                            errors++;
                                            validate30.errors = vErrors;
                                            return false;
                                          } else {
                                            errors = _errs54;
                                            if (vErrors !== null) {
                                              if (_errs54) {
                                                vErrors.length = _errs54;
                                              } else {
                                                vErrors = null;
                                              }
                                            }
                                          }
                                          var valid9 = _errs53 === errors;
                                        } else {
                                          var valid9 = true;
                                        }
                                        if (valid9) {
                                          if (data17.root_request_sha256 !== void 0) {
                                            let data20 = data17.root_request_sha256;
                                            const _errs59 = errors;
                                            const _errs60 = errors;
                                            let valid11 = false;
                                            const _errs61 = errors;
                                            if (errors === _errs61) {
                                              if (typeof data20 === "string") {
                                                if (!pattern10.test(data20)) {
                                                  const err14 = { instancePath: instancePath + "/lineage/root_request_sha256", schemaPath: "#/$defs/SupervisionLineage/properties/root_request_sha256/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                                  if (vErrors === null) {
                                                    vErrors = [err14];
                                                  } else {
                                                    vErrors.push(err14);
                                                  }
                                                  errors++;
                                                }
                                              } else {
                                                const err15 = { instancePath: instancePath + "/lineage/root_request_sha256", schemaPath: "#/$defs/SupervisionLineage/properties/root_request_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                if (vErrors === null) {
                                                  vErrors = [err15];
                                                } else {
                                                  vErrors.push(err15);
                                                }
                                                errors++;
                                              }
                                            }
                                            var _valid3 = _errs61 === errors;
                                            valid11 = valid11 || _valid3;
                                            const _errs63 = errors;
                                            if (data20 !== null) {
                                              const err16 = { instancePath: instancePath + "/lineage/root_request_sha256", schemaPath: "#/$defs/SupervisionLineage/properties/root_request_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                              if (vErrors === null) {
                                                vErrors = [err16];
                                              } else {
                                                vErrors.push(err16);
                                              }
                                              errors++;
                                            }
                                            var _valid3 = _errs63 === errors;
                                            valid11 = valid11 || _valid3;
                                            if (!valid11) {
                                              const err17 = { instancePath: instancePath + "/lineage/root_request_sha256", schemaPath: "#/$defs/SupervisionLineage/properties/root_request_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                              if (vErrors === null) {
                                                vErrors = [err17];
                                              } else {
                                                vErrors.push(err17);
                                              }
                                              errors++;
                                              validate30.errors = vErrors;
                                              return false;
                                            } else {
                                              errors = _errs60;
                                              if (vErrors !== null) {
                                                if (_errs60) {
                                                  vErrors.length = _errs60;
                                                } else {
                                                  vErrors = null;
                                                }
                                              }
                                            }
                                            var valid9 = _errs59 === errors;
                                          } else {
                                            var valid9 = true;
                                          }
                                        }
                                      }
                                    }
                                  }
                                } else {
                                  validate30.errors = [{ instancePath: instancePath + "/lineage", schemaPath: "#/$defs/SupervisionLineage/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs47 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.model !== void 0) {
                                const _errs65 = errors;
                                if (!validate33(data.model, { instancePath: instancePath + "/model", parentData: data, parentDataProperty: "model", rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate33.errors : vErrors.concat(validate33.errors);
                                  errors = vErrors.length;
                                }
                                var valid0 = _errs65 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.planning_request_sha256 !== void 0) {
                                  let data22 = data.planning_request_sha256;
                                  const _errs66 = errors;
                                  if (errors === _errs66) {
                                    if (typeof data22 === "string") {
                                      if (!pattern10.test(data22)) {
                                        validate30.errors = [{ instancePath: instancePath + "/planning_request_sha256", schemaPath: "#/properties/planning_request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                        return false;
                                      }
                                    } else {
                                      validate30.errors = [{ instancePath: instancePath + "/planning_request_sha256", schemaPath: "#/properties/planning_request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid0 = _errs66 === errors;
                                } else {
                                  var valid0 = true;
                                }
                                if (valid0) {
                                  if (data.prompt !== void 0) {
                                    const _errs68 = errors;
                                    if (!validate34(data.prompt, { instancePath: instancePath + "/prompt", parentData: data, parentDataProperty: "prompt", rootData, dynamicAnchors })) {
                                      vErrors = vErrors === null ? validate34.errors : vErrors.concat(validate34.errors);
                                      errors = vErrors.length;
                                    }
                                    var valid0 = _errs68 === errors;
                                  } else {
                                    var valid0 = true;
                                  }
                                  if (valid0) {
                                    if (data.report_stop_reason !== void 0) {
                                      let data24 = data.report_stop_reason;
                                      const _errs69 = errors;
                                      const _errs70 = errors;
                                      let valid12 = false;
                                      const _errs71 = errors;
                                      if (typeof data24 !== "string") {
                                        const err18 = { instancePath: instancePath + "/report_stop_reason", schemaPath: "#/properties/report_stop_reason/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err18];
                                        } else {
                                          vErrors.push(err18);
                                        }
                                        errors++;
                                      }
                                      if (!(data24 === "proposed" || data24 === "abstained" || data24 === "policy_rejected" || data24 === "attempt_limit" || data24 === "checkpoint_deadline" || data24 === "execution_processing_unavailable" || data24 === "required_artifact_unavailable" || data24 === "required_packet_size" || data24 === "required_input_limit" || data24 === "budget_template_unavailable" || data24 === "provider_unconfigured" || data24 === "token_budget_exhausted" || data24 === "accounting_budget_exhausted" || data24 === "provider_usage_overage" || data24 === "repair_attempt_budget_exhausted" || data24 === "repair_token_budget_exhausted" || data24 === "repair_accounting_budget_exhausted")) {
                                        const err19 = { instancePath: instancePath + "/report_stop_reason", schemaPath: "#/properties/report_stop_reason/anyOf/0/enum", keyword: "enum", params: { allowedValues: schema39.properties.report_stop_reason.anyOf[0].enum }, message: "must be equal to one of the allowed values" };
                                        if (vErrors === null) {
                                          vErrors = [err19];
                                        } else {
                                          vErrors.push(err19);
                                        }
                                        errors++;
                                      }
                                      var _valid4 = _errs71 === errors;
                                      valid12 = valid12 || _valid4;
                                      const _errs73 = errors;
                                      if (data24 !== null) {
                                        const err20 = { instancePath: instancePath + "/report_stop_reason", schemaPath: "#/properties/report_stop_reason/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                        if (vErrors === null) {
                                          vErrors = [err20];
                                        } else {
                                          vErrors.push(err20);
                                        }
                                        errors++;
                                      }
                                      var _valid4 = _errs73 === errors;
                                      valid12 = valid12 || _valid4;
                                      if (!valid12) {
                                        const err21 = { instancePath: instancePath + "/report_stop_reason", schemaPath: "#/properties/report_stop_reason/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                        if (vErrors === null) {
                                          vErrors = [err21];
                                        } else {
                                          vErrors.push(err21);
                                        }
                                        errors++;
                                        validate30.errors = vErrors;
                                        return false;
                                      } else {
                                        errors = _errs70;
                                        if (vErrors !== null) {
                                          if (_errs70) {
                                            vErrors.length = _errs70;
                                          } else {
                                            vErrors = null;
                                          }
                                        }
                                      }
                                      var valid0 = _errs69 === errors;
                                    } else {
                                      var valid0 = true;
                                    }
                                    if (valid0) {
                                      if (data.request_sha256 !== void 0) {
                                        let data25 = data.request_sha256;
                                        const _errs75 = errors;
                                        if (errors === _errs75) {
                                          if (typeof data25 === "string") {
                                            if (!pattern10.test(data25)) {
                                              validate30.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                              return false;
                                            }
                                          } else {
                                            validate30.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid0 = _errs75 === errors;
                                      } else {
                                        var valid0 = true;
                                      }
                                      if (valid0) {
                                        if (data.responses !== void 0) {
                                          let data26 = data.responses;
                                          const _errs77 = errors;
                                          if (!(typeof data26 == "number" && (!(data26 % 1) && !isNaN(data26)) && isFinite(data26))) {
                                            validate30.errors = [{ instancePath: instancePath + "/responses", schemaPath: "#/properties/responses/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                            return false;
                                          }
                                          if (errors === _errs77) {
                                            if (typeof data26 == "number" && isFinite(data26)) {
                                              if (data26 > 9007199254740991 || isNaN(data26)) {
                                                validate30.errors = [{ instancePath: instancePath + "/responses", schemaPath: "#/properties/responses/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                                return false;
                                              } else {
                                                if (data26 < 0 || isNaN(data26)) {
                                                  validate30.errors = [{ instancePath: instancePath + "/responses", schemaPath: "#/properties/responses/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                  return false;
                                                }
                                              }
                                            }
                                          }
                                          var valid0 = _errs77 === errors;
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
          validate30.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate30.errors = vErrors;
      return errors === 0;
    }
    validate30.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.decision_id === void 0 && (missing0 = "decision_id")) {
            validate39.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "decision_id" || key0 === "run_id" || key0 === "scope")) {
                validate39.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.decision_id !== void 0) {
                let data0 = data.decision_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate39.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate39.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate39.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate39.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data1 = data.run_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate39.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate39.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate39.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate39.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate39.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate39.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate39.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate39.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate39.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate39.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate39.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate39.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate39.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate39.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate39.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate39.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate39.errors = vErrors;
      return errors === 0;
    }
    validate39.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.revision === void 0 && (missing0 = "revision") || data.frontier_revision === void 0 && (missing0 = "frontier_revision")) {
            validate42.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "frontier_revision" || key0 === "plan_sha256" || key0 === "revision" || key0 === "run_id" || key0 === "scope")) {
                validate42.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.frontier_revision !== void 0) {
                let data0 = data.frontier_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate42.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate42.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate42.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                if (data.plan_sha256 !== void 0) {
                  let data1 = data.plan_sha256;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (!pattern10.test(data1)) {
                        validate42.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate42.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate42.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate42.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate42.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                    if (data.run_id !== void 0) {
                      let data3 = data.run_id;
                      const _errs8 = errors;
                      if (errors === _errs8) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 128) {
                            validate42.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate42.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern4.test(data3)) {
                                validate42.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate42.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
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
                              validate42.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate42.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                      if (func1(data5) > 128) {
                                        validate42.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate42.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data5)) {
                                            validate42.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate42.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        if (func1(data6) > 128) {
                                          validate42.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate42.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data6)) {
                                              validate42.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate42.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate42.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate42.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate42.errors = vErrors;
      return errors === 0;
    }
    validate42.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.cut === void 0 && (missing0 = "cut") || data.epoch === void 0 && (missing0 = "epoch") || data.snapshot_token === void 0 && (missing0 = "snapshot_token")) {
            validate41.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "cut" || key0 === "epoch" || key0 === "snapshot_token")) {
                validate41.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.cut !== void 0) {
                const _errs2 = errors;
                if (!validate42(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate42.errors : vErrors.concat(validate42.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.epoch !== void 0) {
                  let data1 = data.epoch;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (!pattern10.test(data1)) {
                        validate41.errors = [{ instancePath: instancePath + "/epoch", schemaPath: "#/properties/epoch/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate41.errors = [{ instancePath: instancePath + "/epoch", schemaPath: "#/properties/epoch/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.snapshot_token !== void 0) {
                    let data2 = data.snapshot_token;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 4096) {
                          validate41.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate41.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          }
                        }
                      } else {
                        validate41.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          validate41.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate41.errors = vErrors;
      return errors === 0;
    }
    validate41.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate29(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.snapshot === void 0 && (missing0 = "snapshot") || data.reference === void 0 && (missing0 = "reference") || data.total === void 0 && (missing0 = "total") || data.items === void 0 && (missing0 = "items") || data.next_cursor === void 0 && (missing0 = "next_cursor")) {
            validate29.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "items" || key0 === "next_cursor" || key0 === "reference" || key0 === "schema_version" || key0 === "snapshot" || key0 === "total")) {
                validate29.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.items !== void 0) {
                let data0 = data.items;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 10) {
                      validate29.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/maxItems", keyword: "maxItems", params: { limit: 10 }, message: "must NOT have more than 10 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate30(data0[i0], { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate30.errors : vErrors.concat(validate30.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate29.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.next_cursor !== void 0) {
                  let data2 = data.next_cursor;
                  const _errs5 = errors;
                  const _errs6 = errors;
                  let valid2 = false;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (typeof data2 === "string") {
                      if (func1(data2) > 4096) {
                        const err0 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        if (func1(data2) < 1) {
                          const err1 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                          if (vErrors === null) {
                            vErrors = [err1];
                          } else {
                            vErrors.push(err1);
                          }
                          errors++;
                        }
                      }
                    } else {
                      const err2 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err2];
                      } else {
                        vErrors.push(err2);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs7 === errors;
                  valid2 = valid2 || _valid0;
                  const _errs9 = errors;
                  if (data2 !== null) {
                    const err3 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid2 = valid2 || _valid0;
                  if (!valid2) {
                    const err4 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                    validate29.errors = vErrors;
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
                  if (data.reference !== void 0) {
                    const _errs11 = errors;
                    if (!validate39(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate39.errors : vErrors.concat(validate39.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs11 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.schema_version !== void 0) {
                      let data4 = data.schema_version;
                      const _errs12 = errors;
                      if (typeof data4 !== "string") {
                        validate29.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data4) {
                        validate29.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.snapshot !== void 0) {
                        const _errs14 = errors;
                        if (!validate41(data.snapshot, { instancePath: instancePath + "/snapshot", parentData: data, parentDataProperty: "snapshot", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate41.errors : vErrors.concat(validate41.errors);
                          errors = vErrors.length;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.total !== void 0) {
                          let data6 = data.total;
                          const _errs15 = errors;
                          if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                            validate29.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs15) {
                            if (typeof data6 == "number" && isFinite(data6)) {
                              if (data6 > 9007199254740991 || isNaN(data6)) {
                                validate29.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data6 < 0 || isNaN(data6)) {
                                  validate29.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                  return false;
                                }
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
    exports.context = validate45;
    var schema57 = { "additionalProperties": false, "properties": { "artifact": { "$ref": "#/$defs/ArtifactRef" }, "required": { "title": "Required", "type": "boolean" }, "role": { "enum": ["constraint", "source", "capability", "knowledge", "result"], "title": "Role", "type": "string" } }, "required": ["artifact", "role", "required"], "title": "ContextEntry", "type": "object" };
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate48.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate48.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate48.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate48.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate48.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate48.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate48.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate48.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern26.test(data1)) {
                            validate48.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate48.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate48.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate48.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate48.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate48.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate48.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate48.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate48.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate48.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate48.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate48.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate48.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate48.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate48.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate48.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate48.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
                                          validate48.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate48.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        validate48.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate48.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
                                            validate48.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate48.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate48.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                              validate48.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate48.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate48.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate48.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate48.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate48.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate48.errors = vErrors;
      return errors === 0;
    }
    validate48.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.artifact === void 0 && (missing0 = "artifact") || data.role === void 0 && (missing0 = "role") || data.required === void 0 && (missing0 = "required")) {
            validate47.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "required" || key0 === "role")) {
                validate47.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                const _errs2 = errors;
                if (!validate48(data.artifact, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
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
                    validate47.errors = [{ instancePath: instancePath + "/required", schemaPath: "#/properties/required/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
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
                      validate47.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data2 === "constraint" || data2 === "source" || data2 === "capability" || data2 === "knowledge" || data2 === "result")) {
                      validate47.errors = [{ instancePath: instancePath + "/role", schemaPath: "#/properties/role/enum", keyword: "enum", params: { allowedValues: schema57.properties.role.enum }, message: "must be equal to one of the allowed values" }];
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
          validate47.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate47.errors = vErrors;
      return errors === 0;
    }
    validate47.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate46(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
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
          if (data.kind === void 0 && (missing0 = "kind") || data.entry === void 0 && (missing0 = "entry")) {
            validate46.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entry" || key0 === "kind")) {
                validate46.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entry !== void 0) {
                const _errs2 = errors;
                if (!validate47(data.entry, { instancePath: instancePath + "/entry", parentData: data, parentDataProperty: "entry", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate47.errors : vErrors.concat(validate47.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.kind !== void 0) {
                  let data1 = data.kind;
                  const _errs3 = errors;
                  if (typeof data1 !== "string") {
                    validate46.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("included" !== data1) {
                    validate46.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "included" }, message: "must be equal to constant" }];
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
          validate46.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate46.errors = vErrors;
      return errors === 0;
    }
    validate46.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema62 = { "additionalProperties": false, "properties": { "artifact": { "$ref": "#/$defs/ArtifactRef" }, "reason": { "enum": ["budget", "not_relevant", "unavailable", "not_authorized"], "title": "Reason", "type": "string" } }, "required": ["artifact", "reason"], "title": "ContextOmission", "type": "object" };
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
          if (data.artifact === void 0 && (missing0 = "artifact") || data.reason === void 0 && (missing0 = "reason")) {
            validate53.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "reason")) {
                validate53.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                const _errs2 = errors;
                if (!validate48(data.artifact, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate48.errors : vErrors.concat(validate48.errors);
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
                    validate53.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "budget" || data1 === "not_relevant" || data1 === "unavailable" || data1 === "not_authorized")) {
                    validate53.errors = [{ instancePath: instancePath + "/reason", schemaPath: "#/properties/reason/enum", keyword: "enum", params: { allowedValues: schema62.properties.reason.enum }, message: "must be equal to one of the allowed values" }];
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
          if (data.kind === void 0 && (missing0 = "kind") || data.omission === void 0 && (missing0 = "omission")) {
            validate52.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "kind" || key0 === "omission")) {
                validate52.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.kind !== void 0) {
                let data0 = data.kind;
                const _errs2 = errors;
                if (typeof data0 !== "string") {
                  validate52.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                if ("omitted" !== data0) {
                  validate52.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "omitted" }, message: "must be equal to constant" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.omission !== void 0) {
                  const _errs4 = errors;
                  if (!validate53(data.omission, { instancePath: instancePath + "/omission", parentData: data, parentDataProperty: "omission", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate53.errors : vErrors.concat(validate53.errors);
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
          validate52.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate52.errors = vErrors;
      return errors === 0;
    }
    validate52.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.decision_id === void 0 && (missing0 = "decision_id")) {
            validate57.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "decision_id" || key0 === "run_id" || key0 === "scope")) {
                validate57.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.decision_id !== void 0) {
                let data0 = data.decision_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate57.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate57.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate57.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate57.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data1 = data.run_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate57.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate57.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate57.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate57.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate57.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate57.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate57.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate57.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate57.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate57.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate57.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate57.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate57.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate57.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate57.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate57.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate57.errors = vErrors;
      return errors === 0;
    }
    validate57.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.revision === void 0 && (missing0 = "revision") || data.frontier_revision === void 0 && (missing0 = "frontier_revision")) {
            validate60.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "frontier_revision" || key0 === "plan_sha256" || key0 === "revision" || key0 === "run_id" || key0 === "scope")) {
                validate60.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.frontier_revision !== void 0) {
                let data0 = data.frontier_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate60.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate60.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate60.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                if (data.plan_sha256 !== void 0) {
                  let data1 = data.plan_sha256;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (!pattern10.test(data1)) {
                        validate60.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate60.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate60.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate60.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate60.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                    if (data.run_id !== void 0) {
                      let data3 = data.run_id;
                      const _errs8 = errors;
                      if (errors === _errs8) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 128) {
                            validate60.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate60.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern4.test(data3)) {
                                validate60.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate60.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
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
                              validate60.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate60.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                      if (func1(data5) > 128) {
                                        validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate60.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data5)) {
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
                                        if (func1(data6) > 128) {
                                          validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate60.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data6)) {
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
                                    var valid2 = _errs16 === errors;
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
          validate60.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate60.errors = vErrors;
      return errors === 0;
    }
    validate60.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate59(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate59.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.cut === void 0 && (missing0 = "cut") || data.epoch === void 0 && (missing0 = "epoch") || data.snapshot_token === void 0 && (missing0 = "snapshot_token")) {
            validate59.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "cut" || key0 === "epoch" || key0 === "snapshot_token")) {
                validate59.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.cut !== void 0) {
                const _errs2 = errors;
                if (!validate60(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate60.errors : vErrors.concat(validate60.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.epoch !== void 0) {
                  let data1 = data.epoch;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (!pattern10.test(data1)) {
                        validate59.errors = [{ instancePath: instancePath + "/epoch", schemaPath: "#/properties/epoch/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate59.errors = [{ instancePath: instancePath + "/epoch", schemaPath: "#/properties/epoch/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.snapshot_token !== void 0) {
                    let data2 = data.snapshot_token;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 4096) {
                          validate59.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate59.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          }
                        }
                      } else {
                        validate59.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          validate59.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate59.errors = vErrors;
      return errors === 0;
    }
    validate59.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate45(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate45.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.snapshot === void 0 && (missing0 = "snapshot") || data.reference === void 0 && (missing0 = "reference") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.total === void 0 && (missing0 = "total") || data.items === void 0 && (missing0 = "items") || data.next_cursor === void 0 && (missing0 = "next_cursor")) {
            validate45.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "items" || key0 === "next_cursor" || key0 === "reference" || key0 === "request_sha256" || key0 === "schema_version" || key0 === "snapshot" || key0 === "total")) {
                validate45.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.items !== void 0) {
                let data0 = data.items;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 10) {
                      validate45.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/maxItems", keyword: "maxItems", params: { limit: 10 }, message: "must NOT have more than 10 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        let data1 = data0[i0];
                        const _errs4 = errors;
                        const _errs5 = errors;
                        let valid2 = false;
                        let passing0 = null;
                        const _errs6 = errors;
                        if (!validate46(data1, { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate46.errors : vErrors.concat(validate46.errors);
                          errors = vErrors.length;
                        }
                        var _valid0 = _errs6 === errors;
                        if (_valid0) {
                          valid2 = true;
                          passing0 = 0;
                          var props0 = true;
                        }
                        const _errs7 = errors;
                        if (!validate52(data1, { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate52.errors : vErrors.concat(validate52.errors);
                          errors = vErrors.length;
                        }
                        var _valid0 = _errs7 === errors;
                        if (_valid0 && valid2) {
                          valid2 = false;
                          passing0 = [passing0, 1];
                        } else {
                          if (_valid0) {
                            valid2 = true;
                            passing0 = 1;
                            if (props0 !== true) {
                              props0 = true;
                            }
                          }
                        }
                        if (!valid2) {
                          const err0 = { instancePath: instancePath + "/items/" + i0, schemaPath: "#/properties/items/items/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                          validate45.errors = vErrors;
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
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate45.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.next_cursor !== void 0) {
                  let data2 = data.next_cursor;
                  const _errs9 = errors;
                  const _errs10 = errors;
                  let valid3 = false;
                  const _errs11 = errors;
                  if (errors === _errs11) {
                    if (typeof data2 === "string") {
                      if (func1(data2) > 4096) {
                        const err1 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                        if (vErrors === null) {
                          vErrors = [err1];
                        } else {
                          vErrors.push(err1);
                        }
                        errors++;
                      } else {
                        if (func1(data2) < 1) {
                          const err2 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                          if (vErrors === null) {
                            vErrors = [err2];
                          } else {
                            vErrors.push(err2);
                          }
                          errors++;
                        }
                      }
                    } else {
                      const err3 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err3];
                      } else {
                        vErrors.push(err3);
                      }
                      errors++;
                    }
                  }
                  var _valid1 = _errs11 === errors;
                  valid3 = valid3 || _valid1;
                  const _errs13 = errors;
                  if (data2 !== null) {
                    const err4 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                  }
                  var _valid1 = _errs13 === errors;
                  valid3 = valid3 || _valid1;
                  if (!valid3) {
                    const err5 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err5];
                    } else {
                      vErrors.push(err5);
                    }
                    errors++;
                    validate45.errors = vErrors;
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
                  if (data.reference !== void 0) {
                    const _errs15 = errors;
                    if (!validate57(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate57.errors : vErrors.concat(validate57.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs15 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.request_sha256 !== void 0) {
                      let data4 = data.request_sha256;
                      const _errs16 = errors;
                      if (errors === _errs16) {
                        if (typeof data4 === "string") {
                          if (!pattern10.test(data4)) {
                            validate45.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                            return false;
                          }
                        } else {
                          validate45.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs16 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.schema_version !== void 0) {
                        let data5 = data.schema_version;
                        const _errs18 = errors;
                        if (typeof data5 !== "string") {
                          validate45.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data5) {
                          validate45.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs18 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.snapshot !== void 0) {
                          const _errs20 = errors;
                          if (!validate59(data.snapshot, { instancePath: instancePath + "/snapshot", parentData: data, parentDataProperty: "snapshot", rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate59.errors : vErrors.concat(validate59.errors);
                            errors = vErrors.length;
                          }
                          var valid0 = _errs20 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.total !== void 0) {
                            let data7 = data.total;
                            const _errs21 = errors;
                            if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                              validate45.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            if (errors === _errs21) {
                              if (typeof data7 == "number" && isFinite(data7)) {
                                if (data7 > 9007199254740991 || isNaN(data7)) {
                                  validate45.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                  return false;
                                } else {
                                  if (data7 < 0 || isNaN(data7)) {
                                    validate45.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                    return false;
                                  }
                                }
                              }
                            }
                            var valid0 = _errs21 === errors;
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
          validate45.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate45.errors = vErrors;
      return errors === 0;
    }
    validate45.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.responses = validate63;
    var schema69 = { "additionalProperties": false, "properties": { "attempt_ordinal": { "maximum": 16, "minimum": 1, "title": "Attempt Ordinal", "type": "integer" }, "capture": { "anyOf": [{ "$ref": "#/$defs/ArtifactRef" }, { "type": "null" }] }, "captured_bytes": { "maximum": 65536, "minimum": 0, "title": "Captured Bytes", "type": "integer" }, "output_complete": { "title": "Output Complete", "type": "boolean" }, "output_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Output Sha256", "type": "string" }, "reason_code": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Reason Code" }, "response_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Response Id", "type": "string" }, "response_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Response Sha256", "type": "string" }, "selected_by_winner": { "title": "Selected By Winner", "type": "boolean" }, "status": { "enum": ["proposed", "abstained", "invalid", "unavailable", "policy_rejected", "unknown"], "title": "Status", "type": "string" } }, "required": ["response_id", "response_sha256", "attempt_ordinal", "status", "reason_code", "output_sha256", "captured_bytes", "output_complete", "capture", "selected_by_winner"], "title": "CheckpointResponseItem", "type": "object" };
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate65.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate65.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate65.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate65.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate65.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate65.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate65.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate65.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern26.test(data1)) {
                            validate65.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate65.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate65.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate65.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate65.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate65.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate65.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate65.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate65.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate65.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate65.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate65.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate65.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate65.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate65.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate65.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate65.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
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
                                        validate65.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate65.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
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
                                  var valid4 = _errs22 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate65.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                              validate65.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate65.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate65.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate65.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate65.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate65.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate65.errors = vErrors;
      return errors === 0;
    }
    validate65.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.response_id === void 0 && (missing0 = "response_id") || data.response_sha256 === void 0 && (missing0 = "response_sha256") || data.attempt_ordinal === void 0 && (missing0 = "attempt_ordinal") || data.status === void 0 && (missing0 = "status") || data.reason_code === void 0 && (missing0 = "reason_code") || data.output_sha256 === void 0 && (missing0 = "output_sha256") || data.captured_bytes === void 0 && (missing0 = "captured_bytes") || data.output_complete === void 0 && (missing0 = "output_complete") || data.capture === void 0 && (missing0 = "capture") || data.selected_by_winner === void 0 && (missing0 = "selected_by_winner")) {
            validate64.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func25.call(schema69.properties, key0)) {
                validate64.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.attempt_ordinal !== void 0) {
                let data0 = data.attempt_ordinal;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate64.errors = [{ instancePath: instancePath + "/attempt_ordinal", schemaPath: "#/properties/attempt_ordinal/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 16 || isNaN(data0)) {
                      validate64.errors = [{ instancePath: instancePath + "/attempt_ordinal", schemaPath: "#/properties/attempt_ordinal/maximum", keyword: "maximum", params: { comparison: "<=", limit: 16 }, message: "must be <= 16" }];
                      return false;
                    } else {
                      if (data0 < 1 || isNaN(data0)) {
                        validate64.errors = [{ instancePath: instancePath + "/attempt_ordinal", schemaPath: "#/properties/attempt_ordinal/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                if (data.capture !== void 0) {
                  let data1 = data.capture;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  const _errs6 = errors;
                  if (!validate65(data1, { instancePath: instancePath + "/capture", parentData: data, parentDataProperty: "capture", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate65.errors : vErrors.concat(validate65.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs6 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs7 = errors;
                  if (data1 !== null) {
                    const err0 = { instancePath: instancePath + "/capture", schemaPath: "#/properties/capture/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                    const err1 = { instancePath: instancePath + "/capture", schemaPath: "#/properties/capture/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err1];
                    } else {
                      vErrors.push(err1);
                    }
                    errors++;
                    validate64.errors = vErrors;
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
                  if (data.captured_bytes !== void 0) {
                    let data2 = data.captured_bytes;
                    const _errs9 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate64.errors = [{ instancePath: instancePath + "/captured_bytes", schemaPath: "#/properties/captured_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs9) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 65536 || isNaN(data2)) {
                          validate64.errors = [{ instancePath: instancePath + "/captured_bytes", schemaPath: "#/properties/captured_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 65536 }, message: "must be <= 65536" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate64.errors = [{ instancePath: instancePath + "/captured_bytes", schemaPath: "#/properties/captured_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                            return false;
                          }
                        }
                      }
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.output_complete !== void 0) {
                      const _errs11 = errors;
                      if (typeof data.output_complete !== "boolean") {
                        validate64.errors = [{ instancePath: instancePath + "/output_complete", schemaPath: "#/properties/output_complete/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                        return false;
                      }
                      var valid0 = _errs11 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.output_sha256 !== void 0) {
                        let data4 = data.output_sha256;
                        const _errs13 = errors;
                        if (errors === _errs13) {
                          if (typeof data4 === "string") {
                            if (!pattern10.test(data4)) {
                              validate64.errors = [{ instancePath: instancePath + "/output_sha256", schemaPath: "#/properties/output_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate64.errors = [{ instancePath: instancePath + "/output_sha256", schemaPath: "#/properties/output_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs13 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.reason_code !== void 0) {
                          let data5 = data.reason_code;
                          const _errs15 = errors;
                          const _errs16 = errors;
                          let valid2 = false;
                          const _errs17 = errors;
                          if (errors === _errs17) {
                            if (typeof data5 === "string") {
                              if (func1(data5) > 128) {
                                const err2 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              } else {
                                if (func1(data5) < 1) {
                                  const err3 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                  if (vErrors === null) {
                                    vErrors = [err3];
                                  } else {
                                    vErrors.push(err3);
                                  }
                                  errors++;
                                } else {
                                  if (!pattern4.test(data5)) {
                                    const err4 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                              const err5 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err5];
                              } else {
                                vErrors.push(err5);
                              }
                              errors++;
                            }
                          }
                          var _valid1 = _errs17 === errors;
                          valid2 = valid2 || _valid1;
                          const _errs19 = errors;
                          if (data5 !== null) {
                            const err6 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err6];
                            } else {
                              vErrors.push(err6);
                            }
                            errors++;
                          }
                          var _valid1 = _errs19 === errors;
                          valid2 = valid2 || _valid1;
                          if (!valid2) {
                            const err7 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err7];
                            } else {
                              vErrors.push(err7);
                            }
                            errors++;
                            validate64.errors = vErrors;
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
                          if (data.response_id !== void 0) {
                            let data6 = data.response_id;
                            const _errs21 = errors;
                            if (errors === _errs21) {
                              if (typeof data6 === "string") {
                                if (func1(data6) > 128) {
                                  validate64.errors = [{ instancePath: instancePath + "/response_id", schemaPath: "#/properties/response_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data6) < 1) {
                                    validate64.errors = [{ instancePath: instancePath + "/response_id", schemaPath: "#/properties/response_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern4.test(data6)) {
                                      validate64.errors = [{ instancePath: instancePath + "/response_id", schemaPath: "#/properties/response_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate64.errors = [{ instancePath: instancePath + "/response_id", schemaPath: "#/properties/response_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                            }
                            var valid0 = _errs21 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.response_sha256 !== void 0) {
                              let data7 = data.response_sha256;
                              const _errs23 = errors;
                              if (errors === _errs23) {
                                if (typeof data7 === "string") {
                                  if (!pattern10.test(data7)) {
                                    validate64.errors = [{ instancePath: instancePath + "/response_sha256", schemaPath: "#/properties/response_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                    return false;
                                  }
                                } else {
                                  validate64.errors = [{ instancePath: instancePath + "/response_sha256", schemaPath: "#/properties/response_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs23 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.selected_by_winner !== void 0) {
                                const _errs25 = errors;
                                if (typeof data.selected_by_winner !== "boolean") {
                                  validate64.errors = [{ instancePath: instancePath + "/selected_by_winner", schemaPath: "#/properties/selected_by_winner/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                  return false;
                                }
                                var valid0 = _errs25 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.status !== void 0) {
                                  let data9 = data.status;
                                  const _errs27 = errors;
                                  if (typeof data9 !== "string") {
                                    validate64.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if (!(data9 === "proposed" || data9 === "abstained" || data9 === "invalid" || data9 === "unavailable" || data9 === "policy_rejected" || data9 === "unknown")) {
                                    validate64.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema69.properties.status.enum }, message: "must be equal to one of the allowed values" }];
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.decision_id === void 0 && (missing0 = "decision_id")) {
            validate68.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "decision_id" || key0 === "run_id" || key0 === "scope")) {
                validate68.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.decision_id !== void 0) {
                let data0 = data.decision_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate68.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate68.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate68.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate68.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data1 = data.run_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate68.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate68.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate68.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate68.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate68.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate68.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate68.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate68.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate68.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate68.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate68.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate68.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate68.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate68.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate68.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate68.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate68.errors = vErrors;
      return errors === 0;
    }
    validate68.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.revision === void 0 && (missing0 = "revision") || data.frontier_revision === void 0 && (missing0 = "frontier_revision")) {
            validate71.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "frontier_revision" || key0 === "plan_sha256" || key0 === "revision" || key0 === "run_id" || key0 === "scope")) {
                validate71.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.frontier_revision !== void 0) {
                let data0 = data.frontier_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate71.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate71.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate71.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                if (data.plan_sha256 !== void 0) {
                  let data1 = data.plan_sha256;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (!pattern10.test(data1)) {
                        validate71.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate71.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate71.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate71.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate71.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                    if (data.run_id !== void 0) {
                      let data3 = data.run_id;
                      const _errs8 = errors;
                      if (errors === _errs8) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 128) {
                            validate71.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate71.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern4.test(data3)) {
                                validate71.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate71.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
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
                              validate71.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate71.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                      if (func1(data5) > 128) {
                                        validate71.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate71.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data5)) {
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
                                        if (func1(data6) > 128) {
                                          validate71.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate71.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern4.test(data6)) {
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
                                    var valid2 = _errs16 === errors;
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
          validate71.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate71.errors = vErrors;
      return errors === 0;
    }
    validate71.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.cut === void 0 && (missing0 = "cut") || data.epoch === void 0 && (missing0 = "epoch") || data.snapshot_token === void 0 && (missing0 = "snapshot_token")) {
            validate70.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "cut" || key0 === "epoch" || key0 === "snapshot_token")) {
                validate70.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.cut !== void 0) {
                const _errs2 = errors;
                if (!validate71(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate71.errors : vErrors.concat(validate71.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.epoch !== void 0) {
                  let data1 = data.epoch;
                  const _errs3 = errors;
                  if (errors === _errs3) {
                    if (typeof data1 === "string") {
                      if (!pattern10.test(data1)) {
                        validate70.errors = [{ instancePath: instancePath + "/epoch", schemaPath: "#/properties/epoch/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate70.errors = [{ instancePath: instancePath + "/epoch", schemaPath: "#/properties/epoch/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.snapshot_token !== void 0) {
                    let data2 = data.snapshot_token;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 4096) {
                          validate70.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate70.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          }
                        }
                      } else {
                        validate70.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          validate70.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate70.errors = vErrors;
      return errors === 0;
    }
    validate70.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate63(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.snapshot === void 0 && (missing0 = "snapshot") || data.reference === void 0 && (missing0 = "reference") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.total === void 0 && (missing0 = "total") || data.items === void 0 && (missing0 = "items") || data.next_cursor === void 0 && (missing0 = "next_cursor")) {
            validate63.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "items" || key0 === "next_cursor" || key0 === "reference" || key0 === "request_sha256" || key0 === "schema_version" || key0 === "snapshot" || key0 === "total")) {
                validate63.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.items !== void 0) {
                let data0 = data.items;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 10) {
                      validate63.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/maxItems", keyword: "maxItems", params: { limit: 10 }, message: "must NOT have more than 10 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate64(data0[i0], { instancePath: instancePath + "/items/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
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
                    validate63.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.next_cursor !== void 0) {
                  let data2 = data.next_cursor;
                  const _errs5 = errors;
                  const _errs6 = errors;
                  let valid2 = false;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (typeof data2 === "string") {
                      if (func1(data2) > 4096) {
                        const err0 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        if (func1(data2) < 1) {
                          const err1 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                          if (vErrors === null) {
                            vErrors = [err1];
                          } else {
                            vErrors.push(err1);
                          }
                          errors++;
                        }
                      }
                    } else {
                      const err2 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                      if (vErrors === null) {
                        vErrors = [err2];
                      } else {
                        vErrors.push(err2);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs7 === errors;
                  valid2 = valid2 || _valid0;
                  const _errs9 = errors;
                  if (data2 !== null) {
                    const err3 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                  var _valid0 = _errs9 === errors;
                  valid2 = valid2 || _valid0;
                  if (!valid2) {
                    const err4 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
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
                  if (data.reference !== void 0) {
                    const _errs11 = errors;
                    if (!validate68(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate68.errors : vErrors.concat(validate68.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs11 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.request_sha256 !== void 0) {
                      let data4 = data.request_sha256;
                      const _errs12 = errors;
                      if (errors === _errs12) {
                        if (typeof data4 === "string") {
                          if (!pattern10.test(data4)) {
                            validate63.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                            return false;
                          }
                        } else {
                          validate63.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                      }
                      var valid0 = _errs12 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.schema_version !== void 0) {
                        let data5 = data.schema_version;
                        const _errs14 = errors;
                        if (typeof data5 !== "string") {
                          validate63.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data5) {
                          validate63.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs14 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.snapshot !== void 0) {
                          const _errs16 = errors;
                          if (!validate70(data.snapshot, { instancePath: instancePath + "/snapshot", parentData: data, parentDataProperty: "snapshot", rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate70.errors : vErrors.concat(validate70.errors);
                            errors = vErrors.length;
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.total !== void 0) {
                            let data7 = data.total;
                            const _errs17 = errors;
                            if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                              validate63.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            if (errors === _errs17) {
                              if (typeof data7 == "number" && isFinite(data7)) {
                                if (data7 > 9007199254740991 || isNaN(data7)) {
                                  validate63.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                  return false;
                                } else {
                                  if (data7 < 0 || isNaN(data7)) {
                                    validate63.errors = [{ instancePath: instancePath + "/total", schemaPath: "#/properties/total/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                    return false;
                                  }
                                }
                              }
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
    exports.decision = validate74;
    var schema79 = { "additionalProperties": false, "properties": { "kind": { "const": "pending", "title": "Kind", "type": "string" }, "request_sha256": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "title": "Request Sha256" }, "stage": { "enum": ["checkpoint", "requested", "dispatched", "proposed"], "title": "Stage", "type": "string" } }, "required": ["kind", "stage", "request_sha256"], "title": "CheckpointPending", "type": "object" };
    var schema95 = { "additionalProperties": false, "properties": { "action": { "enum": ["continue_unchanged", "block_target"], "title": "Action", "type": "string" }, "kind": { "const": "fallback", "title": "Kind", "type": "string" }, "reason_code": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Reason Code", "type": "string" } }, "required": ["kind", "action", "reason_code"], "title": "CheckpointFallback", "type": "object" };
    var pattern90 = new RegExp("^-?(?:(?:0|[1-9][0-9]{0,99})(?:\\.[0-9]{1,324})?|10{100})$", "u");
    function validate77(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate77.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.field_name === void 0 && (missing0 = "field_name") || data.previous_value_sha256 === void 0 && (missing0 = "previous_value_sha256") || data.value === void 0 && (missing0 = "value")) {
            validate77.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "field_name" || key0 === "previous_value_sha256" || key0 === "value")) {
                validate77.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.field_name !== void 0) {
                let data0 = data.field_name;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate77.errors = [{ instancePath: instancePath + "/field_name", schemaPath: "#/properties/field_name/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate77.errors = [{ instancePath: instancePath + "/field_name", schemaPath: "#/properties/field_name/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate77.errors = [{ instancePath: instancePath + "/field_name", schemaPath: "#/properties/field_name/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate77.errors = [{ instancePath: instancePath + "/field_name", schemaPath: "#/properties/field_name/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.previous_value_sha256 !== void 0) {
                  let data1 = data.previous_value_sha256;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (!pattern10.test(data1)) {
                        validate77.errors = [{ instancePath: instancePath + "/previous_value_sha256", schemaPath: "#/properties/previous_value_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate77.errors = [{ instancePath: instancePath + "/previous_value_sha256", schemaPath: "#/properties/previous_value_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.value !== void 0) {
                    let data2 = data.value;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    let valid1 = false;
                    let passing0 = null;
                    const _errs8 = errors;
                    const _errs9 = errors;
                    if (errors === _errs9) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.kind === void 0 && (missing1 = "kind") || data2.value === void 0 && (missing1 = "value")) {
                          const err0 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/BooleanConstant/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                          if (vErrors === null) {
                            vErrors = [err0];
                          } else {
                            vErrors.push(err0);
                          }
                          errors++;
                        } else {
                          const _errs11 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "kind" || key1 === "value")) {
                              const err1 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/BooleanConstant/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                            if (data2.kind !== void 0) {
                              let data3 = data2.kind;
                              const _errs12 = errors;
                              if (typeof data3 !== "string") {
                                const err2 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/BooleanConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err2];
                                } else {
                                  vErrors.push(err2);
                                }
                                errors++;
                              }
                              if ("boolean" !== data3) {
                                const err3 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/BooleanConstant/properties/kind/const", keyword: "const", params: { allowedValue: "boolean" }, message: "must be equal to constant" };
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
                              if (data2.value !== void 0) {
                                const _errs14 = errors;
                                if (typeof data2.value !== "boolean") {
                                  const err4 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/BooleanConstant/properties/value/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" };
                                  if (vErrors === null) {
                                    vErrors = [err4];
                                  } else {
                                    vErrors.push(err4);
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
                        const err5 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/BooleanConstant/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs8 === errors;
                    if (_valid0) {
                      valid1 = true;
                      passing0 = 0;
                      var props0 = true;
                    }
                    const _errs16 = errors;
                    const _errs17 = errors;
                    if (errors === _errs17) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing2;
                        if (data2.kind === void 0 && (missing2 = "kind") || data2.value === void 0 && (missing2 = "value")) {
                          const err6 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/IntegerConstant/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                          if (vErrors === null) {
                            vErrors = [err6];
                          } else {
                            vErrors.push(err6);
                          }
                          errors++;
                        } else {
                          const _errs19 = errors;
                          for (const key2 in data2) {
                            if (!(key2 === "kind" || key2 === "unit" || key2 === "value")) {
                              const err7 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/IntegerConstant/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                              if (vErrors === null) {
                                vErrors = [err7];
                              } else {
                                vErrors.push(err7);
                              }
                              errors++;
                              break;
                            }
                          }
                          if (_errs19 === errors) {
                            if (data2.kind !== void 0) {
                              let data5 = data2.kind;
                              const _errs20 = errors;
                              if (typeof data5 !== "string") {
                                const err8 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/IntegerConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err8];
                                } else {
                                  vErrors.push(err8);
                                }
                                errors++;
                              }
                              if ("integer" !== data5) {
                                const err9 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/IntegerConstant/properties/kind/const", keyword: "const", params: { allowedValue: "integer" }, message: "must be equal to constant" };
                                if (vErrors === null) {
                                  vErrors = [err9];
                                } else {
                                  vErrors.push(err9);
                                }
                                errors++;
                              }
                              var valid5 = _errs20 === errors;
                            } else {
                              var valid5 = true;
                            }
                            if (valid5) {
                              if (data2.unit !== void 0) {
                                let data6 = data2.unit;
                                const _errs22 = errors;
                                if (errors === _errs22) {
                                  if (typeof data6 === "string") {
                                    if (func1(data6) > 64) {
                                      const err10 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err10];
                                      } else {
                                        vErrors.push(err10);
                                      }
                                      errors++;
                                    } else {
                                      if (func1(data6) < 1) {
                                        const err11 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err11];
                                        } else {
                                          vErrors.push(err11);
                                        }
                                        errors++;
                                      }
                                    }
                                  } else {
                                    const err12 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err12];
                                    } else {
                                      vErrors.push(err12);
                                    }
                                    errors++;
                                  }
                                }
                                var valid5 = _errs22 === errors;
                              } else {
                                var valid5 = true;
                              }
                              if (valid5) {
                                if (data2.value !== void 0) {
                                  let data7 = data2.value;
                                  const _errs24 = errors;
                                  if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                                    const err13 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/IntegerConstant/properties/value/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                    if (vErrors === null) {
                                      vErrors = [err13];
                                    } else {
                                      vErrors.push(err13);
                                    }
                                    errors++;
                                  }
                                  if (errors === _errs24) {
                                    if (typeof data7 == "number" && isFinite(data7)) {
                                      if (data7 > 9007199254740991 || isNaN(data7)) {
                                        const err14 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/IntegerConstant/properties/value/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" };
                                        if (vErrors === null) {
                                          vErrors = [err14];
                                        } else {
                                          vErrors.push(err14);
                                        }
                                        errors++;
                                      } else {
                                        if (data7 < -9007199254740991 || isNaN(data7)) {
                                          const err15 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/IntegerConstant/properties/value/minimum", keyword: "minimum", params: { comparison: ">=", limit: -9007199254740991 }, message: "must be >= -9007199254740991" };
                                          if (vErrors === null) {
                                            vErrors = [err15];
                                          } else {
                                            vErrors.push(err15);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  }
                                  var valid5 = _errs24 === errors;
                                } else {
                                  var valid5 = true;
                                }
                              }
                            }
                          }
                        }
                      } else {
                        const err16 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/IntegerConstant/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err16];
                        } else {
                          vErrors.push(err16);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs16 === errors;
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
                      const _errs26 = errors;
                      const _errs27 = errors;
                      if (errors === _errs27) {
                        if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                          let missing3;
                          if (data2.kind === void 0 && (missing3 = "kind") || data2.value === void 0 && (missing3 = "value")) {
                            const err17 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/NumberValue/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" };
                            if (vErrors === null) {
                              vErrors = [err17];
                            } else {
                              vErrors.push(err17);
                            }
                            errors++;
                          } else {
                            const _errs29 = errors;
                            for (const key3 in data2) {
                              if (!(key3 === "kind" || key3 === "unit" || key3 === "value")) {
                                const err18 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/NumberValue/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" };
                                if (vErrors === null) {
                                  vErrors = [err18];
                                } else {
                                  vErrors.push(err18);
                                }
                                errors++;
                                break;
                              }
                            }
                            if (_errs29 === errors) {
                              if (data2.kind !== void 0) {
                                let data8 = data2.kind;
                                const _errs30 = errors;
                                if (typeof data8 !== "string") {
                                  const err19 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/NumberValue/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err19];
                                  } else {
                                    vErrors.push(err19);
                                  }
                                  errors++;
                                }
                                if ("number" !== data8) {
                                  const err20 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/NumberValue/properties/kind/const", keyword: "const", params: { allowedValue: "number" }, message: "must be equal to constant" };
                                  if (vErrors === null) {
                                    vErrors = [err20];
                                  } else {
                                    vErrors.push(err20);
                                  }
                                  errors++;
                                }
                                var valid7 = _errs30 === errors;
                              } else {
                                var valid7 = true;
                              }
                              if (valid7) {
                                if (data2.unit !== void 0) {
                                  let data9 = data2.unit;
                                  const _errs32 = errors;
                                  if (errors === _errs32) {
                                    if (typeof data9 === "string") {
                                      if (func1(data9) > 64) {
                                        const err21 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/NumberValue/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err21];
                                        } else {
                                          vErrors.push(err21);
                                        }
                                        errors++;
                                      } else {
                                        if (func1(data9) < 1) {
                                          const err22 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/NumberValue/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err22];
                                          } else {
                                            vErrors.push(err22);
                                          }
                                          errors++;
                                        }
                                      }
                                    } else {
                                      const err23 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/NumberValue/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err23];
                                      } else {
                                        vErrors.push(err23);
                                      }
                                      errors++;
                                    }
                                  }
                                  var valid7 = _errs32 === errors;
                                } else {
                                  var valid7 = true;
                                }
                                if (valid7) {
                                  if (data2.value !== void 0) {
                                    let data10 = data2.value;
                                    const _errs34 = errors;
                                    if (errors === _errs34) {
                                      if (typeof data10 === "string") {
                                        if (func1(data10) > 427) {
                                          const err24 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/NumberValue/properties/value/maxLength", keyword: "maxLength", params: { limit: 427 }, message: "must NOT have more than 427 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err24];
                                          } else {
                                            vErrors.push(err24);
                                          }
                                          errors++;
                                        } else {
                                          if (!pattern90.test(data10)) {
                                            const err25 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/NumberValue/properties/value/pattern", keyword: "pattern", params: { pattern: "^-?(?:(?:0|[1-9][0-9]{0,99})(?:\\.[0-9]{1,324})?|10{100})$" }, message: 'must match pattern "^-?(?:(?:0|[1-9][0-9]{0,99})(?:\\.[0-9]{1,324})?|10{100})$"' };
                                            if (vErrors === null) {
                                              vErrors = [err25];
                                            } else {
                                              vErrors.push(err25);
                                            }
                                            errors++;
                                          }
                                        }
                                      } else {
                                        const err26 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/NumberValue/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err26];
                                        } else {
                                          vErrors.push(err26);
                                        }
                                        errors++;
                                      }
                                    }
                                    var valid7 = _errs34 === errors;
                                  } else {
                                    var valid7 = true;
                                  }
                                }
                              }
                            }
                          }
                        } else {
                          const err27 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/NumberValue/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                          if (vErrors === null) {
                            vErrors = [err27];
                          } else {
                            vErrors.push(err27);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs26 === errors;
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
                        const _errs36 = errors;
                        const _errs37 = errors;
                        if (errors === _errs37) {
                          if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                            let missing4;
                            if (data2.kind === void 0 && (missing4 = "kind") || data2.value === void 0 && (missing4 = "value")) {
                              const err28 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/StringConstant/required", keyword: "required", params: { missingProperty: missing4 }, message: "must have required property '" + missing4 + "'" };
                              if (vErrors === null) {
                                vErrors = [err28];
                              } else {
                                vErrors.push(err28);
                              }
                              errors++;
                            } else {
                              const _errs39 = errors;
                              for (const key4 in data2) {
                                if (!(key4 === "kind" || key4 === "value")) {
                                  const err29 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/StringConstant/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key4 }, message: "must NOT have additional properties" };
                                  if (vErrors === null) {
                                    vErrors = [err29];
                                  } else {
                                    vErrors.push(err29);
                                  }
                                  errors++;
                                  break;
                                }
                              }
                              if (_errs39 === errors) {
                                if (data2.kind !== void 0) {
                                  let data11 = data2.kind;
                                  const _errs40 = errors;
                                  if (typeof data11 !== "string") {
                                    const err30 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/StringConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err30];
                                    } else {
                                      vErrors.push(err30);
                                    }
                                    errors++;
                                  }
                                  if ("string" !== data11) {
                                    const err31 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/StringConstant/properties/kind/const", keyword: "const", params: { allowedValue: "string" }, message: "must be equal to constant" };
                                    if (vErrors === null) {
                                      vErrors = [err31];
                                    } else {
                                      vErrors.push(err31);
                                    }
                                    errors++;
                                  }
                                  var valid9 = _errs40 === errors;
                                } else {
                                  var valid9 = true;
                                }
                                if (valid9) {
                                  if (data2.value !== void 0) {
                                    let data12 = data2.value;
                                    const _errs42 = errors;
                                    if (errors === _errs42) {
                                      if (typeof data12 === "string") {
                                        if (func1(data12) > 4096) {
                                          const err32 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/StringConstant/properties/value/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err32];
                                          } else {
                                            vErrors.push(err32);
                                          }
                                          errors++;
                                        }
                                      } else {
                                        const err33 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/StringConstant/properties/value/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err33];
                                        } else {
                                          vErrors.push(err33);
                                        }
                                        errors++;
                                      }
                                    }
                                    var valid9 = _errs42 === errors;
                                  } else {
                                    var valid9 = true;
                                  }
                                }
                              }
                            }
                          } else {
                            const err34 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/StringConstant/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err34];
                            } else {
                              vErrors.push(err34);
                            }
                            errors++;
                          }
                        }
                        var _valid0 = _errs36 === errors;
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
                      const err35 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                      if (vErrors === null) {
                        vErrors = [err35];
                      } else {
                        vErrors.push(err35);
                      }
                      errors++;
                      validate77.errors = vErrors;
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
                }
              }
            }
          }
        } else {
          validate77.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate77.errors = vErrors;
      return errors === 0;
    }
    validate77.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.schema_version === void 0 && (missing0 = "schema_version") || data.node_id === void 0 && (missing0 = "node_id")) {
            validate79.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "node_id" || key0 === "occurrences" || key0 === "schema_version")) {
                validate79.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.node_id !== void 0) {
                let data0 = data.node_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate79.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate79.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate79.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate79.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.occurrences !== void 0) {
                  let data1 = data.occurrences;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (Array.isArray(data1)) {
                      if (data1.length > 16) {
                        validate79.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                        return false;
                      } else {
                        var valid1 = true;
                        const len0 = data1.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          let data2 = data1[i0];
                          const _errs6 = errors;
                          const _errs7 = errors;
                          let valid2 = false;
                          let passing0 = null;
                          const _errs8 = errors;
                          const _errs9 = errors;
                          if (errors === _errs9) {
                            if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                              let missing1;
                              if (data2.kind === void 0 && (missing1 = "kind") || data2.node_id === void 0 && (missing1 = "node_id") || data2.index === void 0 && (missing1 = "index")) {
                                const err0 = { instancePath: instancePath + "/occurrences/" + i0, schemaPath: "#/$defs/LoopOccurrence/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                                if (vErrors === null) {
                                  vErrors = [err0];
                                } else {
                                  vErrors.push(err0);
                                }
                                errors++;
                              } else {
                                const _errs11 = errors;
                                for (const key1 in data2) {
                                  if (!(key1 === "index" || key1 === "kind" || key1 === "node_id")) {
                                    const err1 = { instancePath: instancePath + "/occurrences/" + i0, schemaPath: "#/$defs/LoopOccurrence/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                                  if (data2.index !== void 0) {
                                    let data3 = data2.index;
                                    const _errs12 = errors;
                                    if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                      const err2 = { instancePath: instancePath + "/occurrences/" + i0 + "/index", schemaPath: "#/$defs/LoopOccurrence/properties/index/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                      if (vErrors === null) {
                                        vErrors = [err2];
                                      } else {
                                        vErrors.push(err2);
                                      }
                                      errors++;
                                    }
                                    if (errors === _errs12) {
                                      if (typeof data3 == "number" && isFinite(data3)) {
                                        if (data3 > 9999 || isNaN(data3)) {
                                          const err3 = { instancePath: instancePath + "/occurrences/" + i0 + "/index", schemaPath: "#/$defs/LoopOccurrence/properties/index/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9999 }, message: "must be <= 9999" };
                                          if (vErrors === null) {
                                            vErrors = [err3];
                                          } else {
                                            vErrors.push(err3);
                                          }
                                          errors++;
                                        } else {
                                          if (data3 < 0 || isNaN(data3)) {
                                            const err4 = { instancePath: instancePath + "/occurrences/" + i0 + "/index", schemaPath: "#/$defs/LoopOccurrence/properties/index/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                                    var valid4 = _errs12 === errors;
                                  } else {
                                    var valid4 = true;
                                  }
                                  if (valid4) {
                                    if (data2.kind !== void 0) {
                                      let data4 = data2.kind;
                                      const _errs14 = errors;
                                      if (typeof data4 !== "string") {
                                        const err5 = { instancePath: instancePath + "/occurrences/" + i0 + "/kind", schemaPath: "#/$defs/LoopOccurrence/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err5];
                                        } else {
                                          vErrors.push(err5);
                                        }
                                        errors++;
                                      }
                                      if ("loop" !== data4) {
                                        const err6 = { instancePath: instancePath + "/occurrences/" + i0 + "/kind", schemaPath: "#/$defs/LoopOccurrence/properties/kind/const", keyword: "const", params: { allowedValue: "loop" }, message: "must be equal to constant" };
                                        if (vErrors === null) {
                                          vErrors = [err6];
                                        } else {
                                          vErrors.push(err6);
                                        }
                                        errors++;
                                      }
                                      var valid4 = _errs14 === errors;
                                    } else {
                                      var valid4 = true;
                                    }
                                    if (valid4) {
                                      if (data2.node_id !== void 0) {
                                        let data5 = data2.node_id;
                                        const _errs16 = errors;
                                        if (errors === _errs16) {
                                          if (typeof data5 === "string") {
                                            if (func1(data5) > 128) {
                                              const err7 = { instancePath: instancePath + "/occurrences/" + i0 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                              if (vErrors === null) {
                                                vErrors = [err7];
                                              } else {
                                                vErrors.push(err7);
                                              }
                                              errors++;
                                            } else {
                                              if (func1(data5) < 1) {
                                                const err8 = { instancePath: instancePath + "/occurrences/" + i0 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                if (vErrors === null) {
                                                  vErrors = [err8];
                                                } else {
                                                  vErrors.push(err8);
                                                }
                                                errors++;
                                              } else {
                                                if (!pattern4.test(data5)) {
                                                  const err9 = { instancePath: instancePath + "/occurrences/" + i0 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                                  if (vErrors === null) {
                                                    vErrors = [err9];
                                                  } else {
                                                    vErrors.push(err9);
                                                  }
                                                  errors++;
                                                }
                                              }
                                            }
                                          } else {
                                            const err10 = { instancePath: instancePath + "/occurrences/" + i0 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                            if (vErrors === null) {
                                              vErrors = [err10];
                                            } else {
                                              vErrors.push(err10);
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
                              }
                            } else {
                              const err11 = { instancePath: instancePath + "/occurrences/" + i0, schemaPath: "#/$defs/LoopOccurrence/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                              if (vErrors === null) {
                                vErrors = [err11];
                              } else {
                                vErrors.push(err11);
                              }
                              errors++;
                            }
                          }
                          var _valid0 = _errs8 === errors;
                          if (_valid0) {
                            valid2 = true;
                            passing0 = 0;
                            var props0 = true;
                          }
                          const _errs18 = errors;
                          const _errs19 = errors;
                          if (errors === _errs19) {
                            if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                              let missing2;
                              if (data2.kind === void 0 && (missing2 = "kind") || data2.node_id === void 0 && (missing2 = "node_id") || data2.index === void 0 && (missing2 = "index") || data2.membership_sha256 === void 0 && (missing2 = "membership_sha256")) {
                                const err12 = { instancePath: instancePath + "/occurrences/" + i0, schemaPath: "#/$defs/ScatterOccurrence/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                                if (vErrors === null) {
                                  vErrors = [err12];
                                } else {
                                  vErrors.push(err12);
                                }
                                errors++;
                              } else {
                                const _errs21 = errors;
                                for (const key2 in data2) {
                                  if (!(key2 === "index" || key2 === "kind" || key2 === "membership_sha256" || key2 === "node_id")) {
                                    const err13 = { instancePath: instancePath + "/occurrences/" + i0, schemaPath: "#/$defs/ScatterOccurrence/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                                    if (vErrors === null) {
                                      vErrors = [err13];
                                    } else {
                                      vErrors.push(err13);
                                    }
                                    errors++;
                                    break;
                                  }
                                }
                                if (_errs21 === errors) {
                                  if (data2.index !== void 0) {
                                    let data6 = data2.index;
                                    const _errs22 = errors;
                                    if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                                      const err14 = { instancePath: instancePath + "/occurrences/" + i0 + "/index", schemaPath: "#/$defs/ScatterOccurrence/properties/index/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                      if (vErrors === null) {
                                        vErrors = [err14];
                                      } else {
                                        vErrors.push(err14);
                                      }
                                      errors++;
                                    }
                                    if (errors === _errs22) {
                                      if (typeof data6 == "number" && isFinite(data6)) {
                                        if (data6 > 9999 || isNaN(data6)) {
                                          const err15 = { instancePath: instancePath + "/occurrences/" + i0 + "/index", schemaPath: "#/$defs/ScatterOccurrence/properties/index/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9999 }, message: "must be <= 9999" };
                                          if (vErrors === null) {
                                            vErrors = [err15];
                                          } else {
                                            vErrors.push(err15);
                                          }
                                          errors++;
                                        } else {
                                          if (data6 < 0 || isNaN(data6)) {
                                            const err16 = { instancePath: instancePath + "/occurrences/" + i0 + "/index", schemaPath: "#/$defs/ScatterOccurrence/properties/index/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
                                            if (vErrors === null) {
                                              vErrors = [err16];
                                            } else {
                                              vErrors.push(err16);
                                            }
                                            errors++;
                                          }
                                        }
                                      }
                                    }
                                    var valid6 = _errs22 === errors;
                                  } else {
                                    var valid6 = true;
                                  }
                                  if (valid6) {
                                    if (data2.kind !== void 0) {
                                      let data7 = data2.kind;
                                      const _errs24 = errors;
                                      if (typeof data7 !== "string") {
                                        const err17 = { instancePath: instancePath + "/occurrences/" + i0 + "/kind", schemaPath: "#/$defs/ScatterOccurrence/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                        if (vErrors === null) {
                                          vErrors = [err17];
                                        } else {
                                          vErrors.push(err17);
                                        }
                                        errors++;
                                      }
                                      if ("scatter" !== data7) {
                                        const err18 = { instancePath: instancePath + "/occurrences/" + i0 + "/kind", schemaPath: "#/$defs/ScatterOccurrence/properties/kind/const", keyword: "const", params: { allowedValue: "scatter" }, message: "must be equal to constant" };
                                        if (vErrors === null) {
                                          vErrors = [err18];
                                        } else {
                                          vErrors.push(err18);
                                        }
                                        errors++;
                                      }
                                      var valid6 = _errs24 === errors;
                                    } else {
                                      var valid6 = true;
                                    }
                                    if (valid6) {
                                      if (data2.membership_sha256 !== void 0) {
                                        let data8 = data2.membership_sha256;
                                        const _errs26 = errors;
                                        if (errors === _errs26) {
                                          if (typeof data8 === "string") {
                                            if (!pattern10.test(data8)) {
                                              const err19 = { instancePath: instancePath + "/occurrences/" + i0 + "/membership_sha256", schemaPath: "#/$defs/ScatterOccurrence/properties/membership_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                              if (vErrors === null) {
                                                vErrors = [err19];
                                              } else {
                                                vErrors.push(err19);
                                              }
                                              errors++;
                                            }
                                          } else {
                                            const err20 = { instancePath: instancePath + "/occurrences/" + i0 + "/membership_sha256", schemaPath: "#/$defs/ScatterOccurrence/properties/membership_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                            if (vErrors === null) {
                                              vErrors = [err20];
                                            } else {
                                              vErrors.push(err20);
                                            }
                                            errors++;
                                          }
                                        }
                                        var valid6 = _errs26 === errors;
                                      } else {
                                        var valid6 = true;
                                      }
                                      if (valid6) {
                                        if (data2.node_id !== void 0) {
                                          let data9 = data2.node_id;
                                          const _errs28 = errors;
                                          if (errors === _errs28) {
                                            if (typeof data9 === "string") {
                                              if (func1(data9) > 128) {
                                                const err21 = { instancePath: instancePath + "/occurrences/" + i0 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                                if (vErrors === null) {
                                                  vErrors = [err21];
                                                } else {
                                                  vErrors.push(err21);
                                                }
                                                errors++;
                                              } else {
                                                if (func1(data9) < 1) {
                                                  const err22 = { instancePath: instancePath + "/occurrences/" + i0 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                  if (vErrors === null) {
                                                    vErrors = [err22];
                                                  } else {
                                                    vErrors.push(err22);
                                                  }
                                                  errors++;
                                                } else {
                                                  if (!pattern4.test(data9)) {
                                                    const err23 = { instancePath: instancePath + "/occurrences/" + i0 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                              const err24 = { instancePath: instancePath + "/occurrences/" + i0 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                              if (vErrors === null) {
                                                vErrors = [err24];
                                              } else {
                                                vErrors.push(err24);
                                              }
                                              errors++;
                                            }
                                          }
                                          var valid6 = _errs28 === errors;
                                        } else {
                                          var valid6 = true;
                                        }
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              const err25 = { instancePath: instancePath + "/occurrences/" + i0, schemaPath: "#/$defs/ScatterOccurrence/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                              if (vErrors === null) {
                                vErrors = [err25];
                              } else {
                                vErrors.push(err25);
                              }
                              errors++;
                            }
                          }
                          var _valid0 = _errs18 === errors;
                          if (_valid0 && valid2) {
                            valid2 = false;
                            passing0 = [passing0, 1];
                          } else {
                            if (_valid0) {
                              valid2 = true;
                              passing0 = 1;
                              if (props0 !== true) {
                                props0 = true;
                              }
                            }
                          }
                          if (!valid2) {
                            const err26 = { instancePath: instancePath + "/occurrences/" + i0, schemaPath: "#/properties/occurrences/items/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                            if (vErrors === null) {
                              vErrors = [err26];
                            } else {
                              vErrors.push(err26);
                            }
                            errors++;
                            validate79.errors = vErrors;
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
                          var valid1 = _errs6 === errors;
                          if (!valid1) {
                            break;
                          }
                        }
                      }
                    } else {
                      validate79.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.schema_version !== void 0) {
                    let data10 = data.schema_version;
                    const _errs31 = errors;
                    if (typeof data10 !== "string") {
                      validate79.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("2" !== data10) {
                      validate79.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "2" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs31 === errors;
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
    function validate76(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate76.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.target === void 0 && (missing0 = "target") || data.selection_sha256 === void 0 && (missing0 = "selection_sha256") || data.changes === void 0 && (missing0 = "changes")) {
            validate76.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "changes" || key0 === "kind" || key0 === "selection_sha256" || key0 === "target")) {
                validate76.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.changes !== void 0) {
                let data0 = data.changes;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 64) {
                      validate76.errors = [{ instancePath: instancePath + "/changes", schemaPath: "#/properties/changes/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                      return false;
                    } else {
                      if (data0.length < 1) {
                        validate76.errors = [{ instancePath: instancePath + "/changes", schemaPath: "#/properties/changes/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                        return false;
                      } else {
                        var valid1 = true;
                        const len0 = data0.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs4 = errors;
                          if (!validate77(data0[i0], { instancePath: instancePath + "/changes/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate77.errors : vErrors.concat(validate77.errors);
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
                    validate76.errors = [{ instancePath: instancePath + "/changes", schemaPath: "#/properties/changes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
                  const _errs5 = errors;
                  if (typeof data2 !== "string") {
                    validate76.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("adjusted_materialization_fields" !== data2) {
                    validate76.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "adjusted_materialization_fields" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.selection_sha256 !== void 0) {
                    let data3 = data.selection_sha256;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (typeof data3 === "string") {
                        if (!pattern10.test(data3)) {
                          validate76.errors = [{ instancePath: instancePath + "/selection_sha256", schemaPath: "#/properties/selection_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate76.errors = [{ instancePath: instancePath + "/selection_sha256", schemaPath: "#/properties/selection_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs7 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.target !== void 0) {
                      const _errs9 = errors;
                      if (!validate79(data.target, { instancePath: instancePath + "/target", parentData: data, parentDataProperty: "target", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate79.errors : vErrors.concat(validate79.errors);
                        errors = vErrors.length;
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
          validate76.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate76.errors = vErrors;
      return errors === 0;
    }
    validate76.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema90 = { "additionalProperties": false, "properties": { "content_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Content Sha256", "type": "string" }, "kind": { "enum": ["future_campaign", "evidence_request", "abstained"], "title": "Kind", "type": "string" }, "proposal": { "$ref": "#/$defs/ArtifactRef" } }, "required": ["kind", "proposal", "content_sha256"], "title": "RetainedProposal", "type": "object" };
    function validate83(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate83.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate83.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate83.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate83.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate83.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate83.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate83.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate83.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern26.test(data1)) {
                            validate83.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate83.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate83.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate83.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate83.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate83.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate83.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate83.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate83.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate83.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate83.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate83.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate83.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate83.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate83.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate83.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate83.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data7)) {
                                          validate83.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate83.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        validate83.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate83.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern4.test(data8)) {
                                            validate83.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate83.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate83.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                              validate83.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate83.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate83.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate83.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate83.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate83.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate83.errors = vErrors;
      return errors === 0;
    }
    validate83.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate82(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate82.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.proposal === void 0 && (missing0 = "proposal") || data.content_sha256 === void 0 && (missing0 = "content_sha256")) {
            validate82.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "content_sha256" || key0 === "kind" || key0 === "proposal")) {
                validate82.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (!pattern10.test(data0)) {
                      validate82.errors = [{ instancePath: instancePath + "/content_sha256", schemaPath: "#/properties/content_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate82.errors = [{ instancePath: instancePath + "/content_sha256", schemaPath: "#/properties/content_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
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
                    validate82.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "future_campaign" || data1 === "evidence_request" || data1 === "abstained")) {
                    validate82.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/enum", keyword: "enum", params: { allowedValues: schema90.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.proposal !== void 0) {
                    const _errs6 = errors;
                    if (!validate83(data.proposal, { instancePath: instancePath + "/proposal", parentData: data, parentDataProperty: "proposal", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate83.errors : vErrors.concat(validate83.errors);
                      errors = vErrors.length;
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
          validate82.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate82.errors = vErrors;
      return errors === 0;
    }
    validate82.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate75(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate75.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.kind === void 0 && (missing0 = "kind") || data.request_sha256 === void 0 && (missing0 = "request_sha256") || data.response_sha256 === void 0 && (missing0 = "response_sha256") || data.effect === void 0 && (missing0 = "effect")) {
            validate75.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "effect" || key0 === "kind" || key0 === "request_sha256" || key0 === "response_sha256")) {
                validate75.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.effect !== void 0) {
                let data0 = data.effect;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                let passing0 = null;
                const _errs4 = errors;
                if (!validate76(data0, { instancePath: instancePath + "/effect", parentData: data, parentDataProperty: "effect", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate76.errors : vErrors.concat(validate76.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                if (_valid0) {
                  valid1 = true;
                  passing0 = 0;
                  var props0 = true;
                }
                const _errs5 = errors;
                if (!validate82(data0, { instancePath: instancePath + "/effect", parentData: data, parentDataProperty: "effect", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate82.errors : vErrors.concat(validate82.errors);
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
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (data0 && typeof data0 == "object" && !Array.isArray(data0)) {
                      let missing1;
                      if (data0.kind === void 0 && (missing1 = "kind")) {
                        const err0 = { instancePath: instancePath + "/effect", schemaPath: "#/$defs/ContinuedUnchanged/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        const _errs9 = errors;
                        for (const key1 in data0) {
                          if (!(key1 === "kind")) {
                            const err1 = { instancePath: instancePath + "/effect", schemaPath: "#/$defs/ContinuedUnchanged/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                          if (data0.kind !== void 0) {
                            let data1 = data0.kind;
                            if (typeof data1 !== "string") {
                              const err2 = { instancePath: instancePath + "/effect/kind", schemaPath: "#/$defs/ContinuedUnchanged/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                            }
                            if ("continued" !== data1) {
                              const err3 = { instancePath: instancePath + "/effect/kind", schemaPath: "#/$defs/ContinuedUnchanged/properties/kind/const", keyword: "const", params: { allowedValue: "continued" }, message: "must be equal to constant" };
                              if (vErrors === null) {
                                vErrors = [err3];
                              } else {
                                vErrors.push(err3);
                              }
                              errors++;
                            }
                          }
                        }
                      }
                    } else {
                      const err4 = { instancePath: instancePath + "/effect", schemaPath: "#/$defs/ContinuedUnchanged/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err4];
                      } else {
                        vErrors.push(err4);
                      }
                      errors++;
                    }
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
                  const err5 = { instancePath: instancePath + "/effect", schemaPath: "#/properties/effect/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                  if (vErrors === null) {
                    vErrors = [err5];
                  } else {
                    vErrors.push(err5);
                  }
                  errors++;
                  validate75.errors = vErrors;
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
                if (data.kind !== void 0) {
                  let data2 = data.kind;
                  const _errs13 = errors;
                  if (typeof data2 !== "string") {
                    validate75.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("model_accepted" !== data2) {
                    validate75.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "model_accepted" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs13 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.request_sha256 !== void 0) {
                    let data3 = data.request_sha256;
                    const _errs15 = errors;
                    if (errors === _errs15) {
                      if (typeof data3 === "string") {
                        if (!pattern10.test(data3)) {
                          validate75.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                          return false;
                        }
                      } else {
                        validate75.errors = [{ instancePath: instancePath + "/request_sha256", schemaPath: "#/properties/request_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs15 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.response_sha256 !== void 0) {
                      let data4 = data.response_sha256;
                      const _errs17 = errors;
                      if (errors === _errs17) {
                        if (typeof data4 === "string") {
                          if (!pattern10.test(data4)) {
                            validate75.errors = [{ instancePath: instancePath + "/response_sha256", schemaPath: "#/properties/response_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                            return false;
                          }
                        } else {
                          validate75.errors = [{ instancePath: instancePath + "/response_sha256", schemaPath: "#/properties/response_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
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
          validate75.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate75.errors = vErrors;
      return errors === 0;
    }
    validate75.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.decision_id === void 0 && (missing0 = "decision_id")) {
            validate87.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "decision_id" || key0 === "run_id" || key0 === "scope")) {
                validate87.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.decision_id !== void 0) {
                let data0 = data.decision_id;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 128) {
                      validate87.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate87.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern4.test(data0)) {
                          validate87.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate87.errors = [{ instancePath: instancePath + "/decision_id", schemaPath: "#/properties/decision_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.run_id !== void 0) {
                  let data1 = data.run_id;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 128) {
                        validate87.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate87.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern4.test(data1)) {
                            validate87.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate87.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate87.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "project_id" || key1 === "tenant_id")) {
                              validate87.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate87.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate87.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern4.test(data3)) {
                                        validate87.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate87.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate87.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data4) < 1) {
                                        validate87.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern4.test(data4)) {
                                          validate87.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate87.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate87.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate87.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate87.errors = vErrors;
      return errors === 0;
    }
    validate87.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate74(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.reference === void 0 && (missing0 = "reference") || data.revision === void 0 && (missing0 = "revision") || data.checkpoint_seed_sha256 === void 0 && (missing0 = "checkpoint_seed_sha256") || data.outcome === void 0 && (missing0 = "outcome")) {
            validate74.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "checkpoint_seed_sha256" || key0 === "outcome" || key0 === "profile" || key0 === "reference" || key0 === "revision" || key0 === "schema_version")) {
                validate74.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.checkpoint_seed_sha256 !== void 0) {
                let data0 = data.checkpoint_seed_sha256;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (!pattern10.test(data0)) {
                      validate74.errors = [{ instancePath: instancePath + "/checkpoint_seed_sha256", schemaPath: "#/properties/checkpoint_seed_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate74.errors = [{ instancePath: instancePath + "/checkpoint_seed_sha256", schemaPath: "#/properties/checkpoint_seed_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.outcome !== void 0) {
                  let data1 = data.outcome;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  let passing0 = null;
                  const _errs6 = errors;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.kind === void 0 && (missing1 = "kind") || data1.stage === void 0 && (missing1 = "stage") || data1.request_sha256 === void 0 && (missing1 = "request_sha256")) {
                        const err0 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/CheckpointPending/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        const _errs9 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "kind" || key1 === "request_sha256" || key1 === "stage")) {
                            const err1 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/CheckpointPending/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                          if (data1.kind !== void 0) {
                            let data2 = data1.kind;
                            const _errs10 = errors;
                            if (typeof data2 !== "string") {
                              const err2 = { instancePath: instancePath + "/outcome/kind", schemaPath: "#/$defs/CheckpointPending/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                            }
                            if ("pending" !== data2) {
                              const err3 = { instancePath: instancePath + "/outcome/kind", schemaPath: "#/$defs/CheckpointPending/properties/kind/const", keyword: "const", params: { allowedValue: "pending" }, message: "must be equal to constant" };
                              if (vErrors === null) {
                                vErrors = [err3];
                              } else {
                                vErrors.push(err3);
                              }
                              errors++;
                            }
                            var valid3 = _errs10 === errors;
                          } else {
                            var valid3 = true;
                          }
                          if (valid3) {
                            if (data1.request_sha256 !== void 0) {
                              let data3 = data1.request_sha256;
                              const _errs12 = errors;
                              const _errs13 = errors;
                              let valid4 = false;
                              const _errs14 = errors;
                              if (errors === _errs14) {
                                if (typeof data3 === "string") {
                                  if (!pattern10.test(data3)) {
                                    const err4 = { instancePath: instancePath + "/outcome/request_sha256", schemaPath: "#/$defs/CheckpointPending/properties/request_sha256/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                    if (vErrors === null) {
                                      vErrors = [err4];
                                    } else {
                                      vErrors.push(err4);
                                    }
                                    errors++;
                                  }
                                } else {
                                  const err5 = { instancePath: instancePath + "/outcome/request_sha256", schemaPath: "#/$defs/CheckpointPending/properties/request_sha256/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err5];
                                  } else {
                                    vErrors.push(err5);
                                  }
                                  errors++;
                                }
                              }
                              var _valid1 = _errs14 === errors;
                              valid4 = valid4 || _valid1;
                              const _errs16 = errors;
                              if (data3 !== null) {
                                const err6 = { instancePath: instancePath + "/outcome/request_sha256", schemaPath: "#/$defs/CheckpointPending/properties/request_sha256/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                if (vErrors === null) {
                                  vErrors = [err6];
                                } else {
                                  vErrors.push(err6);
                                }
                                errors++;
                              }
                              var _valid1 = _errs16 === errors;
                              valid4 = valid4 || _valid1;
                              if (!valid4) {
                                const err7 = { instancePath: instancePath + "/outcome/request_sha256", schemaPath: "#/$defs/CheckpointPending/properties/request_sha256/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                if (vErrors === null) {
                                  vErrors = [err7];
                                } else {
                                  vErrors.push(err7);
                                }
                                errors++;
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
                              var valid3 = _errs12 === errors;
                            } else {
                              var valid3 = true;
                            }
                            if (valid3) {
                              if (data1.stage !== void 0) {
                                let data4 = data1.stage;
                                const _errs18 = errors;
                                if (typeof data4 !== "string") {
                                  const err8 = { instancePath: instancePath + "/outcome/stage", schemaPath: "#/$defs/CheckpointPending/properties/stage/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err8];
                                  } else {
                                    vErrors.push(err8);
                                  }
                                  errors++;
                                }
                                if (!(data4 === "checkpoint" || data4 === "requested" || data4 === "dispatched" || data4 === "proposed")) {
                                  const err9 = { instancePath: instancePath + "/outcome/stage", schemaPath: "#/$defs/CheckpointPending/properties/stage/enum", keyword: "enum", params: { allowedValues: schema79.properties.stage.enum }, message: "must be equal to one of the allowed values" };
                                  if (vErrors === null) {
                                    vErrors = [err9];
                                  } else {
                                    vErrors.push(err9);
                                  }
                                  errors++;
                                }
                                var valid3 = _errs18 === errors;
                              } else {
                                var valid3 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      const err10 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/CheckpointPending/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err10];
                      } else {
                        vErrors.push(err10);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs6 === errors;
                  if (_valid0) {
                    valid1 = true;
                    passing0 = 0;
                    var props0 = true;
                  }
                  const _errs20 = errors;
                  if (!validate75(data1, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate75.errors : vErrors.concat(validate75.errors);
                    errors = vErrors.length;
                  }
                  var _valid0 = _errs20 === errors;
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
                    const _errs21 = errors;
                    const _errs22 = errors;
                    if (errors === _errs22) {
                      if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                        let missing2;
                        if (data1.kind === void 0 && (missing2 = "kind") || data1.action === void 0 && (missing2 = "action") || data1.reason_code === void 0 && (missing2 = "reason_code")) {
                          const err11 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/CheckpointFallback/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                          if (vErrors === null) {
                            vErrors = [err11];
                          } else {
                            vErrors.push(err11);
                          }
                          errors++;
                        } else {
                          const _errs24 = errors;
                          for (const key2 in data1) {
                            if (!(key2 === "action" || key2 === "kind" || key2 === "reason_code")) {
                              const err12 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/CheckpointFallback/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                              if (vErrors === null) {
                                vErrors = [err12];
                              } else {
                                vErrors.push(err12);
                              }
                              errors++;
                              break;
                            }
                          }
                          if (_errs24 === errors) {
                            if (data1.action !== void 0) {
                              let data5 = data1.action;
                              const _errs25 = errors;
                              if (typeof data5 !== "string") {
                                const err13 = { instancePath: instancePath + "/outcome/action", schemaPath: "#/$defs/CheckpointFallback/properties/action/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err13];
                                } else {
                                  vErrors.push(err13);
                                }
                                errors++;
                              }
                              if (!(data5 === "continue_unchanged" || data5 === "block_target")) {
                                const err14 = { instancePath: instancePath + "/outcome/action", schemaPath: "#/$defs/CheckpointFallback/properties/action/enum", keyword: "enum", params: { allowedValues: schema95.properties.action.enum }, message: "must be equal to one of the allowed values" };
                                if (vErrors === null) {
                                  vErrors = [err14];
                                } else {
                                  vErrors.push(err14);
                                }
                                errors++;
                              }
                              var valid6 = _errs25 === errors;
                            } else {
                              var valid6 = true;
                            }
                            if (valid6) {
                              if (data1.kind !== void 0) {
                                let data6 = data1.kind;
                                const _errs27 = errors;
                                if (typeof data6 !== "string") {
                                  const err15 = { instancePath: instancePath + "/outcome/kind", schemaPath: "#/$defs/CheckpointFallback/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err15];
                                  } else {
                                    vErrors.push(err15);
                                  }
                                  errors++;
                                }
                                if ("fallback" !== data6) {
                                  const err16 = { instancePath: instancePath + "/outcome/kind", schemaPath: "#/$defs/CheckpointFallback/properties/kind/const", keyword: "const", params: { allowedValue: "fallback" }, message: "must be equal to constant" };
                                  if (vErrors === null) {
                                    vErrors = [err16];
                                  } else {
                                    vErrors.push(err16);
                                  }
                                  errors++;
                                }
                                var valid6 = _errs27 === errors;
                              } else {
                                var valid6 = true;
                              }
                              if (valid6) {
                                if (data1.reason_code !== void 0) {
                                  let data7 = data1.reason_code;
                                  const _errs29 = errors;
                                  if (errors === _errs29) {
                                    if (typeof data7 === "string") {
                                      if (func1(data7) > 128) {
                                        const err17 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/CheckpointFallback/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err17];
                                        } else {
                                          vErrors.push(err17);
                                        }
                                        errors++;
                                      } else {
                                        if (func1(data7) < 1) {
                                          const err18 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/CheckpointFallback/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err18];
                                          } else {
                                            vErrors.push(err18);
                                          }
                                          errors++;
                                        } else {
                                          if (!pattern4.test(data7)) {
                                            const err19 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/CheckpointFallback/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                            if (vErrors === null) {
                                              vErrors = [err19];
                                            } else {
                                              vErrors.push(err19);
                                            }
                                            errors++;
                                          }
                                        }
                                      }
                                    } else {
                                      const err20 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/CheckpointFallback/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err20];
                                      } else {
                                        vErrors.push(err20);
                                      }
                                      errors++;
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
                        const err21 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/CheckpointFallback/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                        if (vErrors === null) {
                          vErrors = [err21];
                        } else {
                          vErrors.push(err21);
                        }
                        errors++;
                      }
                    }
                    var _valid0 = _errs21 === errors;
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
                      const _errs31 = errors;
                      const _errs32 = errors;
                      if (errors === _errs32) {
                        if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                          let missing3;
                          if (data1.kind === void 0 && (missing3 = "kind") || data1.reason_code === void 0 && (missing3 = "reason_code")) {
                            const err22 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/CheckpointCancelled/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" };
                            if (vErrors === null) {
                              vErrors = [err22];
                            } else {
                              vErrors.push(err22);
                            }
                            errors++;
                          } else {
                            const _errs34 = errors;
                            for (const key3 in data1) {
                              if (!(key3 === "kind" || key3 === "reason_code")) {
                                const err23 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/CheckpointCancelled/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key3 }, message: "must NOT have additional properties" };
                                if (vErrors === null) {
                                  vErrors = [err23];
                                } else {
                                  vErrors.push(err23);
                                }
                                errors++;
                                break;
                              }
                            }
                            if (_errs34 === errors) {
                              if (data1.kind !== void 0) {
                                let data8 = data1.kind;
                                const _errs35 = errors;
                                if (typeof data8 !== "string") {
                                  const err24 = { instancePath: instancePath + "/outcome/kind", schemaPath: "#/$defs/CheckpointCancelled/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err24];
                                  } else {
                                    vErrors.push(err24);
                                  }
                                  errors++;
                                }
                                if ("cancelled" !== data8) {
                                  const err25 = { instancePath: instancePath + "/outcome/kind", schemaPath: "#/$defs/CheckpointCancelled/properties/kind/const", keyword: "const", params: { allowedValue: "cancelled" }, message: "must be equal to constant" };
                                  if (vErrors === null) {
                                    vErrors = [err25];
                                  } else {
                                    vErrors.push(err25);
                                  }
                                  errors++;
                                }
                                var valid8 = _errs35 === errors;
                              } else {
                                var valid8 = true;
                              }
                              if (valid8) {
                                if (data1.reason_code !== void 0) {
                                  let data9 = data1.reason_code;
                                  const _errs37 = errors;
                                  if (errors === _errs37) {
                                    if (typeof data9 === "string") {
                                      if (func1(data9) > 128) {
                                        const err26 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/CheckpointCancelled/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err26];
                                        } else {
                                          vErrors.push(err26);
                                        }
                                        errors++;
                                      } else {
                                        if (func1(data9) < 1) {
                                          const err27 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/CheckpointCancelled/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                          if (vErrors === null) {
                                            vErrors = [err27];
                                          } else {
                                            vErrors.push(err27);
                                          }
                                          errors++;
                                        } else {
                                          if (!pattern4.test(data9)) {
                                            const err28 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/CheckpointCancelled/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                            if (vErrors === null) {
                                              vErrors = [err28];
                                            } else {
                                              vErrors.push(err28);
                                            }
                                            errors++;
                                          }
                                        }
                                      }
                                    } else {
                                      const err29 = { instancePath: instancePath + "/outcome/reason_code", schemaPath: "#/$defs/CheckpointCancelled/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err29];
                                      } else {
                                        vErrors.push(err29);
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
                          const err30 = { instancePath: instancePath + "/outcome", schemaPath: "#/$defs/CheckpointCancelled/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                          if (vErrors === null) {
                            vErrors = [err30];
                          } else {
                            vErrors.push(err30);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs31 === errors;
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
                    const err31 = { instancePath: instancePath + "/outcome", schemaPath: "#/properties/outcome/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                    if (vErrors === null) {
                      vErrors = [err31];
                    } else {
                      vErrors.push(err31);
                    }
                    errors++;
                    validate74.errors = vErrors;
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
                  if (data.profile !== void 0) {
                    let data10 = data.profile;
                    const _errs40 = errors;
                    if (typeof data10 !== "string") {
                      validate74.errors = [{ instancePath: instancePath + "/profile", schemaPath: "#/properties/profile/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("checkpoint-decision.v1" !== data10) {
                      validate74.errors = [{ instancePath: instancePath + "/profile", schemaPath: "#/properties/profile/const", keyword: "const", params: { allowedValue: "checkpoint-decision.v1" }, message: "must be equal to constant" }];
                      return false;
                    }
                    var valid0 = _errs40 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.reference !== void 0) {
                      const _errs42 = errors;
                      if (!validate87(data.reference, { instancePath: instancePath + "/reference", parentData: data, parentDataProperty: "reference", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate87.errors : vErrors.concat(validate87.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs42 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.revision !== void 0) {
                        let data12 = data.revision;
                        const _errs43 = errors;
                        if (!(typeof data12 == "number" && (!(data12 % 1) && !isNaN(data12)) && isFinite(data12))) {
                          validate74.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                          return false;
                        }
                        if (errors === _errs43) {
                          if (typeof data12 == "number" && isFinite(data12)) {
                            if (data12 > 9007199254740991 || isNaN(data12)) {
                              validate74.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                              return false;
                            } else {
                              if (data12 < 1 || isNaN(data12)) {
                                validate74.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                                return false;
                              }
                            }
                          }
                        }
                        var valid0 = _errs43 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.schema_version !== void 0) {
                          let data13 = data.schema_version;
                          const _errs45 = errors;
                          if (typeof data13 !== "string") {
                            validate74.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("1" !== data13) {
                            validate74.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs45 === errors;
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
          validate74.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate74.errors = vErrors;
      return errors === 0;
    }
    validate74.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
  }
});
export default require_reviewed_validators();
