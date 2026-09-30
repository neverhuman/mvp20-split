import { test } from "node:test";
import assert from "node:assert/strict";
import { numericInput } from "../../../src/page_models/design/scalar_input.js";

test("numeric form input preserves finite binary64 values and normalizes signed zero", () => {
  for (const [text, expected] of [["1", 1], [" 1.25 ", 1.25], ["1e20", 1e20], ["5e-324", 5e-324], ["-0.0e-9999", 0]] as const)
    assert.equal(numericInput(text, "number"), expected);
  for (const text of ["1e309", "-1e309", "1e-9999", "-1e-9999", "2e-324"])
    assert.throws(() => numericInput(text, "number"), /range|too small/);
});

test("numeric forms reject missing, nondecimal and oversized input", () => {
  for (const text of ["", " ", "NaN", "Infinity", "0x10", "+1", ".1", "01", "1,000", "1_000", "1." , "0".repeat(513)])
    assert.throws(() => numericInput(text, "number"), /decimal/);
});

test("integer fields reject fractions even when binary64 rounds them into an integer", () => {
  for (const text of ["1.00000000000000001", "9007199254740991.1", "1.2", "9007199254740992", "1e20"])
    assert.throws(() => numericInput(text, "integer"), /whole|safe integer/);
  for (const [text, expected] of [["1.0", 1], ["1.2e1", 12], ["1200e-2", 12], ["-9007199254740991", -9007199254740991], ["0e-9999", 0]] as const)
    assert.equal(numericInput(text, "integer"), expected);
});
