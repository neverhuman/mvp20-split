# Await wire and compatibility fixtures

`await_cases.json` contains three manually composed valid definitions (root await, scatter await, loop await) and eight invalid shape examples. They use the previously pinned numeric schemas as synthetic payload types and make no scientific claim.

`await_plan.json` is the independently specified expected plan for the root example: explicit node order/interfaces, empty tool lock, two exact schema pins and separate v3 definition/compiler/plan identities. It was constructed from the authored example and the public hash specification, without invoking the compiler.

`predecessor_schema_pins.json` preserves all 116 published schema hashes from commit `d33dab5`. The compatibility test compares each current file with these frozen hashes; new roots are additive. Existing manifests may add entries, but existing schema bytes may not change.

Contract tests own shape/publication proof; Runtime compiler tests own semantic/exact-plan proof. These examples do not prove external receipt acceptance, timeout races, retention delivery or scientific validity.
