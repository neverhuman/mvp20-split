import base64
import hashlib
import io
import json
import pytest
from PIL import Image
from amphora_chemical_structure.kernel import compute
from amphora_chemical_structure.profile import DerivationProfile
from amphora_chemical_structure.metadata import descriptor, schema_bytes
from amphora_contracts_chemical_structure import StructureResult


def payload(smiles):
    scope={"tenant_id":"internal","project_id":"test"}
    return json.dumps(dict(wire_version="1",scope=scope,candidate=dict(scope=scope,candidate_id="supplied",revision=1),semantic_profile=DerivationProfile.load().reference.model_dump(),origin="supplied",representation_kind="finite_molecule",smiles=smiles)).encode()

def derive(smiles):
    return StructureResult.model_validate_json(compute(payload(smiles)))

@pytest.mark.parametrize("smiles,formula,atoms,charge",[
    ("OCCO","C2H6O2",4,0),
    ("OCCOCCO","C4H10O3",7,0),
    ("c1ccccc1","C6H6",6,0),
    ("[NH4+]","H4N+",1,1),
    ("[Cl-]","Cl-",1,-1),
    ("[13CH4]","[13C]H4",1,0),
    ("[2H]O[2H]","[2H]2O",3,0),
    ("[H]O[H]","H2O",3,0),
])
def test_independently_known_formula_and_atom_counts(smiles,formula,atoms,charge):
    result=derive(smiles); out=result.outcome
    assert out.status=="derived",out
    assert out.formula.text==formula
    assert len(out.graph.atoms)==atoms
    assert out.formula.net_formal_charge==charge
    assert result.source_sha256==hashlib.sha256(payload(smiles)).hexdigest()
    assert result.candidate.candidate_id=="supplied" and result.candidate.revision==1


def test_png_is_bounded_inert_and_matches_hash():
    depiction=derive("OCCOCCO").outcome.depiction
    raw=base64.b64decode(depiction.png_base64,validate=True)
    assert len(raw)<=131072
    assert hashlib.sha256(raw).hexdigest()==depiction.sha256
    with Image.open(io.BytesIO(raw)) as image:
        assert image.format=="PNG" and image.size==(800,600)
        assert not image.info
        image.verify()


def test_deterministic_result_and_exact_source_byte_attribution():
    raw=payload("CCO")
    assert compute(raw)==compute(raw)
    a=StructureResult.model_validate_json(compute(raw))
    b=StructureResult.model_validate_json(compute(b" "+raw))
    assert a.outcome==b.outcome and a.source_sha256!=b.source_sha256


def test_tetrahedral_stereo_and_isotope_preserved():
    a=derive("N[C@@H](C)C(=O)O").outcome
    b=derive("N[C@H](C)C(=O)O").outcome
    assert a.status==b.status=="derived"
    assert a.canonical_isomeric_smiles!=b.canonical_isomeric_smiles
    assert a.formula==b.formula and not a.warnings and not b.warnings
    assert "@" in a.canonical_isomeric_smiles
    assert any(x.isotope==13 for x in derive("[13CH4]").outcome.graph.atoms)


def test_double_bond_stereo_and_unspecified_warning():
    a=derive("F/C=C/F").outcome; b=derive("F/C=C\\F").outcome
    assert a.status==b.status=="derived"
    assert a.canonical_isomeric_smiles!=b.canonical_isomeric_smiles
    assert any(x.stereo!="STEREONONE" and len(x.stereo_atoms)==2 for x in a.graph.bonds)
    assert derive("FC=CF").outcome.warnings==["unspecified_stereochemistry"]
    assert derive("NC(C)C(=O)O").outcome.warnings==["unspecified_stereochemistry"]

@pytest.mark.parametrize("smiles",["C.C","[Na+].[Cl-]","C>>O","*CC*","{CC}","C |foo|","[CH3:1]O","[CH3]","C"*129,"[C@H](C)(C)O"])
def test_unsupported_never_contains_formula_or_depiction(smiles):
    outcome=derive(smiles).outcome
    assert outcome.status=="unsupported",outcome
    assert set(outcome.model_dump())=={"status","code"}

@pytest.mark.parametrize("smiles",["not-smiles","C1CC","C(C)(C)(C)(C)C"])
def test_invalid_smiles_safe_failure(smiles):
    assert derive(smiles).outcome.status=="invalid"


def test_wrong_profile_and_foreign_scope():
    data=json.loads(payload("CCO")); data["semantic_profile"]["sha256"]="0"*64
    assert StructureResult.model_validate_json(compute(json.dumps(data).encode())).outcome.code=="profile_mismatch"
    data["candidate"]["scope"]["project_id"]="foreign"
    with pytest.raises(ValueError,match="invalid_chemical_request"): compute(json.dumps(data).encode())

@pytest.mark.parametrize("raw",[b"x",b"{}",b"x"*262145],ids=["invalid-json","missing-envelope","oversize"])
def test_malformed_transport_has_safe_error(raw):
    with pytest.raises(ValueError,match="invalid_chemical_request"): compute(raw)


def test_descriptor_pins_public_schema_bytes():
    release=descriptor("a"*64)
    assert release.tool.binding.capability_id=="chemistry.chemical-structure"
    assert release.authority_ceiling=="evidence_proposal"
    assert release.tool.inputs[0].schema_ref.sha256==hashlib.sha256(schema_bytes("input")).hexdigest()
    assert release.tool.outputs[0].schema_ref.sha256==hashlib.sha256(schema_bytes("output")).hexdigest()


def test_duplicate_json_keys_rejected():
    raw=payload("CCO")
    duplicate=raw[:-1]+b', "smiles": "O"}'
    with pytest.raises(ValueError,match="invalid_chemical_request"): compute(duplicate)


def test_graph_references_are_internal_and_connected():
    result=derive("OCCOCCO").outcome
    indexes={a.index for a in result.graph.atoms}
    assert indexes==set(range(7))
    assert len(result.graph.bonds)==6
    assert all(b.begin in indexes and b.end in indexes for b in result.graph.bonds)
