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
    exports.snapshot = validate20;
    var func1 = require_ucs2length().default;
    var schema32 = { "additionalProperties": false, "properties": { "activation_id": { "pattern": "^[0-9a-f]{64}$", "title": "Activation Id", "type": "string" }, "kind": { "enum": ["invoke", "branch", "join", "scatter", "iterate", "finish", "await", "artifact_project", "artifact_materialize"], "title": "Kind", "type": "string" }, "path": { "$ref": "#/$defs/ActivationPath" }, "reason_code": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Reason Code" }, "status": { "enum": ["waiting", "ready", "issued", "succeeded", "skipped", "failed", "blocked"], "title": "Status", "type": "string" } }, "required": ["activation_id", "path", "kind", "status", "reason_code"], "title": "GraphNodeViewV3", "type": "object" };
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
          if (data.schema_version === void 0 && (missing0 = "schema_version") || data.node_id === void 0 && (missing0 = "node_id")) {
            validate22.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "node_id" || key0 === "occurrences" || key0 === "schema_version")) {
                validate22.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate22.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate22.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate22.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate22.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate22.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
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
                                                if (!pattern5.test(data5)) {
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
                                            if (!pattern4.test(data8)) {
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
                                                  if (!pattern5.test(data9)) {
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
                            validate22.errors = vErrors;
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
                      validate22.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
                      validate22.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("2" !== data10) {
                      validate22.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "2" }, message: "must be equal to constant" }];
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
          if (data.activation_id === void 0 && (missing0 = "activation_id") || data.path === void 0 && (missing0 = "path") || data.kind === void 0 && (missing0 = "kind") || data.status === void 0 && (missing0 = "status") || data.reason_code === void 0 && (missing0 = "reason_code")) {
            validate21.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "activation_id" || key0 === "kind" || key0 === "path" || key0 === "reason_code" || key0 === "status")) {
                validate21.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (!pattern4.test(data0)) {
                      validate21.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate21.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate21.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "invoke" || data1 === "branch" || data1 === "join" || data1 === "scatter" || data1 === "iterate" || data1 === "finish" || data1 === "await" || data1 === "artifact_project" || data1 === "artifact_materialize")) {
                    validate21.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/enum", keyword: "enum", params: { allowedValues: schema32.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.path !== void 0) {
                    const _errs6 = errors;
                    if (!validate22(data.path, { instancePath: instancePath + "/path", parentData: data, parentDataProperty: "path", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate22.errors : vErrors.concat(validate22.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.reason_code !== void 0) {
                      let data3 = data.reason_code;
                      const _errs7 = errors;
                      const _errs8 = errors;
                      let valid1 = false;
                      const _errs9 = errors;
                      if (errors === _errs9) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 128) {
                            const err0 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                            if (vErrors === null) {
                              vErrors = [err0];
                            } else {
                              vErrors.push(err0);
                            }
                            errors++;
                          } else {
                            if (func1(data3) < 1) {
                              const err1 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                              if (vErrors === null) {
                                vErrors = [err1];
                              } else {
                                vErrors.push(err1);
                              }
                              errors++;
                            } else {
                              if (!pattern5.test(data3)) {
                                const err2 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                          const err3 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err3];
                          } else {
                            vErrors.push(err3);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs9 === errors;
                      valid1 = valid1 || _valid0;
                      const _errs11 = errors;
                      if (data3 !== null) {
                        const err4 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid0 = _errs11 === errors;
                      valid1 = valid1 || _valid0;
                      if (!valid1) {
                        const err5 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                        validate21.errors = vErrors;
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
                      if (data.status !== void 0) {
                        let data4 = data.status;
                        const _errs13 = errors;
                        if (typeof data4 !== "string") {
                          validate21.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if (!(data4 === "waiting" || data4 === "ready" || data4 === "issued" || data4 === "succeeded" || data4 === "skipped" || data4 === "failed" || data4 === "blocked")) {
                          validate21.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema32.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                          return false;
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
          validate21.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate21.errors = vErrors;
      return errors === 0;
    }
    validate21.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema36 = { "additionalProperties": false, "properties": { "budget": { "$ref": "#/$defs/GraphReadBudget" }, "cut": { "$ref": "#/$defs/GraphReadCut" }, "event_cursor": { "maxLength": 4096, "minLength": 1, "title": "Event Cursor", "type": "string" }, "node_count": { "maximum": 1e5, "minimum": 0, "title": "Node Count", "type": "integer" }, "query": { "$ref": "#/$defs/GraphReadQuery" }, "snapshot_token": { "maxLength": 4096, "minLength": 1, "title": "Snapshot Token", "type": "string" }, "status": { "enum": ["running", "completed", "cancelled", "failed", "blocked"], "title": "Status", "type": "string" } }, "required": ["cut", "status", "budget", "query", "node_count", "snapshot_token", "event_cursor"], "title": "GraphReadSnapshot", "type": "object" };
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
                      if (!pattern4.test(data1)) {
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
                              if (!pattern5.test(data3)) {
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
                                          if (!pattern5.test(data5)) {
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
                                            if (!pattern5.test(data6)) {
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
          if (data.cut === void 0 && (missing0 = "cut") || data.status === void 0 && (missing0 = "status") || data.budget === void 0 && (missing0 = "budget") || data.query === void 0 && (missing0 = "query") || data.node_count === void 0 && (missing0 = "node_count") || data.snapshot_token === void 0 && (missing0 = "snapshot_token") || data.event_cursor === void 0 && (missing0 = "event_cursor")) {
            validate25.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "budget" || key0 === "cut" || key0 === "event_cursor" || key0 === "node_count" || key0 === "query" || key0 === "snapshot_token" || key0 === "status")) {
                validate25.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (data0.limit === void 0 && (missing1 = "limit") || data0.reserved === void 0 && (missing1 = "reserved") || data0.spent === void 0 && (missing1 = "spent")) {
                      validate25.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/$defs/GraphReadBudget/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                      return false;
                    } else {
                      const _errs5 = errors;
                      for (const key1 in data0) {
                        if (!(key1 === "limit" || key1 === "reserved" || key1 === "spent")) {
                          validate25.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/$defs/GraphReadBudget/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                          return false;
                          break;
                        }
                      }
                      if (_errs5 === errors) {
                        if (data0.limit !== void 0) {
                          let data1 = data0.limit;
                          const _errs6 = errors;
                          if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                            validate25.errors = [{ instancePath: instancePath + "/budget/limit", schemaPath: "#/$defs/GraphReadBudget/properties/limit/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs6) {
                            if (typeof data1 == "number" && isFinite(data1)) {
                              if (data1 > 9007199254740991 || isNaN(data1)) {
                                validate25.errors = [{ instancePath: instancePath + "/budget/limit", schemaPath: "#/$defs/GraphReadBudget/properties/limit/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data1 < 1 || isNaN(data1)) {
                                  validate25.errors = [{ instancePath: instancePath + "/budget/limit", schemaPath: "#/$defs/GraphReadBudget/properties/limit/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          if (data0.reserved !== void 0) {
                            let data2 = data0.reserved;
                            const _errs8 = errors;
                            if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                              validate25.errors = [{ instancePath: instancePath + "/budget/reserved", schemaPath: "#/$defs/GraphReadBudget/properties/reserved/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                              return false;
                            }
                            if (errors === _errs8) {
                              if (typeof data2 == "number" && isFinite(data2)) {
                                if (data2 > 9007199254740991 || isNaN(data2)) {
                                  validate25.errors = [{ instancePath: instancePath + "/budget/reserved", schemaPath: "#/$defs/GraphReadBudget/properties/reserved/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                  return false;
                                } else {
                                  if (data2 < 0 || isNaN(data2)) {
                                    validate25.errors = [{ instancePath: instancePath + "/budget/reserved", schemaPath: "#/$defs/GraphReadBudget/properties/reserved/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                            if (data0.spent !== void 0) {
                              let data3 = data0.spent;
                              const _errs10 = errors;
                              if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                                validate25.errors = [{ instancePath: instancePath + "/budget/spent", schemaPath: "#/$defs/GraphReadBudget/properties/spent/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                return false;
                              }
                              if (errors === _errs10) {
                                if (typeof data3 == "number" && isFinite(data3)) {
                                  if (data3 > 9007199254740991 || isNaN(data3)) {
                                    validate25.errors = [{ instancePath: instancePath + "/budget/spent", schemaPath: "#/$defs/GraphReadBudget/properties/spent/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                    return false;
                                  } else {
                                    if (data3 < 0 || isNaN(data3)) {
                                      validate25.errors = [{ instancePath: instancePath + "/budget/spent", schemaPath: "#/$defs/GraphReadBudget/properties/spent/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                      return false;
                                    }
                                  }
                                }
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
                    validate25.errors = [{ instancePath: instancePath + "/budget", schemaPath: "#/$defs/GraphReadBudget/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.cut !== void 0) {
                  const _errs12 = errors;
                  if (!validate26(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate26.errors : vErrors.concat(validate26.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs12 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.event_cursor !== void 0) {
                    let data5 = data.event_cursor;
                    const _errs13 = errors;
                    if (errors === _errs13) {
                      if (typeof data5 === "string") {
                        if (func1(data5) > 4096) {
                          validate25.errors = [{ instancePath: instancePath + "/event_cursor", schemaPath: "#/properties/event_cursor/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                          return false;
                        } else {
                          if (func1(data5) < 1) {
                            validate25.errors = [{ instancePath: instancePath + "/event_cursor", schemaPath: "#/properties/event_cursor/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          }
                        }
                      } else {
                        validate25.errors = [{ instancePath: instancePath + "/event_cursor", schemaPath: "#/properties/event_cursor/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs13 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.node_count !== void 0) {
                      let data6 = data.node_count;
                      const _errs15 = errors;
                      if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                        validate25.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      if (errors === _errs15) {
                        if (typeof data6 == "number" && isFinite(data6)) {
                          if (data6 > 1e5 || isNaN(data6)) {
                            validate25.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e5 }, message: "must be <= 100000" }];
                            return false;
                          } else {
                            if (data6 < 0 || isNaN(data6)) {
                              validate25.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                              return false;
                            }
                          }
                        }
                      }
                      var valid0 = _errs15 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.query !== void 0) {
                        let data7 = data.query;
                        const _errs17 = errors;
                        const _errs18 = errors;
                        if (errors === _errs18) {
                          if (data7 && typeof data7 == "object" && !Array.isArray(data7)) {
                            const _errs20 = errors;
                            for (const key2 in data7) {
                              if (!(key2 === "frontier_only" || key2 === "scope_key")) {
                                validate25.errors = [{ instancePath: instancePath + "/query", schemaPath: "#/$defs/GraphReadQuery/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs20 === errors) {
                              if (data7.frontier_only !== void 0) {
                                const _errs21 = errors;
                                if (typeof data7.frontier_only !== "boolean") {
                                  validate25.errors = [{ instancePath: instancePath + "/query/frontier_only", schemaPath: "#/$defs/GraphReadQuery/properties/frontier_only/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                  return false;
                                }
                                var valid4 = _errs21 === errors;
                              } else {
                                var valid4 = true;
                              }
                              if (valid4) {
                                if (data7.scope_key !== void 0) {
                                  let data9 = data7.scope_key;
                                  const _errs23 = errors;
                                  const _errs24 = errors;
                                  let valid5 = false;
                                  const _errs25 = errors;
                                  if (errors === _errs25) {
                                    if (typeof data9 === "string") {
                                      if (!pattern4.test(data9)) {
                                        const err0 = { instancePath: instancePath + "/query/scope_key", schemaPath: "#/$defs/GraphReadQuery/properties/scope_key/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                        if (vErrors === null) {
                                          vErrors = [err0];
                                        } else {
                                          vErrors.push(err0);
                                        }
                                        errors++;
                                      }
                                    } else {
                                      const err1 = { instancePath: instancePath + "/query/scope_key", schemaPath: "#/$defs/GraphReadQuery/properties/scope_key/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err1];
                                      } else {
                                        vErrors.push(err1);
                                      }
                                      errors++;
                                    }
                                  }
                                  var _valid0 = _errs25 === errors;
                                  valid5 = valid5 || _valid0;
                                  const _errs27 = errors;
                                  if (data9 !== null) {
                                    const err2 = { instancePath: instancePath + "/query/scope_key", schemaPath: "#/$defs/GraphReadQuery/properties/scope_key/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                    if (vErrors === null) {
                                      vErrors = [err2];
                                    } else {
                                      vErrors.push(err2);
                                    }
                                    errors++;
                                  }
                                  var _valid0 = _errs27 === errors;
                                  valid5 = valid5 || _valid0;
                                  if (!valid5) {
                                    const err3 = { instancePath: instancePath + "/query/scope_key", schemaPath: "#/$defs/GraphReadQuery/properties/scope_key/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                    if (vErrors === null) {
                                      vErrors = [err3];
                                    } else {
                                      vErrors.push(err3);
                                    }
                                    errors++;
                                    validate25.errors = vErrors;
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
                                  var valid4 = _errs23 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          } else {
                            validate25.errors = [{ instancePath: instancePath + "/query", schemaPath: "#/$defs/GraphReadQuery/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                            return false;
                          }
                        }
                        var valid0 = _errs17 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.snapshot_token !== void 0) {
                          let data10 = data.snapshot_token;
                          const _errs29 = errors;
                          if (errors === _errs29) {
                            if (typeof data10 === "string") {
                              if (func1(data10) > 4096) {
                                validate25.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                                return false;
                              } else {
                                if (func1(data10) < 1) {
                                  validate25.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                }
                              }
                            } else {
                              validate25.errors = [{ instancePath: instancePath + "/snapshot_token", schemaPath: "#/properties/snapshot_token/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid0 = _errs29 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.status !== void 0) {
                            let data11 = data.status;
                            const _errs31 = errors;
                            if (typeof data11 !== "string") {
                              validate25.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if (!(data11 === "running" || data11 === "completed" || data11 === "cancelled" || data11 === "failed" || data11 === "blocked")) {
                              validate25.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema36.properties.status.enum }, message: "must be equal to one of the allowed values" }];
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
          if (data.snapshot === void 0 && (missing0 = "snapshot") || data.nodes === void 0 && (missing0 = "nodes") || data.next_cursor === void 0 && (missing0 = "next_cursor")) {
            validate20.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "next_cursor" || key0 === "nodes" || key0 === "schema_version" || key0 === "snapshot")) {
                validate20.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.next_cursor !== void 0) {
                let data0 = data.next_cursor;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (errors === _errs4) {
                  if (typeof data0 === "string") {
                    if (func1(data0) > 4096) {
                      const err0 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                      if (vErrors === null) {
                        vErrors = [err0];
                      } else {
                        vErrors.push(err0);
                      }
                      errors++;
                    } else {
                      if (func1(data0) < 1) {
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
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs6 = errors;
                if (data0 !== null) {
                  const err3 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                  if (vErrors === null) {
                    vErrors = [err3];
                  } else {
                    vErrors.push(err3);
                  }
                  errors++;
                }
                var _valid0 = _errs6 === errors;
                valid1 = valid1 || _valid0;
                if (!valid1) {
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
                if (data.nodes !== void 0) {
                  let data1 = data.nodes;
                  const _errs8 = errors;
                  if (errors === _errs8) {
                    if (Array.isArray(data1)) {
                      if (data1.length > 100) {
                        validate20.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/maxItems", keyword: "maxItems", params: { limit: 100 }, message: "must NOT have more than 100 items" }];
                        return false;
                      } else {
                        var valid2 = true;
                        const len0 = data1.length;
                        for (let i0 = 0; i0 < len0; i0++) {
                          const _errs10 = errors;
                          if (!validate21(data1[i0], { instancePath: instancePath + "/nodes/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                            vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                            errors = vErrors.length;
                          }
                          var valid2 = _errs10 === errors;
                          if (!valid2) {
                            break;
                          }
                        }
                      }
                    } else {
                      validate20.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                      return false;
                    }
                  }
                  var valid0 = _errs8 === errors;
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
    exports.detail = validate29;
    var schema42 = { "additionalProperties": false, "properties": { "attempt_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Attempt Id", "type": "string" }, "canonical_result": { "title": "Canonical Result", "type": "boolean" }, "completion_id": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Completion Id" }, "fence": { "maximum": 9007199254740991, "minimum": 1, "title": "Fence", "type": "integer" }, "invocation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Invocation Id", "type": "string" }, "settled": { "title": "Settled", "type": "boolean" }, "status": { "enum": ["leased", "succeeded", "abstained", "failed", "expired", "cancelled", "uncertain"], "title": "Status", "type": "string" }, "worker_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Worker Id", "type": "string" } }, "required": ["attempt_id", "invocation_id", "worker_id", "fence", "status", "settled", "completion_id", "canonical_result"], "title": "GraphAttemptView", "type": "object" };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.revision === void 0 && (missing0 = "revision") || data.frontier_revision === void 0 && (missing0 = "frontier_revision")) {
            validate30.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "frontier_revision" || key0 === "plan_sha256" || key0 === "revision" || key0 === "run_id" || key0 === "scope")) {
                validate30.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.frontier_revision !== void 0) {
                let data0 = data.frontier_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate30.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate30.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate30.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                      if (!pattern4.test(data1)) {
                        validate30.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate30.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate30.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate30.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate30.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                            validate30.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate30.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern5.test(data3)) {
                                validate30.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate30.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                              validate30.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate30.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                        validate30.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate30.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data5)) {
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
                                          validate30.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate30.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data6)) {
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
                                    var valid2 = _errs16 === errors;
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
          validate30.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate30.errors = vErrors;
      return errors === 0;
    }
    validate30.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema45 = { "additionalProperties": false, "properties": { "activation_id": { "pattern": "^[0-9a-f]{64}$", "title": "Activation Id", "type": "string" }, "kind": { "enum": ["invoke", "branch", "join", "scatter", "iterate", "finish", "await", "artifact_project", "artifact_materialize"], "title": "Kind", "type": "string" }, "path": { "$ref": "#/$defs/ActivationPath" }, "reason_code": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Reason Code" }, "status": { "enum": ["waiting", "ready", "issued", "succeeded", "skipped", "failed", "blocked"], "title": "Status", "type": "string" } }, "required": ["activation_id", "path", "kind", "status", "reason_code"], "title": "GraphNodeViewV3", "type": "object" };
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
          if (data.schema_version === void 0 && (missing0 = "schema_version") || data.node_id === void 0 && (missing0 = "node_id")) {
            validate33.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "node_id" || key0 === "occurrences" || key0 === "schema_version")) {
                validate33.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate33.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate33.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate33.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate33.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate33.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
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
                                                if (!pattern5.test(data5)) {
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
                                            if (!pattern4.test(data8)) {
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
                                                  if (!pattern5.test(data9)) {
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
                            validate33.errors = vErrors;
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
                      validate33.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
                      validate33.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("2" !== data10) {
                      validate33.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "2" }, message: "must be equal to constant" }];
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
          validate33.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate33.errors = vErrors;
      return errors === 0;
    }
    validate33.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.activation_id === void 0 && (missing0 = "activation_id") || data.path === void 0 && (missing0 = "path") || data.kind === void 0 && (missing0 = "kind") || data.status === void 0 && (missing0 = "status") || data.reason_code === void 0 && (missing0 = "reason_code")) {
            validate32.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "activation_id" || key0 === "kind" || key0 === "path" || key0 === "reason_code" || key0 === "status")) {
                validate32.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (!pattern4.test(data0)) {
                      validate32.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate32.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate32.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "invoke" || data1 === "branch" || data1 === "join" || data1 === "scatter" || data1 === "iterate" || data1 === "finish" || data1 === "await" || data1 === "artifact_project" || data1 === "artifact_materialize")) {
                    validate32.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/enum", keyword: "enum", params: { allowedValues: schema45.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.path !== void 0) {
                    const _errs6 = errors;
                    if (!validate33(data.path, { instancePath: instancePath + "/path", parentData: data, parentDataProperty: "path", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate33.errors : vErrors.concat(validate33.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.reason_code !== void 0) {
                      let data3 = data.reason_code;
                      const _errs7 = errors;
                      const _errs8 = errors;
                      let valid1 = false;
                      const _errs9 = errors;
                      if (errors === _errs9) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 128) {
                            const err0 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                            if (vErrors === null) {
                              vErrors = [err0];
                            } else {
                              vErrors.push(err0);
                            }
                            errors++;
                          } else {
                            if (func1(data3) < 1) {
                              const err1 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                              if (vErrors === null) {
                                vErrors = [err1];
                              } else {
                                vErrors.push(err1);
                              }
                              errors++;
                            } else {
                              if (!pattern5.test(data3)) {
                                const err2 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                          const err3 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err3];
                          } else {
                            vErrors.push(err3);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs9 === errors;
                      valid1 = valid1 || _valid0;
                      const _errs11 = errors;
                      if (data3 !== null) {
                        const err4 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid0 = _errs11 === errors;
                      valid1 = valid1 || _valid0;
                      if (!valid1) {
                        const err5 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                        validate32.errors = vErrors;
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
                      if (data.status !== void 0) {
                        let data4 = data.status;
                        const _errs13 = errors;
                        if (typeof data4 !== "string") {
                          validate32.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if (!(data4 === "waiting" || data4 === "ready" || data4 === "issued" || data4 === "succeeded" || data4 === "skipped" || data4 === "failed" || data4 === "blocked")) {
                          validate32.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema45.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                          return false;
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
          validate32.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate32.errors = vErrors;
      return errors === 0;
    }
    validate32.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema49 = { "additionalProperties": false, "properties": { "artifact": { "anyOf": [{ "$ref": "#/$defs/ArtifactRef" }, { "type": "null" }], "default": null }, "item_count": { "maximum": 1e4, "minimum": 0, "title": "Item Count", "type": "integer" }, "kind": { "enum": ["boolean", "integer", "number", "string", "artifact", "collection"], "title": "Kind", "type": "string" }, "missing_count": { "maximum": 1e4, "minimum": 0, "title": "Missing Count", "type": "integer" }, "port": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Port", "type": "string" } }, "required": ["port", "kind", "item_count", "missing_count"], "title": "GraphOutputSummary", "type": "object" };
    var pattern30 = new RegExp("^[^\\s/]+/[^\\s/]+$", "u");
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate37.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate37.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate37.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate37.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate37.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate37.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate37.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate37.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern30.test(data1)) {
                            validate37.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate37.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate37.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate37.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate37.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate37.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate37.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate37.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate37.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate37.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate37.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate37.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate37.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate37.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate37.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate37.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate37.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data7)) {
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
                                        validate37.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate37.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data8)) {
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
                                  var valid4 = _errs22 === errors;
                                } else {
                                  var valid4 = true;
                                }
                              }
                            }
                          }
                        } else {
                          validate37.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                              validate37.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate37.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate37.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate37.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate37.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate37.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate37.errors = vErrors;
      return errors === 0;
    }
    validate37.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.port === void 0 && (missing0 = "port") || data.kind === void 0 && (missing0 = "kind") || data.item_count === void 0 && (missing0 = "item_count") || data.missing_count === void 0 && (missing0 = "missing_count")) {
            validate36.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "item_count" || key0 === "kind" || key0 === "missing_count" || key0 === "port")) {
                validate36.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                let data0 = data.artifact;
                const _errs2 = errors;
                const _errs3 = errors;
                let valid1 = false;
                const _errs4 = errors;
                if (!validate37(data0, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate37.errors : vErrors.concat(validate37.errors);
                  errors = vErrors.length;
                }
                var _valid0 = _errs4 === errors;
                valid1 = valid1 || _valid0;
                const _errs5 = errors;
                if (data0 !== null) {
                  const err0 = { instancePath: instancePath + "/artifact", schemaPath: "#/properties/artifact/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
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
                  const err1 = { instancePath: instancePath + "/artifact", schemaPath: "#/properties/artifact/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                  if (vErrors === null) {
                    vErrors = [err1];
                  } else {
                    vErrors.push(err1);
                  }
                  errors++;
                  validate36.errors = vErrors;
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
                if (data.item_count !== void 0) {
                  let data1 = data.item_count;
                  const _errs7 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate36.errors = [{ instancePath: instancePath + "/item_count", schemaPath: "#/properties/item_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs7) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 1e4 || isNaN(data1)) {
                        validate36.errors = [{ instancePath: instancePath + "/item_count", schemaPath: "#/properties/item_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e4 }, message: "must be <= 10000" }];
                        return false;
                      } else {
                        if (data1 < 0 || isNaN(data1)) {
                          validate36.errors = [{ instancePath: instancePath + "/item_count", schemaPath: "#/properties/item_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                  if (data.kind !== void 0) {
                    let data2 = data.kind;
                    const _errs9 = errors;
                    if (typeof data2 !== "string") {
                      validate36.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data2 === "boolean" || data2 === "integer" || data2 === "number" || data2 === "string" || data2 === "artifact" || data2 === "collection")) {
                      validate36.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/enum", keyword: "enum", params: { allowedValues: schema49.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs9 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.missing_count !== void 0) {
                      let data3 = data.missing_count;
                      const _errs11 = errors;
                      if (!(typeof data3 == "number" && (!(data3 % 1) && !isNaN(data3)) && isFinite(data3))) {
                        validate36.errors = [{ instancePath: instancePath + "/missing_count", schemaPath: "#/properties/missing_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      if (errors === _errs11) {
                        if (typeof data3 == "number" && isFinite(data3)) {
                          if (data3 > 1e4 || isNaN(data3)) {
                            validate36.errors = [{ instancePath: instancePath + "/missing_count", schemaPath: "#/properties/missing_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e4 }, message: "must be <= 10000" }];
                            return false;
                          } else {
                            if (data3 < 0 || isNaN(data3)) {
                              validate36.errors = [{ instancePath: instancePath + "/missing_count", schemaPath: "#/properties/missing_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                      if (data.port !== void 0) {
                        let data4 = data.port;
                        const _errs13 = errors;
                        if (errors === _errs13) {
                          if (typeof data4 === "string") {
                            if (func1(data4) > 128) {
                              validate36.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func1(data4) < 1) {
                                validate36.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern5.test(data4)) {
                                  validate36.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate36.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
        } else {
          validate36.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate36.errors = vErrors;
      return errors === 0;
    }
    validate36.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.cut === void 0 && (missing0 = "cut") || data.node === void 0 && (missing0 = "node") || data.scope_key === void 0 && (missing0 = "scope_key") || data.parent_activation_id === void 0 && (missing0 = "parent_activation_id") || data.outputs === void 0 && (missing0 = "outputs") || data.attempts === void 0 && (missing0 = "attempts") || data.next_cursor === void 0 && (missing0 = "next_cursor")) {
            validate29.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "attempts" || key0 === "cut" || key0 === "next_cursor" || key0 === "node" || key0 === "outputs" || key0 === "parent_activation_id" || key0 === "schema_version" || key0 === "scope_key")) {
                validate29.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (data0.length > 100) {
                      validate29.errors = [{ instancePath: instancePath + "/attempts", schemaPath: "#/properties/attempts/maxItems", keyword: "maxItems", params: { limit: 100 }, message: "must NOT have more than 100 items" }];
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
                            if (data1.attempt_id === void 0 && (missing1 = "attempt_id") || data1.invocation_id === void 0 && (missing1 = "invocation_id") || data1.worker_id === void 0 && (missing1 = "worker_id") || data1.fence === void 0 && (missing1 = "fence") || data1.status === void 0 && (missing1 = "status") || data1.settled === void 0 && (missing1 = "settled") || data1.completion_id === void 0 && (missing1 = "completion_id") || data1.canonical_result === void 0 && (missing1 = "canonical_result")) {
                              validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0, schemaPath: "#/$defs/GraphAttemptView/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs7 = errors;
                              for (const key1 in data1) {
                                if (!(key1 === "attempt_id" || key1 === "canonical_result" || key1 === "completion_id" || key1 === "fence" || key1 === "invocation_id" || key1 === "settled" || key1 === "status" || key1 === "worker_id")) {
                                  validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0, schemaPath: "#/$defs/GraphAttemptView/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs7 === errors) {
                                if (data1.attempt_id !== void 0) {
                                  let data2 = data1.attempt_id;
                                  const _errs8 = errors;
                                  if (errors === _errs8) {
                                    if (typeof data2 === "string") {
                                      if (func1(data2) > 128) {
                                        validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/attempt_id", schemaPath: "#/$defs/GraphAttemptView/properties/attempt_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data2) < 1) {
                                          validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/attempt_id", schemaPath: "#/$defs/GraphAttemptView/properties/attempt_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data2)) {
                                            validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/attempt_id", schemaPath: "#/$defs/GraphAttemptView/properties/attempt_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/attempt_id", schemaPath: "#/$defs/GraphAttemptView/properties/attempt_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid3 = _errs8 === errors;
                                } else {
                                  var valid3 = true;
                                }
                                if (valid3) {
                                  if (data1.canonical_result !== void 0) {
                                    const _errs10 = errors;
                                    if (typeof data1.canonical_result !== "boolean") {
                                      validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/canonical_result", schemaPath: "#/$defs/GraphAttemptView/properties/canonical_result/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                      return false;
                                    }
                                    var valid3 = _errs10 === errors;
                                  } else {
                                    var valid3 = true;
                                  }
                                  if (valid3) {
                                    if (data1.completion_id !== void 0) {
                                      let data4 = data1.completion_id;
                                      const _errs12 = errors;
                                      const _errs13 = errors;
                                      let valid4 = false;
                                      const _errs14 = errors;
                                      if (errors === _errs14) {
                                        if (typeof data4 === "string") {
                                          if (func1(data4) > 128) {
                                            const err0 = { instancePath: instancePath + "/attempts/" + i0 + "/completion_id", schemaPath: "#/$defs/GraphAttemptView/properties/completion_id/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                            if (vErrors === null) {
                                              vErrors = [err0];
                                            } else {
                                              vErrors.push(err0);
                                            }
                                            errors++;
                                          } else {
                                            if (func1(data4) < 1) {
                                              const err1 = { instancePath: instancePath + "/attempts/" + i0 + "/completion_id", schemaPath: "#/$defs/GraphAttemptView/properties/completion_id/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                              if (vErrors === null) {
                                                vErrors = [err1];
                                              } else {
                                                vErrors.push(err1);
                                              }
                                              errors++;
                                            } else {
                                              if (!pattern5.test(data4)) {
                                                const err2 = { instancePath: instancePath + "/attempts/" + i0 + "/completion_id", schemaPath: "#/$defs/GraphAttemptView/properties/completion_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                          const err3 = { instancePath: instancePath + "/attempts/" + i0 + "/completion_id", schemaPath: "#/$defs/GraphAttemptView/properties/completion_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err3];
                                          } else {
                                            vErrors.push(err3);
                                          }
                                          errors++;
                                        }
                                      }
                                      var _valid0 = _errs14 === errors;
                                      valid4 = valid4 || _valid0;
                                      const _errs16 = errors;
                                      if (data4 !== null) {
                                        const err4 = { instancePath: instancePath + "/attempts/" + i0 + "/completion_id", schemaPath: "#/$defs/GraphAttemptView/properties/completion_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                        if (vErrors === null) {
                                          vErrors = [err4];
                                        } else {
                                          vErrors.push(err4);
                                        }
                                        errors++;
                                      }
                                      var _valid0 = _errs16 === errors;
                                      valid4 = valid4 || _valid0;
                                      if (!valid4) {
                                        const err5 = { instancePath: instancePath + "/attempts/" + i0 + "/completion_id", schemaPath: "#/$defs/GraphAttemptView/properties/completion_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                        if (vErrors === null) {
                                          vErrors = [err5];
                                        } else {
                                          vErrors.push(err5);
                                        }
                                        errors++;
                                        validate29.errors = vErrors;
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
                                      var valid3 = _errs12 === errors;
                                    } else {
                                      var valid3 = true;
                                    }
                                    if (valid3) {
                                      if (data1.fence !== void 0) {
                                        let data5 = data1.fence;
                                        const _errs18 = errors;
                                        if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                          validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/fence", schemaPath: "#/$defs/GraphAttemptView/properties/fence/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                          return false;
                                        }
                                        if (errors === _errs18) {
                                          if (typeof data5 == "number" && isFinite(data5)) {
                                            if (data5 > 9007199254740991 || isNaN(data5)) {
                                              validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/fence", schemaPath: "#/$defs/GraphAttemptView/properties/fence/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                              return false;
                                            } else {
                                              if (data5 < 1 || isNaN(data5)) {
                                                validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/fence", schemaPath: "#/$defs/GraphAttemptView/properties/fence/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                                        if (data1.invocation_id !== void 0) {
                                          let data6 = data1.invocation_id;
                                          const _errs20 = errors;
                                          if (errors === _errs20) {
                                            if (typeof data6 === "string") {
                                              if (func1(data6) > 128) {
                                                validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/invocation_id", schemaPath: "#/$defs/GraphAttemptView/properties/invocation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                return false;
                                              } else {
                                                if (func1(data6) < 1) {
                                                  validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/invocation_id", schemaPath: "#/$defs/GraphAttemptView/properties/invocation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                  return false;
                                                } else {
                                                  if (!pattern5.test(data6)) {
                                                    validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/invocation_id", schemaPath: "#/$defs/GraphAttemptView/properties/invocation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            } else {
                                              validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/invocation_id", schemaPath: "#/$defs/GraphAttemptView/properties/invocation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid3 = _errs20 === errors;
                                        } else {
                                          var valid3 = true;
                                        }
                                        if (valid3) {
                                          if (data1.settled !== void 0) {
                                            const _errs22 = errors;
                                            if (typeof data1.settled !== "boolean") {
                                              validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/settled", schemaPath: "#/$defs/GraphAttemptView/properties/settled/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                                              return false;
                                            }
                                            var valid3 = _errs22 === errors;
                                          } else {
                                            var valid3 = true;
                                          }
                                          if (valid3) {
                                            if (data1.status !== void 0) {
                                              let data8 = data1.status;
                                              const _errs24 = errors;
                                              if (typeof data8 !== "string") {
                                                validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/status", schemaPath: "#/$defs/GraphAttemptView/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                return false;
                                              }
                                              if (!(data8 === "leased" || data8 === "succeeded" || data8 === "abstained" || data8 === "failed" || data8 === "expired" || data8 === "cancelled" || data8 === "uncertain")) {
                                                validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/status", schemaPath: "#/$defs/GraphAttemptView/properties/status/enum", keyword: "enum", params: { allowedValues: schema42.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                                                return false;
                                              }
                                              var valid3 = _errs24 === errors;
                                            } else {
                                              var valid3 = true;
                                            }
                                            if (valid3) {
                                              if (data1.worker_id !== void 0) {
                                                let data9 = data1.worker_id;
                                                const _errs26 = errors;
                                                if (errors === _errs26) {
                                                  if (typeof data9 === "string") {
                                                    if (func1(data9) > 128) {
                                                      validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/worker_id", schemaPath: "#/$defs/GraphAttemptView/properties/worker_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                      return false;
                                                    } else {
                                                      if (func1(data9) < 1) {
                                                        validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/worker_id", schemaPath: "#/$defs/GraphAttemptView/properties/worker_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                        return false;
                                                      } else {
                                                        if (!pattern5.test(data9)) {
                                                          validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/worker_id", schemaPath: "#/$defs/GraphAttemptView/properties/worker_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                          return false;
                                                        }
                                                      }
                                                    }
                                                  } else {
                                                    validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0 + "/worker_id", schemaPath: "#/$defs/GraphAttemptView/properties/worker_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                                    return false;
                                                  }
                                                }
                                                var valid3 = _errs26 === errors;
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
                            validate29.errors = [{ instancePath: instancePath + "/attempts/" + i0, schemaPath: "#/$defs/GraphAttemptView/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                    validate29.errors = [{ instancePath: instancePath + "/attempts", schemaPath: "#/properties/attempts/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.cut !== void 0) {
                  const _errs28 = errors;
                  if (!validate30(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate30.errors : vErrors.concat(validate30.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs28 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.next_cursor !== void 0) {
                    let data11 = data.next_cursor;
                    const _errs29 = errors;
                    const _errs30 = errors;
                    let valid5 = false;
                    const _errs31 = errors;
                    if (errors === _errs31) {
                      if (typeof data11 === "string") {
                        if (func1(data11) > 4096) {
                          const err6 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                          if (vErrors === null) {
                            vErrors = [err6];
                          } else {
                            vErrors.push(err6);
                          }
                          errors++;
                        } else {
                          if (func1(data11) < 1) {
                            const err7 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                            if (vErrors === null) {
                              vErrors = [err7];
                            } else {
                              vErrors.push(err7);
                            }
                            errors++;
                          }
                        }
                      } else {
                        const err8 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err8];
                        } else {
                          vErrors.push(err8);
                        }
                        errors++;
                      }
                    }
                    var _valid1 = _errs31 === errors;
                    valid5 = valid5 || _valid1;
                    const _errs33 = errors;
                    if (data11 !== null) {
                      const err9 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err9];
                      } else {
                        vErrors.push(err9);
                      }
                      errors++;
                    }
                    var _valid1 = _errs33 === errors;
                    valid5 = valid5 || _valid1;
                    if (!valid5) {
                      const err10 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err10];
                      } else {
                        vErrors.push(err10);
                      }
                      errors++;
                      validate29.errors = vErrors;
                      return false;
                    } else {
                      errors = _errs30;
                      if (vErrors !== null) {
                        if (_errs30) {
                          vErrors.length = _errs30;
                        } else {
                          vErrors = null;
                        }
                      }
                    }
                    var valid0 = _errs29 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.node !== void 0) {
                      const _errs35 = errors;
                      if (!validate32(data.node, { instancePath: instancePath + "/node", parentData: data, parentDataProperty: "node", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate32.errors : vErrors.concat(validate32.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs35 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.outputs !== void 0) {
                        let data13 = data.outputs;
                        const _errs36 = errors;
                        if (errors === _errs36) {
                          if (Array.isArray(data13)) {
                            if (data13.length > 64) {
                              validate29.errors = [{ instancePath: instancePath + "/outputs", schemaPath: "#/properties/outputs/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                              return false;
                            } else {
                              var valid6 = true;
                              const len1 = data13.length;
                              for (let i1 = 0; i1 < len1; i1++) {
                                const _errs38 = errors;
                                if (!validate36(data13[i1], { instancePath: instancePath + "/outputs/" + i1, parentData: data13, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                  vErrors = vErrors === null ? validate36.errors : vErrors.concat(validate36.errors);
                                  errors = vErrors.length;
                                }
                                var valid6 = _errs38 === errors;
                                if (!valid6) {
                                  break;
                                }
                              }
                            }
                          } else {
                            validate29.errors = [{ instancePath: instancePath + "/outputs", schemaPath: "#/properties/outputs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs36 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.parent_activation_id !== void 0) {
                          let data15 = data.parent_activation_id;
                          const _errs39 = errors;
                          const _errs40 = errors;
                          let valid7 = false;
                          const _errs41 = errors;
                          if (errors === _errs41) {
                            if (typeof data15 === "string") {
                              if (!pattern4.test(data15)) {
                                const err11 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                if (vErrors === null) {
                                  vErrors = [err11];
                                } else {
                                  vErrors.push(err11);
                                }
                                errors++;
                              }
                            } else {
                              const err12 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err12];
                              } else {
                                vErrors.push(err12);
                              }
                              errors++;
                            }
                          }
                          var _valid2 = _errs41 === errors;
                          valid7 = valid7 || _valid2;
                          const _errs43 = errors;
                          if (data15 !== null) {
                            const err13 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                            if (vErrors === null) {
                              vErrors = [err13];
                            } else {
                              vErrors.push(err13);
                            }
                            errors++;
                          }
                          var _valid2 = _errs43 === errors;
                          valid7 = valid7 || _valid2;
                          if (!valid7) {
                            const err14 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                            if (vErrors === null) {
                              vErrors = [err14];
                            } else {
                              vErrors.push(err14);
                            }
                            errors++;
                            validate29.errors = vErrors;
                            return false;
                          } else {
                            errors = _errs40;
                            if (vErrors !== null) {
                              if (_errs40) {
                                vErrors.length = _errs40;
                              } else {
                                vErrors = null;
                              }
                            }
                          }
                          var valid0 = _errs39 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.schema_version !== void 0) {
                            let data16 = data.schema_version;
                            const _errs45 = errors;
                            if (typeof data16 !== "string") {
                              validate29.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("1" !== data16) {
                              validate29.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs45 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.scope_key !== void 0) {
                              let data17 = data.scope_key;
                              const _errs47 = errors;
                              if (errors === _errs47) {
                                if (typeof data17 === "string") {
                                  if (!pattern4.test(data17)) {
                                    validate29.errors = [{ instancePath: instancePath + "/scope_key", schemaPath: "#/properties/scope_key/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                    return false;
                                  }
                                } else {
                                  validate29.errors = [{ instancePath: instancePath + "/scope_key", schemaPath: "#/properties/scope_key/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          validate29.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate29.errors = vErrors;
      return errors === 0;
    }
    validate29.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.values = validate40;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.revision === void 0 && (missing0 = "revision") || data.frontier_revision === void 0 && (missing0 = "frontier_revision")) {
            validate41.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "frontier_revision" || key0 === "plan_sha256" || key0 === "revision" || key0 === "run_id" || key0 === "scope")) {
                validate41.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.frontier_revision !== void 0) {
                let data0 = data.frontier_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate41.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate41.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate41.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                      if (!pattern4.test(data1)) {
                        validate41.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate41.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate41.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate41.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate41.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                            validate41.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate41.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern5.test(data3)) {
                                validate41.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate41.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                              validate41.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate41.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                        validate41.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate41.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data5)) {
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
                                          validate41.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate41.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data6)) {
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
                                    var valid2 = _errs16 === errors;
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
          validate41.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate41.errors = vErrors;
      return errors === 0;
    }
    validate41.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var pattern44 = new RegExp("^-?(?:(?:0|[1-9][0-9]{0,99})(?:\\.[0-9]{1,324})?|10{100})$", "u");
    function validate45(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate45.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate45.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate45.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate45.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate45.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate45.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate45.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate45.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern30.test(data1)) {
                            validate45.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate45.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate45.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate45.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate45.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate45.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate45.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate45.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate45.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate45.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate45.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate45.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate45.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate45.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate45.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate45.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate45.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data7)) {
                                          validate45.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate45.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        validate45.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate45.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data8)) {
                                            validate45.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate45.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate45.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                              validate45.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate45.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate45.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate45.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate45.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate45.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate45.errors = vErrors;
      return errors === 0;
    }
    validate45.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.kind === void 0 && (missing0 = "kind") || data.artifact === void 0 && (missing0 = "artifact") || data.representation === void 0 && (missing0 = "representation") || data.unit === void 0 && (missing0 = "unit")) {
            validate44.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "kind" || key0 === "representation" || key0 === "unit")) {
                validate44.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                const _errs2 = errors;
                if (!validate45(data.artifact, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate45.errors : vErrors.concat(validate45.errors);
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
                    validate44.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("artifact" !== data1) {
                    validate44.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/const", keyword: "const", params: { allowedValue: "artifact" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.representation !== void 0) {
                    let data2 = data.representation;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (typeof data2 === "string") {
                        if (func1(data2) > 128) {
                          validate44.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/properties/representation/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate44.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/properties/representation/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern5.test(data2)) {
                              validate44.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/properties/representation/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate44.errors = [{ instancePath: instancePath + "/representation", schemaPath: "#/properties/representation/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.unit !== void 0) {
                      let data3 = data.unit;
                      const _errs7 = errors;
                      if (errors === _errs7) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 64) {
                            validate44.errors = [{ instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate44.errors = [{ instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            }
                          }
                        } else {
                          validate44.errors = [{ instancePath: instancePath + "/unit", schemaPath: "#/properties/unit/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          if (data.index === void 0 && (missing0 = "index") || data.value === void 0 && (missing0 = "value")) {
            validate43.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "index" || key0 === "value")) {
                validate43.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.index !== void 0) {
                let data0 = data.index;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate43.errors = [{ instancePath: instancePath + "/index", schemaPath: "#/properties/index/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9999 || isNaN(data0)) {
                      validate43.errors = [{ instancePath: instancePath + "/index", schemaPath: "#/properties/index/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9999 }, message: "must be <= 9999" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate43.errors = [{ instancePath: instancePath + "/index", schemaPath: "#/properties/index/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                if (data.value !== void 0) {
                  let data1 = data.value;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  const _errs6 = errors;
                  const _errs7 = errors;
                  let valid2 = false;
                  let passing0 = null;
                  const _errs8 = errors;
                  const _errs9 = errors;
                  if (errors === _errs9) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.kind === void 0 && (missing1 = "kind") || data1.value === void 0 && (missing1 = "value")) {
                        const err0 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/BooleanConstant/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        const _errs11 = errors;
                        for (const key1 in data1) {
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
                          if (data1.kind !== void 0) {
                            let data2 = data1.kind;
                            const _errs12 = errors;
                            if (typeof data2 !== "string") {
                              const err2 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/BooleanConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                            }
                            if ("boolean" !== data2) {
                              const err3 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/BooleanConstant/properties/kind/const", keyword: "const", params: { allowedValue: "boolean" }, message: "must be equal to constant" };
                              if (vErrors === null) {
                                vErrors = [err3];
                              } else {
                                vErrors.push(err3);
                              }
                              errors++;
                            }
                            var valid4 = _errs12 === errors;
                          } else {
                            var valid4 = true;
                          }
                          if (valid4) {
                            if (data1.value !== void 0) {
                              const _errs14 = errors;
                              if (typeof data1.value !== "boolean") {
                                const err4 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/BooleanConstant/properties/value/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" };
                                if (vErrors === null) {
                                  vErrors = [err4];
                                } else {
                                  vErrors.push(err4);
                                }
                                errors++;
                              }
                              var valid4 = _errs14 === errors;
                            } else {
                              var valid4 = true;
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
                  var _valid1 = _errs8 === errors;
                  if (_valid1) {
                    valid2 = true;
                    passing0 = 0;
                    var props0 = true;
                  }
                  const _errs16 = errors;
                  const _errs17 = errors;
                  if (errors === _errs17) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing2;
                      if (data1.kind === void 0 && (missing2 = "kind") || data1.value === void 0 && (missing2 = "value")) {
                        const err6 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/IntegerConstant/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      } else {
                        const _errs19 = errors;
                        for (const key2 in data1) {
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
                          if (data1.kind !== void 0) {
                            let data4 = data1.kind;
                            const _errs20 = errors;
                            if (typeof data4 !== "string") {
                              const err8 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/IntegerConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err8];
                              } else {
                                vErrors.push(err8);
                              }
                              errors++;
                            }
                            if ("integer" !== data4) {
                              const err9 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/IntegerConstant/properties/kind/const", keyword: "const", params: { allowedValue: "integer" }, message: "must be equal to constant" };
                              if (vErrors === null) {
                                vErrors = [err9];
                              } else {
                                vErrors.push(err9);
                              }
                              errors++;
                            }
                            var valid6 = _errs20 === errors;
                          } else {
                            var valid6 = true;
                          }
                          if (valid6) {
                            if (data1.unit !== void 0) {
                              let data5 = data1.unit;
                              const _errs22 = errors;
                              if (errors === _errs22) {
                                if (typeof data5 === "string") {
                                  if (func1(data5) > 64) {
                                    const err10 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/IntegerConstant/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" };
                                    if (vErrors === null) {
                                      vErrors = [err10];
                                    } else {
                                      vErrors.push(err10);
                                    }
                                    errors++;
                                  } else {
                                    if (func1(data5) < 1) {
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
                              var valid6 = _errs22 === errors;
                            } else {
                              var valid6 = true;
                            }
                            if (valid6) {
                              if (data1.value !== void 0) {
                                let data6 = data1.value;
                                const _errs24 = errors;
                                if (!(typeof data6 == "number" && (!(data6 % 1) && !isNaN(data6)) && isFinite(data6))) {
                                  const err13 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/IntegerConstant/properties/value/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                  if (vErrors === null) {
                                    vErrors = [err13];
                                  } else {
                                    vErrors.push(err13);
                                  }
                                  errors++;
                                }
                                if (errors === _errs24) {
                                  if (typeof data6 == "number" && isFinite(data6)) {
                                    if (data6 > 9007199254740991 || isNaN(data6)) {
                                      const err14 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/IntegerConstant/properties/value/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" };
                                      if (vErrors === null) {
                                        vErrors = [err14];
                                      } else {
                                        vErrors.push(err14);
                                      }
                                      errors++;
                                    } else {
                                      if (data6 < -9007199254740991 || isNaN(data6)) {
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
                                var valid6 = _errs24 === errors;
                              } else {
                                var valid6 = true;
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
                  var _valid1 = _errs16 === errors;
                  if (_valid1 && valid2) {
                    valid2 = false;
                    passing0 = [passing0, 1];
                  } else {
                    if (_valid1) {
                      valid2 = true;
                      passing0 = 1;
                      if (props0 !== true) {
                        props0 = true;
                      }
                    }
                    const _errs26 = errors;
                    const _errs27 = errors;
                    if (errors === _errs27) {
                      if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                        let missing3;
                        if (data1.kind === void 0 && (missing3 = "kind") || data1.value === void 0 && (missing3 = "value")) {
                          const err17 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/NumberValue/required", keyword: "required", params: { missingProperty: missing3 }, message: "must have required property '" + missing3 + "'" };
                          if (vErrors === null) {
                            vErrors = [err17];
                          } else {
                            vErrors.push(err17);
                          }
                          errors++;
                        } else {
                          const _errs29 = errors;
                          for (const key3 in data1) {
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
                            if (data1.kind !== void 0) {
                              let data7 = data1.kind;
                              const _errs30 = errors;
                              if (typeof data7 !== "string") {
                                const err19 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/NumberValue/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err19];
                                } else {
                                  vErrors.push(err19);
                                }
                                errors++;
                              }
                              if ("number" !== data7) {
                                const err20 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/NumberValue/properties/kind/const", keyword: "const", params: { allowedValue: "number" }, message: "must be equal to constant" };
                                if (vErrors === null) {
                                  vErrors = [err20];
                                } else {
                                  vErrors.push(err20);
                                }
                                errors++;
                              }
                              var valid8 = _errs30 === errors;
                            } else {
                              var valid8 = true;
                            }
                            if (valid8) {
                              if (data1.unit !== void 0) {
                                let data8 = data1.unit;
                                const _errs32 = errors;
                                if (errors === _errs32) {
                                  if (typeof data8 === "string") {
                                    if (func1(data8) > 64) {
                                      const err21 = { instancePath: instancePath + "/value/unit", schemaPath: "#/$defs/NumberValue/properties/unit/maxLength", keyword: "maxLength", params: { limit: 64 }, message: "must NOT have more than 64 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err21];
                                      } else {
                                        vErrors.push(err21);
                                      }
                                      errors++;
                                    } else {
                                      if (func1(data8) < 1) {
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
                                var valid8 = _errs32 === errors;
                              } else {
                                var valid8 = true;
                              }
                              if (valid8) {
                                if (data1.value !== void 0) {
                                  let data9 = data1.value;
                                  const _errs34 = errors;
                                  if (errors === _errs34) {
                                    if (typeof data9 === "string") {
                                      if (func1(data9) > 427) {
                                        const err24 = { instancePath: instancePath + "/value/value", schemaPath: "#/$defs/NumberValue/properties/value/maxLength", keyword: "maxLength", params: { limit: 427 }, message: "must NOT have more than 427 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err24];
                                        } else {
                                          vErrors.push(err24);
                                        }
                                        errors++;
                                      } else {
                                        if (!pattern44.test(data9)) {
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
                                  var valid8 = _errs34 === errors;
                                } else {
                                  var valid8 = true;
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
                    var _valid1 = _errs26 === errors;
                    if (_valid1 && valid2) {
                      valid2 = false;
                      passing0 = [passing0, 2];
                    } else {
                      if (_valid1) {
                        valid2 = true;
                        passing0 = 2;
                        if (props0 !== true) {
                          props0 = true;
                        }
                      }
                      const _errs36 = errors;
                      const _errs37 = errors;
                      if (errors === _errs37) {
                        if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                          let missing4;
                          if (data1.kind === void 0 && (missing4 = "kind") || data1.value === void 0 && (missing4 = "value")) {
                            const err28 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/StringConstant/required", keyword: "required", params: { missingProperty: missing4 }, message: "must have required property '" + missing4 + "'" };
                            if (vErrors === null) {
                              vErrors = [err28];
                            } else {
                              vErrors.push(err28);
                            }
                            errors++;
                          } else {
                            const _errs39 = errors;
                            for (const key4 in data1) {
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
                              if (data1.kind !== void 0) {
                                let data10 = data1.kind;
                                const _errs40 = errors;
                                if (typeof data10 !== "string") {
                                  const err30 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/StringConstant/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err30];
                                  } else {
                                    vErrors.push(err30);
                                  }
                                  errors++;
                                }
                                if ("string" !== data10) {
                                  const err31 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/StringConstant/properties/kind/const", keyword: "const", params: { allowedValue: "string" }, message: "must be equal to constant" };
                                  if (vErrors === null) {
                                    vErrors = [err31];
                                  } else {
                                    vErrors.push(err31);
                                  }
                                  errors++;
                                }
                                var valid10 = _errs40 === errors;
                              } else {
                                var valid10 = true;
                              }
                              if (valid10) {
                                if (data1.value !== void 0) {
                                  let data11 = data1.value;
                                  const _errs42 = errors;
                                  if (errors === _errs42) {
                                    if (typeof data11 === "string") {
                                      if (func1(data11) > 4096) {
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
                                  var valid10 = _errs42 === errors;
                                } else {
                                  var valid10 = true;
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
                      var _valid1 = _errs36 === errors;
                      if (_valid1 && valid2) {
                        valid2 = false;
                        passing0 = [passing0, 3];
                      } else {
                        if (_valid1) {
                          valid2 = true;
                          passing0 = 3;
                          if (props0 !== true) {
                            props0 = true;
                          }
                        }
                        const _errs44 = errors;
                        if (!validate44(data1, { instancePath: instancePath + "/value", parentData: data, parentDataProperty: "value", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate44.errors : vErrors.concat(validate44.errors);
                          errors = vErrors.length;
                        }
                        var _valid1 = _errs44 === errors;
                        if (_valid1 && valid2) {
                          valid2 = false;
                          passing0 = [passing0, 4];
                        } else {
                          if (_valid1) {
                            valid2 = true;
                            passing0 = 4;
                            if (props0 !== true) {
                              props0 = true;
                            }
                          }
                        }
                      }
                    }
                  }
                  if (!valid2) {
                    const err35 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf/0/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                    if (vErrors === null) {
                      vErrors = [err35];
                    } else {
                      vErrors.push(err35);
                    }
                    errors++;
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
                  var _valid0 = _errs6 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs46 = errors;
                  const _errs47 = errors;
                  if (errors === _errs47) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing5;
                      if (data1.kind === void 0 && (missing5 = "kind") || data1.reason_code === void 0 && (missing5 = "reason_code") || data1.member_id === void 0 && (missing5 = "member_id")) {
                        const err36 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/MissingValue/required", keyword: "required", params: { missingProperty: missing5 }, message: "must have required property '" + missing5 + "'" };
                        if (vErrors === null) {
                          vErrors = [err36];
                        } else {
                          vErrors.push(err36);
                        }
                        errors++;
                      } else {
                        const _errs49 = errors;
                        for (const key5 in data1) {
                          if (!(key5 === "kind" || key5 === "member_id" || key5 === "reason_code")) {
                            const err37 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/MissingValue/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key5 }, message: "must NOT have additional properties" };
                            if (vErrors === null) {
                              vErrors = [err37];
                            } else {
                              vErrors.push(err37);
                            }
                            errors++;
                            break;
                          }
                        }
                        if (_errs49 === errors) {
                          if (data1.kind !== void 0) {
                            let data12 = data1.kind;
                            const _errs50 = errors;
                            if (typeof data12 !== "string") {
                              const err38 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/MissingValue/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err38];
                              } else {
                                vErrors.push(err38);
                              }
                              errors++;
                            }
                            if ("missing" !== data12) {
                              const err39 = { instancePath: instancePath + "/value/kind", schemaPath: "#/$defs/MissingValue/properties/kind/const", keyword: "const", params: { allowedValue: "missing" }, message: "must be equal to constant" };
                              if (vErrors === null) {
                                vErrors = [err39];
                              } else {
                                vErrors.push(err39);
                              }
                              errors++;
                            }
                            var valid12 = _errs50 === errors;
                          } else {
                            var valid12 = true;
                          }
                          if (valid12) {
                            if (data1.member_id !== void 0) {
                              let data13 = data1.member_id;
                              const _errs52 = errors;
                              if (errors === _errs52) {
                                if (typeof data13 === "string") {
                                  if (func1(data13) > 128) {
                                    const err40 = { instancePath: instancePath + "/value/member_id", schemaPath: "#/$defs/MissingValue/properties/member_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                    if (vErrors === null) {
                                      vErrors = [err40];
                                    } else {
                                      vErrors.push(err40);
                                    }
                                    errors++;
                                  } else {
                                    if (func1(data13) < 1) {
                                      const err41 = { instancePath: instancePath + "/value/member_id", schemaPath: "#/$defs/MissingValue/properties/member_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err41];
                                      } else {
                                        vErrors.push(err41);
                                      }
                                      errors++;
                                    } else {
                                      if (!pattern5.test(data13)) {
                                        const err42 = { instancePath: instancePath + "/value/member_id", schemaPath: "#/$defs/MissingValue/properties/member_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                        if (vErrors === null) {
                                          vErrors = [err42];
                                        } else {
                                          vErrors.push(err42);
                                        }
                                        errors++;
                                      }
                                    }
                                  }
                                } else {
                                  const err43 = { instancePath: instancePath + "/value/member_id", schemaPath: "#/$defs/MissingValue/properties/member_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err43];
                                  } else {
                                    vErrors.push(err43);
                                  }
                                  errors++;
                                }
                              }
                              var valid12 = _errs52 === errors;
                            } else {
                              var valid12 = true;
                            }
                            if (valid12) {
                              if (data1.reason_code !== void 0) {
                                let data14 = data1.reason_code;
                                const _errs54 = errors;
                                if (errors === _errs54) {
                                  if (typeof data14 === "string") {
                                    if (func1(data14) > 128) {
                                      const err44 = { instancePath: instancePath + "/value/reason_code", schemaPath: "#/$defs/MissingValue/properties/reason_code/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err44];
                                      } else {
                                        vErrors.push(err44);
                                      }
                                      errors++;
                                    } else {
                                      if (func1(data14) < 1) {
                                        const err45 = { instancePath: instancePath + "/value/reason_code", schemaPath: "#/$defs/MissingValue/properties/reason_code/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err45];
                                        } else {
                                          vErrors.push(err45);
                                        }
                                        errors++;
                                      } else {
                                        if (!pattern5.test(data14)) {
                                          const err46 = { instancePath: instancePath + "/value/reason_code", schemaPath: "#/$defs/MissingValue/properties/reason_code/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                          if (vErrors === null) {
                                            vErrors = [err46];
                                          } else {
                                            vErrors.push(err46);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  } else {
                                    const err47 = { instancePath: instancePath + "/value/reason_code", schemaPath: "#/$defs/MissingValue/properties/reason_code/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err47];
                                    } else {
                                      vErrors.push(err47);
                                    }
                                    errors++;
                                  }
                                }
                                var valid12 = _errs54 === errors;
                              } else {
                                var valid12 = true;
                              }
                            }
                          }
                        }
                      }
                    } else {
                      const err48 = { instancePath: instancePath + "/value", schemaPath: "#/$defs/MissingValue/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err48];
                      } else {
                        vErrors.push(err48);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs46 === errors;
                  valid1 = valid1 || _valid0;
                  if (_valid0) {
                    if (props0 !== true) {
                      props0 = true;
                    }
                  }
                  if (!valid1) {
                    const err49 = { instancePath: instancePath + "/value", schemaPath: "#/properties/value/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err49];
                    } else {
                      vErrors.push(err49);
                    }
                    errors++;
                    validate43.errors = vErrors;
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
    function validate40(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.cut === void 0 && (missing0 = "cut") || data.activation_id === void 0 && (missing0 = "activation_id") || data.port === void 0 && (missing0 = "port") || data.item_count === void 0 && (missing0 = "item_count") || data.items === void 0 && (missing0 = "items") || data.next_cursor === void 0 && (missing0 = "next_cursor")) {
            validate40.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "activation_id" || key0 === "cut" || key0 === "item_count" || key0 === "items" || key0 === "next_cursor" || key0 === "port" || key0 === "schema_version")) {
                validate40.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (!pattern4.test(data0)) {
                      validate40.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate40.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.cut !== void 0) {
                  const _errs4 = errors;
                  if (!validate41(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                    vErrors = vErrors === null ? validate41.errors : vErrors.concat(validate41.errors);
                    errors = vErrors.length;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.item_count !== void 0) {
                    let data2 = data.item_count;
                    const _errs5 = errors;
                    if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                      validate40.errors = [{ instancePath: instancePath + "/item_count", schemaPath: "#/properties/item_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs5) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 1e4 || isNaN(data2)) {
                          validate40.errors = [{ instancePath: instancePath + "/item_count", schemaPath: "#/properties/item_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e4 }, message: "must be <= 10000" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate40.errors = [{ instancePath: instancePath + "/item_count", schemaPath: "#/properties/item_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                    if (data.items !== void 0) {
                      let data3 = data.items;
                      const _errs7 = errors;
                      if (errors === _errs7) {
                        if (Array.isArray(data3)) {
                          if (data3.length > 100) {
                            validate40.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/maxItems", keyword: "maxItems", params: { limit: 100 }, message: "must NOT have more than 100 items" }];
                            return false;
                          } else {
                            var valid1 = true;
                            const len0 = data3.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs9 = errors;
                              if (!validate43(data3[i0], { instancePath: instancePath + "/items/" + i0, parentData: data3, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                vErrors = vErrors === null ? validate43.errors : vErrors.concat(validate43.errors);
                                errors = vErrors.length;
                              }
                              var valid1 = _errs9 === errors;
                              if (!valid1) {
                                break;
                              }
                            }
                          }
                        } else {
                          validate40.errors = [{ instancePath: instancePath + "/items", schemaPath: "#/properties/items/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                          return false;
                        }
                      }
                      var valid0 = _errs7 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.next_cursor !== void 0) {
                        let data5 = data.next_cursor;
                        const _errs10 = errors;
                        const _errs11 = errors;
                        let valid2 = false;
                        const _errs12 = errors;
                        if (errors === _errs12) {
                          if (typeof data5 === "string") {
                            if (func1(data5) > 4096) {
                              const err0 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            } else {
                              if (func1(data5) < 1) {
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
                        var _valid0 = _errs12 === errors;
                        valid2 = valid2 || _valid0;
                        const _errs14 = errors;
                        if (data5 !== null) {
                          const err3 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err3];
                          } else {
                            vErrors.push(err3);
                          }
                          errors++;
                        }
                        var _valid0 = _errs14 === errors;
                        valid2 = valid2 || _valid0;
                        if (!valid2) {
                          const err4 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err4];
                          } else {
                            vErrors.push(err4);
                          }
                          errors++;
                          validate40.errors = vErrors;
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
                        if (data.port !== void 0) {
                          let data6 = data.port;
                          const _errs16 = errors;
                          if (errors === _errs16) {
                            if (typeof data6 === "string") {
                              if (func1(data6) > 128) {
                                validate40.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                return false;
                              } else {
                                if (func1(data6) < 1) {
                                  validate40.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                  return false;
                                } else {
                                  if (!pattern5.test(data6)) {
                                    validate40.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                    return false;
                                  }
                                }
                              }
                            } else {
                              validate40.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                          }
                          var valid0 = _errs16 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.schema_version !== void 0) {
                            let data7 = data.schema_version;
                            const _errs18 = errors;
                            if (typeof data7 !== "string") {
                              validate40.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("1" !== data7) {
                              validate40.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                              return false;
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
        } else {
          validate40.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate40.errors = vErrors;
      return errors === 0;
    }
    validate40.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.events = validate49;
    function validate49(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.observed_revision === void 0 && (missing0 = "observed_revision") || data.entries === void 0 && (missing0 = "entries") || data.next_cursor === void 0 && (missing0 = "next_cursor") || data.has_more === void 0 && (missing0 = "has_more")) {
            validate49.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "entries" || key0 === "has_more" || key0 === "next_cursor" || key0 === "observed_revision" || key0 === "run_id" || key0 === "schema_version" || key0 === "scope")) {
                validate49.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.entries !== void 0) {
                let data0 = data.entries;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 100) {
                      validate49.errors = [{ instancePath: instancePath + "/entries", schemaPath: "#/properties/entries/maxItems", keyword: "maxItems", params: { limit: 100 }, message: "must NOT have more than 100 items" }];
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
                            if (data1.event_id === void 0 && (missing1 = "event_id") || data1.revision === void 0 && (missing1 = "revision")) {
                              validate49.errors = [{ instancePath: instancePath + "/entries/" + i0, schemaPath: "#/$defs/GraphInvalidation/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs7 = errors;
                              for (const key1 in data1) {
                                if (!(key1 === "event_id" || key1 === "kind" || key1 === "revision")) {
                                  validate49.errors = [{ instancePath: instancePath + "/entries/" + i0, schemaPath: "#/$defs/GraphInvalidation/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                  return false;
                                  break;
                                }
                              }
                              if (_errs7 === errors) {
                                if (data1.event_id !== void 0) {
                                  let data2 = data1.event_id;
                                  const _errs8 = errors;
                                  if (errors === _errs8) {
                                    if (typeof data2 === "string") {
                                      if (func1(data2) > 128) {
                                        validate49.errors = [{ instancePath: instancePath + "/entries/" + i0 + "/event_id", schemaPath: "#/$defs/GraphInvalidation/properties/event_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data2) < 1) {
                                          validate49.errors = [{ instancePath: instancePath + "/entries/" + i0 + "/event_id", schemaPath: "#/$defs/GraphInvalidation/properties/event_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data2)) {
                                            validate49.errors = [{ instancePath: instancePath + "/entries/" + i0 + "/event_id", schemaPath: "#/$defs/GraphInvalidation/properties/event_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate49.errors = [{ instancePath: instancePath + "/entries/" + i0 + "/event_id", schemaPath: "#/$defs/GraphInvalidation/properties/event_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid3 = _errs8 === errors;
                                } else {
                                  var valid3 = true;
                                }
                                if (valid3) {
                                  if (data1.kind !== void 0) {
                                    let data3 = data1.kind;
                                    const _errs10 = errors;
                                    if (typeof data3 !== "string") {
                                      validate49.errors = [{ instancePath: instancePath + "/entries/" + i0 + "/kind", schemaPath: "#/$defs/GraphInvalidation/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                    if ("run_changed" !== data3) {
                                      validate49.errors = [{ instancePath: instancePath + "/entries/" + i0 + "/kind", schemaPath: "#/$defs/GraphInvalidation/properties/kind/const", keyword: "const", params: { allowedValue: "run_changed" }, message: "must be equal to constant" }];
                                      return false;
                                    }
                                    var valid3 = _errs10 === errors;
                                  } else {
                                    var valid3 = true;
                                  }
                                  if (valid3) {
                                    if (data1.revision !== void 0) {
                                      let data4 = data1.revision;
                                      const _errs12 = errors;
                                      if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                                        validate49.errors = [{ instancePath: instancePath + "/entries/" + i0 + "/revision", schemaPath: "#/$defs/GraphInvalidation/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                        return false;
                                      }
                                      if (errors === _errs12) {
                                        if (typeof data4 == "number" && isFinite(data4)) {
                                          if (data4 > 9007199254740991 || isNaN(data4)) {
                                            validate49.errors = [{ instancePath: instancePath + "/entries/" + i0 + "/revision", schemaPath: "#/$defs/GraphInvalidation/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                            return false;
                                          } else {
                                            if (data4 < 0 || isNaN(data4)) {
                                              validate49.errors = [{ instancePath: instancePath + "/entries/" + i0 + "/revision", schemaPath: "#/$defs/GraphInvalidation/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                              return false;
                                            }
                                          }
                                        }
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
                            validate49.errors = [{ instancePath: instancePath + "/entries/" + i0, schemaPath: "#/$defs/GraphInvalidation/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                    validate49.errors = [{ instancePath: instancePath + "/entries", schemaPath: "#/properties/entries/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.has_more !== void 0) {
                  const _errs14 = errors;
                  if (typeof data.has_more !== "boolean") {
                    validate49.errors = [{ instancePath: instancePath + "/has_more", schemaPath: "#/properties/has_more/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
                    return false;
                  }
                  var valid0 = _errs14 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.next_cursor !== void 0) {
                    let data6 = data.next_cursor;
                    const _errs16 = errors;
                    if (errors === _errs16) {
                      if (typeof data6 === "string") {
                        if (func1(data6) > 4096) {
                          validate49.errors = [{ instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" }];
                          return false;
                        } else {
                          if (func1(data6) < 1) {
                            validate49.errors = [{ instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          }
                        }
                      } else {
                        validate49.errors = [{ instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs16 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.observed_revision !== void 0) {
                      let data7 = data.observed_revision;
                      const _errs18 = errors;
                      if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                        validate49.errors = [{ instancePath: instancePath + "/observed_revision", schemaPath: "#/properties/observed_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      if (errors === _errs18) {
                        if (typeof data7 == "number" && isFinite(data7)) {
                          if (data7 > 9007199254740991 || isNaN(data7)) {
                            validate49.errors = [{ instancePath: instancePath + "/observed_revision", schemaPath: "#/properties/observed_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                            return false;
                          } else {
                            if (data7 < 0 || isNaN(data7)) {
                              validate49.errors = [{ instancePath: instancePath + "/observed_revision", schemaPath: "#/properties/observed_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                      if (data.run_id !== void 0) {
                        let data8 = data.run_id;
                        const _errs20 = errors;
                        if (errors === _errs20) {
                          if (typeof data8 === "string") {
                            if (func1(data8) > 128) {
                              validate49.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func1(data8) < 1) {
                                validate49.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern5.test(data8)) {
                                  validate49.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate49.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs20 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.schema_version !== void 0) {
                          let data9 = data.schema_version;
                          const _errs22 = errors;
                          if (typeof data9 !== "string") {
                            validate49.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("1" !== data9) {
                            validate49.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs22 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.scope !== void 0) {
                            let data10 = data.scope;
                            const _errs24 = errors;
                            const _errs25 = errors;
                            if (errors === _errs25) {
                              if (data10 && typeof data10 == "object" && !Array.isArray(data10)) {
                                let missing2;
                                if (data10.tenant_id === void 0 && (missing2 = "tenant_id") || data10.project_id === void 0 && (missing2 = "project_id")) {
                                  validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                  return false;
                                } else {
                                  const _errs27 = errors;
                                  for (const key2 in data10) {
                                    if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                      validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                      return false;
                                      break;
                                    }
                                  }
                                  if (_errs27 === errors) {
                                    if (data10.project_id !== void 0) {
                                      let data11 = data10.project_id;
                                      const _errs28 = errors;
                                      if (errors === _errs28) {
                                        if (typeof data11 === "string") {
                                          if (func1(data11) > 128) {
                                            validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                            return false;
                                          } else {
                                            if (func1(data11) < 1) {
                                              validate49.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                              return false;
                                            } else {
                                              if (!pattern5.test(data11)) {
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
                                      var valid5 = _errs28 === errors;
                                    } else {
                                      var valid5 = true;
                                    }
                                    if (valid5) {
                                      if (data10.tenant_id !== void 0) {
                                        let data12 = data10.tenant_id;
                                        const _errs30 = errors;
                                        if (errors === _errs30) {
                                          if (typeof data12 === "string") {
                                            if (func1(data12) > 128) {
                                              validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                              return false;
                                            } else {
                                              if (func1(data12) < 1) {
                                                validate49.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                return false;
                                              } else {
                                                if (!pattern5.test(data12)) {
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
                                        var valid5 = _errs30 === errors;
                                      } else {
                                        var valid5 = true;
                                      }
                                    }
                                  }
                                }
                              } else {
                                validate49.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
    exports.scopes = validate50;
    function validate51(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.revision === void 0 && (missing0 = "revision") || data.frontier_revision === void 0 && (missing0 = "frontier_revision")) {
            validate51.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "frontier_revision" || key0 === "plan_sha256" || key0 === "revision" || key0 === "run_id" || key0 === "scope")) {
                validate51.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.frontier_revision !== void 0) {
                let data0 = data.frontier_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate51.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate51.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate51.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                      if (!pattern4.test(data1)) {
                        validate51.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate51.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate51.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate51.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate51.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                            validate51.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate51.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern5.test(data3)) {
                                validate51.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate51.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                              validate51.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate51.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                        validate51.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate51.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data5)) {
                                            validate51.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate51.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                          validate51.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate51.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data6)) {
                                              validate51.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate51.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate51.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate51.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate51.errors = vErrors;
      return errors === 0;
    }
    validate51.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema72 = { "additionalProperties": false, "properties": { "definition_path": { "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 16, "title": "Definition Path", "type": "array" }, "node_count": { "maximum": 256, "minimum": 0, "title": "Node Count", "type": "integer" }, "occurrences": { "items": { "discriminator": { "mapping": { "loop": "#/$defs/LoopOccurrence", "scatter": "#/$defs/ScatterOccurrence" }, "propertyName": "kind" }, "oneOf": [{ "$ref": "#/$defs/LoopOccurrence" }, { "$ref": "#/$defs/ScatterOccurrence" }] }, "maxItems": 16, "title": "Occurrences", "type": "array" }, "parent_activation_id": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "title": "Parent Activation Id" }, "scope_key": { "pattern": "^[0-9a-f]{64}$", "title": "Scope Key", "type": "string" }, "status": { "enum": ["active", "completed", "failed", "skipped", "blocked"], "title": "Status", "type": "string" } }, "required": ["scope_key", "definition_path", "occurrences", "parent_activation_id", "status", "node_count"], "title": "GraphScopeView", "type": "object" };
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
          if (data.scope_key === void 0 && (missing0 = "scope_key") || data.definition_path === void 0 && (missing0 = "definition_path") || data.occurrences === void 0 && (missing0 = "occurrences") || data.parent_activation_id === void 0 && (missing0 = "parent_activation_id") || data.status === void 0 && (missing0 = "status") || data.node_count === void 0 && (missing0 = "node_count")) {
            validate53.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "definition_path" || key0 === "node_count" || key0 === "occurrences" || key0 === "parent_activation_id" || key0 === "scope_key" || key0 === "status")) {
                validate53.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.definition_path !== void 0) {
                let data0 = data.definition_path;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 16) {
                      validate53.errors = [{ instancePath: instancePath + "/definition_path", schemaPath: "#/properties/definition_path/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        let data1 = data0[i0];
                        const _errs4 = errors;
                        if (errors === _errs4) {
                          if (typeof data1 === "string") {
                            if (func1(data1) > 128) {
                              validate53.errors = [{ instancePath: instancePath + "/definition_path/" + i0, schemaPath: "#/properties/definition_path/items/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func1(data1) < 1) {
                                validate53.errors = [{ instancePath: instancePath + "/definition_path/" + i0, schemaPath: "#/properties/definition_path/items/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern5.test(data1)) {
                                  validate53.errors = [{ instancePath: instancePath + "/definition_path/" + i0, schemaPath: "#/properties/definition_path/items/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate53.errors = [{ instancePath: instancePath + "/definition_path/" + i0, schemaPath: "#/properties/definition_path/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate53.errors = [{ instancePath: instancePath + "/definition_path", schemaPath: "#/properties/definition_path/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.node_count !== void 0) {
                  let data2 = data.node_count;
                  const _errs6 = errors;
                  if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                    validate53.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs6) {
                    if (typeof data2 == "number" && isFinite(data2)) {
                      if (data2 > 256 || isNaN(data2)) {
                        validate53.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 256 }, message: "must be <= 256" }];
                        return false;
                      } else {
                        if (data2 < 0 || isNaN(data2)) {
                          validate53.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                  if (data.occurrences !== void 0) {
                    let data3 = data.occurrences;
                    const _errs8 = errors;
                    if (errors === _errs8) {
                      if (Array.isArray(data3)) {
                        if (data3.length > 16) {
                          validate53.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                          return false;
                        } else {
                          var valid2 = true;
                          const len1 = data3.length;
                          for (let i1 = 0; i1 < len1; i1++) {
                            let data4 = data3[i1];
                            const _errs10 = errors;
                            const _errs11 = errors;
                            let valid3 = false;
                            let passing0 = null;
                            const _errs12 = errors;
                            const _errs13 = errors;
                            if (errors === _errs13) {
                              if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                                let missing1;
                                if (data4.kind === void 0 && (missing1 = "kind") || data4.node_id === void 0 && (missing1 = "node_id") || data4.index === void 0 && (missing1 = "index")) {
                                  const err0 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/LoopOccurrence/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                                  if (vErrors === null) {
                                    vErrors = [err0];
                                  } else {
                                    vErrors.push(err0);
                                  }
                                  errors++;
                                } else {
                                  const _errs15 = errors;
                                  for (const key1 in data4) {
                                    if (!(key1 === "index" || key1 === "kind" || key1 === "node_id")) {
                                      const err1 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/LoopOccurrence/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                      if (vErrors === null) {
                                        vErrors = [err1];
                                      } else {
                                        vErrors.push(err1);
                                      }
                                      errors++;
                                      break;
                                    }
                                  }
                                  if (_errs15 === errors) {
                                    if (data4.index !== void 0) {
                                      let data5 = data4.index;
                                      const _errs16 = errors;
                                      if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                        const err2 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/LoopOccurrence/properties/index/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                        if (vErrors === null) {
                                          vErrors = [err2];
                                        } else {
                                          vErrors.push(err2);
                                        }
                                        errors++;
                                      }
                                      if (errors === _errs16) {
                                        if (typeof data5 == "number" && isFinite(data5)) {
                                          if (data5 > 9999 || isNaN(data5)) {
                                            const err3 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/LoopOccurrence/properties/index/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9999 }, message: "must be <= 9999" };
                                            if (vErrors === null) {
                                              vErrors = [err3];
                                            } else {
                                              vErrors.push(err3);
                                            }
                                            errors++;
                                          } else {
                                            if (data5 < 0 || isNaN(data5)) {
                                              const err4 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/LoopOccurrence/properties/index/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                                      var valid5 = _errs16 === errors;
                                    } else {
                                      var valid5 = true;
                                    }
                                    if (valid5) {
                                      if (data4.kind !== void 0) {
                                        let data6 = data4.kind;
                                        const _errs18 = errors;
                                        if (typeof data6 !== "string") {
                                          const err5 = { instancePath: instancePath + "/occurrences/" + i1 + "/kind", schemaPath: "#/$defs/LoopOccurrence/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err5];
                                          } else {
                                            vErrors.push(err5);
                                          }
                                          errors++;
                                        }
                                        if ("loop" !== data6) {
                                          const err6 = { instancePath: instancePath + "/occurrences/" + i1 + "/kind", schemaPath: "#/$defs/LoopOccurrence/properties/kind/const", keyword: "const", params: { allowedValue: "loop" }, message: "must be equal to constant" };
                                          if (vErrors === null) {
                                            vErrors = [err6];
                                          } else {
                                            vErrors.push(err6);
                                          }
                                          errors++;
                                        }
                                        var valid5 = _errs18 === errors;
                                      } else {
                                        var valid5 = true;
                                      }
                                      if (valid5) {
                                        if (data4.node_id !== void 0) {
                                          let data7 = data4.node_id;
                                          const _errs20 = errors;
                                          if (errors === _errs20) {
                                            if (typeof data7 === "string") {
                                              if (func1(data7) > 128) {
                                                const err7 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                                if (vErrors === null) {
                                                  vErrors = [err7];
                                                } else {
                                                  vErrors.push(err7);
                                                }
                                                errors++;
                                              } else {
                                                if (func1(data7) < 1) {
                                                  const err8 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                  if (vErrors === null) {
                                                    vErrors = [err8];
                                                  } else {
                                                    vErrors.push(err8);
                                                  }
                                                  errors++;
                                                } else {
                                                  if (!pattern5.test(data7)) {
                                                    const err9 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                              const err10 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                              if (vErrors === null) {
                                                vErrors = [err10];
                                              } else {
                                                vErrors.push(err10);
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
                                }
                              } else {
                                const err11 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/LoopOccurrence/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                if (vErrors === null) {
                                  vErrors = [err11];
                                } else {
                                  vErrors.push(err11);
                                }
                                errors++;
                              }
                            }
                            var _valid0 = _errs12 === errors;
                            if (_valid0) {
                              valid3 = true;
                              passing0 = 0;
                              var props0 = true;
                            }
                            const _errs22 = errors;
                            const _errs23 = errors;
                            if (errors === _errs23) {
                              if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                                let missing2;
                                if (data4.kind === void 0 && (missing2 = "kind") || data4.node_id === void 0 && (missing2 = "node_id") || data4.index === void 0 && (missing2 = "index") || data4.membership_sha256 === void 0 && (missing2 = "membership_sha256")) {
                                  const err12 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/ScatterOccurrence/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                                  if (vErrors === null) {
                                    vErrors = [err12];
                                  } else {
                                    vErrors.push(err12);
                                  }
                                  errors++;
                                } else {
                                  const _errs25 = errors;
                                  for (const key2 in data4) {
                                    if (!(key2 === "index" || key2 === "kind" || key2 === "membership_sha256" || key2 === "node_id")) {
                                      const err13 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/ScatterOccurrence/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                                      if (vErrors === null) {
                                        vErrors = [err13];
                                      } else {
                                        vErrors.push(err13);
                                      }
                                      errors++;
                                      break;
                                    }
                                  }
                                  if (_errs25 === errors) {
                                    if (data4.index !== void 0) {
                                      let data8 = data4.index;
                                      const _errs26 = errors;
                                      if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)) && isFinite(data8))) {
                                        const err14 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/ScatterOccurrence/properties/index/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                        if (vErrors === null) {
                                          vErrors = [err14];
                                        } else {
                                          vErrors.push(err14);
                                        }
                                        errors++;
                                      }
                                      if (errors === _errs26) {
                                        if (typeof data8 == "number" && isFinite(data8)) {
                                          if (data8 > 9999 || isNaN(data8)) {
                                            const err15 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/ScatterOccurrence/properties/index/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9999 }, message: "must be <= 9999" };
                                            if (vErrors === null) {
                                              vErrors = [err15];
                                            } else {
                                              vErrors.push(err15);
                                            }
                                            errors++;
                                          } else {
                                            if (data8 < 0 || isNaN(data8)) {
                                              const err16 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/ScatterOccurrence/properties/index/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                                      var valid7 = _errs26 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                    if (valid7) {
                                      if (data4.kind !== void 0) {
                                        let data9 = data4.kind;
                                        const _errs28 = errors;
                                        if (typeof data9 !== "string") {
                                          const err17 = { instancePath: instancePath + "/occurrences/" + i1 + "/kind", schemaPath: "#/$defs/ScatterOccurrence/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err17];
                                          } else {
                                            vErrors.push(err17);
                                          }
                                          errors++;
                                        }
                                        if ("scatter" !== data9) {
                                          const err18 = { instancePath: instancePath + "/occurrences/" + i1 + "/kind", schemaPath: "#/$defs/ScatterOccurrence/properties/kind/const", keyword: "const", params: { allowedValue: "scatter" }, message: "must be equal to constant" };
                                          if (vErrors === null) {
                                            vErrors = [err18];
                                          } else {
                                            vErrors.push(err18);
                                          }
                                          errors++;
                                        }
                                        var valid7 = _errs28 === errors;
                                      } else {
                                        var valid7 = true;
                                      }
                                      if (valid7) {
                                        if (data4.membership_sha256 !== void 0) {
                                          let data10 = data4.membership_sha256;
                                          const _errs30 = errors;
                                          if (errors === _errs30) {
                                            if (typeof data10 === "string") {
                                              if (!pattern4.test(data10)) {
                                                const err19 = { instancePath: instancePath + "/occurrences/" + i1 + "/membership_sha256", schemaPath: "#/$defs/ScatterOccurrence/properties/membership_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                                if (vErrors === null) {
                                                  vErrors = [err19];
                                                } else {
                                                  vErrors.push(err19);
                                                }
                                                errors++;
                                              }
                                            } else {
                                              const err20 = { instancePath: instancePath + "/occurrences/" + i1 + "/membership_sha256", schemaPath: "#/$defs/ScatterOccurrence/properties/membership_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                              if (vErrors === null) {
                                                vErrors = [err20];
                                              } else {
                                                vErrors.push(err20);
                                              }
                                              errors++;
                                            }
                                          }
                                          var valid7 = _errs30 === errors;
                                        } else {
                                          var valid7 = true;
                                        }
                                        if (valid7) {
                                          if (data4.node_id !== void 0) {
                                            let data11 = data4.node_id;
                                            const _errs32 = errors;
                                            if (errors === _errs32) {
                                              if (typeof data11 === "string") {
                                                if (func1(data11) > 128) {
                                                  const err21 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                                  if (vErrors === null) {
                                                    vErrors = [err21];
                                                  } else {
                                                    vErrors.push(err21);
                                                  }
                                                  errors++;
                                                } else {
                                                  if (func1(data11) < 1) {
                                                    const err22 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                    if (vErrors === null) {
                                                      vErrors = [err22];
                                                    } else {
                                                      vErrors.push(err22);
                                                    }
                                                    errors++;
                                                  } else {
                                                    if (!pattern5.test(data11)) {
                                                      const err23 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                                const err24 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                if (vErrors === null) {
                                                  vErrors = [err24];
                                                } else {
                                                  vErrors.push(err24);
                                                }
                                                errors++;
                                              }
                                            }
                                            var valid7 = _errs32 === errors;
                                          } else {
                                            var valid7 = true;
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              } else {
                                const err25 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/ScatterOccurrence/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                if (vErrors === null) {
                                  vErrors = [err25];
                                } else {
                                  vErrors.push(err25);
                                }
                                errors++;
                              }
                            }
                            var _valid0 = _errs22 === errors;
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
                            }
                            if (!valid3) {
                              const err26 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/properties/occurrences/items/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                              if (vErrors === null) {
                                vErrors = [err26];
                              } else {
                                vErrors.push(err26);
                              }
                              errors++;
                              validate53.errors = vErrors;
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
                            var valid2 = _errs10 === errors;
                            if (!valid2) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate53.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs8 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.parent_activation_id !== void 0) {
                      let data12 = data.parent_activation_id;
                      const _errs35 = errors;
                      const _errs36 = errors;
                      let valid8 = false;
                      const _errs37 = errors;
                      if (errors === _errs37) {
                        if (typeof data12 === "string") {
                          if (!pattern4.test(data12)) {
                            const err27 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                            if (vErrors === null) {
                              vErrors = [err27];
                            } else {
                              vErrors.push(err27);
                            }
                            errors++;
                          }
                        } else {
                          const err28 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err28];
                          } else {
                            vErrors.push(err28);
                          }
                          errors++;
                        }
                      }
                      var _valid1 = _errs37 === errors;
                      valid8 = valid8 || _valid1;
                      const _errs39 = errors;
                      if (data12 !== null) {
                        const err29 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err29];
                        } else {
                          vErrors.push(err29);
                        }
                        errors++;
                      }
                      var _valid1 = _errs39 === errors;
                      valid8 = valid8 || _valid1;
                      if (!valid8) {
                        const err30 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err30];
                        } else {
                          vErrors.push(err30);
                        }
                        errors++;
                        validate53.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs36;
                        if (vErrors !== null) {
                          if (_errs36) {
                            vErrors.length = _errs36;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs35 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.scope_key !== void 0) {
                        let data13 = data.scope_key;
                        const _errs41 = errors;
                        if (errors === _errs41) {
                          if (typeof data13 === "string") {
                            if (!pattern4.test(data13)) {
                              validate53.errors = [{ instancePath: instancePath + "/scope_key", schemaPath: "#/properties/scope_key/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate53.errors = [{ instancePath: instancePath + "/scope_key", schemaPath: "#/properties/scope_key/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs41 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.status !== void 0) {
                          let data14 = data.status;
                          const _errs43 = errors;
                          if (typeof data14 !== "string") {
                            validate53.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if (!(data14 === "active" || data14 === "completed" || data14 === "failed" || data14 === "skipped" || data14 === "blocked")) {
                            validate53.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema72.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                            return false;
                          }
                          var valid0 = _errs43 === errors;
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
    function validate50(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate50.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.cut === void 0 && (missing0 = "cut") || data.parent_activation_id === void 0 && (missing0 = "parent_activation_id") || data.scope_count === void 0 && (missing0 = "scope_count") || data.scopes === void 0 && (missing0 = "scopes") || data.next_cursor === void 0 && (missing0 = "next_cursor")) {
            validate50.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "cut" || key0 === "next_cursor" || key0 === "parent_activation_id" || key0 === "schema_version" || key0 === "scope_count" || key0 === "scopes")) {
                validate50.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.cut !== void 0) {
                const _errs2 = errors;
                if (!validate51(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate51.errors : vErrors.concat(validate51.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.next_cursor !== void 0) {
                  let data1 = data.next_cursor;
                  const _errs3 = errors;
                  const _errs4 = errors;
                  let valid1 = false;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (typeof data1 === "string") {
                      if (func1(data1) > 4096) {
                        const err0 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        if (func1(data1) < 1) {
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
                  var _valid0 = _errs5 === errors;
                  valid1 = valid1 || _valid0;
                  const _errs7 = errors;
                  if (data1 !== null) {
                    const err3 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                    if (vErrors === null) {
                      vErrors = [err3];
                    } else {
                      vErrors.push(err3);
                    }
                    errors++;
                  }
                  var _valid0 = _errs7 === errors;
                  valid1 = valid1 || _valid0;
                  if (!valid1) {
                    const err4 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                    if (vErrors === null) {
                      vErrors = [err4];
                    } else {
                      vErrors.push(err4);
                    }
                    errors++;
                    validate50.errors = vErrors;
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
                  if (data.parent_activation_id !== void 0) {
                    let data2 = data.parent_activation_id;
                    const _errs9 = errors;
                    const _errs10 = errors;
                    let valid2 = false;
                    const _errs11 = errors;
                    if (errors === _errs11) {
                      if (typeof data2 === "string") {
                        if (!pattern4.test(data2)) {
                          const err5 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                          if (vErrors === null) {
                            vErrors = [err5];
                          } else {
                            vErrors.push(err5);
                          }
                          errors++;
                        }
                      } else {
                        const err6 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                        if (vErrors === null) {
                          vErrors = [err6];
                        } else {
                          vErrors.push(err6);
                        }
                        errors++;
                      }
                    }
                    var _valid1 = _errs11 === errors;
                    valid2 = valid2 || _valid1;
                    const _errs13 = errors;
                    if (data2 !== null) {
                      const err7 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                      if (vErrors === null) {
                        vErrors = [err7];
                      } else {
                        vErrors.push(err7);
                      }
                      errors++;
                    }
                    var _valid1 = _errs13 === errors;
                    valid2 = valid2 || _valid1;
                    if (!valid2) {
                      const err8 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                      if (vErrors === null) {
                        vErrors = [err8];
                      } else {
                        vErrors.push(err8);
                      }
                      errors++;
                      validate50.errors = vErrors;
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
                    if (data.schema_version !== void 0) {
                      let data3 = data.schema_version;
                      const _errs15 = errors;
                      if (typeof data3 !== "string") {
                        validate50.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      if ("1" !== data3) {
                        validate50.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                        return false;
                      }
                      var valid0 = _errs15 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.scope_count !== void 0) {
                        let data4 = data.scope_count;
                        const _errs17 = errors;
                        if (!(typeof data4 == "number" && (!(data4 % 1) && !isNaN(data4)) && isFinite(data4))) {
                          validate50.errors = [{ instancePath: instancePath + "/scope_count", schemaPath: "#/properties/scope_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                          return false;
                        }
                        if (errors === _errs17) {
                          if (typeof data4 == "number" && isFinite(data4)) {
                            if (data4 > 1e5 || isNaN(data4)) {
                              validate50.errors = [{ instancePath: instancePath + "/scope_count", schemaPath: "#/properties/scope_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e5 }, message: "must be <= 100000" }];
                              return false;
                            } else {
                              if (data4 < 0 || isNaN(data4)) {
                                validate50.errors = [{ instancePath: instancePath + "/scope_count", schemaPath: "#/properties/scope_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                return false;
                              }
                            }
                          }
                        }
                        var valid0 = _errs17 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.scopes !== void 0) {
                          let data5 = data.scopes;
                          const _errs19 = errors;
                          if (errors === _errs19) {
                            if (Array.isArray(data5)) {
                              if (data5.length > 100) {
                                validate50.errors = [{ instancePath: instancePath + "/scopes", schemaPath: "#/properties/scopes/maxItems", keyword: "maxItems", params: { limit: 100 }, message: "must NOT have more than 100 items" }];
                                return false;
                              } else {
                                var valid3 = true;
                                const len0 = data5.length;
                                for (let i0 = 0; i0 < len0; i0++) {
                                  const _errs21 = errors;
                                  if (!validate53(data5[i0], { instancePath: instancePath + "/scopes/" + i0, parentData: data5, parentDataProperty: i0, rootData, dynamicAnchors })) {
                                    vErrors = vErrors === null ? validate53.errors : vErrors.concat(validate53.errors);
                                    errors = vErrors.length;
                                  }
                                  var valid3 = _errs21 === errors;
                                  if (!valid3) {
                                    break;
                                  }
                                }
                              }
                            } else {
                              validate50.errors = [{ instancePath: instancePath + "/scopes", schemaPath: "#/properties/scopes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
        } else {
          validate50.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate50.errors = vErrors;
      return errors === 0;
    }
    validate50.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.topology = validate55;
    var schema75 = { "$defs": { "ActivationPath": { "additionalProperties": false, "properties": { "node_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Node Id", "type": "string" }, "occurrences": { "default": [], "items": { "discriminator": { "mapping": { "loop": "#/$defs/LoopOccurrence", "scatter": "#/$defs/ScatterOccurrence" }, "propertyName": "kind" }, "oneOf": [{ "$ref": "#/$defs/LoopOccurrence" }, { "$ref": "#/$defs/ScatterOccurrence" }] }, "maxItems": 16, "title": "Occurrences", "type": "array" }, "schema_version": { "const": "2", "title": "Schema Version", "type": "string" } }, "required": ["schema_version", "node_id"], "title": "ActivationPath", "type": "object" }, "GraphControlLink": { "additionalProperties": false, "properties": { "route": { "enum": ["next", "true", "false"], "title": "Route", "type": "string" }, "source": { "pattern": "^[0-9a-f]{64}$", "title": "Source", "type": "string" }, "target": { "pattern": "^[0-9a-f]{64}$", "title": "Target", "type": "string" } }, "required": ["source", "target", "route"], "title": "GraphControlLink", "type": "object" }, "GraphNodeViewV3": { "additionalProperties": false, "properties": { "activation_id": { "pattern": "^[0-9a-f]{64}$", "title": "Activation Id", "type": "string" }, "kind": { "enum": ["invoke", "branch", "join", "scatter", "iterate", "finish", "await", "artifact_project", "artifact_materialize"], "title": "Kind", "type": "string" }, "path": { "$ref": "#/$defs/ActivationPath" }, "reason_code": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Reason Code" }, "status": { "enum": ["waiting", "ready", "issued", "succeeded", "skipped", "failed", "blocked"], "title": "Status", "type": "string" } }, "required": ["activation_id", "path", "kind", "status", "reason_code"], "title": "GraphNodeViewV3", "type": "object" }, "GraphReadCut": { "additionalProperties": false, "properties": { "frontier_revision": { "maximum": 9007199254740991, "minimum": 0, "title": "Frontier Revision", "type": "integer" }, "plan_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Plan Sha256", "type": "string" }, "revision": { "maximum": 9007199254740991, "minimum": 0, "title": "Revision", "type": "integer" }, "run_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Run Id", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "run_id", "plan_sha256", "revision", "frontier_revision"], "title": "GraphReadCut", "type": "object" }, "GraphScopeView": { "additionalProperties": false, "properties": { "definition_path": { "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 16, "title": "Definition Path", "type": "array" }, "node_count": { "maximum": 256, "minimum": 0, "title": "Node Count", "type": "integer" }, "occurrences": { "items": { "discriminator": { "mapping": { "loop": "#/$defs/LoopOccurrence", "scatter": "#/$defs/ScatterOccurrence" }, "propertyName": "kind" }, "oneOf": [{ "$ref": "#/$defs/LoopOccurrence" }, { "$ref": "#/$defs/ScatterOccurrence" }] }, "maxItems": 16, "title": "Occurrences", "type": "array" }, "parent_activation_id": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "title": "Parent Activation Id" }, "scope_key": { "pattern": "^[0-9a-f]{64}$", "title": "Scope Key", "type": "string" }, "status": { "enum": ["active", "completed", "failed", "skipped", "blocked"], "title": "Status", "type": "string" } }, "required": ["scope_key", "definition_path", "occurrences", "parent_activation_id", "status", "node_count"], "title": "GraphScopeView", "type": "object" }, "GraphTopologyNode": { "additionalProperties": false, "properties": { "activation": { "$ref": "#/$defs/GraphNodeViewV3" }, "child_scope_count": { "maximum": 1e5, "minimum": 0, "title": "Child Scope Count", "type": "integer" } }, "required": ["activation", "child_scope_count"], "title": "GraphTopologyNode", "type": "object" }, "GraphTopologyQuery": { "additionalProperties": false, "properties": { "focus_activation_id": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "default": null, "title": "Focus Activation Id" }, "radius": { "default": 1, "maximum": 2, "minimum": 0, "title": "Radius", "type": "integer" } }, "title": "GraphTopologyQuery", "type": "object" }, "LoopOccurrence": { "additionalProperties": false, "properties": { "index": { "maximum": 9999, "minimum": 0, "title": "Index", "type": "integer" }, "kind": { "const": "loop", "title": "Kind", "type": "string" }, "node_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Node Id", "type": "string" } }, "required": ["kind", "node_id", "index"], "title": "LoopOccurrence", "type": "object" }, "ScatterOccurrence": { "additionalProperties": false, "properties": { "index": { "maximum": 9999, "minimum": 0, "title": "Index", "type": "integer" }, "kind": { "const": "scatter", "title": "Kind", "type": "string" }, "membership_sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Membership Sha256", "type": "string" }, "node_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Node Id", "type": "string" } }, "required": ["kind", "node_id", "index", "membership_sha256"], "title": "ScatterOccurrence", "type": "object" }, "Scope": { "additionalProperties": false, "properties": { "project_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Project Id", "type": "string" }, "tenant_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Tenant Id", "type": "string" } }, "required": ["tenant_id", "project_id"], "title": "Scope", "type": "object" } }, "$id": "urn:amphora:graph-runtime.topology-page:1:serialization", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": { "cut": { "$ref": "#/$defs/GraphReadCut" }, "edge_count": { "maximum": 1024, "minimum": 0, "title": "Edge Count", "type": "integer" }, "edges": { "items": { "$ref": "#/$defs/GraphControlLink" }, "maxItems": 1024, "title": "Edges", "type": "array" }, "graph_scope": { "$ref": "#/$defs/GraphScopeView" }, "next_cursor": { "anyOf": [{ "maxLength": 4096, "minLength": 1, "type": "string" }, { "type": "null" }], "title": "Next Cursor" }, "node_count": { "maximum": 256, "minimum": 0, "title": "Node Count", "type": "integer" }, "nodes": { "items": { "$ref": "#/$defs/GraphTopologyNode" }, "maxItems": 100, "title": "Nodes", "type": "array" }, "query": { "$ref": "#/$defs/GraphTopologyQuery" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" } }, "required": ["cut", "graph_scope", "query", "node_count", "edge_count", "nodes", "edges", "next_cursor"], "title": "GraphTopologyPage", "type": "object" };
    var schema78 = { "additionalProperties": false, "properties": { "route": { "enum": ["next", "true", "false"], "title": "Route", "type": "string" }, "source": { "pattern": "^[0-9a-f]{64}$", "title": "Source", "type": "string" }, "target": { "pattern": "^[0-9a-f]{64}$", "title": "Target", "type": "string" } }, "required": ["source", "target", "route"], "title": "GraphControlLink", "type": "object" };
    var func115 = Object.prototype.hasOwnProperty;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.revision === void 0 && (missing0 = "revision") || data.frontier_revision === void 0 && (missing0 = "frontier_revision")) {
            validate56.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "frontier_revision" || key0 === "plan_sha256" || key0 === "revision" || key0 === "run_id" || key0 === "scope")) {
                validate56.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.frontier_revision !== void 0) {
                let data0 = data.frontier_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate56.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate56.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate56.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                      if (!pattern4.test(data1)) {
                        validate56.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate56.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate56.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate56.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate56.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                            validate56.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate56.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern5.test(data3)) {
                                validate56.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate56.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                              validate56.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate56.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                        validate56.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate56.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data5)) {
                                            validate56.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate56.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                          validate56.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate56.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data6)) {
                                              validate56.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                              return false;
                                            }
                                          }
                                        }
                                      } else {
                                        validate56.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate56.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate56.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate56.errors = vErrors;
      return errors === 0;
    }
    validate56.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema79 = { "additionalProperties": false, "properties": { "definition_path": { "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 16, "title": "Definition Path", "type": "array" }, "node_count": { "maximum": 256, "minimum": 0, "title": "Node Count", "type": "integer" }, "occurrences": { "items": { "discriminator": { "mapping": { "loop": "#/$defs/LoopOccurrence", "scatter": "#/$defs/ScatterOccurrence" }, "propertyName": "kind" }, "oneOf": [{ "$ref": "#/$defs/LoopOccurrence" }, { "$ref": "#/$defs/ScatterOccurrence" }] }, "maxItems": 16, "title": "Occurrences", "type": "array" }, "parent_activation_id": { "anyOf": [{ "pattern": "^[0-9a-f]{64}$", "type": "string" }, { "type": "null" }], "title": "Parent Activation Id" }, "scope_key": { "pattern": "^[0-9a-f]{64}$", "title": "Scope Key", "type": "string" }, "status": { "enum": ["active", "completed", "failed", "skipped", "blocked"], "title": "Status", "type": "string" } }, "required": ["scope_key", "definition_path", "occurrences", "parent_activation_id", "status", "node_count"], "title": "GraphScopeView", "type": "object" };
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
          if (data.scope_key === void 0 && (missing0 = "scope_key") || data.definition_path === void 0 && (missing0 = "definition_path") || data.occurrences === void 0 && (missing0 = "occurrences") || data.parent_activation_id === void 0 && (missing0 = "parent_activation_id") || data.status === void 0 && (missing0 = "status") || data.node_count === void 0 && (missing0 = "node_count")) {
            validate58.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "definition_path" || key0 === "node_count" || key0 === "occurrences" || key0 === "parent_activation_id" || key0 === "scope_key" || key0 === "status")) {
                validate58.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.definition_path !== void 0) {
                let data0 = data.definition_path;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 16) {
                      validate58.errors = [{ instancePath: instancePath + "/definition_path", schemaPath: "#/properties/definition_path/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        let data1 = data0[i0];
                        const _errs4 = errors;
                        if (errors === _errs4) {
                          if (typeof data1 === "string") {
                            if (func1(data1) > 128) {
                              validate58.errors = [{ instancePath: instancePath + "/definition_path/" + i0, schemaPath: "#/properties/definition_path/items/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                              return false;
                            } else {
                              if (func1(data1) < 1) {
                                validate58.errors = [{ instancePath: instancePath + "/definition_path/" + i0, schemaPath: "#/properties/definition_path/items/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                return false;
                              } else {
                                if (!pattern5.test(data1)) {
                                  validate58.errors = [{ instancePath: instancePath + "/definition_path/" + i0, schemaPath: "#/properties/definition_path/items/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                  return false;
                                }
                              }
                            }
                          } else {
                            validate58.errors = [{ instancePath: instancePath + "/definition_path/" + i0, schemaPath: "#/properties/definition_path/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate58.errors = [{ instancePath: instancePath + "/definition_path", schemaPath: "#/properties/definition_path/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.node_count !== void 0) {
                  let data2 = data.node_count;
                  const _errs6 = errors;
                  if (!(typeof data2 == "number" && (!(data2 % 1) && !isNaN(data2)) && isFinite(data2))) {
                    validate58.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs6) {
                    if (typeof data2 == "number" && isFinite(data2)) {
                      if (data2 > 256 || isNaN(data2)) {
                        validate58.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 256 }, message: "must be <= 256" }];
                        return false;
                      } else {
                        if (data2 < 0 || isNaN(data2)) {
                          validate58.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                  if (data.occurrences !== void 0) {
                    let data3 = data.occurrences;
                    const _errs8 = errors;
                    if (errors === _errs8) {
                      if (Array.isArray(data3)) {
                        if (data3.length > 16) {
                          validate58.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
                          return false;
                        } else {
                          var valid2 = true;
                          const len1 = data3.length;
                          for (let i1 = 0; i1 < len1; i1++) {
                            let data4 = data3[i1];
                            const _errs10 = errors;
                            const _errs11 = errors;
                            let valid3 = false;
                            let passing0 = null;
                            const _errs12 = errors;
                            const _errs13 = errors;
                            if (errors === _errs13) {
                              if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                                let missing1;
                                if (data4.kind === void 0 && (missing1 = "kind") || data4.node_id === void 0 && (missing1 = "node_id") || data4.index === void 0 && (missing1 = "index")) {
                                  const err0 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/LoopOccurrence/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                                  if (vErrors === null) {
                                    vErrors = [err0];
                                  } else {
                                    vErrors.push(err0);
                                  }
                                  errors++;
                                } else {
                                  const _errs15 = errors;
                                  for (const key1 in data4) {
                                    if (!(key1 === "index" || key1 === "kind" || key1 === "node_id")) {
                                      const err1 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/LoopOccurrence/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
                                      if (vErrors === null) {
                                        vErrors = [err1];
                                      } else {
                                        vErrors.push(err1);
                                      }
                                      errors++;
                                      break;
                                    }
                                  }
                                  if (_errs15 === errors) {
                                    if (data4.index !== void 0) {
                                      let data5 = data4.index;
                                      const _errs16 = errors;
                                      if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                        const err2 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/LoopOccurrence/properties/index/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                        if (vErrors === null) {
                                          vErrors = [err2];
                                        } else {
                                          vErrors.push(err2);
                                        }
                                        errors++;
                                      }
                                      if (errors === _errs16) {
                                        if (typeof data5 == "number" && isFinite(data5)) {
                                          if (data5 > 9999 || isNaN(data5)) {
                                            const err3 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/LoopOccurrence/properties/index/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9999 }, message: "must be <= 9999" };
                                            if (vErrors === null) {
                                              vErrors = [err3];
                                            } else {
                                              vErrors.push(err3);
                                            }
                                            errors++;
                                          } else {
                                            if (data5 < 0 || isNaN(data5)) {
                                              const err4 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/LoopOccurrence/properties/index/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                                      var valid5 = _errs16 === errors;
                                    } else {
                                      var valid5 = true;
                                    }
                                    if (valid5) {
                                      if (data4.kind !== void 0) {
                                        let data6 = data4.kind;
                                        const _errs18 = errors;
                                        if (typeof data6 !== "string") {
                                          const err5 = { instancePath: instancePath + "/occurrences/" + i1 + "/kind", schemaPath: "#/$defs/LoopOccurrence/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err5];
                                          } else {
                                            vErrors.push(err5);
                                          }
                                          errors++;
                                        }
                                        if ("loop" !== data6) {
                                          const err6 = { instancePath: instancePath + "/occurrences/" + i1 + "/kind", schemaPath: "#/$defs/LoopOccurrence/properties/kind/const", keyword: "const", params: { allowedValue: "loop" }, message: "must be equal to constant" };
                                          if (vErrors === null) {
                                            vErrors = [err6];
                                          } else {
                                            vErrors.push(err6);
                                          }
                                          errors++;
                                        }
                                        var valid5 = _errs18 === errors;
                                      } else {
                                        var valid5 = true;
                                      }
                                      if (valid5) {
                                        if (data4.node_id !== void 0) {
                                          let data7 = data4.node_id;
                                          const _errs20 = errors;
                                          if (errors === _errs20) {
                                            if (typeof data7 === "string") {
                                              if (func1(data7) > 128) {
                                                const err7 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                                if (vErrors === null) {
                                                  vErrors = [err7];
                                                } else {
                                                  vErrors.push(err7);
                                                }
                                                errors++;
                                              } else {
                                                if (func1(data7) < 1) {
                                                  const err8 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                  if (vErrors === null) {
                                                    vErrors = [err8];
                                                  } else {
                                                    vErrors.push(err8);
                                                  }
                                                  errors++;
                                                } else {
                                                  if (!pattern5.test(data7)) {
                                                    const err9 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                              const err10 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/LoopOccurrence/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                              if (vErrors === null) {
                                                vErrors = [err10];
                                              } else {
                                                vErrors.push(err10);
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
                                }
                              } else {
                                const err11 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/LoopOccurrence/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                if (vErrors === null) {
                                  vErrors = [err11];
                                } else {
                                  vErrors.push(err11);
                                }
                                errors++;
                              }
                            }
                            var _valid0 = _errs12 === errors;
                            if (_valid0) {
                              valid3 = true;
                              passing0 = 0;
                              var props0 = true;
                            }
                            const _errs22 = errors;
                            const _errs23 = errors;
                            if (errors === _errs23) {
                              if (data4 && typeof data4 == "object" && !Array.isArray(data4)) {
                                let missing2;
                                if (data4.kind === void 0 && (missing2 = "kind") || data4.node_id === void 0 && (missing2 = "node_id") || data4.index === void 0 && (missing2 = "index") || data4.membership_sha256 === void 0 && (missing2 = "membership_sha256")) {
                                  const err12 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/ScatterOccurrence/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                                  if (vErrors === null) {
                                    vErrors = [err12];
                                  } else {
                                    vErrors.push(err12);
                                  }
                                  errors++;
                                } else {
                                  const _errs25 = errors;
                                  for (const key2 in data4) {
                                    if (!(key2 === "index" || key2 === "kind" || key2 === "membership_sha256" || key2 === "node_id")) {
                                      const err13 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/ScatterOccurrence/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                                      if (vErrors === null) {
                                        vErrors = [err13];
                                      } else {
                                        vErrors.push(err13);
                                      }
                                      errors++;
                                      break;
                                    }
                                  }
                                  if (_errs25 === errors) {
                                    if (data4.index !== void 0) {
                                      let data8 = data4.index;
                                      const _errs26 = errors;
                                      if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)) && isFinite(data8))) {
                                        const err14 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/ScatterOccurrence/properties/index/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                        if (vErrors === null) {
                                          vErrors = [err14];
                                        } else {
                                          vErrors.push(err14);
                                        }
                                        errors++;
                                      }
                                      if (errors === _errs26) {
                                        if (typeof data8 == "number" && isFinite(data8)) {
                                          if (data8 > 9999 || isNaN(data8)) {
                                            const err15 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/ScatterOccurrence/properties/index/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9999 }, message: "must be <= 9999" };
                                            if (vErrors === null) {
                                              vErrors = [err15];
                                            } else {
                                              vErrors.push(err15);
                                            }
                                            errors++;
                                          } else {
                                            if (data8 < 0 || isNaN(data8)) {
                                              const err16 = { instancePath: instancePath + "/occurrences/" + i1 + "/index", schemaPath: "#/$defs/ScatterOccurrence/properties/index/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" };
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
                                      var valid7 = _errs26 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                    if (valid7) {
                                      if (data4.kind !== void 0) {
                                        let data9 = data4.kind;
                                        const _errs28 = errors;
                                        if (typeof data9 !== "string") {
                                          const err17 = { instancePath: instancePath + "/occurrences/" + i1 + "/kind", schemaPath: "#/$defs/ScatterOccurrence/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err17];
                                          } else {
                                            vErrors.push(err17);
                                          }
                                          errors++;
                                        }
                                        if ("scatter" !== data9) {
                                          const err18 = { instancePath: instancePath + "/occurrences/" + i1 + "/kind", schemaPath: "#/$defs/ScatterOccurrence/properties/kind/const", keyword: "const", params: { allowedValue: "scatter" }, message: "must be equal to constant" };
                                          if (vErrors === null) {
                                            vErrors = [err18];
                                          } else {
                                            vErrors.push(err18);
                                          }
                                          errors++;
                                        }
                                        var valid7 = _errs28 === errors;
                                      } else {
                                        var valid7 = true;
                                      }
                                      if (valid7) {
                                        if (data4.membership_sha256 !== void 0) {
                                          let data10 = data4.membership_sha256;
                                          const _errs30 = errors;
                                          if (errors === _errs30) {
                                            if (typeof data10 === "string") {
                                              if (!pattern4.test(data10)) {
                                                const err19 = { instancePath: instancePath + "/occurrences/" + i1 + "/membership_sha256", schemaPath: "#/$defs/ScatterOccurrence/properties/membership_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                                if (vErrors === null) {
                                                  vErrors = [err19];
                                                } else {
                                                  vErrors.push(err19);
                                                }
                                                errors++;
                                              }
                                            } else {
                                              const err20 = { instancePath: instancePath + "/occurrences/" + i1 + "/membership_sha256", schemaPath: "#/$defs/ScatterOccurrence/properties/membership_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                              if (vErrors === null) {
                                                vErrors = [err20];
                                              } else {
                                                vErrors.push(err20);
                                              }
                                              errors++;
                                            }
                                          }
                                          var valid7 = _errs30 === errors;
                                        } else {
                                          var valid7 = true;
                                        }
                                        if (valid7) {
                                          if (data4.node_id !== void 0) {
                                            let data11 = data4.node_id;
                                            const _errs32 = errors;
                                            if (errors === _errs32) {
                                              if (typeof data11 === "string") {
                                                if (func1(data11) > 128) {
                                                  const err21 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                                  if (vErrors === null) {
                                                    vErrors = [err21];
                                                  } else {
                                                    vErrors.push(err21);
                                                  }
                                                  errors++;
                                                } else {
                                                  if (func1(data11) < 1) {
                                                    const err22 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                                    if (vErrors === null) {
                                                      vErrors = [err22];
                                                    } else {
                                                      vErrors.push(err22);
                                                    }
                                                    errors++;
                                                  } else {
                                                    if (!pattern5.test(data11)) {
                                                      const err23 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                                const err24 = { instancePath: instancePath + "/occurrences/" + i1 + "/node_id", schemaPath: "#/$defs/ScatterOccurrence/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                                if (vErrors === null) {
                                                  vErrors = [err24];
                                                } else {
                                                  vErrors.push(err24);
                                                }
                                                errors++;
                                              }
                                            }
                                            var valid7 = _errs32 === errors;
                                          } else {
                                            var valid7 = true;
                                          }
                                        }
                                      }
                                    }
                                  }
                                }
                              } else {
                                const err25 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/$defs/ScatterOccurrence/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                                if (vErrors === null) {
                                  vErrors = [err25];
                                } else {
                                  vErrors.push(err25);
                                }
                                errors++;
                              }
                            }
                            var _valid0 = _errs22 === errors;
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
                            }
                            if (!valid3) {
                              const err26 = { instancePath: instancePath + "/occurrences/" + i1, schemaPath: "#/properties/occurrences/items/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                              if (vErrors === null) {
                                vErrors = [err26];
                              } else {
                                vErrors.push(err26);
                              }
                              errors++;
                              validate58.errors = vErrors;
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
                            var valid2 = _errs10 === errors;
                            if (!valid2) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate58.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs8 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.parent_activation_id !== void 0) {
                      let data12 = data.parent_activation_id;
                      const _errs35 = errors;
                      const _errs36 = errors;
                      let valid8 = false;
                      const _errs37 = errors;
                      if (errors === _errs37) {
                        if (typeof data12 === "string") {
                          if (!pattern4.test(data12)) {
                            const err27 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                            if (vErrors === null) {
                              vErrors = [err27];
                            } else {
                              vErrors.push(err27);
                            }
                            errors++;
                          }
                        } else {
                          const err28 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err28];
                          } else {
                            vErrors.push(err28);
                          }
                          errors++;
                        }
                      }
                      var _valid1 = _errs37 === errors;
                      valid8 = valid8 || _valid1;
                      const _errs39 = errors;
                      if (data12 !== null) {
                        const err29 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err29];
                        } else {
                          vErrors.push(err29);
                        }
                        errors++;
                      }
                      var _valid1 = _errs39 === errors;
                      valid8 = valid8 || _valid1;
                      if (!valid8) {
                        const err30 = { instancePath: instancePath + "/parent_activation_id", schemaPath: "#/properties/parent_activation_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err30];
                        } else {
                          vErrors.push(err30);
                        }
                        errors++;
                        validate58.errors = vErrors;
                        return false;
                      } else {
                        errors = _errs36;
                        if (vErrors !== null) {
                          if (_errs36) {
                            vErrors.length = _errs36;
                          } else {
                            vErrors = null;
                          }
                        }
                      }
                      var valid0 = _errs35 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.scope_key !== void 0) {
                        let data13 = data.scope_key;
                        const _errs41 = errors;
                        if (errors === _errs41) {
                          if (typeof data13 === "string") {
                            if (!pattern4.test(data13)) {
                              validate58.errors = [{ instancePath: instancePath + "/scope_key", schemaPath: "#/properties/scope_key/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate58.errors = [{ instancePath: instancePath + "/scope_key", schemaPath: "#/properties/scope_key/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                        }
                        var valid0 = _errs41 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.status !== void 0) {
                          let data14 = data.status;
                          const _errs43 = errors;
                          if (typeof data14 !== "string") {
                            validate58.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if (!(data14 === "active" || data14 === "completed" || data14 === "failed" || data14 === "skipped" || data14 === "blocked")) {
                            validate58.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema79.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                            return false;
                          }
                          var valid0 = _errs43 === errors;
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
          validate58.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate58.errors = vErrors;
      return errors === 0;
    }
    validate58.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema83 = { "additionalProperties": false, "properties": { "activation_id": { "pattern": "^[0-9a-f]{64}$", "title": "Activation Id", "type": "string" }, "kind": { "enum": ["invoke", "branch", "join", "scatter", "iterate", "finish", "await", "artifact_project", "artifact_materialize"], "title": "Kind", "type": "string" }, "path": { "$ref": "#/$defs/ActivationPath" }, "reason_code": { "anyOf": [{ "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, { "type": "null" }], "title": "Reason Code" }, "status": { "enum": ["waiting", "ready", "issued", "succeeded", "skipped", "failed", "blocked"], "title": "Status", "type": "string" } }, "required": ["activation_id", "path", "kind", "status", "reason_code"], "title": "GraphNodeViewV3", "type": "object" };
    function validate62(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate62.evaluated;
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
            validate62.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "node_id" || key0 === "occurrences" || key0 === "schema_version")) {
                validate62.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate62.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate62.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate62.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate62.errors = [{ instancePath: instancePath + "/node_id", schemaPath: "#/properties/node_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate62.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/maxItems", keyword: "maxItems", params: { limit: 16 }, message: "must NOT have more than 16 items" }];
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
                                                if (!pattern5.test(data5)) {
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
                                            if (!pattern4.test(data8)) {
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
                                                  if (!pattern5.test(data9)) {
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
                            validate62.errors = vErrors;
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
                      validate62.errors = [{ instancePath: instancePath + "/occurrences", schemaPath: "#/properties/occurrences/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
                      validate62.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("2" !== data10) {
                      validate62.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "2" }, message: "must be equal to constant" }];
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
          validate62.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate62.errors = vErrors;
      return errors === 0;
    }
    validate62.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.activation_id === void 0 && (missing0 = "activation_id") || data.path === void 0 && (missing0 = "path") || data.kind === void 0 && (missing0 = "kind") || data.status === void 0 && (missing0 = "status") || data.reason_code === void 0 && (missing0 = "reason_code")) {
            validate61.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "activation_id" || key0 === "kind" || key0 === "path" || key0 === "reason_code" || key0 === "status")) {
                validate61.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                    if (!pattern4.test(data0)) {
                      validate61.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate61.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate61.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if (!(data1 === "invoke" || data1 === "branch" || data1 === "join" || data1 === "scatter" || data1 === "iterate" || data1 === "finish" || data1 === "await" || data1 === "artifact_project" || data1 === "artifact_materialize")) {
                    validate61.errors = [{ instancePath: instancePath + "/kind", schemaPath: "#/properties/kind/enum", keyword: "enum", params: { allowedValues: schema83.properties.kind.enum }, message: "must be equal to one of the allowed values" }];
                    return false;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.path !== void 0) {
                    const _errs6 = errors;
                    if (!validate62(data.path, { instancePath: instancePath + "/path", parentData: data, parentDataProperty: "path", rootData, dynamicAnchors })) {
                      vErrors = vErrors === null ? validate62.errors : vErrors.concat(validate62.errors);
                      errors = vErrors.length;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.reason_code !== void 0) {
                      let data3 = data.reason_code;
                      const _errs7 = errors;
                      const _errs8 = errors;
                      let valid1 = false;
                      const _errs9 = errors;
                      if (errors === _errs9) {
                        if (typeof data3 === "string") {
                          if (func1(data3) > 128) {
                            const err0 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                            if (vErrors === null) {
                              vErrors = [err0];
                            } else {
                              vErrors.push(err0);
                            }
                            errors++;
                          } else {
                            if (func1(data3) < 1) {
                              const err1 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                              if (vErrors === null) {
                                vErrors = [err1];
                              } else {
                                vErrors.push(err1);
                              }
                              errors++;
                            } else {
                              if (!pattern5.test(data3)) {
                                const err2 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                          const err3 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                          if (vErrors === null) {
                            vErrors = [err3];
                          } else {
                            vErrors.push(err3);
                          }
                          errors++;
                        }
                      }
                      var _valid0 = _errs9 === errors;
                      valid1 = valid1 || _valid0;
                      const _errs11 = errors;
                      if (data3 !== null) {
                        const err4 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                        if (vErrors === null) {
                          vErrors = [err4];
                        } else {
                          vErrors.push(err4);
                        }
                        errors++;
                      }
                      var _valid0 = _errs11 === errors;
                      valid1 = valid1 || _valid0;
                      if (!valid1) {
                        const err5 = { instancePath: instancePath + "/reason_code", schemaPath: "#/properties/reason_code/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                        if (vErrors === null) {
                          vErrors = [err5];
                        } else {
                          vErrors.push(err5);
                        }
                        errors++;
                        validate61.errors = vErrors;
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
                      if (data.status !== void 0) {
                        let data4 = data.status;
                        const _errs13 = errors;
                        if (typeof data4 !== "string") {
                          validate61.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if (!(data4 === "waiting" || data4 === "ready" || data4 === "issued" || data4 === "succeeded" || data4 === "skipped" || data4 === "failed" || data4 === "blocked")) {
                          validate61.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/enum", keyword: "enum", params: { allowedValues: schema83.properties.status.enum }, message: "must be equal to one of the allowed values" }];
                          return false;
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
          validate61.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate61.errors = vErrors;
      return errors === 0;
    }
    validate61.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.activation === void 0 && (missing0 = "activation") || data.child_scope_count === void 0 && (missing0 = "child_scope_count")) {
            validate60.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "activation" || key0 === "child_scope_count")) {
                validate60.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.activation !== void 0) {
                const _errs2 = errors;
                if (!validate61(data.activation, { instancePath: instancePath + "/activation", parentData: data, parentDataProperty: "activation", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate61.errors : vErrors.concat(validate61.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.child_scope_count !== void 0) {
                  let data1 = data.child_scope_count;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate60.errors = [{ instancePath: instancePath + "/child_scope_count", schemaPath: "#/properties/child_scope_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 1e5 || isNaN(data1)) {
                        validate60.errors = [{ instancePath: instancePath + "/child_scope_count", schemaPath: "#/properties/child_scope_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e5 }, message: "must be <= 100000" }];
                        return false;
                      } else {
                        if (data1 < 0 || isNaN(data1)) {
                          validate60.errors = [{ instancePath: instancePath + "/child_scope_count", schemaPath: "#/properties/child_scope_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                          return false;
                        }
                      }
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
          validate60.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate60.errors = vErrors;
      return errors === 0;
    }
    validate60.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate55(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate55.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.cut === void 0 && (missing0 = "cut") || data.graph_scope === void 0 && (missing0 = "graph_scope") || data.query === void 0 && (missing0 = "query") || data.node_count === void 0 && (missing0 = "node_count") || data.edge_count === void 0 && (missing0 = "edge_count") || data.nodes === void 0 && (missing0 = "nodes") || data.edges === void 0 && (missing0 = "edges") || data.next_cursor === void 0 && (missing0 = "next_cursor")) {
            validate55.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func115.call(schema75.properties, key0)) {
                validate55.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.cut !== void 0) {
                const _errs2 = errors;
                if (!validate56(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate56.errors : vErrors.concat(validate56.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.edge_count !== void 0) {
                  let data1 = data.edge_count;
                  const _errs3 = errors;
                  if (!(typeof data1 == "number" && (!(data1 % 1) && !isNaN(data1)) && isFinite(data1))) {
                    validate55.errors = [{ instancePath: instancePath + "/edge_count", schemaPath: "#/properties/edge_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs3) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 1024 || isNaN(data1)) {
                        validate55.errors = [{ instancePath: instancePath + "/edge_count", schemaPath: "#/properties/edge_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1024 }, message: "must be <= 1024" }];
                        return false;
                      } else {
                        if (data1 < 0 || isNaN(data1)) {
                          validate55.errors = [{ instancePath: instancePath + "/edge_count", schemaPath: "#/properties/edge_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                  if (data.edges !== void 0) {
                    let data2 = data.edges;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (Array.isArray(data2)) {
                        if (data2.length > 1024) {
                          validate55.errors = [{ instancePath: instancePath + "/edges", schemaPath: "#/properties/edges/maxItems", keyword: "maxItems", params: { limit: 1024 }, message: "must NOT have more than 1024 items" }];
                          return false;
                        } else {
                          var valid1 = true;
                          const len0 = data2.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            let data3 = data2[i0];
                            const _errs7 = errors;
                            const _errs8 = errors;
                            if (errors === _errs8) {
                              if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                                let missing1;
                                if (data3.source === void 0 && (missing1 = "source") || data3.target === void 0 && (missing1 = "target") || data3.route === void 0 && (missing1 = "route")) {
                                  validate55.errors = [{ instancePath: instancePath + "/edges/" + i0, schemaPath: "#/$defs/GraphControlLink/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                  return false;
                                } else {
                                  const _errs10 = errors;
                                  for (const key1 in data3) {
                                    if (!(key1 === "route" || key1 === "source" || key1 === "target")) {
                                      validate55.errors = [{ instancePath: instancePath + "/edges/" + i0, schemaPath: "#/$defs/GraphControlLink/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                      return false;
                                      break;
                                    }
                                  }
                                  if (_errs10 === errors) {
                                    if (data3.route !== void 0) {
                                      let data4 = data3.route;
                                      const _errs11 = errors;
                                      if (typeof data4 !== "string") {
                                        validate55.errors = [{ instancePath: instancePath + "/edges/" + i0 + "/route", schemaPath: "#/$defs/GraphControlLink/properties/route/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                        return false;
                                      }
                                      if (!(data4 === "next" || data4 === "true" || data4 === "false")) {
                                        validate55.errors = [{ instancePath: instancePath + "/edges/" + i0 + "/route", schemaPath: "#/$defs/GraphControlLink/properties/route/enum", keyword: "enum", params: { allowedValues: schema78.properties.route.enum }, message: "must be equal to one of the allowed values" }];
                                        return false;
                                      }
                                      var valid3 = _errs11 === errors;
                                    } else {
                                      var valid3 = true;
                                    }
                                    if (valid3) {
                                      if (data3.source !== void 0) {
                                        let data5 = data3.source;
                                        const _errs13 = errors;
                                        if (errors === _errs13) {
                                          if (typeof data5 === "string") {
                                            if (!pattern4.test(data5)) {
                                              validate55.errors = [{ instancePath: instancePath + "/edges/" + i0 + "/source", schemaPath: "#/$defs/GraphControlLink/properties/source/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                              return false;
                                            }
                                          } else {
                                            validate55.errors = [{ instancePath: instancePath + "/edges/" + i0 + "/source", schemaPath: "#/$defs/GraphControlLink/properties/source/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                            return false;
                                          }
                                        }
                                        var valid3 = _errs13 === errors;
                                      } else {
                                        var valid3 = true;
                                      }
                                      if (valid3) {
                                        if (data3.target !== void 0) {
                                          let data6 = data3.target;
                                          const _errs15 = errors;
                                          if (errors === _errs15) {
                                            if (typeof data6 === "string") {
                                              if (!pattern4.test(data6)) {
                                                validate55.errors = [{ instancePath: instancePath + "/edges/" + i0 + "/target", schemaPath: "#/$defs/GraphControlLink/properties/target/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                                return false;
                                              }
                                            } else {
                                              validate55.errors = [{ instancePath: instancePath + "/edges/" + i0 + "/target", schemaPath: "#/$defs/GraphControlLink/properties/target/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                              return false;
                                            }
                                          }
                                          var valid3 = _errs15 === errors;
                                        } else {
                                          var valid3 = true;
                                        }
                                      }
                                    }
                                  }
                                }
                              } else {
                                validate55.errors = [{ instancePath: instancePath + "/edges/" + i0, schemaPath: "#/$defs/GraphControlLink/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                return false;
                              }
                            }
                            var valid1 = _errs7 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate55.errors = [{ instancePath: instancePath + "/edges", schemaPath: "#/properties/edges/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                        return false;
                      }
                    }
                    var valid0 = _errs5 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.graph_scope !== void 0) {
                      const _errs17 = errors;
                      if (!validate58(data.graph_scope, { instancePath: instancePath + "/graph_scope", parentData: data, parentDataProperty: "graph_scope", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate58.errors : vErrors.concat(validate58.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs17 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.next_cursor !== void 0) {
                        let data8 = data.next_cursor;
                        const _errs18 = errors;
                        const _errs19 = errors;
                        let valid4 = false;
                        const _errs20 = errors;
                        if (errors === _errs20) {
                          if (typeof data8 === "string") {
                            if (func1(data8) > 4096) {
                              const err0 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/0/maxLength", keyword: "maxLength", params: { limit: 4096 }, message: "must NOT have more than 4096 characters" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            } else {
                              if (func1(data8) < 1) {
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
                        var _valid0 = _errs20 === errors;
                        valid4 = valid4 || _valid0;
                        const _errs22 = errors;
                        if (data8 !== null) {
                          const err3 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                          if (vErrors === null) {
                            vErrors = [err3];
                          } else {
                            vErrors.push(err3);
                          }
                          errors++;
                        }
                        var _valid0 = _errs22 === errors;
                        valid4 = valid4 || _valid0;
                        if (!valid4) {
                          const err4 = { instancePath: instancePath + "/next_cursor", schemaPath: "#/properties/next_cursor/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                          if (vErrors === null) {
                            vErrors = [err4];
                          } else {
                            vErrors.push(err4);
                          }
                          errors++;
                          validate55.errors = vErrors;
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
                        if (data.node_count !== void 0) {
                          let data9 = data.node_count;
                          const _errs24 = errors;
                          if (!(typeof data9 == "number" && (!(data9 % 1) && !isNaN(data9)) && isFinite(data9))) {
                            validate55.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs24) {
                            if (typeof data9 == "number" && isFinite(data9)) {
                              if (data9 > 256 || isNaN(data9)) {
                                validate55.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/maximum", keyword: "maximum", params: { comparison: "<=", limit: 256 }, message: "must be <= 256" }];
                                return false;
                              } else {
                                if (data9 < 0 || isNaN(data9)) {
                                  validate55.errors = [{ instancePath: instancePath + "/node_count", schemaPath: "#/properties/node_count/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                          if (data.nodes !== void 0) {
                            let data10 = data.nodes;
                            const _errs26 = errors;
                            if (errors === _errs26) {
                              if (Array.isArray(data10)) {
                                if (data10.length > 100) {
                                  validate55.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/maxItems", keyword: "maxItems", params: { limit: 100 }, message: "must NOT have more than 100 items" }];
                                  return false;
                                } else {
                                  var valid5 = true;
                                  const len1 = data10.length;
                                  for (let i1 = 0; i1 < len1; i1++) {
                                    const _errs28 = errors;
                                    if (!validate60(data10[i1], { instancePath: instancePath + "/nodes/" + i1, parentData: data10, parentDataProperty: i1, rootData, dynamicAnchors })) {
                                      vErrors = vErrors === null ? validate60.errors : vErrors.concat(validate60.errors);
                                      errors = vErrors.length;
                                    }
                                    var valid5 = _errs28 === errors;
                                    if (!valid5) {
                                      break;
                                    }
                                  }
                                }
                              } else {
                                validate55.errors = [{ instancePath: instancePath + "/nodes", schemaPath: "#/properties/nodes/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                                return false;
                              }
                            }
                            var valid0 = _errs26 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.query !== void 0) {
                              let data12 = data.query;
                              const _errs29 = errors;
                              const _errs30 = errors;
                              if (errors === _errs30) {
                                if (data12 && typeof data12 == "object" && !Array.isArray(data12)) {
                                  const _errs32 = errors;
                                  for (const key2 in data12) {
                                    if (!(key2 === "focus_activation_id" || key2 === "radius")) {
                                      validate55.errors = [{ instancePath: instancePath + "/query", schemaPath: "#/$defs/GraphTopologyQuery/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                      return false;
                                      break;
                                    }
                                  }
                                  if (_errs32 === errors) {
                                    if (data12.focus_activation_id !== void 0) {
                                      let data13 = data12.focus_activation_id;
                                      const _errs33 = errors;
                                      const _errs34 = errors;
                                      let valid8 = false;
                                      const _errs35 = errors;
                                      if (errors === _errs35) {
                                        if (typeof data13 === "string") {
                                          if (!pattern4.test(data13)) {
                                            const err5 = { instancePath: instancePath + "/query/focus_activation_id", schemaPath: "#/$defs/GraphTopologyQuery/properties/focus_activation_id/anyOf/0/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                            if (vErrors === null) {
                                              vErrors = [err5];
                                            } else {
                                              vErrors.push(err5);
                                            }
                                            errors++;
                                          }
                                        } else {
                                          const err6 = { instancePath: instancePath + "/query/focus_activation_id", schemaPath: "#/$defs/GraphTopologyQuery/properties/focus_activation_id/anyOf/0/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err6];
                                          } else {
                                            vErrors.push(err6);
                                          }
                                          errors++;
                                        }
                                      }
                                      var _valid1 = _errs35 === errors;
                                      valid8 = valid8 || _valid1;
                                      const _errs37 = errors;
                                      if (data13 !== null) {
                                        const err7 = { instancePath: instancePath + "/query/focus_activation_id", schemaPath: "#/$defs/GraphTopologyQuery/properties/focus_activation_id/anyOf/1/type", keyword: "type", params: { type: "null" }, message: "must be null" };
                                        if (vErrors === null) {
                                          vErrors = [err7];
                                        } else {
                                          vErrors.push(err7);
                                        }
                                        errors++;
                                      }
                                      var _valid1 = _errs37 === errors;
                                      valid8 = valid8 || _valid1;
                                      if (!valid8) {
                                        const err8 = { instancePath: instancePath + "/query/focus_activation_id", schemaPath: "#/$defs/GraphTopologyQuery/properties/focus_activation_id/anyOf", keyword: "anyOf", params: {}, message: "must match a schema in anyOf" };
                                        if (vErrors === null) {
                                          vErrors = [err8];
                                        } else {
                                          vErrors.push(err8);
                                        }
                                        errors++;
                                        validate55.errors = vErrors;
                                        return false;
                                      } else {
                                        errors = _errs34;
                                        if (vErrors !== null) {
                                          if (_errs34) {
                                            vErrors.length = _errs34;
                                          } else {
                                            vErrors = null;
                                          }
                                        }
                                      }
                                      var valid7 = _errs33 === errors;
                                    } else {
                                      var valid7 = true;
                                    }
                                    if (valid7) {
                                      if (data12.radius !== void 0) {
                                        let data14 = data12.radius;
                                        const _errs39 = errors;
                                        if (!(typeof data14 == "number" && (!(data14 % 1) && !isNaN(data14)) && isFinite(data14))) {
                                          validate55.errors = [{ instancePath: instancePath + "/query/radius", schemaPath: "#/$defs/GraphTopologyQuery/properties/radius/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                          return false;
                                        }
                                        if (errors === _errs39) {
                                          if (typeof data14 == "number" && isFinite(data14)) {
                                            if (data14 > 2 || isNaN(data14)) {
                                              validate55.errors = [{ instancePath: instancePath + "/query/radius", schemaPath: "#/$defs/GraphTopologyQuery/properties/radius/maximum", keyword: "maximum", params: { comparison: "<=", limit: 2 }, message: "must be <= 2" }];
                                              return false;
                                            } else {
                                              if (data14 < 0 || isNaN(data14)) {
                                                validate55.errors = [{ instancePath: instancePath + "/query/radius", schemaPath: "#/$defs/GraphTopologyQuery/properties/radius/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                return false;
                                              }
                                            }
                                          }
                                        }
                                        var valid7 = _errs39 === errors;
                                      } else {
                                        var valid7 = true;
                                      }
                                    }
                                  }
                                } else {
                                  validate55.errors = [{ instancePath: instancePath + "/query", schemaPath: "#/$defs/GraphTopologyQuery/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                                  return false;
                                }
                              }
                              var valid0 = _errs29 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.schema_version !== void 0) {
                                let data15 = data.schema_version;
                                const _errs41 = errors;
                                if (typeof data15 !== "string") {
                                  validate55.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("1" !== data15) {
                                  validate55.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid0 = _errs41 === errors;
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
          validate55.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate55.errors = vErrors;
      return errors === 0;
    }
    validate55.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.catalog = validate66;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.revision === void 0 && (missing0 = "revision") || data.frontier_revision === void 0 && (missing0 = "frontier_revision")) {
            validate67.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "frontier_revision" || key0 === "plan_sha256" || key0 === "revision" || key0 === "run_id" || key0 === "scope")) {
                validate67.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.frontier_revision !== void 0) {
                let data0 = data.frontier_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate67.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate67.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate67.errors = [{ instancePath: instancePath + "/frontier_revision", schemaPath: "#/properties/frontier_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                      if (!pattern4.test(data1)) {
                        validate67.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate67.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate67.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                      return false;
                    }
                    if (errors === _errs6) {
                      if (typeof data2 == "number" && isFinite(data2)) {
                        if (data2 > 9007199254740991 || isNaN(data2)) {
                          validate67.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                          return false;
                        } else {
                          if (data2 < 0 || isNaN(data2)) {
                            validate67.errors = [{ instancePath: instancePath + "/revision", schemaPath: "#/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                            validate67.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate67.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern5.test(data3)) {
                                validate67.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate67.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                              validate67.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                              return false;
                            } else {
                              const _errs13 = errors;
                              for (const key1 in data4) {
                                if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                  validate67.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                        validate67.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data5) < 1) {
                                          validate67.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data5)) {
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
                                          validate67.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data6) < 1) {
                                            validate67.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data6)) {
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
                                    var valid2 = _errs16 === errors;
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
          validate67.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate67.errors = vErrors;
      return errors === 0;
    }
    validate67.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    var schema91 = { "additionalProperties": false, "properties": { "filters": { "items": { "discriminator": { "mapping": { "digest": "#/$defs/DigestViewFilter", "integer": "#/$defs/RadiusViewFilter" }, "propertyName": "kind" }, "oneOf": [{ "$ref": "#/$defs/DigestViewFilter" }, { "$ref": "#/$defs/RadiusViewFilter" }] }, "maxItems": 3, "title": "Filters", "type": "array" }, "owner": { "const": "campaign-runtime", "default": "campaign-runtime", "title": "Owner", "type": "string" }, "required_capability": { "enum": ["runtime.authored-topology.v1", "runtime.successor-lineage.v1"], "title": "Required Capability", "type": "string" }, "result_bound": { "maximum": 256, "minimum": 1, "title": "Result Bound", "type": "integer" }, "result_schema": { "enum": ["graph-runtime.topology-page", "graph-runtime.successor-lineage"], "title": "Result Schema", "type": "string" }, "result_schema_version": { "const": "1", "default": "1", "title": "Result Schema Version", "type": "string" }, "view_id": { "enum": ["execution_topology", "successor_lineage"], "title": "View Id", "type": "string" }, "view_version": { "const": "1", "default": "1", "title": "View Version", "type": "string" } }, "required": ["view_id", "result_schema", "required_capability", "result_bound", "filters"], "title": "GraphViewDefinition", "type": "object" };
    var schema92 = { "additionalProperties": false, "properties": { "kind": { "const": "digest", "default": "digest", "title": "Kind", "type": "string" }, "name": { "enum": ["scope_key", "focus_activation_id"], "title": "Name", "type": "string" }, "required": { "title": "Required", "type": "boolean" } }, "required": ["name", "required"], "title": "DigestViewFilter", "type": "object" };
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
          if (data.view_id === void 0 && (missing0 = "view_id") || data.result_schema === void 0 && (missing0 = "result_schema") || data.required_capability === void 0 && (missing0 = "required_capability") || data.result_bound === void 0 && (missing0 = "result_bound") || data.filters === void 0 && (missing0 = "filters")) {
            validate69.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "filters" || key0 === "owner" || key0 === "required_capability" || key0 === "result_bound" || key0 === "result_schema" || key0 === "result_schema_version" || key0 === "view_id" || key0 === "view_version")) {
                validate69.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.filters !== void 0) {
                let data0 = data.filters;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 3) {
                      validate69.errors = [{ instancePath: instancePath + "/filters", schemaPath: "#/properties/filters/maxItems", keyword: "maxItems", params: { limit: 3 }, message: "must NOT have more than 3 items" }];
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
                        const _errs7 = errors;
                        if (errors === _errs7) {
                          if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                            let missing1;
                            if (data1.name === void 0 && (missing1 = "name") || data1.required === void 0 && (missing1 = "required")) {
                              const err0 = { instancePath: instancePath + "/filters/" + i0, schemaPath: "#/$defs/DigestViewFilter/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                              if (vErrors === null) {
                                vErrors = [err0];
                              } else {
                                vErrors.push(err0);
                              }
                              errors++;
                            } else {
                              const _errs9 = errors;
                              for (const key1 in data1) {
                                if (!(key1 === "kind" || key1 === "name" || key1 === "required")) {
                                  const err1 = { instancePath: instancePath + "/filters/" + i0, schemaPath: "#/$defs/DigestViewFilter/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                                    const err2 = { instancePath: instancePath + "/filters/" + i0 + "/kind", schemaPath: "#/$defs/DigestViewFilter/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err2];
                                    } else {
                                      vErrors.push(err2);
                                    }
                                    errors++;
                                  }
                                  if ("digest" !== data2) {
                                    const err3 = { instancePath: instancePath + "/filters/" + i0 + "/kind", schemaPath: "#/$defs/DigestViewFilter/properties/kind/const", keyword: "const", params: { allowedValue: "digest" }, message: "must be equal to constant" };
                                    if (vErrors === null) {
                                      vErrors = [err3];
                                    } else {
                                      vErrors.push(err3);
                                    }
                                    errors++;
                                  }
                                  var valid4 = _errs10 === errors;
                                } else {
                                  var valid4 = true;
                                }
                                if (valid4) {
                                  if (data1.name !== void 0) {
                                    let data3 = data1.name;
                                    const _errs12 = errors;
                                    if (typeof data3 !== "string") {
                                      const err4 = { instancePath: instancePath + "/filters/" + i0 + "/name", schemaPath: "#/$defs/DigestViewFilter/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                      if (vErrors === null) {
                                        vErrors = [err4];
                                      } else {
                                        vErrors.push(err4);
                                      }
                                      errors++;
                                    }
                                    if (!(data3 === "scope_key" || data3 === "focus_activation_id")) {
                                      const err5 = { instancePath: instancePath + "/filters/" + i0 + "/name", schemaPath: "#/$defs/DigestViewFilter/properties/name/enum", keyword: "enum", params: { allowedValues: schema92.properties.name.enum }, message: "must be equal to one of the allowed values" };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                    }
                                    var valid4 = _errs12 === errors;
                                  } else {
                                    var valid4 = true;
                                  }
                                  if (valid4) {
                                    if (data1.required !== void 0) {
                                      const _errs14 = errors;
                                      if (typeof data1.required !== "boolean") {
                                        const err6 = { instancePath: instancePath + "/filters/" + i0 + "/required", schemaPath: "#/$defs/DigestViewFilter/properties/required/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" };
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
                                  }
                                }
                              }
                            }
                          } else {
                            const err7 = { instancePath: instancePath + "/filters/" + i0, schemaPath: "#/$defs/DigestViewFilter/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err7];
                            } else {
                              vErrors.push(err7);
                            }
                            errors++;
                          }
                        }
                        var _valid0 = _errs6 === errors;
                        if (_valid0) {
                          valid2 = true;
                          passing0 = 0;
                          var props0 = true;
                        }
                        const _errs16 = errors;
                        const _errs17 = errors;
                        if (errors === _errs17) {
                          if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                            const _errs19 = errors;
                            for (const key2 in data1) {
                              if (!(key2 === "default" || key2 === "kind" || key2 === "maximum" || key2 === "minimum" || key2 === "name" || key2 === "required")) {
                                const err8 = { instancePath: instancePath + "/filters/" + i0, schemaPath: "#/$defs/RadiusViewFilter/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                                if (vErrors === null) {
                                  vErrors = [err8];
                                } else {
                                  vErrors.push(err8);
                                }
                                errors++;
                                break;
                              }
                            }
                            if (_errs19 === errors) {
                              if (data1.default !== void 0) {
                                let data5 = data1.default;
                                const _errs20 = errors;
                                if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                  const err9 = { instancePath: instancePath + "/filters/" + i0 + "/default", schemaPath: "#/$defs/RadiusViewFilter/properties/default/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                  if (vErrors === null) {
                                    vErrors = [err9];
                                  } else {
                                    vErrors.push(err9);
                                  }
                                  errors++;
                                }
                                if (1 !== data5) {
                                  const err10 = { instancePath: instancePath + "/filters/" + i0 + "/default", schemaPath: "#/$defs/RadiusViewFilter/properties/default/const", keyword: "const", params: { allowedValue: 1 }, message: "must be equal to constant" };
                                  if (vErrors === null) {
                                    vErrors = [err10];
                                  } else {
                                    vErrors.push(err10);
                                  }
                                  errors++;
                                }
                                var valid6 = _errs20 === errors;
                              } else {
                                var valid6 = true;
                              }
                              if (valid6) {
                                if (data1.kind !== void 0) {
                                  let data6 = data1.kind;
                                  const _errs22 = errors;
                                  if (typeof data6 !== "string") {
                                    const err11 = { instancePath: instancePath + "/filters/" + i0 + "/kind", schemaPath: "#/$defs/RadiusViewFilter/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err11];
                                    } else {
                                      vErrors.push(err11);
                                    }
                                    errors++;
                                  }
                                  if ("integer" !== data6) {
                                    const err12 = { instancePath: instancePath + "/filters/" + i0 + "/kind", schemaPath: "#/$defs/RadiusViewFilter/properties/kind/const", keyword: "const", params: { allowedValue: "integer" }, message: "must be equal to constant" };
                                    if (vErrors === null) {
                                      vErrors = [err12];
                                    } else {
                                      vErrors.push(err12);
                                    }
                                    errors++;
                                  }
                                  var valid6 = _errs22 === errors;
                                } else {
                                  var valid6 = true;
                                }
                                if (valid6) {
                                  if (data1.maximum !== void 0) {
                                    let data7 = data1.maximum;
                                    const _errs24 = errors;
                                    if (!(typeof data7 == "number" && (!(data7 % 1) && !isNaN(data7)) && isFinite(data7))) {
                                      const err13 = { instancePath: instancePath + "/filters/" + i0 + "/maximum", schemaPath: "#/$defs/RadiusViewFilter/properties/maximum/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                      if (vErrors === null) {
                                        vErrors = [err13];
                                      } else {
                                        vErrors.push(err13);
                                      }
                                      errors++;
                                    }
                                    if (2 !== data7) {
                                      const err14 = { instancePath: instancePath + "/filters/" + i0 + "/maximum", schemaPath: "#/$defs/RadiusViewFilter/properties/maximum/const", keyword: "const", params: { allowedValue: 2 }, message: "must be equal to constant" };
                                      if (vErrors === null) {
                                        vErrors = [err14];
                                      } else {
                                        vErrors.push(err14);
                                      }
                                      errors++;
                                    }
                                    var valid6 = _errs24 === errors;
                                  } else {
                                    var valid6 = true;
                                  }
                                  if (valid6) {
                                    if (data1.minimum !== void 0) {
                                      let data8 = data1.minimum;
                                      const _errs26 = errors;
                                      if (!(typeof data8 == "number" && (!(data8 % 1) && !isNaN(data8)) && isFinite(data8))) {
                                        const err15 = { instancePath: instancePath + "/filters/" + i0 + "/minimum", schemaPath: "#/$defs/RadiusViewFilter/properties/minimum/type", keyword: "type", params: { type: "integer" }, message: "must be integer" };
                                        if (vErrors === null) {
                                          vErrors = [err15];
                                        } else {
                                          vErrors.push(err15);
                                        }
                                        errors++;
                                      }
                                      if (0 !== data8) {
                                        const err16 = { instancePath: instancePath + "/filters/" + i0 + "/minimum", schemaPath: "#/$defs/RadiusViewFilter/properties/minimum/const", keyword: "const", params: { allowedValue: 0 }, message: "must be equal to constant" };
                                        if (vErrors === null) {
                                          vErrors = [err16];
                                        } else {
                                          vErrors.push(err16);
                                        }
                                        errors++;
                                      }
                                      var valid6 = _errs26 === errors;
                                    } else {
                                      var valid6 = true;
                                    }
                                    if (valid6) {
                                      if (data1.name !== void 0) {
                                        let data9 = data1.name;
                                        const _errs28 = errors;
                                        if (typeof data9 !== "string") {
                                          const err17 = { instancePath: instancePath + "/filters/" + i0 + "/name", schemaPath: "#/$defs/RadiusViewFilter/properties/name/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                          if (vErrors === null) {
                                            vErrors = [err17];
                                          } else {
                                            vErrors.push(err17);
                                          }
                                          errors++;
                                        }
                                        if ("radius" !== data9) {
                                          const err18 = { instancePath: instancePath + "/filters/" + i0 + "/name", schemaPath: "#/$defs/RadiusViewFilter/properties/name/const", keyword: "const", params: { allowedValue: "radius" }, message: "must be equal to constant" };
                                          if (vErrors === null) {
                                            vErrors = [err18];
                                          } else {
                                            vErrors.push(err18);
                                          }
                                          errors++;
                                        }
                                        var valid6 = _errs28 === errors;
                                      } else {
                                        var valid6 = true;
                                      }
                                      if (valid6) {
                                        if (data1.required !== void 0) {
                                          let data10 = data1.required;
                                          const _errs30 = errors;
                                          if (typeof data10 !== "boolean") {
                                            const err19 = { instancePath: instancePath + "/filters/" + i0 + "/required", schemaPath: "#/$defs/RadiusViewFilter/properties/required/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" };
                                            if (vErrors === null) {
                                              vErrors = [err19];
                                            } else {
                                              vErrors.push(err19);
                                            }
                                            errors++;
                                          }
                                          if (false !== data10) {
                                            const err20 = { instancePath: instancePath + "/filters/" + i0 + "/required", schemaPath: "#/$defs/RadiusViewFilter/properties/required/const", keyword: "const", params: { allowedValue: false }, message: "must be equal to constant" };
                                            if (vErrors === null) {
                                              vErrors = [err20];
                                            } else {
                                              vErrors.push(err20);
                                            }
                                            errors++;
                                          }
                                          var valid6 = _errs30 === errors;
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
                            const err21 = { instancePath: instancePath + "/filters/" + i0, schemaPath: "#/$defs/RadiusViewFilter/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                            if (vErrors === null) {
                              vErrors = [err21];
                            } else {
                              vErrors.push(err21);
                            }
                            errors++;
                          }
                        }
                        var _valid0 = _errs16 === errors;
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
                          const err22 = { instancePath: instancePath + "/filters/" + i0, schemaPath: "#/properties/filters/items/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                          if (vErrors === null) {
                            vErrors = [err22];
                          } else {
                            vErrors.push(err22);
                          }
                          errors++;
                          validate69.errors = vErrors;
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
                    validate69.errors = [{ instancePath: instancePath + "/filters", schemaPath: "#/properties/filters/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.owner !== void 0) {
                  let data11 = data.owner;
                  const _errs33 = errors;
                  if (typeof data11 !== "string") {
                    validate69.errors = [{ instancePath: instancePath + "/owner", schemaPath: "#/properties/owner/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("campaign-runtime" !== data11) {
                    validate69.errors = [{ instancePath: instancePath + "/owner", schemaPath: "#/properties/owner/const", keyword: "const", params: { allowedValue: "campaign-runtime" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs33 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.required_capability !== void 0) {
                    let data12 = data.required_capability;
                    const _errs35 = errors;
                    if (typeof data12 !== "string") {
                      validate69.errors = [{ instancePath: instancePath + "/required_capability", schemaPath: "#/properties/required_capability/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if (!(data12 === "runtime.authored-topology.v1" || data12 === "runtime.successor-lineage.v1")) {
                      validate69.errors = [{ instancePath: instancePath + "/required_capability", schemaPath: "#/properties/required_capability/enum", keyword: "enum", params: { allowedValues: schema91.properties.required_capability.enum }, message: "must be equal to one of the allowed values" }];
                      return false;
                    }
                    var valid0 = _errs35 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.result_bound !== void 0) {
                      let data13 = data.result_bound;
                      const _errs37 = errors;
                      if (!(typeof data13 == "number" && (!(data13 % 1) && !isNaN(data13)) && isFinite(data13))) {
                        validate69.errors = [{ instancePath: instancePath + "/result_bound", schemaPath: "#/properties/result_bound/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                        return false;
                      }
                      if (errors === _errs37) {
                        if (typeof data13 == "number" && isFinite(data13)) {
                          if (data13 > 256 || isNaN(data13)) {
                            validate69.errors = [{ instancePath: instancePath + "/result_bound", schemaPath: "#/properties/result_bound/maximum", keyword: "maximum", params: { comparison: "<=", limit: 256 }, message: "must be <= 256" }];
                            return false;
                          } else {
                            if (data13 < 1 || isNaN(data13)) {
                              validate69.errors = [{ instancePath: instancePath + "/result_bound", schemaPath: "#/properties/result_bound/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
                              return false;
                            }
                          }
                        }
                      }
                      var valid0 = _errs37 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.result_schema !== void 0) {
                        let data14 = data.result_schema;
                        const _errs39 = errors;
                        if (typeof data14 !== "string") {
                          validate69.errors = [{ instancePath: instancePath + "/result_schema", schemaPath: "#/properties/result_schema/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if (!(data14 === "graph-runtime.topology-page" || data14 === "graph-runtime.successor-lineage")) {
                          validate69.errors = [{ instancePath: instancePath + "/result_schema", schemaPath: "#/properties/result_schema/enum", keyword: "enum", params: { allowedValues: schema91.properties.result_schema.enum }, message: "must be equal to one of the allowed values" }];
                          return false;
                        }
                        var valid0 = _errs39 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.result_schema_version !== void 0) {
                          let data15 = data.result_schema_version;
                          const _errs41 = errors;
                          if (typeof data15 !== "string") {
                            validate69.errors = [{ instancePath: instancePath + "/result_schema_version", schemaPath: "#/properties/result_schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                            return false;
                          }
                          if ("1" !== data15) {
                            validate69.errors = [{ instancePath: instancePath + "/result_schema_version", schemaPath: "#/properties/result_schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                            return false;
                          }
                          var valid0 = _errs41 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.view_id !== void 0) {
                            let data16 = data.view_id;
                            const _errs43 = errors;
                            if (typeof data16 !== "string") {
                              validate69.errors = [{ instancePath: instancePath + "/view_id", schemaPath: "#/properties/view_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if (!(data16 === "execution_topology" || data16 === "successor_lineage")) {
                              validate69.errors = [{ instancePath: instancePath + "/view_id", schemaPath: "#/properties/view_id/enum", keyword: "enum", params: { allowedValues: schema91.properties.view_id.enum }, message: "must be equal to one of the allowed values" }];
                              return false;
                            }
                            var valid0 = _errs43 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.view_version !== void 0) {
                              let data17 = data.view_version;
                              const _errs45 = errors;
                              if (typeof data17 !== "string") {
                                validate69.errors = [{ instancePath: instancePath + "/view_version", schemaPath: "#/properties/view_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("1" !== data17) {
                                validate69.errors = [{ instancePath: instancePath + "/view_version", schemaPath: "#/properties/view_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
    function validate66(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate66.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.cut === void 0 && (missing0 = "cut") || data.views === void 0 && (missing0 = "views")) {
            validate66.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "cut" || key0 === "schema_version" || key0 === "views")) {
                validate66.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.cut !== void 0) {
                const _errs2 = errors;
                if (!validate67(data.cut, { instancePath: instancePath + "/cut", parentData: data, parentDataProperty: "cut", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate67.errors : vErrors.concat(validate67.errors);
                  errors = vErrors.length;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.schema_version !== void 0) {
                  let data1 = data.schema_version;
                  const _errs3 = errors;
                  if (typeof data1 !== "string") {
                    validate66.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                  if ("1" !== data1) {
                    validate66.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                    return false;
                  }
                  var valid0 = _errs3 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.views !== void 0) {
                    let data2 = data.views;
                    const _errs5 = errors;
                    if (errors === _errs5) {
                      if (Array.isArray(data2)) {
                        if (data2.length > 2) {
                          validate66.errors = [{ instancePath: instancePath + "/views", schemaPath: "#/properties/views/maxItems", keyword: "maxItems", params: { limit: 2 }, message: "must NOT have more than 2 items" }];
                          return false;
                        } else {
                          var valid1 = true;
                          const len0 = data2.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs7 = errors;
                            if (!validate69(data2[i0], { instancePath: instancePath + "/views/" + i0, parentData: data2, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate69.errors : vErrors.concat(validate69.errors);
                              errors = vErrors.length;
                            }
                            var valid1 = _errs7 === errors;
                            if (!valid1) {
                              break;
                            }
                          }
                        }
                      } else {
                        validate66.errors = [{ instancePath: instancePath + "/views", schemaPath: "#/properties/views/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
          validate66.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate66.errors = vErrors;
      return errors === 0;
    }
    validate66.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.lineage = validate71;
    function validate72(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      let vErrors = null;
      let errors = 0;
      const evaluated0 = validate72.evaluated;
      if (evaluated0.dynamicProps) {
        evaluated0.props = void 0;
      }
      if (evaluated0.dynamicItems) {
        evaluated0.items = void 0;
      }
      if (errors === 0) {
        if (data && typeof data == "object" && !Array.isArray(data)) {
          let missing0;
          if (data.target_port === void 0 && (missing0 = "target_port") || data.source === void 0 && (missing0 = "source") || data.expected_value_sha256 === void 0 && (missing0 = "expected_value_sha256")) {
            validate72.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "expected_value_sha256" || key0 === "source" || key0 === "target_port")) {
                validate72.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.expected_value_sha256 !== void 0) {
                let data0 = data.expected_value_sha256;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (typeof data0 === "string") {
                    if (!pattern4.test(data0)) {
                      validate72.errors = [{ instancePath: instancePath + "/expected_value_sha256", schemaPath: "#/properties/expected_value_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                      return false;
                    }
                  } else {
                    validate72.errors = [{ instancePath: instancePath + "/expected_value_sha256", schemaPath: "#/properties/expected_value_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.source !== void 0) {
                  let data1 = data.source;
                  const _errs4 = errors;
                  const _errs5 = errors;
                  let valid1 = false;
                  let passing0 = null;
                  const _errs6 = errors;
                  const _errs7 = errors;
                  if (errors === _errs7) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing1;
                      if (data1.port === void 0 && (missing1 = "port")) {
                        const err0 = { instancePath: instancePath + "/source", schemaPath: "#/$defs/RunOutputSource/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" };
                        if (vErrors === null) {
                          vErrors = [err0];
                        } else {
                          vErrors.push(err0);
                        }
                        errors++;
                      } else {
                        const _errs9 = errors;
                        for (const key1 in data1) {
                          if (!(key1 === "kind" || key1 === "port")) {
                            const err1 = { instancePath: instancePath + "/source", schemaPath: "#/$defs/RunOutputSource/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" };
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
                              const err2 = { instancePath: instancePath + "/source/kind", schemaPath: "#/$defs/RunOutputSource/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                              if (vErrors === null) {
                                vErrors = [err2];
                              } else {
                                vErrors.push(err2);
                              }
                              errors++;
                            }
                            if ("run_output" !== data2) {
                              const err3 = { instancePath: instancePath + "/source/kind", schemaPath: "#/$defs/RunOutputSource/properties/kind/const", keyword: "const", params: { allowedValue: "run_output" }, message: "must be equal to constant" };
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
                            if (data1.port !== void 0) {
                              let data3 = data1.port;
                              const _errs12 = errors;
                              if (errors === _errs12) {
                                if (typeof data3 === "string") {
                                  if (func1(data3) > 128) {
                                    const err4 = { instancePath: instancePath + "/source/port", schemaPath: "#/$defs/RunOutputSource/properties/port/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                    if (vErrors === null) {
                                      vErrors = [err4];
                                    } else {
                                      vErrors.push(err4);
                                    }
                                    errors++;
                                  } else {
                                    if (func1(data3) < 1) {
                                      const err5 = { instancePath: instancePath + "/source/port", schemaPath: "#/$defs/RunOutputSource/properties/port/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err5];
                                      } else {
                                        vErrors.push(err5);
                                      }
                                      errors++;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        const err6 = { instancePath: instancePath + "/source/port", schemaPath: "#/$defs/RunOutputSource/properties/port/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
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
                                  const err7 = { instancePath: instancePath + "/source/port", schemaPath: "#/$defs/RunOutputSource/properties/port/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                  if (vErrors === null) {
                                    vErrors = [err7];
                                  } else {
                                    vErrors.push(err7);
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
                      const err8 = { instancePath: instancePath + "/source", schemaPath: "#/$defs/RunOutputSource/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err8];
                      } else {
                        vErrors.push(err8);
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
                  const _errs14 = errors;
                  const _errs15 = errors;
                  if (errors === _errs15) {
                    if (data1 && typeof data1 == "object" && !Array.isArray(data1)) {
                      let missing2;
                      if (data1.activation_id === void 0 && (missing2 = "activation_id") || data1.port === void 0 && (missing2 = "port")) {
                        const err9 = { instancePath: instancePath + "/source", schemaPath: "#/$defs/NodeOutputSource/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" };
                        if (vErrors === null) {
                          vErrors = [err9];
                        } else {
                          vErrors.push(err9);
                        }
                        errors++;
                      } else {
                        const _errs17 = errors;
                        for (const key2 in data1) {
                          if (!(key2 === "activation_id" || key2 === "kind" || key2 === "port")) {
                            const err10 = { instancePath: instancePath + "/source", schemaPath: "#/$defs/NodeOutputSource/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" };
                            if (vErrors === null) {
                              vErrors = [err10];
                            } else {
                              vErrors.push(err10);
                            }
                            errors++;
                            break;
                          }
                        }
                        if (_errs17 === errors) {
                          if (data1.activation_id !== void 0) {
                            let data4 = data1.activation_id;
                            const _errs18 = errors;
                            if (errors === _errs18) {
                              if (typeof data4 === "string") {
                                if (!pattern4.test(data4)) {
                                  const err11 = { instancePath: instancePath + "/source/activation_id", schemaPath: "#/$defs/NodeOutputSource/properties/activation_id/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' };
                                  if (vErrors === null) {
                                    vErrors = [err11];
                                  } else {
                                    vErrors.push(err11);
                                  }
                                  errors++;
                                }
                              } else {
                                const err12 = { instancePath: instancePath + "/source/activation_id", schemaPath: "#/$defs/NodeOutputSource/properties/activation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err12];
                                } else {
                                  vErrors.push(err12);
                                }
                                errors++;
                              }
                            }
                            var valid5 = _errs18 === errors;
                          } else {
                            var valid5 = true;
                          }
                          if (valid5) {
                            if (data1.kind !== void 0) {
                              let data5 = data1.kind;
                              const _errs20 = errors;
                              if (typeof data5 !== "string") {
                                const err13 = { instancePath: instancePath + "/source/kind", schemaPath: "#/$defs/NodeOutputSource/properties/kind/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                if (vErrors === null) {
                                  vErrors = [err13];
                                } else {
                                  vErrors.push(err13);
                                }
                                errors++;
                              }
                              if ("node_output" !== data5) {
                                const err14 = { instancePath: instancePath + "/source/kind", schemaPath: "#/$defs/NodeOutputSource/properties/kind/const", keyword: "const", params: { allowedValue: "node_output" }, message: "must be equal to constant" };
                                if (vErrors === null) {
                                  vErrors = [err14];
                                } else {
                                  vErrors.push(err14);
                                }
                                errors++;
                              }
                              var valid5 = _errs20 === errors;
                            } else {
                              var valid5 = true;
                            }
                            if (valid5) {
                              if (data1.port !== void 0) {
                                let data6 = data1.port;
                                const _errs22 = errors;
                                if (errors === _errs22) {
                                  if (typeof data6 === "string") {
                                    if (func1(data6) > 128) {
                                      const err15 = { instancePath: instancePath + "/source/port", schemaPath: "#/$defs/NodeOutputSource/properties/port/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" };
                                      if (vErrors === null) {
                                        vErrors = [err15];
                                      } else {
                                        vErrors.push(err15);
                                      }
                                      errors++;
                                    } else {
                                      if (func1(data6) < 1) {
                                        const err16 = { instancePath: instancePath + "/source/port", schemaPath: "#/$defs/NodeOutputSource/properties/port/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" };
                                        if (vErrors === null) {
                                          vErrors = [err16];
                                        } else {
                                          vErrors.push(err16);
                                        }
                                        errors++;
                                      } else {
                                        if (!pattern5.test(data6)) {
                                          const err17 = { instancePath: instancePath + "/source/port", schemaPath: "#/$defs/NodeOutputSource/properties/port/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' };
                                          if (vErrors === null) {
                                            vErrors = [err17];
                                          } else {
                                            vErrors.push(err17);
                                          }
                                          errors++;
                                        }
                                      }
                                    }
                                  } else {
                                    const err18 = { instancePath: instancePath + "/source/port", schemaPath: "#/$defs/NodeOutputSource/properties/port/type", keyword: "type", params: { type: "string" }, message: "must be string" };
                                    if (vErrors === null) {
                                      vErrors = [err18];
                                    } else {
                                      vErrors.push(err18);
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
                      const err19 = { instancePath: instancePath + "/source", schemaPath: "#/$defs/NodeOutputSource/type", keyword: "type", params: { type: "object" }, message: "must be object" };
                      if (vErrors === null) {
                        vErrors = [err19];
                      } else {
                        vErrors.push(err19);
                      }
                      errors++;
                    }
                  }
                  var _valid0 = _errs14 === errors;
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
                    const err20 = { instancePath: instancePath + "/source", schemaPath: "#/properties/source/oneOf", keyword: "oneOf", params: { passingSchemas: passing0 }, message: "must match exactly one schema in oneOf" };
                    if (vErrors === null) {
                      vErrors = [err20];
                    } else {
                      vErrors.push(err20);
                    }
                    errors++;
                    validate72.errors = vErrors;
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
                  if (data.target_port !== void 0) {
                    let data7 = data.target_port;
                    const _errs25 = errors;
                    if (errors === _errs25) {
                      if (typeof data7 === "string") {
                        if (func1(data7) > 128) {
                          validate72.errors = [{ instancePath: instancePath + "/target_port", schemaPath: "#/properties/target_port/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func1(data7) < 1) {
                            validate72.errors = [{ instancePath: instancePath + "/target_port", schemaPath: "#/properties/target_port/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern5.test(data7)) {
                              validate72.errors = [{ instancePath: instancePath + "/target_port", schemaPath: "#/properties/target_port/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate72.errors = [{ instancePath: instancePath + "/target_port", schemaPath: "#/properties/target_port/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs25 === errors;
                  } else {
                    var valid0 = true;
                  }
                }
              }
            }
          }
        } else {
          validate72.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate72.errors = vErrors;
      return errors === 0;
    }
    validate72.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    function validate71(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.plan_sha256 === void 0 && (missing0 = "plan_sha256") || data.predecessor === void 0 && (missing0 = "predecessor") || data.carried === void 0 && (missing0 = "carried") || data.transfer_sha256 === void 0 && (missing0 = "transfer_sha256")) {
            validate71.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "carried" || key0 === "plan_sha256" || key0 === "predecessor" || key0 === "run_id" || key0 === "schema_version" || key0 === "scope" || key0 === "transfer_sha256")) {
                validate71.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.carried !== void 0) {
                let data0 = data.carried;
                const _errs2 = errors;
                if (errors === _errs2) {
                  if (Array.isArray(data0)) {
                    if (data0.length > 64) {
                      validate71.errors = [{ instancePath: instancePath + "/carried", schemaPath: "#/properties/carried/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                      return false;
                    } else {
                      var valid1 = true;
                      const len0 = data0.length;
                      for (let i0 = 0; i0 < len0; i0++) {
                        const _errs4 = errors;
                        if (!validate72(data0[i0], { instancePath: instancePath + "/carried/" + i0, parentData: data0, parentDataProperty: i0, rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate72.errors : vErrors.concat(validate72.errors);
                          errors = vErrors.length;
                        }
                        var valid1 = _errs4 === errors;
                        if (!valid1) {
                          break;
                        }
                      }
                    }
                  } else {
                    validate71.errors = [{ instancePath: instancePath + "/carried", schemaPath: "#/properties/carried/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                    return false;
                  }
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.plan_sha256 !== void 0) {
                  let data2 = data.plan_sha256;
                  const _errs5 = errors;
                  if (errors === _errs5) {
                    if (typeof data2 === "string") {
                      if (!pattern4.test(data2)) {
                        validate71.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                        return false;
                      }
                    } else {
                      validate71.errors = [{ instancePath: instancePath + "/plan_sha256", schemaPath: "#/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                  }
                  var valid0 = _errs5 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.predecessor !== void 0) {
                    let data3 = data.predecessor;
                    const _errs7 = errors;
                    const _errs8 = errors;
                    if (errors === _errs8) {
                      if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                        let missing1;
                        if (data3.run_id === void 0 && (missing1 = "run_id") || data3.plan_sha256 === void 0 && (missing1 = "plan_sha256") || data3.revision === void 0 && (missing1 = "revision")) {
                          validate71.errors = [{ instancePath: instancePath + "/predecessor", schemaPath: "#/$defs/PredecessorCut/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs10 = errors;
                          for (const key1 in data3) {
                            if (!(key1 === "plan_sha256" || key1 === "revision" || key1 === "run_id")) {
                              validate71.errors = [{ instancePath: instancePath + "/predecessor", schemaPath: "#/$defs/PredecessorCut/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs10 === errors) {
                            if (data3.plan_sha256 !== void 0) {
                              let data4 = data3.plan_sha256;
                              const _errs11 = errors;
                              if (errors === _errs11) {
                                if (typeof data4 === "string") {
                                  if (!pattern4.test(data4)) {
                                    validate71.errors = [{ instancePath: instancePath + "/predecessor/plan_sha256", schemaPath: "#/$defs/PredecessorCut/properties/plan_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                    return false;
                                  }
                                } else {
                                  validate71.errors = [{ instancePath: instancePath + "/predecessor/plan_sha256", schemaPath: "#/$defs/PredecessorCut/properties/plan_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                              }
                              var valid3 = _errs11 === errors;
                            } else {
                              var valid3 = true;
                            }
                            if (valid3) {
                              if (data3.revision !== void 0) {
                                let data5 = data3.revision;
                                const _errs13 = errors;
                                if (!(typeof data5 == "number" && (!(data5 % 1) && !isNaN(data5)) && isFinite(data5))) {
                                  validate71.errors = [{ instancePath: instancePath + "/predecessor/revision", schemaPath: "#/$defs/PredecessorCut/properties/revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                                  return false;
                                }
                                if (errors === _errs13) {
                                  if (typeof data5 == "number" && isFinite(data5)) {
                                    if (data5 > 9007199254740991 || isNaN(data5)) {
                                      validate71.errors = [{ instancePath: instancePath + "/predecessor/revision", schemaPath: "#/$defs/PredecessorCut/properties/revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                      return false;
                                    } else {
                                      if (data5 < 0 || isNaN(data5)) {
                                        validate71.errors = [{ instancePath: instancePath + "/predecessor/revision", schemaPath: "#/$defs/PredecessorCut/properties/revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                        return false;
                                      }
                                    }
                                  }
                                }
                                var valid3 = _errs13 === errors;
                              } else {
                                var valid3 = true;
                              }
                              if (valid3) {
                                if (data3.run_id !== void 0) {
                                  let data6 = data3.run_id;
                                  const _errs15 = errors;
                                  if (errors === _errs15) {
                                    if (typeof data6 === "string") {
                                      if (func1(data6) > 128) {
                                        validate71.errors = [{ instancePath: instancePath + "/predecessor/run_id", schemaPath: "#/$defs/PredecessorCut/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data6) < 1) {
                                          validate71.errors = [{ instancePath: instancePath + "/predecessor/run_id", schemaPath: "#/$defs/PredecessorCut/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data6)) {
                                            validate71.errors = [{ instancePath: instancePath + "/predecessor/run_id", schemaPath: "#/$defs/PredecessorCut/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate71.errors = [{ instancePath: instancePath + "/predecessor/run_id", schemaPath: "#/$defs/PredecessorCut/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid3 = _errs15 === errors;
                                } else {
                                  var valid3 = true;
                                }
                              }
                            }
                          }
                        }
                      } else {
                        validate71.errors = [{ instancePath: instancePath + "/predecessor", schemaPath: "#/$defs/PredecessorCut/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs7 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.run_id !== void 0) {
                      let data7 = data.run_id;
                      const _errs17 = errors;
                      if (errors === _errs17) {
                        if (typeof data7 === "string") {
                          if (func1(data7) > 128) {
                            validate71.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data7) < 1) {
                              validate71.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern5.test(data7)) {
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
                      var valid0 = _errs17 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.schema_version !== void 0) {
                        let data8 = data.schema_version;
                        const _errs19 = errors;
                        if (typeof data8 !== "string") {
                          validate71.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data8) {
                          validate71.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs19 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.scope !== void 0) {
                          let data9 = data.scope;
                          const _errs21 = errors;
                          const _errs22 = errors;
                          if (errors === _errs22) {
                            if (data9 && typeof data9 == "object" && !Array.isArray(data9)) {
                              let missing2;
                              if (data9.tenant_id === void 0 && (missing2 = "tenant_id") || data9.project_id === void 0 && (missing2 = "project_id")) {
                                validate71.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                return false;
                              } else {
                                const _errs24 = errors;
                                for (const key2 in data9) {
                                  if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                    validate71.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs24 === errors) {
                                  if (data9.project_id !== void 0) {
                                    let data10 = data9.project_id;
                                    const _errs25 = errors;
                                    if (errors === _errs25) {
                                      if (typeof data10 === "string") {
                                        if (func1(data10) > 128) {
                                          validate71.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                          return false;
                                        } else {
                                          if (func1(data10) < 1) {
                                            validate71.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                            return false;
                                          } else {
                                            if (!pattern5.test(data10)) {
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
                                    var valid5 = _errs25 === errors;
                                  } else {
                                    var valid5 = true;
                                  }
                                  if (valid5) {
                                    if (data9.tenant_id !== void 0) {
                                      let data11 = data9.tenant_id;
                                      const _errs27 = errors;
                                      if (errors === _errs27) {
                                        if (typeof data11 === "string") {
                                          if (func1(data11) > 128) {
                                            validate71.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                            return false;
                                          } else {
                                            if (func1(data11) < 1) {
                                              validate71.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                              return false;
                                            } else {
                                              if (!pattern5.test(data11)) {
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
                                      var valid5 = _errs27 === errors;
                                    } else {
                                      var valid5 = true;
                                    }
                                  }
                                }
                              }
                            } else {
                              validate71.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                              return false;
                            }
                          }
                          var valid0 = _errs21 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.transfer_sha256 !== void 0) {
                            let data12 = data.transfer_sha256;
                            const _errs29 = errors;
                            if (errors === _errs29) {
                              if (typeof data12 === "string") {
                                if (!pattern4.test(data12)) {
                                  validate71.errors = [{ instancePath: instancePath + "/transfer_sha256", schemaPath: "#/properties/transfer_sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                  return false;
                                }
                              } else {
                                validate71.errors = [{ instancePath: instancePath + "/transfer_sha256", schemaPath: "#/properties/transfer_sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
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
          validate71.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate71.errors = vErrors;
      return errors === 0;
    }
    validate71.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.completion = validate74;
    var schema100 = { "$defs": { "Abstained": { "additionalProperties": false, "properties": { "reason_code": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Reason Code", "type": "string" }, "status": { "const": "abstained", "title": "Status", "type": "string" } }, "required": ["status", "reason_code"], "title": "Abstained", "type": "object" }, "ArtifactRef": { "additionalProperties": false, "properties": { "artifact_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Artifact Id", "type": "string" }, "media_type": { "maxLength": 128, "minLength": 3, "pattern": "^[^\\s/]+/[^\\s/]+$", "title": "Media Type", "type": "string" }, "schema_ref": { "$ref": "#/$defs/SchemaRef" }, "scope": { "$ref": "#/$defs/Scope" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "size_bytes": { "maximum": 9007199254740991, "minimum": 0, "title": "Size Bytes", "type": "integer" } }, "required": ["artifact_id", "scope", "sha256", "media_type", "schema_ref", "size_bytes"], "title": "ArtifactRef", "type": "object" }, "Completion": { "additionalProperties": false, "properties": { "attempt_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Attempt Id", "type": "string" }, "fence": { "maximum": 9007199254740991, "minimum": 1, "title": "Fence", "type": "integer" }, "invocation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Invocation Id", "type": "string" }, "outcome": { "discriminator": { "mapping": { "abstained": "#/$defs/Abstained", "failed": "#/$defs/Failed", "succeeded": "#/$defs/Succeeded", "uncertain_external_effect": "#/$defs/Uncertain" }, "propertyName": "status" }, "oneOf": [{ "$ref": "#/$defs/Succeeded" }, { "$ref": "#/$defs/Abstained" }, { "$ref": "#/$defs/Failed" }, { "$ref": "#/$defs/Uncertain" }], "title": "Outcome" }, "schema_version": { "const": "1", "title": "Schema Version", "type": "string" } }, "required": ["schema_version", "invocation_id", "attempt_id", "fence", "outcome"], "title": "Completion", "type": "object" }, "Failed": { "additionalProperties": false, "properties": { "reason_code": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Reason Code", "type": "string" }, "retryable": { "title": "Retryable", "type": "boolean" }, "status": { "const": "failed", "title": "Status", "type": "string" } }, "required": ["status", "reason_code", "retryable"], "title": "Failed", "type": "object" }, "InputBinding": { "additionalProperties": false, "properties": { "artifact": { "$ref": "#/$defs/ArtifactRef" }, "port": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Port", "type": "string" } }, "required": ["port", "artifact"], "title": "InputBinding", "type": "object" }, "SchemaRef": { "additionalProperties": false, "properties": { "schema_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Schema Id", "type": "string" }, "sha256": { "pattern": "^[0-9a-f]{64}$", "title": "Sha256", "type": "string" }, "version": { "const": "1", "title": "Version", "type": "string" } }, "required": ["schema_id", "version", "sha256"], "title": "SchemaRef", "type": "object" }, "Scope": { "additionalProperties": false, "properties": { "project_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Project Id", "type": "string" }, "tenant_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Tenant Id", "type": "string" } }, "required": ["tenant_id", "project_id"], "title": "Scope", "type": "object" }, "Succeeded": { "additionalProperties": false, "properties": { "checkpoint": { "anyOf": [{ "$ref": "#/$defs/ArtifactRef" }, { "type": "null" }], "default": null }, "outputs": { "items": { "$ref": "#/$defs/InputBinding" }, "maxItems": 64, "minItems": 1, "title": "Outputs", "type": "array" }, "status": { "const": "succeeded", "title": "Status", "type": "string" } }, "required": ["status", "outputs"], "title": "Succeeded", "type": "object" }, "Uncertain": { "additionalProperties": false, "properties": { "operation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Operation Id", "type": "string" }, "reason_code": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Reason Code", "type": "string" }, "status": { "const": "uncertain_external_effect", "title": "Status", "type": "string" } }, "required": ["status", "operation_id", "reason_code"], "title": "Uncertain", "type": "object" } }, "$id": "urn:amphora:runtime.completion-record:1:serialization", "$schema": "https://json-schema.org/draft/2020-12/schema", "additionalProperties": false, "properties": { "accepted_run_revision": { "maximum": 9007199254740991, "minimum": 0, "title": "Accepted Run Revision", "type": "integer" }, "activation_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Activation Id", "type": "string" }, "canonical_result": { "title": "Canonical Result", "type": "boolean" }, "completion_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Completion Id", "type": "string" }, "result": { "$ref": "#/$defs/Completion" }, "retention_reservation_ids": { "default": [], "items": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "type": "string" }, "maxItems": 65, "title": "Retention Reservation Ids", "type": "array" }, "run_id": { "maxLength": 128, "minLength": 1, "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]*$", "title": "Run Id", "type": "string" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" }, "scope": { "$ref": "#/$defs/Scope" } }, "required": ["scope", "run_id", "completion_id", "activation_id", "accepted_run_revision", "canonical_result", "result"], "title": "CompletionRecord", "type": "object" };
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate77.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate77.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate77.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate77.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate77.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate77.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate77.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate77.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern30.test(data1)) {
                            validate77.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate77.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate77.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate77.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate77.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate77.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate77.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate77.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate77.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate77.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate77.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate77.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate77.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate77.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate77.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate77.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate77.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data7)) {
                                          validate77.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate77.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        validate77.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate77.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data8)) {
                                            validate77.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate77.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate77.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                              validate77.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate77.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate77.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate77.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate77.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          if (data.port === void 0 && (missing0 = "port") || data.artifact === void 0 && (missing0 = "artifact")) {
            validate79.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact" || key0 === "port")) {
                validate79.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.artifact !== void 0) {
                const _errs2 = errors;
                if (!validate77(data.artifact, { instancePath: instancePath + "/artifact", parentData: data, parentDataProperty: "artifact", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate77.errors : vErrors.concat(validate77.errors);
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
                        validate79.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate79.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data1)) {
                            validate79.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate79.errors = [{ instancePath: instancePath + "/port", schemaPath: "#/properties/port/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
          if (data.status === void 0 && (missing0 = "status") || data.outputs === void 0 && (missing0 = "outputs")) {
            validate76.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "checkpoint" || key0 === "outputs" || key0 === "status")) {
                validate76.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                if (!validate77(data0, { instancePath: instancePath + "/checkpoint", parentData: data, parentDataProperty: "checkpoint", rootData, dynamicAnchors })) {
                  vErrors = vErrors === null ? validate77.errors : vErrors.concat(validate77.errors);
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
                  validate76.errors = vErrors;
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
                        validate76.errors = [{ instancePath: instancePath + "/outputs", schemaPath: "#/properties/outputs/maxItems", keyword: "maxItems", params: { limit: 64 }, message: "must NOT have more than 64 items" }];
                        return false;
                      } else {
                        if (data1.length < 1) {
                          validate76.errors = [{ instancePath: instancePath + "/outputs", schemaPath: "#/properties/outputs/minItems", keyword: "minItems", params: { limit: 1 }, message: "must NOT have fewer than 1 items" }];
                          return false;
                        } else {
                          var valid2 = true;
                          const len0 = data1.length;
                          for (let i0 = 0; i0 < len0; i0++) {
                            const _errs9 = errors;
                            if (!validate79(data1[i0], { instancePath: instancePath + "/outputs/" + i0, parentData: data1, parentDataProperty: i0, rootData, dynamicAnchors })) {
                              vErrors = vErrors === null ? validate79.errors : vErrors.concat(validate79.errors);
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
                      validate76.errors = [{ instancePath: instancePath + "/outputs", schemaPath: "#/properties/outputs/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
                      validate76.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                      return false;
                    }
                    if ("succeeded" !== data3) {
                      validate76.errors = [{ instancePath: instancePath + "/status", schemaPath: "#/properties/status/const", keyword: "const", params: { allowedValue: "succeeded" }, message: "must be equal to constant" }];
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
          validate76.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate76.errors = vErrors;
      return errors === 0;
    }
    validate76.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.schema_version === void 0 && (missing0 = "schema_version") || data.invocation_id === void 0 && (missing0 = "invocation_id") || data.attempt_id === void 0 && (missing0 = "attempt_id") || data.fence === void 0 && (missing0 = "fence") || data.outcome === void 0 && (missing0 = "outcome")) {
            validate75.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "attempt_id" || key0 === "fence" || key0 === "invocation_id" || key0 === "outcome" || key0 === "schema_version")) {
                validate75.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate75.errors = [{ instancePath: instancePath + "/attempt_id", schemaPath: "#/properties/attempt_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate75.errors = [{ instancePath: instancePath + "/attempt_id", schemaPath: "#/properties/attempt_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate75.errors = [{ instancePath: instancePath + "/attempt_id", schemaPath: "#/properties/attempt_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate75.errors = [{ instancePath: instancePath + "/attempt_id", schemaPath: "#/properties/attempt_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                    validate75.errors = [{ instancePath: instancePath + "/fence", schemaPath: "#/properties/fence/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                    return false;
                  }
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 9007199254740991 || isNaN(data1)) {
                        validate75.errors = [{ instancePath: instancePath + "/fence", schemaPath: "#/properties/fence/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                        return false;
                      } else {
                        if (data1 < 1 || isNaN(data1)) {
                          validate75.errors = [{ instancePath: instancePath + "/fence", schemaPath: "#/properties/fence/minimum", keyword: "minimum", params: { comparison: ">=", limit: 1 }, message: "must be >= 1" }];
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
                          validate75.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                          return false;
                        } else {
                          if (func1(data2) < 1) {
                            validate75.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          } else {
                            if (!pattern5.test(data2)) {
                              validate75.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                              return false;
                            }
                          }
                        }
                      } else {
                        validate75.errors = [{ instancePath: instancePath + "/invocation_id", schemaPath: "#/properties/invocation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      if (!validate76(data3, { instancePath: instancePath + "/outcome", parentData: data, parentDataProperty: "outcome", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate76.errors : vErrors.concat(validate76.errors);
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
                                        if (!pattern5.test(data4)) {
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
                                          if (!pattern5.test(data6)) {
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
                                            if (!pattern5.test(data9)) {
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
                                              if (!pattern5.test(data10)) {
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
                        validate75.errors = vErrors;
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
                          validate75.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data12) {
                          validate75.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
          validate75.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate75.errors = vErrors;
      return errors === 0;
    }
    validate75.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
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
          if (data.scope === void 0 && (missing0 = "scope") || data.run_id === void 0 && (missing0 = "run_id") || data.completion_id === void 0 && (missing0 = "completion_id") || data.activation_id === void 0 && (missing0 = "activation_id") || data.accepted_run_revision === void 0 && (missing0 = "accepted_run_revision") || data.canonical_result === void 0 && (missing0 = "canonical_result") || data.result === void 0 && (missing0 = "result")) {
            validate74.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func115.call(schema100.properties, key0)) {
                validate74.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.accepted_run_revision !== void 0) {
                let data0 = data.accepted_run_revision;
                const _errs2 = errors;
                if (!(typeof data0 == "number" && (!(data0 % 1) && !isNaN(data0)) && isFinite(data0))) {
                  validate74.errors = [{ instancePath: instancePath + "/accepted_run_revision", schemaPath: "#/properties/accepted_run_revision/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                  return false;
                }
                if (errors === _errs2) {
                  if (typeof data0 == "number" && isFinite(data0)) {
                    if (data0 > 9007199254740991 || isNaN(data0)) {
                      validate74.errors = [{ instancePath: instancePath + "/accepted_run_revision", schemaPath: "#/properties/accepted_run_revision/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                      return false;
                    } else {
                      if (data0 < 0 || isNaN(data0)) {
                        validate74.errors = [{ instancePath: instancePath + "/accepted_run_revision", schemaPath: "#/properties/accepted_run_revision/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
                        validate74.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 1) {
                          validate74.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                          return false;
                        } else {
                          if (!pattern5.test(data1)) {
                            validate74.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate74.errors = [{ instancePath: instancePath + "/activation_id", schemaPath: "#/properties/activation_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                      validate74.errors = [{ instancePath: instancePath + "/canonical_result", schemaPath: "#/properties/canonical_result/type", keyword: "type", params: { type: "boolean" }, message: "must be boolean" }];
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
                            validate74.errors = [{ instancePath: instancePath + "/completion_id", schemaPath: "#/properties/completion_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                            return false;
                          } else {
                            if (func1(data3) < 1) {
                              validate74.errors = [{ instancePath: instancePath + "/completion_id", schemaPath: "#/properties/completion_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                              return false;
                            } else {
                              if (!pattern5.test(data3)) {
                                validate74.errors = [{ instancePath: instancePath + "/completion_id", schemaPath: "#/properties/completion_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                return false;
                              }
                            }
                          }
                        } else {
                          validate74.errors = [{ instancePath: instancePath + "/completion_id", schemaPath: "#/properties/completion_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        if (!validate75(data.result, { instancePath: instancePath + "/result", parentData: data, parentDataProperty: "result", rootData, dynamicAnchors })) {
                          vErrors = vErrors === null ? validate75.errors : vErrors.concat(validate75.errors);
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
                                validate74.errors = [{ instancePath: instancePath + "/retention_reservation_ids", schemaPath: "#/properties/retention_reservation_ids/maxItems", keyword: "maxItems", params: { limit: 65 }, message: "must NOT have more than 65 items" }];
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
                                        validate74.errors = [{ instancePath: instancePath + "/retention_reservation_ids/" + i0, schemaPath: "#/properties/retention_reservation_ids/items/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data6) < 1) {
                                          validate74.errors = [{ instancePath: instancePath + "/retention_reservation_ids/" + i0, schemaPath: "#/properties/retention_reservation_ids/items/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data6)) {
                                            validate74.errors = [{ instancePath: instancePath + "/retention_reservation_ids/" + i0, schemaPath: "#/properties/retention_reservation_ids/items/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate74.errors = [{ instancePath: instancePath + "/retention_reservation_ids/" + i0, schemaPath: "#/properties/retention_reservation_ids/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                              validate74.errors = [{ instancePath: instancePath + "/retention_reservation_ids", schemaPath: "#/properties/retention_reservation_ids/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
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
                                  validate74.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                  return false;
                                } else {
                                  if (func1(data7) < 1) {
                                    validate74.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                    return false;
                                  } else {
                                    if (!pattern5.test(data7)) {
                                      validate74.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                      return false;
                                    }
                                  }
                                }
                              } else {
                                validate74.errors = [{ instancePath: instancePath + "/run_id", schemaPath: "#/properties/run_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                validate74.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("1" !== data8) {
                                validate74.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                                      validate74.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                                      return false;
                                    } else {
                                      const _errs22 = errors;
                                      for (const key1 in data9) {
                                        if (!(key1 === "project_id" || key1 === "tenant_id")) {
                                          validate74.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                                validate74.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                return false;
                                              } else {
                                                if (func1(data10) < 1) {
                                                  validate74.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                  return false;
                                                } else {
                                                  if (!pattern5.test(data10)) {
                                                    validate74.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                    return false;
                                                  }
                                                }
                                              }
                                            } else {
                                              validate74.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                                  validate74.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                                  return false;
                                                } else {
                                                  if (func1(data11) < 1) {
                                                    validate74.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                                    return false;
                                                  } else {
                                                    if (!pattern5.test(data11)) {
                                                      validate74.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                                      return false;
                                                    }
                                                  }
                                                }
                                              } else {
                                                validate74.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate74.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          validate74.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate74.errors = vErrors;
      return errors === 0;
    }
    validate74.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
    exports.artifact = validate84;
    function validate84(data, { instancePath = "", parentData, parentDataProperty, rootData = data, dynamicAnchors = {} } = {}) {
      ;
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
          if (data.artifact_id === void 0 && (missing0 = "artifact_id") || data.scope === void 0 && (missing0 = "scope") || data.sha256 === void 0 && (missing0 = "sha256") || data.media_type === void 0 && (missing0 = "media_type") || data.schema_ref === void 0 && (missing0 = "schema_ref") || data.size_bytes === void 0 && (missing0 = "size_bytes")) {
            validate84.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "artifact_id" || key0 === "media_type" || key0 === "schema_ref" || key0 === "scope" || key0 === "sha256" || key0 === "size_bytes")) {
                validate84.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
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
                      validate84.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func1(data0) < 1) {
                        validate84.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
                      } else {
                        if (!pattern5.test(data0)) {
                          validate84.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                          return false;
                        }
                      }
                    }
                  } else {
                    validate84.errors = [{ instancePath: instancePath + "/artifact_id", schemaPath: "#/properties/artifact_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                        validate84.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                        return false;
                      } else {
                        if (func1(data1) < 3) {
                          validate84.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/minLength", keyword: "minLength", params: { limit: 3 }, message: "must NOT have fewer than 3 characters" }];
                          return false;
                        } else {
                          if (!pattern30.test(data1)) {
                            validate84.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/pattern", keyword: "pattern", params: { pattern: "^[^\\s/]+/[^\\s/]+$" }, message: 'must match pattern "^[^\\s/]+/[^\\s/]+$"' }];
                            return false;
                          }
                        }
                      }
                    } else {
                      validate84.errors = [{ instancePath: instancePath + "/media_type", schemaPath: "#/properties/media_type/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate84.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "schema_id" || key1 === "sha256" || key1 === "version")) {
                              validate84.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
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
                                    validate84.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                    return false;
                                  } else {
                                    if (func1(data3) < 1) {
                                      validate84.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                      return false;
                                    } else {
                                      if (!pattern5.test(data3)) {
                                        validate84.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                        return false;
                                      }
                                    }
                                  }
                                } else {
                                  validate84.errors = [{ instancePath: instancePath + "/schema_ref/schema_id", schemaPath: "#/$defs/SchemaRef/properties/schema_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                      validate84.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                                      return false;
                                    }
                                  } else {
                                    validate84.errors = [{ instancePath: instancePath + "/schema_ref/sha256", schemaPath: "#/$defs/SchemaRef/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                    validate84.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if ("1" !== data5) {
                                    validate84.errors = [{ instancePath: instancePath + "/schema_ref/version", schemaPath: "#/$defs/SchemaRef/properties/version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
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
                        validate84.errors = [{ instancePath: instancePath + "/schema_ref", schemaPath: "#/$defs/SchemaRef/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                            validate84.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                            return false;
                          } else {
                            const _errs19 = errors;
                            for (const key2 in data6) {
                              if (!(key2 === "project_id" || key2 === "tenant_id")) {
                                validate84.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
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
                                      validate84.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func1(data7) < 1) {
                                        validate84.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      } else {
                                        if (!pattern5.test(data7)) {
                                          validate84.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                          return false;
                                        }
                                      }
                                    }
                                  } else {
                                    validate84.errors = [{ instancePath: instancePath + "/scope/project_id", schemaPath: "#/$defs/Scope/properties/project_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                                        validate84.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                        return false;
                                      } else {
                                        if (func1(data8) < 1) {
                                          validate84.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        } else {
                                          if (!pattern5.test(data8)) {
                                            validate84.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/pattern", keyword: "pattern", params: { pattern: "^[A-Za-z0-9][A-Za-z0-9._:-]*$" }, message: 'must match pattern "^[A-Za-z0-9][A-Za-z0-9._:-]*$"' }];
                                            return false;
                                          }
                                        }
                                      }
                                    } else {
                                      validate84.errors = [{ instancePath: instancePath + "/scope/tenant_id", schemaPath: "#/$defs/Scope/properties/tenant_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                          validate84.errors = [{ instancePath: instancePath + "/scope", schemaPath: "#/$defs/Scope/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
                              validate84.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/pattern", keyword: "pattern", params: { pattern: "^[0-9a-f]{64}$" }, message: 'must match pattern "^[0-9a-f]{64}$"' }];
                              return false;
                            }
                          } else {
                            validate84.errors = [{ instancePath: instancePath + "/sha256", schemaPath: "#/properties/sha256/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
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
                            validate84.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/type", keyword: "type", params: { type: "integer" }, message: "must be integer" }];
                            return false;
                          }
                          if (errors === _errs26) {
                            if (typeof data10 == "number" && isFinite(data10)) {
                              if (data10 > 9007199254740991 || isNaN(data10)) {
                                validate84.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/maximum", keyword: "maximum", params: { comparison: "<=", limit: 9007199254740991 }, message: "must be <= 9007199254740991" }];
                                return false;
                              } else {
                                if (data10 < 0 || isNaN(data10)) {
                                  validate84.errors = [{ instancePath: instancePath + "/size_bytes", schemaPath: "#/properties/size_bytes/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
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
          validate84.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate84.errors = vErrors;
      return errors === 0;
    }
    validate84.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
  }
});
export default require_reviewed_validators();
