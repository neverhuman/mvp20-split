# Compiler public golden material

`numeric-release.json` is the public numeric-affine 0.2.0 descriptor with the actual BP-03 image identity, paired with exact published `input.json`/`output.json` bytes. Its descriptor and schema hashes must match the manually specified wire-v2 plan in `contracts/fixtures/v2/executable_cases.json`. These files are independent of compiler output; do not regenerate expected plans from a compiler under test.

The owning suite is `tests/compiler`. These local fixtures establish deterministic semantic behavior. Actual independently installed tool/Registry compatibility is a separate acceptance tier.
