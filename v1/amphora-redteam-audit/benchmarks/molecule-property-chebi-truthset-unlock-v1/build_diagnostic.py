#!/usr/bin/env python3
"""Deterministic AUDIT diagnostic builder for the molecule-property ChEBI truth-set
+ RDKit-backend unlock (2026-07-25). Recomputes every ChEBI-derived fact from the
hash-verified CC-BY-4.0 release so the two-replay SHA-256 gate is meaningful.
Writes the diagnostic to the path given as argv[1]. Promotes nothing."""
import gzip, sys, json, hashlib
from rdkit import Chem
from rdkit import RDLogger
RDLogger.DisableLog('rdApp.*')

ROOT = "."
SDF = "amphora-molecule-property/reference/chebi/rel252/chebi_3_stars.sdf.gz"
LIC = "amphora-molecule-property/reference/chebi/rel252/LICENSE.txt"
EXPECTED_PAYLOAD_SHA = "8f17627476c66e899dabe3cd7ae1cbb94f7ee6c67f2ee91f077a77a19c940ad7"
EXPECTED_LICENSE_SHA = "fe7b4ce83b8381cc5b216bbb4af73c570688d1b819c73bbaed8ca401f4677cd6"

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

epoxide   = Chem.MolFromSmarts("[C;R1]1[O;R1][C;R1]1")
prim_amine= Chem.MolFromSmarts("[NX3;H2;!$(NC=O);!$(N=*)]")
sec_amine = Chem.MolFromSmarts("[NX3;H1;!$(NC=O);!$(N=*);!$(N-a)]")

tot=parsed=single=defined=n_epoxide=n_amine=n_inscope=n_multi_ep=0
with gzip.open(SDF,'rb') as fh:
    for mol in Chem.ForwardSDMolSupplier(fh, sanitize=True, removeHs=True):
        tot+=1
        if mol is None: continue
        parsed+=1
        smi=Chem.MolToSmiles(mol)
        if '.' in smi: continue
        single+=1
        if '*' in smi: continue
        defined+=1
        has_ep=mol.HasSubstructMatch(epoxide)
        has_am=mol.HasSubstructMatch(prim_amine) or mol.HasSubstructMatch(sec_amine)
        if has_ep:
            n_epoxide+=1
            if len(mol.GetSubstructMatches(epoxide))>=2: n_multi_ep+=1
        if has_am: n_amine+=1
        if has_ep or has_am: n_inscope+=1

payload_sha=sha(SDF); license_sha=sha(LIC)

diag={
 "schema":"amphora.redteam-audit.molecule-property-chebi-truthset-unlock.v1",
 "study_id":"MOLECULE_PROPERTY_CHEBI_TRUTHSET_UNLOCK_V1",
 "authority":"AUDIT_ONLY",
 "promotes":False,
 "host":"canonical (xbabe2) /home/ubuntu/amphora/build/mvp20-split",
 "target_module":"amphora-molecule-property",
 "chebi_acquisition":{
   "source_id":"chebi_fixed_release_truth_set",
   "publisher":"EMBL-EBI ChEBI",
   "release_id":"ChEBI-252",
   "license":"CC BY 4.0",
   "download_url":"https://ftp.ebi.ac.uk/pub/databases/chebi/archive/rel252/SDF/chebi_3_stars.sdf.gz",
   "payload_sha256_observed":payload_sha,
   "payload_sha256_expected":EXPECTED_PAYLOAD_SHA,
   "payload_hash_matches_fetchlock":payload_sha==EXPECTED_PAYLOAD_SHA,
   "license_sha256_observed":license_sha,
   "license_sha256_expected":EXPECTED_LICENSE_SHA,
   "license_hash_matches_fetchlock":license_sha==EXPECTED_LICENSE_SHA,
 },
 "in_scope_reactive_molecule_census":{
   "definition":"single-component, RDKit-2026.03.2 parseable, no wildcard/polymer; in-scope = has oxirane epoxide OR non-amide/non-imine primary or secondary amine N-H",
   "smarts":{"epoxide":"[C;R1]1[O;R1][C;R1]1","primary_amine":"[NX3;H2;!$(NC=O);!$(N=*)]","secondary_amine":"[NX3;H1;!$(NC=O);!$(N=*);!$(N-a)]"},
   "total_records":tot,"rdkit_parsed":parsed,"single_component":single,
   "defined_no_wildcard":defined,"with_epoxide":n_epoxide,"epoxide_multi_ge2":n_multi_ep,
   "with_amine_NH":n_amine,"in_scope_epoxide_or_amine":n_inscope,
   "minimum_300_gate_reachable":n_inscope>=300,
   "margin_over_gate_x":round(n_inscope/300,1),
 },
 "rdkit_backend_unlock":{
   "note":"amphora-tui + amphora-phase0-reviewer rebuilt with --features rdkit against pinned RDKit C++ 2026.03.2; observed live via 'benchmark run --locked --module amphora-molecule-property'",
   "backend_available_before":False,
   "backend_available_after":True,
   "detected_version":"2026.03.2","exact_version_match":True,
   "gate_pinned_rdkit_2026_03_2_available_before":False,
   "gate_pinned_rdkit_2026_03_2_available_after":True,
   "live_max_abs_eew_ahew_error_g_per_eq":0.033799999999999386,
   "chemistry_gates_now_passing":["equivalent_weight_max_abs_error_at_most_0_5","reactive_group_counts_100_percent","structure_identity_and_mass_agree","invalid_and_out_of_domain_rejection_100_percent","all_exact_controls_executed"],
   "still_failing_gates":["minimum_300_truth_set_molecules","independent_reference_receipt_bound","sealed_controls_present"],
 },
 "honest_ceiling":"AUDIT_ONLY. No phase0 evaluation/review/promotion minted. No existing receipt or manifest modified. Raw ChEBI acquisition confers no derivative or promotion authority; the >=300 truth set still requires PubChem PUG-REST identity/formula/mass cross-check per selection_lock, an independent reference receipt, and sealed controls before any ceremony.",
}
open(sys.argv[1],'w').write(json.dumps(diag,indent=2,sort_keys=True))
print("wrote",sys.argv[1],"in_scope=",n_inscope,"payload_match=",payload_sha==EXPECTED_PAYLOAD_SHA)
