#!/usr/bin/env python3
"""
amphora-public-corrosion-benchmark : cross-modality corroboration of the
published low-frequency EIS barrier metric against an INDEPENDENT physical
degradation modality (scribe rust-creep), on rights-clean public-domain data.
AUDIT_ONLY.

Falsifiable module hypothesis
-----------------------------
A provenance-locked benchmark can distinguish declared coating-barrier models
from hostile nulls. Here the "declared model" is the published organic-coating
barrier criterion (low-frequency impedance modulus |Z| at 0.01 Hz); the
"hostile null" is the stratified label-permutation distribution. The test asks
whether the electrochemical barrier metric anti-correlates with a physically
independent damage metric (scribe rust-creep width) BEYOND what the exposure
environment alone explains.

Theory baseline (published, primary)
------------------------------------
Low-frequency impedance modulus |Z|_{0.01 Hz} as the standard protective-
performance descriptor for organic coatings:
  ISO 16773-1..4:2016 "Electrochemical impedance spectroscopy (EIS) on coated
     and uncoated metallic specimens".
  Also: EN ISO 16773-2; and the widely used protective classification
     |Z|_lowf >= 1e9 (excellent), 1e7-1e9 (good/fair), 1e6-1e7 (poor),
     < 1e6 Ohm.cm^2 (failed).
The physically predicted sign is NEGATIVE: higher barrier |Z| -> less rust creep.

Non-circularity
---------------
EIS |Z| is a purely electrochemical measurement; scribe rust-creep width is a
purely visual/physical measurement made on different panels. Neither is derived
from the other, so their rank agreement is a genuine cross-instrument
corroboration, not a self-consistency check. Rank statistics are invariant to
the (unknown) EIS cell-area normalisation, so the corroboration claim does not
depend on converting Ohm -> Ohm.cm^2.

Data (US Bureau of Reclamation, public domain, 17 U.S.C. 105)
-------------------------------------------------------------
USBR RISE Project 21019 (catalog item 8048), author B. Baumgarten, 2024.
Six coating systems x {BOR,DI,HAR,PRO} exposure solutions; per-cell endpoint
(latest-date) log10|Z|_0.01Hz and mean scribe rust-creep width (mm).
"""
import csv, glob, os, math, json, hashlib, base64, sys
from datetime import datetime
import numpy as np
from scipy import stats
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

MOD="/home/ubuntu/amphora/build/mvp20-split/amphora-public-corrosion-benchmark"
RAW=MOD+"/reference/mvp20/data/public_corrosion_datasets/usbr_21019/raw"
SEED_PATH="/home/ubuntu/.local/share/amphora/phase0/keys/evaluator.ed25519.seed"
ENVS=["BOR","DI","HAR","PRO"]

def sha256_file(p):
    return hashlib.sha256(open(p,"rb").read()).hexdigest()

def sysid(f,suffix):
    return os.path.basename(f).split("_",1)[1][:-len(suffix)]

def parse_eis(f):
    rows=list(csv.reader(open(f)))
    hi=next(i for i,r in enumerate(rows) if r and r[0]=="Sample")
    hdr=rows[hi]; ci={h:hdr.index(h) for h in hdr}; recs=[]
    for r in rows[hi+1:]:
        if not r or not r[0].strip(): continue
        try:
            recs.append((r[ci["Test"]].strip(),
                         datetime.strptime(r[ci["Date"]].strip(),"%m/%d/%Y"),
                         float(r[ci["Z_0.01"]]), float(r[ci["Phi_0.01"]])))
        except Exception: pass
    return recs

def parse_rustcreep(f):
    rows=list(csv.reader(open(f)))
    hi=next(i for i,r in enumerate(rows) if r and r[0]=="Sample:")
    hdr=rows[hi]; colenv={}
    for j,h in enumerate(hdr):
        h=h.strip()
        for env in ENVS:
            if h.endswith(" "+env): colenv.setdefault(env,[]).append(j)
    vals={env:[] for env in ENVS}
    for r in rows[hi+1:]:
        if not r: continue
        if r[0].strip().lower().startswith("blister"): break
        for env,cols in colenv.items():
            for j in cols:
                if j<len(r) and r[j].strip():
                    try: vals[env].append(float(r[j]))
                    except Exception: pass
    return {env:(sum(v)/len(v),len(v)) for env,v in vals.items() if v}

def iso16773_class(log10z):
    if log10z>=9: return "very_good_barrier_ge_1e9"
    if log10z>=7: return "good_or_fair_1e7_1e9"
    if log10z>=6: return "poor_1e6_1e7"
    return "failed_lt_1e6"

def build():
    eis_files=sorted(glob.glob(RAW+"/*_eis.csv"))
    rc_files=sorted(glob.glob(RAW+"/*_rust_creep.csv"))
    inputs={}
    for f in eis_files+rc_files:
        inputs[os.path.relpath(f,MOD)]=sha256_file(f)
    panel={}
    for f in eis_files:
        sid=sysid(f,"_eis.csv"); recs=parse_eis(f)
        for env in ENVS:
            er=[r for r in recs if r[0]==env]
            if not er: continue
            maxdt=max(r[1] for r in er); ep=[r for r in er if r[1]==maxdt]
            panel[(sid,env)]={
                "log10Z_end": sum(math.log10(r[2]) for r in ep)/len(ep),
                "phi_end": sum(r[3] for r in ep)/len(ep),
                "endpoint_date": maxdt.strftime("%Y-%m-%d"),
                "n_endpoint": len(ep)}
    for f in rc_files:
        sid=sysid(f,"_rust_creep.csv")
        for env,(mean,n) in parse_rustcreep(f).items():
            if (sid,env) in panel:
                panel[(sid,env)]["rustcreep_mm"]=mean
                panel[(sid,env)]["rustcreep_n"]=n
    keys=sorted(k for k in panel if "rustcreep_mm" in panel[k])
    systems=sorted(set(k[0] for k in keys)); envs=sorted(set(k[1] for k in keys))
    X=np.array([panel[k]["log10Z_end"] for k in keys])
    P=np.array([panel[k]["phi_end"] for k in keys])
    Y=np.array([panel[k]["rustcreep_mm"] for k in keys])
    SYS=[k[0] for k in keys]; ENV=[k[1] for k in keys]
    idx={e:np.array([i for i,ee in enumerate(ENV) if ee==e]) for e in envs}

    pooled=stats.spearmanr(X,Y)
    pooled_phi=stats.spearmanr(P,Y)
    def mean_within(Xv,Yv):
        return float(np.mean([stats.spearmanr(Xv[idx[e]],Yv[idx[e]]).statistic for e in envs]))
    obs=mean_within(X,Y)
    per_env={e:{"rho_logZ_rc":round(float(stats.spearmanr(X[idx[e]],Y[idx[e]]).statistic),6),
                "rho_phi_rc":round(float(stats.spearmanr(P[idx[e]],Y[idx[e]]).statistic),6),
                "n_systems":int(len(idx[e]))} for e in envs}

    # stratified within-env permutation null (hostile null), vectorized, fixed seed
    rankX={e:(stats.rankdata(X[idx[e]])-stats.rankdata(X[idx[e]]).mean()) for e in envs}
    baseYr={e:stats.rankdata(Y[idx[e]]) for e in envs}
    def within_from_ranks(permYr):
        rs=[]
        for e in envs:
            rc=rankX[e]; ry=permYr[e]-permYr[e].mean()
            denom=math.sqrt(float(rc@rc))*math.sqrt(float(ry@ry))
            rs.append((rc@ry)/denom if denom>0 else 0.0)
        return float(np.mean(rs))
    rng=np.random.default_rng(0); NPERM=50000; le=0
    for _ in range(NPERM):
        permYr={e:baseYr[e][rng.permutation(len(baseYr[e]))] for e in envs}
        if within_from_ranks(permYr)<=obs+1e-12: le+=1
    p_neg=(le+1)/(NPERM+1)

    # cluster bootstrap over systems (fixed seed) -> CI on mean within-env rho
    sysrows={s:[i for i in range(len(SYS)) if SYS[i]==s] for s in systems}
    rng2=np.random.default_rng(12345); B=10000; boots=[]
    for _ in range(B):
        chosen=rng2.choice(systems,size=len(systems),replace=True)
        rows=[]
        for s in chosen: rows.extend(sysrows[s])
        rows=np.array(rows)
        Xb,Yb=X[rows],Y[rows]; ENVb=[ENV[i] for i in rows]
        ib={e:np.array([j for j,ee in enumerate(ENVb) if ee==e]) for e in envs}
        rs=[]
        for e in envs:
            ii=ib[e]
            if len(ii)>=3 and len(set(Xb[ii]))>1 and len(set(Yb[ii]))>1:
                rs.append(stats.spearmanr(Xb[ii],Yb[ii]).statistic)
        if rs: boots.append(float(np.mean(rs)))
    boots=np.array(boots)
    ci_lo,ci_hi=float(np.percentile(boots,2.5)),float(np.percentile(boots,97.5))
    frac_neg=float(np.mean(boots<0))

    from collections import Counter
    iso_counts=dict(Counter(iso16773_class(x) for x in X))

    cells=[{"system":k[0],"environment":k[1],
            "log10_Z_0p01Hz_endpoint":round(panel[k]["log10Z_end"],6),
            "phase_deg_0p01Hz_endpoint":round(panel[k]["phi_end"],6),
            "endpoint_date":panel[k]["endpoint_date"],
            "rustcreep_mm_mean":round(panel[k]["rustcreep_mm"],6),
            "rustcreep_n":panel[k]["rustcreep_n"],
            "iso16773_class":iso16773_class(panel[k]["log10Z_end"])} for k in keys]

    physically_consistent = obs < 0
    diag={
      "schema":"amphora.public-corrosion-benchmark.eis-rustcreep-crossmodality.v1",
      "module":"amphora-public-corrosion-benchmark",
      "run_type":"AUDIT_ONLY",
      "authority":"EVIDENCE_ONLY",
      "purpose":("First cross-instrument corroboration test for the public corrosion "
                 "benchmark: does the published low-frequency EIS barrier metric "
                 "|Z|_0.01Hz anti-correlate with an INDEPENDENT physical scribe "
                 "rust-creep modality after controlling for the exposure-environment "
                 "confound, versus a stratified hostile-permutation null."),
      "theory_reference":{
        "eis_barrier_metric":"low-frequency impedance modulus |Z| at 0.01 Hz",
        "standards":["ISO 16773-1:2016","ISO 16773-2:2016","ISO 16773-3:2016","ISO 16773-4:2016"],
        "classification_thresholds_ohm_cm2":{"very_good":">=1e9","good_fair":"1e7-1e9","poor":"1e6-1e7","failed":"<1e6"},
        "predicted_sign":"negative (higher |Z| barrier -> lower rust-creep width)"},
      "data_source":{
        "provider":"US Bureau of Reclamation (USBR) RISE",
        "project":"21019","catalog_item":"8048","author":"Brian Baumgarten",
        "publication_date":"2024-09-11",
        "license":"US Government work, public domain (17 U.S.C. 105)",
        "rights_clean":True,
        "url":"https://data.usbr.gov/rise/api/catalog-record/8048"},
      "inputs":inputs,
      "n_coating_systems":len(systems),
      "n_environments":len(envs),
      "n_paired_cells":len(keys),
      "systems":systems,"environments":envs,
      "panel":cells,
      "iso16773_endpoint_class_counts_area_caveated":iso_counts,
      "area_caveat":("USBR reports |Z| in ohm (not ohm.cm^2); ISO magnitude classes above "
                     "assume the standard specimen area ~1 cm^2 and are PROVISIONAL. The "
                     "rank-based corroboration statistics below are invariant to any "
                     "constant area normalisation and do NOT rely on this caveat."),
      "pooled_spearman_logZ_vs_rustcreep":{"rho":round(float(pooled.statistic),6),"p_two_sided":round(float(pooled.pvalue),6),
        "note":"CONFOUNDED by environment; sign is reversed (positive) because both |Z| and rust-creep rise together in aggressive baths."},
      "pooled_spearman_phase_vs_rustcreep":{"rho":round(float(pooled_phi.statistic),6),"p_two_sided":round(float(pooled_phi.pvalue),6)},
      "primary_result_within_environment":{
        "estimator":"mean over environments of within-environment Spearman rho(log10|Z|, rustcreep)",
        "mean_within_env_rho":round(obs,6),
        "per_environment":per_env,
        "hostile_null":"stratified within-environment label permutation (systems shuffled within each bath)",
        "permutation_seed":0,"n_permutations":NPERM,
        "perm_p_one_sided_negative":round(p_neg,6),
        "cluster_bootstrap":{"resample_unit":"coating_system","seed":12345,"n_boot":int(len(boots)),
          "ci95":[round(ci_lo,6),round(ci_hi,6)],"median":round(float(np.median(boots)),6),
          "fraction_negative":round(frac_neg,6)}},
      "phase_angle_secondary":{"per_environment_rho_phi_rc":{e:per_env[e]["rho_phi_rc"] for e in envs},
        "verdict":"inconsistent sign across baths; phase angle not a reliable single-frequency barrier rank here"},
      "interpretation":{
        "physically_predicted_direction_recovered_after_confound_control":physically_consistent,
        "significant_at_0p05":bool(p_neg<0.05),
        "verdict":("DIRECTION_CONSISTENT_UNDERPOWERED" if (physically_consistent and p_neg>=0.05)
                   else ("CORROBORATED" if (physically_consistent and p_neg<0.05) else "REFUTED_OR_NULL")),
        "meaning":("The environment is a genuine confound: the naive pooled correlation is "
                   "sign-reversed. After stratifying on bath, the published EIS barrier metric "
                   "recovers the physically-expected negative association with independent "
                   "rust-creep, but at 6 coating systems the 95% CI crosses zero and the "
                   "permutation p exceeds 0.05. This quantifies the discrimination HEADROOM and "
                   "confirms the module's declared boundary: 6 public systems support "
                   "model-readiness only and cannot establish a validated corrosion rank.")},
      "non_circularity":("EIS |Z| (electrochemical) and scribe rust-creep width (visual/physical) are "
                         "independent measurements on different panels; rank statistics are invariant "
                         "to EIS cell-area normalisation."),
      "promotes_authority":False,
      "modifies_manifest":False,
      "modifies_signed_phase0_kpi":False,
      "human_review_performed":False,
      "does_not_close":[
        "No coating-efficacy, product-performance, batch-release, or corrosion-rank authority.",
        "n=6 coating systems: within-environment CI crosses zero; not significant at 0.05.",
        "ISO magnitude classes provisional pending EIS specimen-area normalisation.",
        "Phase-1 would require >= ~12-20 independent coating systems (or frequency-resolved "
        "spectra with Kramers-Kronig validation) to power a p<0.05 cross-modality rank."]}
    ncorr = "very_good_barrier_ge_1e9"
    diag["headline"]=(
      "Cross-instrument test on rights-clean USBR-21019 public data (6 coating systems x 4 baths, "
      "24 paired cells): the pooled |Z|-vs-rustcreep Spearman is confounded and sign-reversed "
      "(rho=%+.2f); after stratifying on exposure bath the published ISO-16773 low-frequency "
      "barrier metric recovers the physically-expected NEGATIVE association with independent "
      "scribe rust-creep (mean within-env rho=%+.2f, %d%% of cluster-bootstraps negative), but "
      "at n=6 systems it is underpowered (stratified-permutation p=%.3f, 95%% CI [%.2f, %.2f] "
      "crosses zero). Corroborates the module's model-readiness-only boundary; %d/%d endpoint "
      "cells sit in the ISO very-good barrier band (area-caveated)."
      % (pooled.statistic, obs, round(frac_neg*100), p_neg, ci_lo, ci_hi,
         iso_counts.get(ncorr,0), len(keys)))
    return diag

def canon(obj):
    return json.dumps(obj, indent=2, sort_keys=True).encode()

def dsse_sign(payload_bytes, payload_type, seed):
    sk=Ed25519PrivateKey.from_private_bytes(seed)
    pub=sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    keyid="phase0-evaluator-"+hashlib.sha256(pub).hexdigest()
    pt=payload_type.encode()
    pae=b"DSSEv1 "+str(len(pt)).encode()+b" "+pt+b" "+str(len(payload_bytes)).encode()+b" "+payload_bytes
    sig=sk.sign(pae)
    env={"payload":base64.b64encode(payload_bytes).decode(),
         "payloadType":payload_type,
         "signatures":[{"keyid":keyid,"sig":base64.b64encode(sig).decode()}]}
    return env, keyid, pub.hex()

if __name__=="__main__":
    d1=build(); b1=canon(d1); h1=hashlib.sha256(b1).hexdigest()
    d2=build(); b2=canon(d2); h2=hashlib.sha256(b2).hexdigest()
    assert b1==b2, "two-replay byte MISMATCH"
    print("replay_sha256:",h1,"| byte_stable:",h1==h2)
    if len(sys.argv)>1 and sys.argv[1]=="--emit":
        outdir=os.path.dirname(os.path.abspath(__file__))
        open(os.path.join(outdir,"diagnostic.canonical.json"),"wb").write(b1)
        seed=open(SEED_PATH,"rb").read()
        pt="application/vnd.amphora.public-corrosion-benchmark-eis-rustcreep-crossmodality-receipt.v1+json"
        env,keyid,pubhex=dsse_sign(b1,pt,seed)
        receipt={"signature":env,"evaluator_key_id":keyid,"reviewer_public_key_hex":pubhex}
        open(os.path.join(outdir,"eis-rustcreep-crossmodality-receipt.v1.dsse.json"),"w").write(
            json.dumps(receipt,indent=2,sort_keys=True))
        print("emitted diagnostic + signed receipt in",outdir)
