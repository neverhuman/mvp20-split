#!/usr/bin/env python3
"""
amphora-public-corrosion-benchmark : multi-instrument rank-CONCORDANCE test.

Motivation
----------
The prior receipt (eis-rustcreep-crossmodality-v1) established that the published
low-frequency EIS barrier metric |Z|_0.01Hz recovers the physically-expected
NEGATIVE association with independent scribe rust-creep AFTER controlling for the
exposure-bath confound, but was UNDERPOWERED at a single instrument-pair
(mean within-env Spearman rho=-0.30, permutation p=0.096). The natural
power-boosting successor is an OMNIBUS concordance test that integrates a THIRD
independent corrosion-protection instrument (wet pull-off adhesion) and asks
whether the k independent instruments agree on the system ordering better than a
hostile permutation null.

Theory baseline (published, primary)
------------------------------------
Kendall's coefficient of concordance W:
  Kendall, M.G. & Babington Smith, B. (1939) "The Problem of m Rankings",
  Annals of Mathematical Statistics 10(3):275-287. DOI:10.1214/aoms/1177732186.
  W = 12 S / ( k^2 (n^3 - n) - k sum(T_i) )   (with tie correction T_i).
Friedman omnibus chi-square:
  Friedman, M. (1937) J. Am. Stat. Assoc. 32:675-701. DOI:10.1080/01621459.1937.10503522.
  chi2 = k (n-1) W,  df = n-1;  F = (k-1)W / (1-W),  df1 = n-1-2/k, df2 = (k-1)(n-1-2/k).
EIS barrier descriptor: ISO 16773-1..4:2016 low-frequency |Z| for organic coatings.

Non-circularity
---------------
The three primary instruments are physically independent measurements on
different panels: EIS (electrochemical), scribe rust-creep width (visual on
scribed panels), wet pull-off adhesion (hydraulic pull stub). None is derived
from another; rank concordance among them is genuine cross-instrument
corroboration. All endpoints are oriented so that a HIGHER rank = BETTER
protective performance, using an a-priori physical polarity (barrier up = good;
creep down = good; pull-off strength up = good). Rank statistics are invariant
to the unknown EIS cell-area normalisation.

Confound control
----------------
Each system is reduced to ONE scalar per instrument by aggregating over an
IDENTICAL exposure-bath set (BOR/DI/HAR/PRO for the two bath-resolved
instruments), so exposure environment is balanced across systems by design and
cannot act as the lurking variable that reversed the naive pooled correlation.

Data (US Bureau of Reclamation RISE, public domain, 17 U.S.C. 105)
------------------------------------------------------------------
USBR project 21019, catalog item 8048, author B. Baumgarten, 2024-09-11.
Six benchmark vinyl coating systems. AUDIT_ONLY.
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

def sha256_file(p): return hashlib.sha256(open(p,"rb").read()).hexdigest()
def sysid(f,suffix): return os.path.basename(f).split("_",1)[1][:-len(suffix)]

def parse_eis(f):
    rows=list(csv.reader(open(f)))
    hi=next(i for i,r in enumerate(rows) if r and r[0]=="Sample")
    hdr=rows[hi]; ci={h:hdr.index(h) for h in hdr}; recs=[]
    for r in rows[hi+1:]:
        if not r or not r[0].strip(): continue
        try:
            recs.append((r[ci["Test"]].strip(),
                         datetime.strptime(r[ci["Date"]].strip(),"%m/%d/%Y"),
                         float(r[ci["Z_0.01"]])))
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
    return {env:(sum(v)/len(v)) for env,v in vals.items() if v}

def parse_wet_adhesion(f):
    rows=list(csv.reader(open(f)))
    in_wet=False; hdr_seen=False; vals=[]
    for r in rows:
        if not r: continue
        c0=r[0].strip().lower()
        if c0.startswith("wet adhesion"): in_wet=True; hdr_seen=False; continue
        if c0.startswith("dry adhesion"): break
        if not in_wet: continue
        if r[0].strip()=="Test" or (len(r)>1 and r[1].strip().lower().startswith("failure pressure")):
            hdr_seen=True; continue
        if hdr_seen and len(r)>1 and r[1].strip():
            try: vals.append(float(r[1]))
            except Exception: pass
    return (float(np.median(vals)) if vals else None), len(vals)

def parse_impact(f):
    rows=list(csv.reader(open(f))); vals=[]; hdr_i=None
    for i,r in enumerate(rows):
        if r and any(c.strip().lower().startswith("impact") for c in r) and \
           any(c.strip().lower()=="coating" for c in r):
            hdr_i=i; break
    if hdr_i is None: return None,0
    for r in rows[hdr_i+1:]:
        for c in r:
            c=c.strip()
            try:
                v=float(c)
                if 0<v<=2000: vals.append(v)
            except Exception: pass
    return (float(np.median(vals)) if vals else None), len(vals)

def build():
    eis_files=sorted(glob.glob(RAW+"/*_eis.csv"))
    rc_files=sorted(glob.glob(RAW+"/*_rust_creep.csv"))
    ad_files=sorted(glob.glob(RAW+"/*_wet_dry_adhesion.csv"))
    im_files=sorted(glob.glob(RAW+"/*_impact.csv"))
    inputs={}
    for f in eis_files+rc_files+ad_files+im_files:
        inputs[os.path.relpath(f,MOD)]=sha256_file(f)
    eis_sys={}
    for f in eis_files:
        sid=sysid(f,"_eis.csv"); recs=parse_eis(f); perbath={}
        for env in ENVS:
            er=[r for r in recs if r[0]==env]
            if not er: continue
            maxdt=max(r[1] for r in er); ep=[r for r in er if r[1]==maxdt]
            perbath[env]=float(np.median([math.log10(r[2]) for r in ep]))
        if set(perbath)==set(ENVS):
            eis_sys[sid]={"perbath_log10Z":{e:round(perbath[e],6) for e in ENVS},
                          "score":float(np.median(list(perbath.values())))}
    rc_sys={}
    for f in rc_files:
        sid=sysid(f,"_rust_creep.csv"); perbath=parse_rustcreep(f)
        if set(perbath)>=set(ENVS):
            mean_creep=float(np.mean([perbath[e] for e in ENVS]))
            rc_sys[sid]={"perbath_creep_mm":{e:round(perbath[e],6) for e in ENVS},
                         "mean_creep_mm":mean_creep,"resistance_score":-mean_creep}
    ad_sys={}
    for f in ad_files:
        sid=sysid(f,"_wet_dry_adhesion.csv"); med,nn=parse_wet_adhesion(f)
        if med is not None: ad_sys[sid]={"wet_pulloff_psi_median":med,"n":nn}
    im_sys={}
    for f in im_files:
        sid=sysid(f,"_impact.csv"); med,nn=parse_impact(f)
        if med is not None: im_sys[sid]={"impact_inlb_median":med,"n":nn}
    systems=sorted(set(eis_sys)&set(rc_sys)&set(ad_sys))
    instruments=[
        ("eis_barrier_log10Z","ISO16773 low-frequency |Z|_0.01Hz (electrochemical barrier)",
         [eis_sys[s]["score"] for s in systems]),
        ("rustcreep_resistance","negative mean scribe rust-creep width mm (visual, scribed panels)",
         [rc_sys[s]["resistance_score"] for s in systems]),
        ("wet_adhesion_pulloff","median wet pull-off failure pressure psi (hydraulic stub)",
         [ad_sys[s]["wet_pulloff_psi_median"] for s in systems]),
    ]
    return systems,instruments,{"eis":eis_sys,"rc":rc_sys,"ad":ad_sys,"im":im_sys},inputs

def kendall_w(score_rows):
    k=len(score_rows); n=len(score_rows[0])
    R=np.array([stats.rankdata(row) for row in score_rows])
    colsum=R.sum(axis=0)
    Rbar=k*(n+1)/2.0
    S=float(np.sum((colsum-Rbar)**2))
    Tsum=0.0
    for row in score_rows:
        _,cnt=np.unique(row,return_counts=True)
        Tsum+=float(np.sum(cnt**3-cnt))
    denom=k*k*(n**3-n)-k*Tsum
    W=12.0*S/denom if denom>0 else 0.0
    chi2=k*(n-1)*W; df=n-1
    chi2_p=float(stats.chi2.sf(chi2,df))
    df1=n-1-2.0/k; df2=(k-1)*df1
    if 0<W<1:
        F=(k-1)*W/(1-W); F_p=float(stats.f.sf(F,df1,df2))
    elif W>=1:
        F=float("inf"); F_p=0.0
    else:
        F=0.0; F_p=1.0
    return {"W":W,"S":S,"tie_correction_T":Tsum,"chi2":chi2,"chi2_df":df,"chi2_p":chi2_p,
            "F":F,"F_df1":df1,"F_df2":df2,"F_p":F_p,
            "colsum_ranks":[float(x) for x in colsum],
            "rank_matrix":[[float(x) for x in row] for row in R]}

def perm_null(score_rows,nperm,seed):
    """Exact-MC permutation p for Kendall's W. Ranks (with ties) are fixed per
    instrument and the denominator is constant, so W is monotone in the column-sum
    dispersion S; permuting columns per row and comparing S is exact and vectorized."""
    k=len(score_rows); n=len(score_rows[0])
    Rrows=np.array([stats.rankdata(r) for r in score_rows])   # k x n fixed rank rows
    Rbar=k*(n+1)/2.0
    S_obs=float(np.sum((Rrows.sum(axis=0)-Rbar)**2))
    rng=np.random.default_rng(seed)
    colsum=np.zeros((nperm,n))
    for i in range(k):
        perm=np.argsort(rng.random((nperm,n)),axis=1)   # independent col perm per row
        colsum+=Rrows[i][perm]
    S=np.sum((colsum-Rbar)**2,axis=1)
    ge=int(np.sum(S>=S_obs-1e-9))
    return (ge+1)/(nperm+1)

def jackknife_W(score_rows):
    n=len(score_rows[0]); ws=[]
    for drop in range(n):
        sub=[[v for i,v in enumerate(row) if i!=drop] for row in score_rows]
        ws.append(kendall_w(sub)["W"])
    return {"leave_one_system_out_W":[round(w,6) for w in ws],
            "min":round(min(ws),6),"max":round(max(ws),6),"mean":round(float(np.mean(ws)),6)}

def pairwise_spearman(names,score_rows):
    out={}
    for a in range(len(names)):
        for b in range(a+1,len(names)):
            rho=stats.spearmanr(score_rows[a],score_rows[b]).statistic
            out[names[a]+"__vs__"+names[b]]=round(float(rho),6)
    return out

def diagnostic():
    systems,instruments,raw,inputs=build()
    names=[i[0] for i in instruments]
    descs={i[0]:i[1] for i in instruments}
    score_rows=[i[2] for i in instruments]
    k=len(instruments); n=len(systems)
    w=kendall_w(score_rows)
    NPERM=200000; PSEED=20260728
    p_perm=perm_null(score_rows,NPERM,PSEED)
    jk=jackknife_W(score_rows)
    pw=pairwise_spearman(names,score_rows)
    mean_pair=round(float(np.mean(list(pw.values()))),6)
    sec=None; im=raw["im"]
    if all(s in im for s in systems):
        rows4=score_rows+[[im[s]["impact_inlb_median"] for s in systems]]
        names4=names+["impact_toughness"]
        w4=kendall_w(rows4); p4=perm_null(rows4,NPERM,PSEED+1)
        sec={"instruments":names4,
             "note":("Adds a MECHANICAL toughness endpoint to the 3 corrosion-protection "
                     "instruments; tests a broader 'coating quality' latent that MIXES "
                     "corrosion and mechanical performance, not a pure corrosion rank."),
             "W":round(w4["W"],6),"chi2":round(w4["chi2"],6),"chi2_p":round(w4["chi2_p"],6),
             "perm_p_one_sided":round(p4,6),
             "impact_inlb_by_system":{s:im[s]["impact_inlb_median"] for s in systems}}
    per_system_scores={s:{
        "eis_barrier_log10Z":round(raw["eis"][s]["score"],6),
        "eis_perbath_log10Z":raw["eis"][s]["perbath_log10Z"],
        "rustcreep_mean_mm":round(raw["rc"][s]["mean_creep_mm"],6),
        "rustcreep_resistance_score":round(raw["rc"][s]["resistance_score"],6),
        "wet_pulloff_psi_median":round(raw["ad"][s]["wet_pulloff_psi_median"],6)}
        for s in systems}
    significant=bool(p_perm<0.05)
    verdict=("CONCORDANT_SIGNIFICANT" if significant else
             ("CONCORDANT_DIRECTION_UNDERPOWERED" if (w["W"]>=0.5 and mean_pair>0) else
              "WEAK_OR_NULL_CONCORDANCE"))
    diag={
      "schema":"amphora.public-corrosion-benchmark.multi-instrument-concordance.v1",
      "module":"amphora-public-corrosion-benchmark","run_type":"AUDIT_ONLY","authority":"EVIDENCE_ONLY",
      "purpose":("Omnibus rank-concordance successor to the underpowered single-pair "
                 "cross-modality test: do k=3 physically-independent corrosion-protection "
                 "instruments (EIS barrier |Z|_0.01Hz, scribe rust-creep resistance, wet "
                 "pull-off adhesion) agree on the ordering of 6 benchmark coating systems "
                 "beyond a hostile permutation null, via Kendall's coefficient of concordance "
                 "W with a Friedman chi-square omnibus, an exact-Monte-Carlo permutation p, and "
                 "leave-one-system-out stability."),
      "theory_reference":{
        "concordance":"Kendall & Babington Smith 1939, Ann. Math. Statist. 10(3):275-287, DOI:10.1214/aoms/1177732186",
        "omnibus":"Friedman 1937, JASA 32:675-701, DOI:10.1080/01621459.1937.10503522",
        "eis_barrier":"ISO 16773-1..4:2016 low-frequency |Z| for organic coatings",
        "orientation_prior":"all endpoints oriented higher-rank=better protection (barrier up, creep down, pull-off up)"},
      "data_source":{
        "provider":"US Bureau of Reclamation (USBR) RISE","project":"21019","catalog_item":"8048",
        "author":"Brian Baumgarten","publication_date":"2024-09-11",
        "license":"US Government work, public domain (17 U.S.C. 105)","rights_clean":True,
        "url":"https://data.usbr.gov/rise/api/catalog-record/8048"},
      "inputs":inputs,
      "instruments":{nm:descs[nm] for nm in names},
      "n_coating_systems":n,"n_instruments":k,"systems":systems,
      "confound_control":("each system reduced to one scalar per bath-resolved instrument by "
                          "aggregating over the IDENTICAL bath set BOR/DI/HAR/PRO, so exposure "
                          "environment is balanced across systems by design"),
      "per_system_scores":per_system_scores,
      "kendall_W":{
        "W":round(w["W"],6),"S":round(w["S"],6),"tie_correction_T":round(w["tie_correction_T"],6),
        "friedman_chi2":round(w["chi2"],6),"chi2_df":w["chi2_df"],"chi2_p":round(w["chi2_p"],6),
        "F_approx":round(w["F"],6),"F_df1":round(w["F_df1"],6),"F_df2":round(w["F_df2"],6),
        "F_p":round(w["F_p"],6),
        "column_rank_sums_by_system":{systems[i]:w["colsum_ranks"][i] for i in range(n)},
        "hostile_null":"independent column permutation of each instrument's ranks",
        "permutation_seed":PSEED,"n_permutations":NPERM,"perm_p_one_sided":round(p_perm,6),
        "leave_one_system_out":jk},
      "pairwise_spearman":pw,"mean_pairwise_spearman":mean_pair,
      "W_from_mean_pairwise_check":round((1+(k-1)*mean_pair)/k,6),
      "secondary_with_mechanical_impact":sec,
      "interpretation":{
        "concordance_direction_positive":bool(mean_pair>0 and w["W"]>=(1.0/k)),
        "significant_at_0p05":significant,"verdict":verdict,
        "meaning":("Kendall's W integrates a third independent instrument beyond the prior "
                   "EIS x rust-creep pair. W ranges 0 (no agreement) to 1 (identical rankings); "
                   "the Friedman chi2 and exact-MC permutation p test it against independent "
                   "rankings. At n=6 systems the omnibus remains underpowered, but W and the "
                   "leave-one-out band quantify how strongly the independent corrosion "
                   "instruments co-order coating quality and set a concrete power target.")},
      "non_circularity":("EIS (electrochemical), scribe rust-creep (visual), and wet pull-off "
                         "adhesion (hydraulic) are independent measurements on different panels; "
                         "concordance is genuine cross-instrument corroboration and rank statistics "
                         "are invariant to EIS cell-area normalisation."),
      "promotes_authority":False,"modifies_manifest":False,
      "modifies_signed_phase0_kpi":False,"human_review_performed":False,
      "does_not_close":[
        "No coating-efficacy, product-performance, batch-release, or corrosion-rank authority.",
        "n=6 systems: Friedman df=5, omnibus underpowered; a single system swaps the tail.",
        "wet pull-off psi is a strength proxy, not a retained-adhesion ratio; area-caveated EIS.",
        "Phase-1 needs >= ~12-20 independent systems (or frequency-resolved KK-validated spectra) "
        "to power a p<0.05 multi-instrument concordance and a calibrated coating-quality rank."]}
    diag["headline"]=(
      "Multi-instrument concordance on rights-clean USBR-21019 (6 vinyl coating systems, 3 "
      "physically-independent corrosion instruments: EIS barrier, scribe rust-creep resistance, "
      "wet pull-off adhesion): Kendall's W=%.3f (Friedman chi2=%.2f, df=5, chi2 p=%.3f; exact-MC "
      "permutation p=%.3f over %d perms), mean pairwise Spearman=%+.3f, leave-one-system-out W in "
      "[%.3f, %.3f]. %s: the independent instruments %s co-order coating quality, but at n=6 the "
      "omnibus %s at 0.05 -- integrating a third instrument extends the prior single-pair test "
      "while confirming the module's model-readiness-only boundary."
      % (w["W"], w["chi2"], w["chi2_p"], p_perm, NPERM, mean_pair, jk["min"], jk["max"],
         verdict, ("positively" if mean_pair>0 else "do not consistently"),
         ("is significant" if significant else "remains underpowered")))
    return diag

def canon(obj): return json.dumps(obj,indent=2,sort_keys=True).encode()

def dsse_sign(payload_bytes,payload_type,seed):
    sk=Ed25519PrivateKey.from_private_bytes(seed)
    pub=sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
    keyid="phase0-evaluator-"+hashlib.sha256(pub).hexdigest()
    pt=payload_type.encode()
    pae=b"DSSEv1 "+str(len(pt)).encode()+b" "+pt+b" "+str(len(payload_bytes)).encode()+b" "+payload_bytes
    sig=sk.sign(pae)
    env={"payload":base64.b64encode(payload_bytes).decode(),"payloadType":payload_type,
         "signatures":[{"keyid":keyid,"sig":base64.b64encode(sig).decode()}]}
    return env,keyid,pub.hex()

if __name__=="__main__":
    d1=diagnostic(); b1=canon(d1); h1=hashlib.sha256(b1).hexdigest()
    d2=diagnostic(); b2=canon(d2); h2=hashlib.sha256(b2).hexdigest()
    assert b1==b2, "two-replay byte MISMATCH"
    print("replay_sha256:",h1,"| byte_stable:",h1==h2)
    print("W=",d1["kendall_W"]["W"],"perm_p=",d1["kendall_W"]["perm_p_one_sided"],
          "mean_pair=",d1["mean_pairwise_spearman"],"verdict=",d1["interpretation"]["verdict"])
    print("systems=",d1["systems"])
    if len(sys.argv)>1 and sys.argv[1]=="--emit":
        outdir=os.path.dirname(os.path.abspath(__file__))
        open(os.path.join(outdir,"diagnostic.canonical.json"),"wb").write(b1)
        seed=open(SEED_PATH,"rb").read()
        pt="application/vnd.amphora.public-corrosion-benchmark-multi-instrument-concordance-receipt.v1+json"
        env,keyid,pubhex=dsse_sign(b1,pt,seed)
        receipt={"signature":env,"evaluator_key_id":keyid,"reviewer_public_key_hex":pubhex}
        open(os.path.join(outdir,"multi-instrument-concordance-receipt.v1.dsse.json"),"w").write(
            json.dumps(receipt,indent=2,sort_keys=True))
        print("emitted diagnostic + signed receipt in",outdir)
