/** Parse human numeric text before binary64 conversion loses evidence of underflow. */
export function numericInput(text: string, kind: "integer" | "number"): number {
  const value = text.trim();
  if (value.length > 512 || !/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(value)) throw new Error("Enter a decimal number.");
  const number = Number(value);
  if (!Number.isFinite(number)) throw new Error("Number exceeds the supported range.");
  if (number === 0 && /[1-9]/.test(value.split(/[eE]/)[0]!)) throw new Error("Number is too small to retain without becoming zero.");
  if (kind === "integer" && !Number.isSafeInteger(number)) throw new Error("Enter a whole number within the safe integer range.");
  // A fractional decimal can round to an integer. Integer input must not accept that loss.
  if (kind === "integer") {
    const [mantissa, exponentText = "0"] = value.split(/[eE]/);
    const unsigned = mantissa!.replace(/^-/, ""), [whole = "", fraction = ""] = unsigned.split(".");
    const digits = whole + fraction, exponent = Number(exponentText);
    const decimalPlaces = fraction.length - exponent;
    if (decimalPlaces > 0 && /[1-9]/.test(digits.slice(Math.max(0, digits.length - decimalPlaces))))
      throw new Error("Enter an exact whole number.");
  }
  return number === 0 ? 0 : number;
}
