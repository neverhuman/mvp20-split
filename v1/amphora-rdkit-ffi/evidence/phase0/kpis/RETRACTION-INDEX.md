# amphora-rdkit-ffi retraction index

| claim | refuted-by | superseded-by | date |
|---|---|---|---|
| W-FFI2 fire-1 fix: is_cyanamide_substituted_guanidine_carbon detects dicyandiamide by inspecting only the formally-double-bonded imine nitrogen (`amphora-rdkit-ffi/evidence/phase0/repairs/W-FFI2/attempts/w-ffi2-rdkit-ffi-cyanoguanidine-repair-receipt.v1.dsse.json`, sha256 f84176546fdc3dc6e1892b5bb34026b1ada2c214fd2fb945978305023bbb87e5) | W-FFI2 fire-2 tautomer-representation-invariance probe: 3 of 5 chemically-valid tautomer/atom-ordering SMILES for dicyandiamide (same molecule, formula C2H4N4) scored 0 active hydrogens instead of 4, reproducing the original W-FFI1 defect via representation choice alone | `amphora-rdkit-ffi/evidence/phase0/repairs/W-FFI2/attempts/w-ffi2-rdkit-ffi-tautomer-invariance-repair-receipt.v1.dsse.json` (sha256 2c20f4b464ccd091233eabccb5292bdb3b0a35f3be761100f57ac4a8484cb676) | 2026-08-06 |
