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
    exports.hansen_solvency = validate20;
    var schema31 = { "$defs": { "Point": { "additionalProperties": false, "properties": { "dispersion": { "maximum": 1e6, "minimum": 0, "title": "Dispersion", "type": "number" }, "hydrogen_bond": { "maximum": 1e6, "minimum": 0, "title": "Hydrogen Bond", "type": "number" }, "polar": { "maximum": 1e6, "minimum": 0, "title": "Polar", "type": "number" } }, "required": ["dispersion", "polar", "hydrogen_bond"], "title": "Point", "type": "object" }, "SolvencyInput": { "additionalProperties": false, "properties": { "candidate_id": { "maxLength": 128, "minLength": 1, "title": "Candidate Id", "type": "string" }, "interaction_radius": { "exclusiveMinimum": 0, "maximum": 1e6, "title": "Interaction Radius", "type": "number" }, "parameter_context": { "maxLength": 2048, "minLength": 1, "title": "Parameter Context", "type": "string" }, "polymer": { "$ref": "#/$defs/Point" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" }, "solvent": { "$ref": "#/$defs/Point" } }, "required": ["candidate_id", "parameter_context", "polymer", "solvent", "interaction_radius"], "title": "SolvencyInput", "type": "object" } }, "additionalProperties": false, "properties": { "candidate_id": { "title": "Candidate Id", "type": "string" }, "distance": { "title": "Distance", "type": "number" }, "distance_squared": { "title": "Distance Squared", "type": "number" }, "input_parameters": { "$ref": "#/$defs/SolvencyInput" }, "limitation": { "title": "Limitation", "type": "string" }, "procedure": { "items": { "type": "string" }, "title": "Procedure", "type": "array" }, "relative_energy_difference": { "title": "Relative Energy Difference", "type": "number" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" }, "scientific_status": { "const": "unvalidated_screen", "default": "unvalidated_screen", "title": "Scientific Status", "type": "string" }, "sphere_position": { "enum": ["inside", "boundary", "outside"], "title": "Sphere Position", "type": "string" } }, "required": ["candidate_id", "input_parameters", "distance_squared", "distance", "relative_energy_difference", "sphere_position", "procedure", "limitation"], "title": "SolvencyOutput", "type": "object", "$id": "urn:amphora:scientific:hansen-solvency" };
    var func1 = Object.prototype.hasOwnProperty;
    var func2 = require_ucs2length().default;
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
          if (data.candidate_id === void 0 && (missing0 = "candidate_id") || data.parameter_context === void 0 && (missing0 = "parameter_context") || data.polymer === void 0 && (missing0 = "polymer") || data.solvent === void 0 && (missing0 = "solvent") || data.interaction_radius === void 0 && (missing0 = "interaction_radius")) {
            validate21.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!(key0 === "candidate_id" || key0 === "interaction_radius" || key0 === "parameter_context" || key0 === "polymer" || key0 === "schema_version" || key0 === "solvent")) {
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
                    if (func2(data0) > 128) {
                      validate21.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                      return false;
                    } else {
                      if (func2(data0) < 1) {
                        validate21.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                        return false;
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
                if (data.interaction_radius !== void 0) {
                  let data1 = data.interaction_radius;
                  const _errs4 = errors;
                  if (errors === _errs4) {
                    if (typeof data1 == "number" && isFinite(data1)) {
                      if (data1 > 1e6 || isNaN(data1)) {
                        validate21.errors = [{ instancePath: instancePath + "/interaction_radius", schemaPath: "#/properties/interaction_radius/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e6 }, message: "must be <= 1000000" }];
                        return false;
                      } else {
                        if (data1 <= 0 || isNaN(data1)) {
                          validate21.errors = [{ instancePath: instancePath + "/interaction_radius", schemaPath: "#/properties/interaction_radius/exclusiveMinimum", keyword: "exclusiveMinimum", params: { comparison: ">", limit: 0 }, message: "must be > 0" }];
                          return false;
                        }
                      }
                    } else {
                      validate21.errors = [{ instancePath: instancePath + "/interaction_radius", schemaPath: "#/properties/interaction_radius/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                      return false;
                    }
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.parameter_context !== void 0) {
                    let data2 = data.parameter_context;
                    const _errs6 = errors;
                    if (errors === _errs6) {
                      if (typeof data2 === "string") {
                        if (func2(data2) > 2048) {
                          validate21.errors = [{ instancePath: instancePath + "/parameter_context", schemaPath: "#/properties/parameter_context/maxLength", keyword: "maxLength", params: { limit: 2048 }, message: "must NOT have more than 2048 characters" }];
                          return false;
                        } else {
                          if (func2(data2) < 1) {
                            validate21.errors = [{ instancePath: instancePath + "/parameter_context", schemaPath: "#/properties/parameter_context/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                            return false;
                          }
                        }
                      } else {
                        validate21.errors = [{ instancePath: instancePath + "/parameter_context", schemaPath: "#/properties/parameter_context/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.polymer !== void 0) {
                      let data3 = data.polymer;
                      const _errs8 = errors;
                      const _errs9 = errors;
                      if (errors === _errs9) {
                        if (data3 && typeof data3 == "object" && !Array.isArray(data3)) {
                          let missing1;
                          if (data3.dispersion === void 0 && (missing1 = "dispersion") || data3.polar === void 0 && (missing1 = "polar") || data3.hydrogen_bond === void 0 && (missing1 = "hydrogen_bond")) {
                            validate21.errors = [{ instancePath: instancePath + "/polymer", schemaPath: "#/$defs/Point/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                            return false;
                          } else {
                            const _errs11 = errors;
                            for (const key1 in data3) {
                              if (!(key1 === "dispersion" || key1 === "hydrogen_bond" || key1 === "polar")) {
                                validate21.errors = [{ instancePath: instancePath + "/polymer", schemaPath: "#/$defs/Point/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                                return false;
                                break;
                              }
                            }
                            if (_errs11 === errors) {
                              if (data3.dispersion !== void 0) {
                                let data4 = data3.dispersion;
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data4 == "number" && isFinite(data4)) {
                                    if (data4 > 1e6 || isNaN(data4)) {
                                      validate21.errors = [{ instancePath: instancePath + "/polymer/dispersion", schemaPath: "#/$defs/Point/properties/dispersion/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e6 }, message: "must be <= 1000000" }];
                                      return false;
                                    } else {
                                      if (data4 < 0 || isNaN(data4)) {
                                        validate21.errors = [{ instancePath: instancePath + "/polymer/dispersion", schemaPath: "#/$defs/Point/properties/dispersion/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                        return false;
                                      }
                                    }
                                  } else {
                                    validate21.errors = [{ instancePath: instancePath + "/polymer/dispersion", schemaPath: "#/$defs/Point/properties/dispersion/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                    return false;
                                  }
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data3.hydrogen_bond !== void 0) {
                                  let data5 = data3.hydrogen_bond;
                                  const _errs14 = errors;
                                  if (errors === _errs14) {
                                    if (typeof data5 == "number" && isFinite(data5)) {
                                      if (data5 > 1e6 || isNaN(data5)) {
                                        validate21.errors = [{ instancePath: instancePath + "/polymer/hydrogen_bond", schemaPath: "#/$defs/Point/properties/hydrogen_bond/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e6 }, message: "must be <= 1000000" }];
                                        return false;
                                      } else {
                                        if (data5 < 0 || isNaN(data5)) {
                                          validate21.errors = [{ instancePath: instancePath + "/polymer/hydrogen_bond", schemaPath: "#/$defs/Point/properties/hydrogen_bond/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                          return false;
                                        }
                                      }
                                    } else {
                                      validate21.errors = [{ instancePath: instancePath + "/polymer/hydrogen_bond", schemaPath: "#/$defs/Point/properties/hydrogen_bond/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                      return false;
                                    }
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                                if (valid2) {
                                  if (data3.polar !== void 0) {
                                    let data6 = data3.polar;
                                    const _errs16 = errors;
                                    if (errors === _errs16) {
                                      if (typeof data6 == "number" && isFinite(data6)) {
                                        if (data6 > 1e6 || isNaN(data6)) {
                                          validate21.errors = [{ instancePath: instancePath + "/polymer/polar", schemaPath: "#/$defs/Point/properties/polar/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e6 }, message: "must be <= 1000000" }];
                                          return false;
                                        } else {
                                          if (data6 < 0 || isNaN(data6)) {
                                            validate21.errors = [{ instancePath: instancePath + "/polymer/polar", schemaPath: "#/$defs/Point/properties/polar/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                            return false;
                                          }
                                        }
                                      } else {
                                        validate21.errors = [{ instancePath: instancePath + "/polymer/polar", schemaPath: "#/$defs/Point/properties/polar/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
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
                        } else {
                          validate21.errors = [{ instancePath: instancePath + "/polymer", schemaPath: "#/$defs/Point/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                          return false;
                        }
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.schema_version !== void 0) {
                        let data7 = data.schema_version;
                        const _errs18 = errors;
                        if (typeof data7 !== "string") {
                          validate21.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        if ("1" !== data7) {
                          validate21.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                          return false;
                        }
                        var valid0 = _errs18 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.solvent !== void 0) {
                          let data8 = data.solvent;
                          const _errs20 = errors;
                          const _errs21 = errors;
                          if (errors === _errs21) {
                            if (data8 && typeof data8 == "object" && !Array.isArray(data8)) {
                              let missing2;
                              if (data8.dispersion === void 0 && (missing2 = "dispersion") || data8.polar === void 0 && (missing2 = "polar") || data8.hydrogen_bond === void 0 && (missing2 = "hydrogen_bond")) {
                                validate21.errors = [{ instancePath: instancePath + "/solvent", schemaPath: "#/$defs/Point/required", keyword: "required", params: { missingProperty: missing2 }, message: "must have required property '" + missing2 + "'" }];
                                return false;
                              } else {
                                const _errs23 = errors;
                                for (const key2 in data8) {
                                  if (!(key2 === "dispersion" || key2 === "hydrogen_bond" || key2 === "polar")) {
                                    validate21.errors = [{ instancePath: instancePath + "/solvent", schemaPath: "#/$defs/Point/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key2 }, message: "must NOT have additional properties" }];
                                    return false;
                                    break;
                                  }
                                }
                                if (_errs23 === errors) {
                                  if (data8.dispersion !== void 0) {
                                    let data9 = data8.dispersion;
                                    const _errs24 = errors;
                                    if (errors === _errs24) {
                                      if (typeof data9 == "number" && isFinite(data9)) {
                                        if (data9 > 1e6 || isNaN(data9)) {
                                          validate21.errors = [{ instancePath: instancePath + "/solvent/dispersion", schemaPath: "#/$defs/Point/properties/dispersion/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e6 }, message: "must be <= 1000000" }];
                                          return false;
                                        } else {
                                          if (data9 < 0 || isNaN(data9)) {
                                            validate21.errors = [{ instancePath: instancePath + "/solvent/dispersion", schemaPath: "#/$defs/Point/properties/dispersion/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                            return false;
                                          }
                                        }
                                      } else {
                                        validate21.errors = [{ instancePath: instancePath + "/solvent/dispersion", schemaPath: "#/$defs/Point/properties/dispersion/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                        return false;
                                      }
                                    }
                                    var valid4 = _errs24 === errors;
                                  } else {
                                    var valid4 = true;
                                  }
                                  if (valid4) {
                                    if (data8.hydrogen_bond !== void 0) {
                                      let data10 = data8.hydrogen_bond;
                                      const _errs26 = errors;
                                      if (errors === _errs26) {
                                        if (typeof data10 == "number" && isFinite(data10)) {
                                          if (data10 > 1e6 || isNaN(data10)) {
                                            validate21.errors = [{ instancePath: instancePath + "/solvent/hydrogen_bond", schemaPath: "#/$defs/Point/properties/hydrogen_bond/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e6 }, message: "must be <= 1000000" }];
                                            return false;
                                          } else {
                                            if (data10 < 0 || isNaN(data10)) {
                                              validate21.errors = [{ instancePath: instancePath + "/solvent/hydrogen_bond", schemaPath: "#/$defs/Point/properties/hydrogen_bond/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                              return false;
                                            }
                                          }
                                        } else {
                                          validate21.errors = [{ instancePath: instancePath + "/solvent/hydrogen_bond", schemaPath: "#/$defs/Point/properties/hydrogen_bond/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                          return false;
                                        }
                                      }
                                      var valid4 = _errs26 === errors;
                                    } else {
                                      var valid4 = true;
                                    }
                                    if (valid4) {
                                      if (data8.polar !== void 0) {
                                        let data11 = data8.polar;
                                        const _errs28 = errors;
                                        if (errors === _errs28) {
                                          if (typeof data11 == "number" && isFinite(data11)) {
                                            if (data11 > 1e6 || isNaN(data11)) {
                                              validate21.errors = [{ instancePath: instancePath + "/solvent/polar", schemaPath: "#/$defs/Point/properties/polar/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e6 }, message: "must be <= 1000000" }];
                                              return false;
                                            } else {
                                              if (data11 < 0 || isNaN(data11)) {
                                                validate21.errors = [{ instancePath: instancePath + "/solvent/polar", schemaPath: "#/$defs/Point/properties/polar/minimum", keyword: "minimum", params: { comparison: ">=", limit: 0 }, message: "must be >= 0" }];
                                                return false;
                                              }
                                            }
                                          } else {
                                            validate21.errors = [{ instancePath: instancePath + "/solvent/polar", schemaPath: "#/$defs/Point/properties/polar/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                            return false;
                                          }
                                        }
                                        var valid4 = _errs28 === errors;
                                      } else {
                                        var valid4 = true;
                                      }
                                    }
                                  }
                                }
                              }
                            } else {
                              validate21.errors = [{ instancePath: instancePath + "/solvent", schemaPath: "#/$defs/Point/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
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
          if (data.candidate_id === void 0 && (missing0 = "candidate_id") || data.input_parameters === void 0 && (missing0 = "input_parameters") || data.distance_squared === void 0 && (missing0 = "distance_squared") || data.distance === void 0 && (missing0 = "distance") || data.relative_energy_difference === void 0 && (missing0 = "relative_energy_difference") || data.sphere_position === void 0 && (missing0 = "sphere_position") || data.procedure === void 0 && (missing0 = "procedure") || data.limitation === void 0 && (missing0 = "limitation")) {
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
              if (data.candidate_id !== void 0) {
                const _errs2 = errors;
                if (typeof data.candidate_id !== "string") {
                  validate20.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.distance !== void 0) {
                  let data1 = data.distance;
                  const _errs4 = errors;
                  if (!(typeof data1 == "number" && isFinite(data1))) {
                    validate20.errors = [{ instancePath: instancePath + "/distance", schemaPath: "#/properties/distance/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                    return false;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.distance_squared !== void 0) {
                    let data2 = data.distance_squared;
                    const _errs6 = errors;
                    if (!(typeof data2 == "number" && isFinite(data2))) {
                      validate20.errors = [{ instancePath: instancePath + "/distance_squared", schemaPath: "#/properties/distance_squared/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                      return false;
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.input_parameters !== void 0) {
                      const _errs8 = errors;
                      if (!validate21(data.input_parameters, { instancePath: instancePath + "/input_parameters", parentData: data, parentDataProperty: "input_parameters", rootData, dynamicAnchors })) {
                        vErrors = vErrors === null ? validate21.errors : vErrors.concat(validate21.errors);
                        errors = vErrors.length;
                      }
                      var valid0 = _errs8 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.limitation !== void 0) {
                        const _errs9 = errors;
                        if (typeof data.limitation !== "string") {
                          validate20.errors = [{ instancePath: instancePath + "/limitation", schemaPath: "#/properties/limitation/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                          return false;
                        }
                        var valid0 = _errs9 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.procedure !== void 0) {
                          let data5 = data.procedure;
                          const _errs11 = errors;
                          if (errors === _errs11) {
                            if (Array.isArray(data5)) {
                              var valid1 = true;
                              const len0 = data5.length;
                              for (let i0 = 0; i0 < len0; i0++) {
                                const _errs13 = errors;
                                if (typeof data5[i0] !== "string") {
                                  validate20.errors = [{ instancePath: instancePath + "/procedure/" + i0, schemaPath: "#/properties/procedure/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                var valid1 = _errs13 === errors;
                                if (!valid1) {
                                  break;
                                }
                              }
                            } else {
                              validate20.errors = [{ instancePath: instancePath + "/procedure", schemaPath: "#/properties/procedure/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                              return false;
                            }
                          }
                          var valid0 = _errs11 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.relative_energy_difference !== void 0) {
                            let data7 = data.relative_energy_difference;
                            const _errs15 = errors;
                            if (!(typeof data7 == "number" && isFinite(data7))) {
                              validate20.errors = [{ instancePath: instancePath + "/relative_energy_difference", schemaPath: "#/properties/relative_energy_difference/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                              return false;
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
                                validate20.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("1" !== data8) {
                                validate20.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs17 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.scientific_status !== void 0) {
                                let data9 = data.scientific_status;
                                const _errs19 = errors;
                                if (typeof data9 !== "string") {
                                  validate20.errors = [{ instancePath: instancePath + "/scientific_status", schemaPath: "#/properties/scientific_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                  return false;
                                }
                                if ("unvalidated_screen" !== data9) {
                                  validate20.errors = [{ instancePath: instancePath + "/scientific_status", schemaPath: "#/properties/scientific_status/const", keyword: "const", params: { allowedValue: "unvalidated_screen" }, message: "must be equal to constant" }];
                                  return false;
                                }
                                var valid0 = _errs19 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.sphere_position !== void 0) {
                                  let data10 = data.sphere_position;
                                  const _errs21 = errors;
                                  if (typeof data10 !== "string") {
                                    validate20.errors = [{ instancePath: instancePath + "/sphere_position", schemaPath: "#/properties/sphere_position/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                  if (!(data10 === "inside" || data10 === "boundary" || data10 === "outside")) {
                                    validate20.errors = [{ instancePath: instancePath + "/sphere_position", schemaPath: "#/properties/sphere_position/enum", keyword: "enum", params: { allowedValues: schema31.properties.sphere_position.enum }, message: "must be equal to one of the allowed values" }];
                                    return false;
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
    exports.arrhenius_viscosity = validate23;
    var schema35 = { "$defs": { "ViscosityInput": { "additionalProperties": false, "properties": { "activation_energy_j_mol": { "exclusiveMinimum": 0, "maximum": 1e100, "title": "Activation Energy J Mol", "type": "number" }, "candidate_id": { "maxLength": 128, "minLength": 1, "title": "Candidate Id", "type": "string" }, "parameter_context": { "maxLength": 2048, "minLength": 1, "title": "Parameter Context", "type": "string" }, "reference_temperature_c": { "maximum": 500, "minimum": -273.14, "title": "Reference Temperature C", "type": "number" }, "reference_viscosity_pa_s": { "exclusiveMinimum": 0, "maximum": 1e100, "title": "Reference Viscosity Pa S", "type": "number" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" }, "temperature_c": { "maximum": 500, "minimum": -273.14, "title": "Temperature C", "type": "number" } }, "required": ["candidate_id", "parameter_context", "reference_viscosity_pa_s", "reference_temperature_c", "temperature_c", "activation_energy_j_mol"], "title": "ViscosityInput", "type": "object" } }, "additionalProperties": false, "properties": { "candidate_id": { "title": "Candidate Id", "type": "string" }, "exponent": { "title": "Exponent", "type": "number" }, "input_parameters": { "$ref": "#/$defs/ViscosityInput" }, "limitation": { "title": "Limitation", "type": "string" }, "procedure": { "items": { "type": "string" }, "title": "Procedure", "type": "array" }, "reference_temperature_k": { "title": "Reference Temperature K", "type": "number" }, "schema_version": { "const": "1", "default": "1", "title": "Schema Version", "type": "string" }, "scientific_status": { "const": "unvalidated_screen", "default": "unvalidated_screen", "title": "Scientific Status", "type": "string" }, "temperature_k": { "title": "Temperature K", "type": "number" }, "viscosity_pa_s": { "title": "Viscosity Pa S", "type": "number" } }, "required": ["candidate_id", "input_parameters", "reference_temperature_k", "temperature_k", "exponent", "viscosity_pa_s", "procedure", "limitation"], "title": "ViscosityOutput", "type": "object", "$id": "urn:amphora:scientific:arrhenius-viscosity" };
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
          if (data.candidate_id === void 0 && (missing0 = "candidate_id") || data.input_parameters === void 0 && (missing0 = "input_parameters") || data.reference_temperature_k === void 0 && (missing0 = "reference_temperature_k") || data.temperature_k === void 0 && (missing0 = "temperature_k") || data.exponent === void 0 && (missing0 = "exponent") || data.viscosity_pa_s === void 0 && (missing0 = "viscosity_pa_s") || data.procedure === void 0 && (missing0 = "procedure") || data.limitation === void 0 && (missing0 = "limitation")) {
            validate23.errors = [{ instancePath, schemaPath: "#/required", keyword: "required", params: { missingProperty: missing0 }, message: "must have required property '" + missing0 + "'" }];
            return false;
          } else {
            const _errs1 = errors;
            for (const key0 in data) {
              if (!func1.call(schema35.properties, key0)) {
                validate23.errors = [{ instancePath, schemaPath: "#/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key0 }, message: "must NOT have additional properties" }];
                return false;
                break;
              }
            }
            if (_errs1 === errors) {
              if (data.candidate_id !== void 0) {
                const _errs2 = errors;
                if (typeof data.candidate_id !== "string") {
                  validate23.errors = [{ instancePath: instancePath + "/candidate_id", schemaPath: "#/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                  return false;
                }
                var valid0 = _errs2 === errors;
              } else {
                var valid0 = true;
              }
              if (valid0) {
                if (data.exponent !== void 0) {
                  let data1 = data.exponent;
                  const _errs4 = errors;
                  if (!(typeof data1 == "number" && isFinite(data1))) {
                    validate23.errors = [{ instancePath: instancePath + "/exponent", schemaPath: "#/properties/exponent/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                    return false;
                  }
                  var valid0 = _errs4 === errors;
                } else {
                  var valid0 = true;
                }
                if (valid0) {
                  if (data.input_parameters !== void 0) {
                    let data2 = data.input_parameters;
                    const _errs6 = errors;
                    const _errs7 = errors;
                    if (errors === _errs7) {
                      if (data2 && typeof data2 == "object" && !Array.isArray(data2)) {
                        let missing1;
                        if (data2.candidate_id === void 0 && (missing1 = "candidate_id") || data2.parameter_context === void 0 && (missing1 = "parameter_context") || data2.reference_viscosity_pa_s === void 0 && (missing1 = "reference_viscosity_pa_s") || data2.reference_temperature_c === void 0 && (missing1 = "reference_temperature_c") || data2.temperature_c === void 0 && (missing1 = "temperature_c") || data2.activation_energy_j_mol === void 0 && (missing1 = "activation_energy_j_mol")) {
                          validate23.errors = [{ instancePath: instancePath + "/input_parameters", schemaPath: "#/$defs/ViscosityInput/required", keyword: "required", params: { missingProperty: missing1 }, message: "must have required property '" + missing1 + "'" }];
                          return false;
                        } else {
                          const _errs9 = errors;
                          for (const key1 in data2) {
                            if (!(key1 === "activation_energy_j_mol" || key1 === "candidate_id" || key1 === "parameter_context" || key1 === "reference_temperature_c" || key1 === "reference_viscosity_pa_s" || key1 === "schema_version" || key1 === "temperature_c")) {
                              validate23.errors = [{ instancePath: instancePath + "/input_parameters", schemaPath: "#/$defs/ViscosityInput/additionalProperties", keyword: "additionalProperties", params: { additionalProperty: key1 }, message: "must NOT have additional properties" }];
                              return false;
                              break;
                            }
                          }
                          if (_errs9 === errors) {
                            if (data2.activation_energy_j_mol !== void 0) {
                              let data3 = data2.activation_energy_j_mol;
                              const _errs10 = errors;
                              if (errors === _errs10) {
                                if (typeof data3 == "number" && isFinite(data3)) {
                                  if (data3 > 1e100 || isNaN(data3)) {
                                    validate23.errors = [{ instancePath: instancePath + "/input_parameters/activation_energy_j_mol", schemaPath: "#/$defs/ViscosityInput/properties/activation_energy_j_mol/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e100 }, message: "must be <= 1e+100" }];
                                    return false;
                                  } else {
                                    if (data3 <= 0 || isNaN(data3)) {
                                      validate23.errors = [{ instancePath: instancePath + "/input_parameters/activation_energy_j_mol", schemaPath: "#/$defs/ViscosityInput/properties/activation_energy_j_mol/exclusiveMinimum", keyword: "exclusiveMinimum", params: { comparison: ">", limit: 0 }, message: "must be > 0" }];
                                      return false;
                                    }
                                  }
                                } else {
                                  validate23.errors = [{ instancePath: instancePath + "/input_parameters/activation_energy_j_mol", schemaPath: "#/$defs/ViscosityInput/properties/activation_energy_j_mol/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                  return false;
                                }
                              }
                              var valid2 = _errs10 === errors;
                            } else {
                              var valid2 = true;
                            }
                            if (valid2) {
                              if (data2.candidate_id !== void 0) {
                                let data4 = data2.candidate_id;
                                const _errs12 = errors;
                                if (errors === _errs12) {
                                  if (typeof data4 === "string") {
                                    if (func2(data4) > 128) {
                                      validate23.errors = [{ instancePath: instancePath + "/input_parameters/candidate_id", schemaPath: "#/$defs/ViscosityInput/properties/candidate_id/maxLength", keyword: "maxLength", params: { limit: 128 }, message: "must NOT have more than 128 characters" }];
                                      return false;
                                    } else {
                                      if (func2(data4) < 1) {
                                        validate23.errors = [{ instancePath: instancePath + "/input_parameters/candidate_id", schemaPath: "#/$defs/ViscosityInput/properties/candidate_id/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                        return false;
                                      }
                                    }
                                  } else {
                                    validate23.errors = [{ instancePath: instancePath + "/input_parameters/candidate_id", schemaPath: "#/$defs/ViscosityInput/properties/candidate_id/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                    return false;
                                  }
                                }
                                var valid2 = _errs12 === errors;
                              } else {
                                var valid2 = true;
                              }
                              if (valid2) {
                                if (data2.parameter_context !== void 0) {
                                  let data5 = data2.parameter_context;
                                  const _errs14 = errors;
                                  if (errors === _errs14) {
                                    if (typeof data5 === "string") {
                                      if (func2(data5) > 2048) {
                                        validate23.errors = [{ instancePath: instancePath + "/input_parameters/parameter_context", schemaPath: "#/$defs/ViscosityInput/properties/parameter_context/maxLength", keyword: "maxLength", params: { limit: 2048 }, message: "must NOT have more than 2048 characters" }];
                                        return false;
                                      } else {
                                        if (func2(data5) < 1) {
                                          validate23.errors = [{ instancePath: instancePath + "/input_parameters/parameter_context", schemaPath: "#/$defs/ViscosityInput/properties/parameter_context/minLength", keyword: "minLength", params: { limit: 1 }, message: "must NOT have fewer than 1 characters" }];
                                          return false;
                                        }
                                      }
                                    } else {
                                      validate23.errors = [{ instancePath: instancePath + "/input_parameters/parameter_context", schemaPath: "#/$defs/ViscosityInput/properties/parameter_context/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                      return false;
                                    }
                                  }
                                  var valid2 = _errs14 === errors;
                                } else {
                                  var valid2 = true;
                                }
                                if (valid2) {
                                  if (data2.reference_temperature_c !== void 0) {
                                    let data6 = data2.reference_temperature_c;
                                    const _errs16 = errors;
                                    if (errors === _errs16) {
                                      if (typeof data6 == "number" && isFinite(data6)) {
                                        if (data6 > 500 || isNaN(data6)) {
                                          validate23.errors = [{ instancePath: instancePath + "/input_parameters/reference_temperature_c", schemaPath: "#/$defs/ViscosityInput/properties/reference_temperature_c/maximum", keyword: "maximum", params: { comparison: "<=", limit: 500 }, message: "must be <= 500" }];
                                          return false;
                                        } else {
                                          if (data6 < -273.14 || isNaN(data6)) {
                                            validate23.errors = [{ instancePath: instancePath + "/input_parameters/reference_temperature_c", schemaPath: "#/$defs/ViscosityInput/properties/reference_temperature_c/minimum", keyword: "minimum", params: { comparison: ">=", limit: -273.14 }, message: "must be >= -273.14" }];
                                            return false;
                                          }
                                        }
                                      } else {
                                        validate23.errors = [{ instancePath: instancePath + "/input_parameters/reference_temperature_c", schemaPath: "#/$defs/ViscosityInput/properties/reference_temperature_c/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                        return false;
                                      }
                                    }
                                    var valid2 = _errs16 === errors;
                                  } else {
                                    var valid2 = true;
                                  }
                                  if (valid2) {
                                    if (data2.reference_viscosity_pa_s !== void 0) {
                                      let data7 = data2.reference_viscosity_pa_s;
                                      const _errs18 = errors;
                                      if (errors === _errs18) {
                                        if (typeof data7 == "number" && isFinite(data7)) {
                                          if (data7 > 1e100 || isNaN(data7)) {
                                            validate23.errors = [{ instancePath: instancePath + "/input_parameters/reference_viscosity_pa_s", schemaPath: "#/$defs/ViscosityInput/properties/reference_viscosity_pa_s/maximum", keyword: "maximum", params: { comparison: "<=", limit: 1e100 }, message: "must be <= 1e+100" }];
                                            return false;
                                          } else {
                                            if (data7 <= 0 || isNaN(data7)) {
                                              validate23.errors = [{ instancePath: instancePath + "/input_parameters/reference_viscosity_pa_s", schemaPath: "#/$defs/ViscosityInput/properties/reference_viscosity_pa_s/exclusiveMinimum", keyword: "exclusiveMinimum", params: { comparison: ">", limit: 0 }, message: "must be > 0" }];
                                              return false;
                                            }
                                          }
                                        } else {
                                          validate23.errors = [{ instancePath: instancePath + "/input_parameters/reference_viscosity_pa_s", schemaPath: "#/$defs/ViscosityInput/properties/reference_viscosity_pa_s/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                          return false;
                                        }
                                      }
                                      var valid2 = _errs18 === errors;
                                    } else {
                                      var valid2 = true;
                                    }
                                    if (valid2) {
                                      if (data2.schema_version !== void 0) {
                                        let data8 = data2.schema_version;
                                        const _errs20 = errors;
                                        if (typeof data8 !== "string") {
                                          validate23.errors = [{ instancePath: instancePath + "/input_parameters/schema_version", schemaPath: "#/$defs/ViscosityInput/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                          return false;
                                        }
                                        if ("1" !== data8) {
                                          validate23.errors = [{ instancePath: instancePath + "/input_parameters/schema_version", schemaPath: "#/$defs/ViscosityInput/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                                          return false;
                                        }
                                        var valid2 = _errs20 === errors;
                                      } else {
                                        var valid2 = true;
                                      }
                                      if (valid2) {
                                        if (data2.temperature_c !== void 0) {
                                          let data9 = data2.temperature_c;
                                          const _errs22 = errors;
                                          if (errors === _errs22) {
                                            if (typeof data9 == "number" && isFinite(data9)) {
                                              if (data9 > 500 || isNaN(data9)) {
                                                validate23.errors = [{ instancePath: instancePath + "/input_parameters/temperature_c", schemaPath: "#/$defs/ViscosityInput/properties/temperature_c/maximum", keyword: "maximum", params: { comparison: "<=", limit: 500 }, message: "must be <= 500" }];
                                                return false;
                                              } else {
                                                if (data9 < -273.14 || isNaN(data9)) {
                                                  validate23.errors = [{ instancePath: instancePath + "/input_parameters/temperature_c", schemaPath: "#/$defs/ViscosityInput/properties/temperature_c/minimum", keyword: "minimum", params: { comparison: ">=", limit: -273.14 }, message: "must be >= -273.14" }];
                                                  return false;
                                                }
                                              }
                                            } else {
                                              validate23.errors = [{ instancePath: instancePath + "/input_parameters/temperature_c", schemaPath: "#/$defs/ViscosityInput/properties/temperature_c/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                              return false;
                                            }
                                          }
                                          var valid2 = _errs22 === errors;
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
                        }
                      } else {
                        validate23.errors = [{ instancePath: instancePath + "/input_parameters", schemaPath: "#/$defs/ViscosityInput/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
                        return false;
                      }
                    }
                    var valid0 = _errs6 === errors;
                  } else {
                    var valid0 = true;
                  }
                  if (valid0) {
                    if (data.limitation !== void 0) {
                      const _errs24 = errors;
                      if (typeof data.limitation !== "string") {
                        validate23.errors = [{ instancePath: instancePath + "/limitation", schemaPath: "#/properties/limitation/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                        return false;
                      }
                      var valid0 = _errs24 === errors;
                    } else {
                      var valid0 = true;
                    }
                    if (valid0) {
                      if (data.procedure !== void 0) {
                        let data11 = data.procedure;
                        const _errs26 = errors;
                        if (errors === _errs26) {
                          if (Array.isArray(data11)) {
                            var valid3 = true;
                            const len0 = data11.length;
                            for (let i0 = 0; i0 < len0; i0++) {
                              const _errs28 = errors;
                              if (typeof data11[i0] !== "string") {
                                validate23.errors = [{ instancePath: instancePath + "/procedure/" + i0, schemaPath: "#/properties/procedure/items/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              var valid3 = _errs28 === errors;
                              if (!valid3) {
                                break;
                              }
                            }
                          } else {
                            validate23.errors = [{ instancePath: instancePath + "/procedure", schemaPath: "#/properties/procedure/type", keyword: "type", params: { type: "array" }, message: "must be array" }];
                            return false;
                          }
                        }
                        var valid0 = _errs26 === errors;
                      } else {
                        var valid0 = true;
                      }
                      if (valid0) {
                        if (data.reference_temperature_k !== void 0) {
                          let data13 = data.reference_temperature_k;
                          const _errs30 = errors;
                          if (!(typeof data13 == "number" && isFinite(data13))) {
                            validate23.errors = [{ instancePath: instancePath + "/reference_temperature_k", schemaPath: "#/properties/reference_temperature_k/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                            return false;
                          }
                          var valid0 = _errs30 === errors;
                        } else {
                          var valid0 = true;
                        }
                        if (valid0) {
                          if (data.schema_version !== void 0) {
                            let data14 = data.schema_version;
                            const _errs32 = errors;
                            if (typeof data14 !== "string") {
                              validate23.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                              return false;
                            }
                            if ("1" !== data14) {
                              validate23.errors = [{ instancePath: instancePath + "/schema_version", schemaPath: "#/properties/schema_version/const", keyword: "const", params: { allowedValue: "1" }, message: "must be equal to constant" }];
                              return false;
                            }
                            var valid0 = _errs32 === errors;
                          } else {
                            var valid0 = true;
                          }
                          if (valid0) {
                            if (data.scientific_status !== void 0) {
                              let data15 = data.scientific_status;
                              const _errs34 = errors;
                              if (typeof data15 !== "string") {
                                validate23.errors = [{ instancePath: instancePath + "/scientific_status", schemaPath: "#/properties/scientific_status/type", keyword: "type", params: { type: "string" }, message: "must be string" }];
                                return false;
                              }
                              if ("unvalidated_screen" !== data15) {
                                validate23.errors = [{ instancePath: instancePath + "/scientific_status", schemaPath: "#/properties/scientific_status/const", keyword: "const", params: { allowedValue: "unvalidated_screen" }, message: "must be equal to constant" }];
                                return false;
                              }
                              var valid0 = _errs34 === errors;
                            } else {
                              var valid0 = true;
                            }
                            if (valid0) {
                              if (data.temperature_k !== void 0) {
                                let data16 = data.temperature_k;
                                const _errs36 = errors;
                                if (!(typeof data16 == "number" && isFinite(data16))) {
                                  validate23.errors = [{ instancePath: instancePath + "/temperature_k", schemaPath: "#/properties/temperature_k/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                  return false;
                                }
                                var valid0 = _errs36 === errors;
                              } else {
                                var valid0 = true;
                              }
                              if (valid0) {
                                if (data.viscosity_pa_s !== void 0) {
                                  let data17 = data.viscosity_pa_s;
                                  const _errs38 = errors;
                                  if (!(typeof data17 == "number" && isFinite(data17))) {
                                    validate23.errors = [{ instancePath: instancePath + "/viscosity_pa_s", schemaPath: "#/properties/viscosity_pa_s/type", keyword: "type", params: { type: "number" }, message: "must be number" }];
                                    return false;
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
        } else {
          validate23.errors = [{ instancePath, schemaPath: "#/type", keyword: "type", params: { type: "object" }, message: "must be object" }];
          return false;
        }
      }
      validate23.errors = vErrors;
      return errors === 0;
    }
    validate23.evaluated = { "props": true, "dynamicProps": false, "dynamicItems": false };
  }
});
export default require_reviewed_validators();
