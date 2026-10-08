// Generated from exact public schema snapshots.
export const scientificSchemas = {
  "materials.hansen-solvency.output": {
    "sha256": "fa0575e5ef90f2b414bd0cf8522855ff09875649ec9db03d0bbb0d87682de711",
    "schema": {
      "$defs": {
        "Point": {
          "additionalProperties": false,
          "properties": {
            "dispersion": {
              "maximum": 1000000,
              "minimum": 0,
              "title": "Dispersion",
              "type": "number"
            },
            "hydrogen_bond": {
              "maximum": 1000000,
              "minimum": 0,
              "title": "Hydrogen Bond",
              "type": "number"
            },
            "polar": {
              "maximum": 1000000,
              "minimum": 0,
              "title": "Polar",
              "type": "number"
            }
          },
          "required": [
            "dispersion",
            "polar",
            "hydrogen_bond"
          ],
          "title": "Point",
          "type": "object"
        },
        "SolvencyInput": {
          "additionalProperties": false,
          "properties": {
            "candidate_id": {
              "maxLength": 128,
              "minLength": 1,
              "title": "Candidate Id",
              "type": "string"
            },
            "interaction_radius": {
              "exclusiveMinimum": 0,
              "maximum": 1000000,
              "title": "Interaction Radius",
              "type": "number"
            },
            "parameter_context": {
              "maxLength": 2048,
              "minLength": 1,
              "title": "Parameter Context",
              "type": "string"
            },
            "polymer": {
              "$ref": "#/$defs/Point"
            },
            "schema_version": {
              "const": "1",
              "default": "1",
              "title": "Schema Version",
              "type": "string"
            },
            "solvent": {
              "$ref": "#/$defs/Point"
            }
          },
          "required": [
            "candidate_id",
            "parameter_context",
            "polymer",
            "solvent",
            "interaction_radius"
          ],
          "title": "SolvencyInput",
          "type": "object"
        }
      },
      "additionalProperties": false,
      "properties": {
        "candidate_id": {
          "title": "Candidate Id",
          "type": "string"
        },
        "distance": {
          "title": "Distance",
          "type": "number"
        },
        "distance_squared": {
          "title": "Distance Squared",
          "type": "number"
        },
        "input_parameters": {
          "$ref": "#/$defs/SolvencyInput"
        },
        "limitation": {
          "title": "Limitation",
          "type": "string"
        },
        "procedure": {
          "items": {
            "type": "string"
          },
          "title": "Procedure",
          "type": "array"
        },
        "relative_energy_difference": {
          "title": "Relative Energy Difference",
          "type": "number"
        },
        "schema_version": {
          "const": "1",
          "default": "1",
          "title": "Schema Version",
          "type": "string"
        },
        "scientific_status": {
          "const": "unvalidated_screen",
          "default": "unvalidated_screen",
          "title": "Scientific Status",
          "type": "string"
        },
        "sphere_position": {
          "enum": [
            "inside",
            "boundary",
            "outside"
          ],
          "title": "Sphere Position",
          "type": "string"
        }
      },
      "required": [
        "candidate_id",
        "input_parameters",
        "distance_squared",
        "distance",
        "relative_energy_difference",
        "sphere_position",
        "procedure",
        "limitation"
      ],
      "title": "SolvencyOutput",
      "type": "object"
    }
  },
  "materials.arrhenius-viscosity.output": {
    "sha256": "a52eec59df1fc594d63c3c1e4323d83ad36a74db26d481f833504db18b97760c",
    "schema": {
      "$defs": {
        "ViscosityInput": {
          "additionalProperties": false,
          "properties": {
            "activation_energy_j_mol": {
              "exclusiveMinimum": 0,
              "maximum": 1e+100,
              "title": "Activation Energy J Mol",
              "type": "number"
            },
            "candidate_id": {
              "maxLength": 128,
              "minLength": 1,
              "title": "Candidate Id",
              "type": "string"
            },
            "parameter_context": {
              "maxLength": 2048,
              "minLength": 1,
              "title": "Parameter Context",
              "type": "string"
            },
            "reference_temperature_c": {
              "maximum": 500,
              "minimum": -273.14,
              "title": "Reference Temperature C",
              "type": "number"
            },
            "reference_viscosity_pa_s": {
              "exclusiveMinimum": 0,
              "maximum": 1e+100,
              "title": "Reference Viscosity Pa S",
              "type": "number"
            },
            "schema_version": {
              "const": "1",
              "default": "1",
              "title": "Schema Version",
              "type": "string"
            },
            "temperature_c": {
              "maximum": 500,
              "minimum": -273.14,
              "title": "Temperature C",
              "type": "number"
            }
          },
          "required": [
            "candidate_id",
            "parameter_context",
            "reference_viscosity_pa_s",
            "reference_temperature_c",
            "temperature_c",
            "activation_energy_j_mol"
          ],
          "title": "ViscosityInput",
          "type": "object"
        }
      },
      "additionalProperties": false,
      "properties": {
        "candidate_id": {
          "title": "Candidate Id",
          "type": "string"
        },
        "exponent": {
          "title": "Exponent",
          "type": "number"
        },
        "input_parameters": {
          "$ref": "#/$defs/ViscosityInput"
        },
        "limitation": {
          "title": "Limitation",
          "type": "string"
        },
        "procedure": {
          "items": {
            "type": "string"
          },
          "title": "Procedure",
          "type": "array"
        },
        "reference_temperature_k": {
          "title": "Reference Temperature K",
          "type": "number"
        },
        "schema_version": {
          "const": "1",
          "default": "1",
          "title": "Schema Version",
          "type": "string"
        },
        "scientific_status": {
          "const": "unvalidated_screen",
          "default": "unvalidated_screen",
          "title": "Scientific Status",
          "type": "string"
        },
        "temperature_k": {
          "title": "Temperature K",
          "type": "number"
        },
        "viscosity_pa_s": {
          "title": "Viscosity Pa S",
          "type": "number"
        }
      },
      "required": [
        "candidate_id",
        "input_parameters",
        "reference_temperature_k",
        "temperature_k",
        "exponent",
        "viscosity_pa_s",
        "procedure",
        "limitation"
      ],
      "title": "ViscosityOutput",
      "type": "object"
    }
  }
} as const;
