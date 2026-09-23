#!/usr/bin/env python3
"""network-tg-feasibility-v4 -- PROTOCOL-CURATION feasibility red-team.

AUDIT_ONLY red-team increment on the HIGHEST-value UNVALIDATED coating gap:
glass transition temperature of DGEBA + amine marine networks (target
amphora-molecule-property glass_transition capability). Promotes nothing,
touches no existing receipt/manifest, signs no Phase-0 evaluation/review.
All work on xbabe2 canonical host.

WHAT IS NEW vs v3 / crosslink-density-v1
----------------------------------------
v3 (signed) built the backbone-rigidity descriptor B (LOO Tg MAE 35.73 C) and
diagnosed that connectivity cannot encode the crosslink-functionality boost.
crosslink-density-v1 (signed) built the a-priori Flory crosslink strand density
n_x and showed the physically-correct 2-axis (B + n_x) model IN-SAMPLE explains
the residual structure but its LOO OVERFITS at n=7 (35.73 -> 48.96 C), concluding
the binding constraint is DATA QUANTITY (n>=12).

Both prior runs asserted "acquire n>=12 rights-clean points." THIS run tests
whether that is even sufficient, by asking the sharper question a founder needs
answered: *what kind* of data, and *can the >=25 C gate be met at all?*

NEW CONTRIBUTIONS (all deterministic, two-replay byte-stable):
 1. QUANTIFIED CURE-STATE PROTOCOL SENSITIVITY from page-verified CC-BY evidence
    gathered THIS run (MDPI Polymers 2023 15(4)990 = PMC9962791, CC BY): the SAME
    amine shifts 27-46 C between cure states (IPDA full-cure 158 vs cold-cure 112
    = 46 C; DDS post-cured ~208 vs the paper's hot-cure reference 181 = 27 C).
    These cold-cure values are recorded as EVIDENCE and are DELIBERATELY NOT
    merged into the protocol-consistent training set.
 2. GATE-FEASIBILITY PROOF: the G2 target (LOO MAE <= 25 C) sits BELOW the
    27-46 C cross-cure-state scatter of a single amine but ABOVE the ~8.6 C
    same-protocol inter-lab floor (DDS 220/200/204). => the <=25 C gate is
    achievable ONLY on a cure-controlled dataset; naive rights-clean aggregation
    across the open literature (which mixes cold-cure and post-cured networks)
    can NEVER satisfy it regardless of model quality. The wall is protocol-
    consistent CURATION, not raw data volume.
 3. A leverage-based DATA-REQUIREMENT estimate translating "n>=12" into the OLS
    prediction-variance de-leveraging gained from n=7 -> 12 -> 20.
 4. An honest DATA-ACQUISITION LOG of every rights-clean source tried this run
    and the exact reason each was rejected (protocol mismatch / non-discrete
    hardener / paywall / robots-403).

HONESTY POSTURE: no promotion; n=7 unique protocol-consistent systems is
UNCHANGED (0 new merged points); B and n_x are non-circular (measured Tg is
never a feature); every number is deterministic and two-replay byte-stable.
"""
import hashlib, itertools, json, math, sys
from rdkit import Chem
from rdkit.Chem import Descriptors
import numpy as np


def rnd(x, n=6):
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return None
        return round(x, n)
    if isinstance(x, dict):
        return {k: rnd(v, n) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [rnd(v, n) for v in x]
    return x


DGEBA = "CC(C)(c1ccc(OCC2CO2)cc1)c1ccc(OCC2CO2)cc1"
_dg = Chem.MolFromSmiles(DGEBA)
EEW = round(Descriptors.MolWt(_dg) / 2.0, 4)
M_DGEBA = round(Descriptors.MolWt(_dg), 4)

# ---- protocol-consistent rights-clean measurements (identical provenance to signed v3/xlink-v1) ----
# "stoichiometric full cure" networks only. fields:
# amine, smiles, Tg_C, source_id, citation, license, method, cure, amine_class, active_amine_H
RAW = [
 ("IPDA","NCC1(C)CC(N)CC(C)(C)C1",158,"S1","May 1988 Ch.6 p.209","individual-fact-CC0","DSC","stoichiometric full cure","cycloaliphatic",4),
 ("m-XDA","NCc1cccc(CN)c1",100,"S1","May 1988 Ch.6 p.210","individual-fact-CC0","DSC","stoichiometric full cure","araliphatic",4),
 ("DDS","Nc1ccc(S(=O)(=O)c2ccc(N)cc2)cc1",220,"S1","May 1988 Ch.6 p.208","individual-fact-CC0","DSC","stoichiometric full cure","aromatic",4),
 ("TETA","NCCNCCNCCN",120,"S1","May 1988 Ch.6","individual-fact-CC0","DSC","stoichiometric full cure","aliphatic",6),
 ("DETA","NCCNCCN",115,"S1","May 1988 Ch.6","individual-fact-CC0","DSC","stoichiometric full cure","aliphatic",5),
 ("DDS","Nc1ccc(S(=O)(=O)c2ccc(N)cc2)cc1",200,"S2","Polymers 2024 16(1)67 doi:10.3390/polym16010067 (EP-DDS pristine)","CC-BY-4.0","DSC 10C/min N2","150C/2h+180C/3h","aromatic",4),
 ("1,3-BAC","NCC1CCCC(CN)C1",97,"S2","Polymers 2024 16(1)67 (EP-CYDM pristine)","CC-BY-4.0","DSC 10C/min N2","70C/4h+130C/2h+150C/1h","cycloaliphatic",4),
 ("C8DA","NCCCCCCCCN",94,"S2","Polymers 2024 16(1)67 (EP-8CH2DA pristine)","CC-BY-4.0","DSC 10C/min N2","70C/4h+130C/2h+150C/1h","aliphatic",4),
 ("DDS","Nc1ccc(S(=O)(=O)c2ccc(N)cc2)cc1",204,"S3","Savonnet 2018 ACS SusChemEng 6 / arXiv:1911.08960 Tab.1","individual-fact","DSC","stoichiometric full cure","aromatic",4),
]

# ---- NEW page-verified CC-BY cross-protocol EVIDENCE, DELIBERATELY NOT MERGED ----
# Source: Kraslawski et al., "Synthesis, Curing and Thermal Behavior of Amine
# Hardeners from Potentially Renewable Sources", Polymers 2023, 15(4), 990;
# doi:10.3390/polym15040990; open-access CC BY; hosted PMC9962791. Read from the
# PMC full-text page THIS run. Reference-hardener Tg, DGEBA, DSC 10 K/min.
# These are LOWER-cure-state references than the fully post-cured S1/S2/S3 set:
# the paper's OWN IPDA (112 C) and DDS (181 C) references disagree with the fully
# post-cured literature by 27-46 C, which is exactly the confound this run
# quantifies. Recorded as evidence; NOT used as training rows.
PROTOCOL_EVIDENCE = [
 {"amine":"IPDA","Tg_C_cold_cure":112,"cure_state":"cold-cure reference",
  "source":"Polymers 2023 15(4)990 (PMC9962791) Table 1","license":"CC-BY-4.0","dsc":"10 K/min"},
 {"amine":"DDS","Tg_C_this_paper":181,"cure_state":"hot-cure reference",
  "source":"Polymers 2023 15(4)990 (PMC9962791) Table 1","license":"CC-BY-4.0","dsc":"10 K/min"},
]

# ---------------- descriptors (non-circular; measured Tg never a feature) ----------------
def reactive_N(mol):
    return [a.GetIdx() for a in mol.GetAtoms() if a.GetSymbol()=="N" and a.GetTotalNumHs()>0]

def _bond_rigid_binary(b):
    return 1.0 if (b.GetIsAromatic() or b.IsInRing() or b.GetBondTypeAsDouble()>1.0) else 0.0

def backbone_rigidity(smiles):
    mol=Chem.MolFromSmiles(smiles); Ns=reactive_N(mol); fr=[]
    for i,j in itertools.combinations(Ns,2):
        path=Chem.GetShortestPath(mol,i,j); num=0.0; den=0
        for k in range(len(path)-1):
            b=mol.GetBondBetweenAtoms(path[k],path[k+1]); num+=_bond_rigid_binary(b); den+=1
        if den>0: fr.append(num/den)
    return float(np.mean(fr)) if fr else 0.0

def crosslink_nx(smiles):
    """Flory perfect-network crosslink strand density n_x [mol/kg], a-priori,
    density-free -- identical formula to signed network-crosslink-density-v1.
    Every reactive amine N (>=1 H) is an f=3 junction after full stoichiometric
    cure with difunctional DGEBA: strands per amine = 1.5*n_N; repeat mass =
    M_amine + (n_NH/2)*M_DGEBA."""
    mol=Chem.MolFromSmiles(smiles)
    n_NH=sum(a.GetTotalNumHs() for a in mol.GetAtoms() if a.GetSymbol()=="N" and a.GetTotalNumHs()>0)
    n_N =sum(1 for a in mol.GetAtoms() if a.GetSymbol()=="N" and a.GetTotalNumHs()>0)
    M_amine=Descriptors.MolWt(mol)
    repeat_mass=M_amine+(n_NH/2.0)*M_DGEBA
    nu=1.5*n_N
    return 1000.0*nu/repeat_mass

# ---------------- consensus (unique-7, protocol-consistent) ----------------
systems={}
for amine,smi,tg,sid,cit,lic,meth,cure,cls,fh in RAW:
    systems.setdefault(amine,{"smiles":smi,"class":cls,"tgs":[],"aH":fh})
    systems[amine]["tgs"].append(tg)

uniq=[]
for amine,d in sorted(systems.items()):
    tg=float(np.mean(d["tgs"]))
    uniq.append({
        "amine":amine,"system":f"DGEBA+{amine}","amine_class":d["class"],
        "n_measurements":len(d["tgs"]),"tg_values_C":d["tgs"],
        "Tg_consensus_C":round(tg,4),
        "B_backbone":round(backbone_rigidity(d["smiles"]),6),
        "n_x_mol_per_kg":round(crosslink_nx(d["smiles"]),6),
        "active_amine_H":d["aH"],
    })
uniq.sort(key=lambda r:r["amine"])
y=np.array([r["Tg_consensus_C"] for r in uniq])
B=np.array([r["B_backbone"] for r in uniq])
NX=np.array([r["n_x_mol_per_kg"] for r in uniq])
n=len(y)

# ---------------- 1-desc and 2-desc LOO (reproduces v3 35.73 and xlink 48.96) ----------------
def loo(cols):
    X=np.column_stack([np.ones(n)]+[c for c in cols]); errs=[]
    for t in range(n):
        m=np.ones(n,bool); m[t]=False
        beta,_,_,_=np.linalg.lstsq(X[m],y[m],rcond=None)
        errs.append(float(X[t]@beta)-y[t])
    errs=np.array(errs)
    return {"n_params":X.shape[1],"loo_mae_C":round(float(np.mean(np.abs(errs))),6),
            "loo_rmse_C":round(float(np.sqrt(np.mean(errs**2))),6)}

def insample(cols):
    X=np.column_stack([np.ones(n)]+[c for c in cols])
    beta,_,_,_=np.linalg.lstsq(X,y,rcond=None)
    pred=X@beta; res=pred-y; p=X.shape[1]
    ss_res=float(np.sum(res**2)); ss_tot=float(np.sum((y-np.mean(y))**2))
    dof=max(n-p,1)
    return {"n_params":p,"insample_rmse_C":round(float(np.sqrt(np.mean(res**2))),6),
            "insample_r2":round(1.0-ss_res/ss_tot,6),
            "unbiased_sigma_C":round(float(np.sqrt(ss_res/dof)),6),
            "coefficients":[round(float(b),6) for b in beta]}

loo_B    = loo([B])
loo_nx   = loo([NX])
loo_Bnx  = loo([B,NX])
ins_Bnx  = insample([B,NX])
null_loo = round(float(np.mean([abs(t-np.mean(np.delete(y,i))) for i,t in enumerate(y)])),6)

# ---------------- cure-state protocol sensitivity (the NEW quantified confound) ----------------
dds_full = [r for r in RAW if r[0]=="DDS"]            # 220,200,204 -> same-protocol scatter
dds_vals = [r[2] for r in dds_full]
dds_mean = float(np.mean(dds_vals))
same_protocol_std = float(np.std(dds_vals))           # population std (matches v3's 8.64)
same_protocol_range = float(max(dds_vals)-min(dds_vals))
ipda_full = 158.0
ipda_cold = 112.0
dds_this_paper = 181.0
protocol_sensitivity = {
 "same_protocol_inter_lab_floor_C":{
   "system":"DGEBA+DDS post-cured","measurements":dds_vals,"mean_C":round(dds_mean,4),
   "population_std_C":round(same_protocol_std,4),"range_C":round(same_protocol_range,4),
   "reading":"fully-post-cured DDS across 3 independent labs scatters ~8.6 C (std) / 20 C "
             "(range): this is the irreducible SAME-PROTOCOL Tg noise floor."},
 "cross_protocol_scatter_same_amine_C":{
   "IPDA_fullcure_minus_coldcure":round(ipda_full-ipda_cold,4),
   "DDS_postcure_consensus_minus_thispaper":round(dds_mean-dds_this_paper,4),
   "evidence_ids":["Polymers 2023 15(4)990 PMC9962791 (CC BY): IPDA 112 C, DDS 181 C",
                   "post-cured set: IPDA 158 C (May 1988), DDS consensus 208 C (S1/S2/S3)"],
   "reading":"the SAME amine shifts 27-46 C purely from cure state (cold/hot reference vs "
             "full post-cure). Cure state, not chemistry, dominates at this magnitude."},
}

# ---------------- gate feasibility (the decision-relevant conclusion) ----------------
G2_target=25.0
gate_feasibility={
 "G2_target_loo_mae_C":G2_target,
 "same_protocol_floor_C":round(same_protocol_std,4),
 "cross_protocol_scatter_C_range":[round(dds_mean-dds_this_paper,4),round(ipda_full-ipda_cold,4)],
 "G2_below_same_protocol_floor":bool(G2_target>same_protocol_std),
 "G2_below_cross_protocol_scatter":bool(G2_target < (ipda_full-ipda_cold)),
 "conclusion":("The <=25 C G2 gate lies ABOVE the ~8.6 C same-protocol inter-lab floor "
   "(=> achievable in principle) but BELOW the 27-46 C cross-cure-state scatter of a single "
   "amine (=> UNACHIEVABLE on any dataset that mixes cure states). Therefore the network-Tg "
   "Phase-0 KPI is gated on protocol-CONSISTENT curation, not merely on rights-clean data "
   "VOLUME: a model trained on protocol-mixed open-literature Tg cannot reach <=25 C no matter "
   "how good it is, because the LABELS themselves disagree by more than the gate."),
}

# ---------------- data-requirement (leverage de-leveraging) ----------------
def mean_leverage_inflation(nn,p):
    # OLS: mean hat-diagonal = p/nn; LOO residual = e_i/(1-h_ii); at mean leverage the
    # prediction-error inflation vs in-sample sigma is 1/sqrt(1 - p/nn).
    h=p/nn
    return round(float(1.0/math.sqrt(max(1e-9,1.0-h))),4) if h<1 else None
p2=3  # intercept + B + n_x
data_requirement={
 "model":"2-descriptor OLS (intercept + B + n_x), p=3, the minimum the governing physics needs",
 "insample_2desc_rmse_C":ins_Bnx["insample_rmse_C"],
 "insample_2desc_r2":ins_Bnx["insample_r2"],
 "unbiased_sigma_2desc_C":ins_Bnx["unbiased_sigma_C"],
 "mean_leverage_prediction_inflation_vs_sigma":{
   "n=7":mean_leverage_inflation(7,p2),"n=12":mean_leverage_inflation(12,p2),
   "n=20":mean_leverage_inflation(20,p2),"n=30":mean_leverage_inflation(30,p2)},
 "two_binding_constraints":{
   "C1_leverage_data_scarcity":("At n=7 the 3-param model burns 43% of its DoF on leverage "
     "(mean hat=0.43), inflating held-out error ~1.32x over the in-sample sigma -- which is why "
     "the 2-axis LOO (48.96 C) is WORSE than the 1-axis LOO (35.73 C) even though the 2-axis "
     "IN-SAMPLE fit is tighter than the 1-axis in-sample fit. By n>=12 the inflation falls to "
     "~1.15x and by n>=20 to ~1.08x, so n>=12 (G1) is the minimum for a LOO that reflects model "
     "SKILL rather than leverage."),
   "C2_model_structural_error":("HONEST CEILING: the linear B+n_x in-sample RMSE is already "
     "{:.1f} C (R2 {:.2f}) at n=7 -- essentially AT the <=25 C gate. More protocol-consistent "
     "data DE-LEVERAGES the LOO but cannot push a LINEAR 2-descriptor model below its own "
     "~26 C in-sample structural error, which is dominated by systems a linear B+n_x cannot "
     "encode: the DDS aromatic-sulfone rigidity (under-fit) and the IPDA gem-dimethyl STERIC "
     "boost (v3's diagnosed missing axis). So crossing <=25 C requires a steric/side-group "
     "descriptor OR a nonlinear model IN ADDITION to more data.").format(
       ins_Bnx["insample_rmse_C"],ins_Bnx["insample_r2"])},
 "reading":("The <=25 C gate is co-gated: (C1) a protocol-controlled set of n>=12 (ideally ~20) "
   "to make the LOO trustworthy, AND (C2) a third steric/side-group descriptor (or nonlinearity) "
   "to lower the ~26 C linear-model structural floor. Neither alone suffices."),
}

# ---------------- honest data-acquisition log (this run's real attempts) ----------------
acquisition_log={
 "new_protocol_consistent_points_merged_this_run":0,
 "attempts":[
  {"source":"Polymers 2023 15(4)990 (PMC9962791)","license":"CC-BY-4.0","fetched":True,
   "outcome":"EVIDENCE_NOT_MERGED",
   "reason":"DGEBA + amines but cold/hot-cure reference Tg (IPDA 112, DDS 181) disagree with the "
            "fully-post-cured training set by 27-46 C -> merging would inject a cure-state bias "
            "larger than the G2 gate. Used to QUANTIFY the confound instead."},
  {"source":"PMC7023579 'Extender Particle Size ... Model Epoxy Coatings'","license":"CC-BY","fetched":True,
   "outcome":"REJECTED",
   "reason":"cures a bisphenol-A epoxy with a phenalkamine (cardanol-based NON-DISCRETE mixture) "
            "-> no single-molecule SMILES -> no computable a-priori descriptor."},
  {"source":"PMC9607094 'l-Arginine as a Bio-Based Curing Agent'","license":"CC-BY","fetched":True,
   "outcome":"REJECTED",
   "reason":"reported Tg values (52.9/100.4/96.8) are Tg0 of fresh/uncured or accelerator-only "
            "mixtures, not the fully-cured network Tg the model targets."},
  {"source":"mdpi.com direct article HTML","license":"CC-BY","fetched":False,
   "outcome":"INACCESSIBLE","reason":"HTTP 403 to automated fetch (publisher bot block); PMC "
            "mirror used where an open-access copy exists."},
  {"source":"IJPS 10.1155/2019/9604714 (DGEBA-EDA)","license":"unknown","fetched":False,
   "outcome":"INACCESSIBLE","reason":"HTTP 402 paywall to automated fetch."},
  {"source":"arXiv:1911.08960 (Savonnet divanillin)","license":"arXiv","fetched":"partial",
   "outcome":"NOT_ADDED","reason":"PDF stream unparseable via fetch; its DDS reference (204 C) is "
            "already in the set as S3; its novel divanillin diamines are exotic bio-based "
            "structures outside marine-coating scope and carry SMILES-verification risk."},
 ],
 "standard":"a Tg value is merged ONLY if it is (a) rights-clean, (b) page-verified from a "
            "fetchable source, (c) a fully-cured stoichiometric DGEBA+DISCRETE-amine network, and "
            "(d) protocol-consistent (single declared cure state) with the existing set.",
}

# ---------------- live phase-0 reconciliation (governance-only; 0/29 VALIDATED) ----------------
mm=json.loads(open("module-manifest.json").read())
mods=mm["modules"]
sci=[m.get("scientific_readiness") for m in mods]
try:
    p0=json.loads(open("config/program/phase0-decision-report.v2.json").read())
    p0mods=p0.get("modules",[])
    phase_counts={}
    for m in p0mods:
        ph=m.get("phase"); phase_counts[ph]=phase_counts.get(ph,0)+1
    phase0_target={}
    for m in p0mods:
        if m.get("phase")=="PHASE_0":
            t=m.get("target_status"); phase0_target[t]=phase0_target.get(t,0)+1
except Exception as e:
    phase_counts={"error":str(e)}; phase0_target={}
phase0_recon={
 "n_modules":len(mods),
 "n_scientific_readiness_VALIDATED":sum(1 for s in sci if s=="VALIDATED"),
 "scientific_readiness_distribution":{v:sci.count(v) for v in sorted(set(sci))},
 "phase0_decision_report_phase_distribution":phase_counts,
 "phase0_modules_target_status_distribution":phase0_target,
 "finding":("0 of 29 modules are scientific_readiness=VALIDATED. The 10 modules the decision "
   "report labels PHASE_0 are governance/engineering completions: 7 target_status=NOT_APPLICABLE "
   "(deterministic-control/infra) and 3 LOCKED_INTERNAL (solvency, process-qc-twin, tolerance-"
   "robustness) -- none are externally-validated predictive science. 'FULL Phase-0' is a "
   "governance milestone, NOT a count of validated scientific capabilities. Founder skepticism "
   "is correct. network-Tg remains the highest-value scientific gap and is NOT closed by this run."),
}

# ---------------- verdict ----------------
verdict=("PROTOCOL_CURATION_AND_MODEL_CO_LIMITED (NOT a Phase-0 promotion). This run sharpens the "
 "prior 'just acquire n>=12' framing into TWO quantified, decision-relevant findings. FINDING 1 "
 "(new, from page-verified CC-BY evidence): the SAME amine's Tg shifts 27-46 C purely with cure "
 "state (IPDA full 158 vs cold 112; DDS post-cured 208 vs hot-cure ref 181) -- LARGER than the "
 "<=25 C G2 gate. The gate sits ABOVE the ~8.6 C same-protocol inter-lab floor but BELOW the "
 "27-46 C cross-cure-state scatter, so the network-Tg KPI is achievable ONLY on a protocol-"
 "CONTROLLED rights-clean dataset; naive aggregation of open-literature Tg (which mixes cure "
 "states) can never reach it. FINDING 2 (honest ceiling): the two governing non-circular "
 "descriptors B (1-axis LOO {:.2f} C) and Flory n_x are in hand, but their LINEAR combination "
 "already has ~26 C in-sample RMSE (R2 0.55) at n=7 -- so more data DE-LEVERAGES the LOO yet "
 "cannot cross <=25 C without a steric/side-group descriptor (IPDA gem-dimethyl; DDS sulfone) or "
 "a nonlinear model. Concrete spec to close the gap: (a) >=5 additional fully-post-cured DGEBA + "
 "DISCRETE-amine Tg points under ONE declared cure protocol + ONE DSC rate (n>=12, ideally ~20), "
 "AND (b) a third steric descriptor. 0 new points merged this run -- all fetchable rights-clean "
 "candidates failed protocol/discreteness/access screens (logged). Founder takeaway: network-Tg "
 "is the highest-value gap, its physics is understood, and it is blocked by protocol-consistent "
 "data curation PLUS one more descriptor, NOT by governance."
 ).format(loo_B["loo_mae_C"])

diag={
 "schema":"amphora.redteam-audit.network-tg-feasibility-v4.diagnostic.v1",
 "authority":"AUDIT_ONLY",
 "target_module":"amphora-molecule-property",
 "target_capability":"glass_transition_temperature_of_DGEBA_amine_networks",
 "target_kpi_id":"network-tg-protocol-curation-feasibility-v4",
 "predecessor":"network-tg-feasibility-v3 + network-crosslink-density-v1 (both signed; untouched)",
 "supersedes_nothing":True,
 "DGEBA_smiles":DGEBA,"EEW_DGEBA":EEW,"M_DGEBA":M_DGEBA,
 "theory":{
   "descriptors":{
     "B_backbone":"N-to-N shortest-path rigid-bond fraction (rigid = aromatic|in-ring|multiple).",
     "n_x_mol_per_kg":"Flory perfect-network crosslink strand density from amine SMILES + DGEBA "
                      "molar mass ONLY; strands/amine = 1.5*n_N; density-free."},
   "non_circularity":"both descriptors computed purely from amine SMILES; measured Tg never a feature",
   "governing_physics":"network Tg rises with BOTH strand stiffness (B) AND crosslink density (n_x) "
                       "(DiBenedetto/Fox-Loshaek/Van Krevelen ch.6); a single descriptor is "
                       "structurally insufficient, so >=2 params are mandatory."},
 "protocol_consistent_training_set":{
   "n_unique_systems":n,"n_measurements":len(RAW),"independent_sources":3,
   "classes_spanned":sorted(set(r["amine_class"] for r in uniq)),
   "systems":uniq},
 "cross_protocol_evidence_not_merged":PROTOCOL_EVIDENCE,
 "protocol_sensitivity":protocol_sensitivity,
 "gate_feasibility":gate_feasibility,
 "models":{
   "loo_B_1axis":loo_B,"loo_nx_1axis":loo_nx,"loo_B_plus_nx_2axis":loo_Bnx,
   "insample_B_plus_nx_2axis":ins_Bnx,"loo_null_mean_Tg_C":null_loo,
   "reading":("1-axis B LOO {:.2f} C (reproduces signed v3); 2-axis LOO {:.2f} C (reproduces "
     "signed xlink-v1 overfit). The 2-axis IN-SAMPLE R2 is only {:.3f} (RMSE {:.1f} C): the two "
     "descriptors capture the crosslink-density and stiffness axes but a LINEAR B+n_x still "
     "leaves ~45% of in-sample variance unexplained (DDS sulfone rigidity, IPDA gem-dimethyl "
     "sterics). So the model is CO-limited: n=7 data starvation (in-sample->LOO blow-up) AND a "
     "linear-form/steric structural error already ~AT the gate. See data_requirement."
     ).format(loo_B["loo_mae_C"],loo_Bnx["loo_mae_C"],ins_Bnx["insample_r2"],ins_Bnx["insample_rmse_C"])},
 "data_requirement":data_requirement,
 "acquisition_log":acquisition_log,
 "incumbent_state_from_signed_receipts":{
   "polyuniverse_ml_MAE_C":39.119479,
   "raw_van_krevelen_MAE_C":109.077814,
   "v3_backbone_LOO_C":35.730624,
   "xlink_v1_2axis_LOO_C":48.96,
   "note":"quoted from signed in-tree audits; B/n_x LOO recomputed here and must match."},
 "phase0_reconciliation_redteam":phase0_recon,
 "verdict":verdict,
 "honest_limitations":[
   "n=7 protocol-consistent unique systems is UNCHANGED; still below the n>=12 G1 gate.",
   "the cold-cure evidence (IPDA 112, DDS 181) is a REFERENCE-hardener datum, not a full cure "
   "map; it bounds the cure-state effect but is not itself a merged training label.",
   "the leverage inflation figures are mean-leverage OLS approximations, not a substitute for a "
   "real learning curve, which requires the very data that is missing.",
   "protocol consistency is necessary but not sufficient: a real dataset must also fix DSC rate "
   "and (mid-point vs onset) Tg convention, which add further scatter if uncontrolled.",
 ],
 "does_not":[
   "does NOT promote amphora-molecule-property or any module to PHASE_0 or VALIDATED",
   "does NOT add any PHASE_0 module or modify the 66 signed receipts or the manifest",
   "does NOT fabricate, web-summarize, mid-range, or MERGE any cross-protocol Tg value",
   "does NOT perform PHASE0_EVALUATOR / PHASE0_INTERNAL_REVIEWER signing",
   "does NOT claim a validated Tg KPI: G1 (n>=12) and G2 (<=25 C) remain unmet",
 ],
}

diag=rnd(diag)
out=json.dumps(diag,indent=2,sort_keys=True)
if len(sys.argv)>1:
    open(sys.argv[1],"w").write(out)
sys.stderr.write("SHA256 "+hashlib.sha256(out.encode()).hexdigest()+"\n")
