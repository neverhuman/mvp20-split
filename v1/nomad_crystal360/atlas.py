"""Fast, auditable CrystalAtlas descriptors.

The module deliberately keeps the original Crystal360 feature pack separate.  Atlas
features are generated from one exact periodic-neighbour cache and carry a small
machine-readable definition alongside every value.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from itertools import combinations_with_replacement
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd
from pymatgen.core import Structure

from .constants import ELEMENTS

PAIR_TYPES = tuple((a, b) for a in ELEMENTS for b in ELEMENTS)
TRIPLET_TYPES = tuple((c, a, b) for c in ELEMENTS for a, b in combinations_with_replacement(ELEMENTS, 2))
_PROP_NAMES = ("Z", "atomic_mass", "X", "row", "group", "mendeleev_no", "atomic_radius",
               "van_der_waals_radius", "metallic_radius", "thermal_conductivity", "melting_point",
               "boiling_point", "density_of_solid", "molar_volume", "electron_affinity",
               "ionization_energy", "coefficient_of_thermal_expansion", "electrical_resistivity")


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    family: str
    formula: str
    unit: str
    neighbors: str
    normalization: str
    interpretation: str
    invariance: str = "translation, rotation, atom permutation, periodic wrapping"
    provenance: str = "CrystalAtlas v1; public training geometry only"


@dataclass(frozen=True)
class NeighborCache:
    symbols: tuple[str, ...]
    center: np.ndarray
    neighbor: np.ndarray
    distances: np.ndarray
    vectors: np.ndarray
    volume: float
    lattice: np.ndarray

    @classmethod
    def from_structure(cls, structure: Structure, cutoff: float = 12.0) -> "NeighborCache":
        # Pymatgen's neighbour-image convention is relative to the stored fractional
        # coordinates; normalize once so callers may pass translated/unwrapped cells.
        frac = np.asarray(structure.frac_coords, dtype=float) % 1.0
        wrapped = Structure(structure.lattice, structure.species, frac)
        i, j, images, d = wrapped.get_neighbor_list(cutoff, numerical_tol=1e-8)
        i = np.asarray(i, dtype=np.int32); j = np.asarray(j, dtype=np.int32)
        d = np.asarray(d, dtype=np.float64)
        vectors = (frac[j] + np.asarray(images, dtype=np.float64) - frac[i]) @ np.asarray(structure.lattice.matrix, dtype=float)
        keep = (d > 1e-8) & (d <= cutoff + 1e-7)
        return cls(tuple(str(s.specie.symbol) for s in structure), i[keep], j[keep], np.round(d[keep], 8), vectors[keep],
                   float(structure.volume), np.asarray(structure.lattice.matrix, dtype=float))


def _definition(name: str, family: str, formula: str, unit: str = "1", neighbors: str = "12 Å exact PBC",
                normalization: str = "intensive per structure", interpretation: str = "physically interpretable") -> FeatureDefinition:
    return FeatureDefinition(name, family, formula, unit, neighbors, normalization, interpretation)


def _element_values(symbols: tuple[str, ...]) -> tuple[np.ndarray, dict[str, float]]:
    from pymatgen.core import Element
    vals: dict[str, float] = {}
    for prop in _PROP_NAMES:
        a = []
        for symbol in ELEMENTS:
            value = getattr(Element(symbol), prop, None)
            try: value = float(value)
            except (TypeError, ValueError): value = math.nan
            a.append(value)
        if np.all(np.isfinite(a)): vals[prop] = np.asarray(a, dtype=float)
    counts = np.asarray([symbols.count(e) for e in ELEMENTS], dtype=float)
    return counts, vals


def _composition_features(cache: NeighborCache) -> tuple[dict[str, float], list[FeatureDefinition]]:
    counts, properties = _element_values(cache.symbols)
    frac = counts / max(counts.sum(), 1.0)
    out: dict[str, float] = {}; defs: list[FeatureDefinition] = []
    for e, x in zip(ELEMENTS, frac):
        for p in range(1, 11):
            n = f"atlas_comp_fraction_{e}_power_{p:02d}"; out[n] = float(x ** p)
            defs.append(_definition(n, "composition", f"x_{e}^{p}", "1", "none", "fraction of atoms", "stoichiometric disorder"))
        n=f"atlas_comp_fraction_{e}_logit"; out[n]=float(np.log(max(x,1e-30)/max(1-x,1e-30))); defs.append(_definition(n,"composition",f"log(x_{e}/(1-x_{e}))","1","none","fraction transform","stoichiometric composition"))
    for prop, table in properties.items():
        v = table * frac
        mean = float(v.sum()); raw = table[frac > 0]
        for stat, value, formula in (("mean", mean, f"Σx_i {prop}_i"), ("std", float(np.sqrt(np.sum(frac*(table-mean)**2))), f"sqrt(Σx_i({prop}_i-μ)^2)"),
                                     ("min", float(raw.min()) if raw.size else math.nan, f"min({prop})"), ("max", float(raw.max()) if raw.size else math.nan, f"max({prop})"),
                                     ("range", float(raw.max()-raw.min()) if raw.size else math.nan, f"range({prop})")):
            n = f"atlas_comp_{prop}_{stat}"; out[n] = value
            defs.append(_definition(n, "composition", formula, "property-dependent", "none", "composition weighted", f"elemental {prop}"))
        for p in range(2, 9):
            n = f"atlas_comp_{prop}_central_moment_{p:02d}"; out[n] = float(np.sum(frac*(table-mean)**p))
            defs.append(_definition(n, "composition", f"Σx_i({prop}_i-μ)^{p}", "property-dependent", "none", "composition weighted", f"elemental {prop} disorder"))
    for prop, table in properties.items():
        for p in range(1, 9):
            n = f"atlas_mismatch_{prop}_mean_abs_power_{p:02d}"
            out[n] = float(sum(frac[a]*frac[b]*abs(table[a]-table[b])**p for a in range(4) for b in range(a+1,4)))
            defs.append(_definition(n, "composition", f"Σ_(i<j)x_ix_j|Δ{prop}|^{p}", "property-dependent", "none", "pair-fraction weighted", f"elemental {prop} mismatch"))
    for q in range(1, 21):
        n = f"atlas_disorder_renyi_{q:02d}"; out[n] = float((1.0-np.sum(frac**(q+1)))/q)
        defs.append(_definition(n, "composition", f"(1-Σx_i^{q+1})/{q}", "1", "none", "intensive", "composition disorder"))
    for e, x in zip(ELEMENTS, frac):
        for p in range(1, 9):
            n=f"atlas_disorder_{e}_entropy_contribution_{p:02d}"; out[n]=float(-x*np.log(max(x,1e-30))**p)
            defs.append(_definition(n,"composition",f"-x_{e} log(x_{e})^{p}","1","none","intensive","element fraction disorder"))
    for prop, table in properties.items():
        positive = np.all(table > 0)
        if positive:
            for p in range(1, 9):
                n=f"atlas_comp_{prop}_weighted_geomean_{p:02d}"; out[n]=float(np.exp(np.sum(frac*np.log(table**p))/p)); defs.append(_definition(n,"composition",f"exp(Σx_i log({prop}_i^{p})/{p})","property-dependent","none","composition weighted","elemental geometric mean"))
        for p in range(1, 9):
            n=f"atlas_mismatch_{prop}_weighted_abs_{p:02d}"; out[n]=float(sum(frac[a]*frac[b]*abs(table[a]-table[b])/(abs(table[a])+abs(table[b])+1e-12)**(1/p) for a in range(4) for b in range(a+1,4))); defs.append(_definition(n,"composition",f"Σx_ix_j |Δ{prop}|/(|{prop}_i|+|{prop}_j|)^(1/{p})","1","none","pair-fraction weighted","relative elemental mismatch"))
    return out, defs


def _pair_features(cache: NeighborCache) -> tuple[dict[str, float], list[FeatureDefinition]]:
    out: dict[str, float] = {}; defs: list[FeatureDefinition] = []
    # 0.1 Å RDF/CDF, 0.15 Å Gaussian integrals, inverse moments, and first 16 neighbours.
    rdf_edges = np.arange(0.0, 12.0001, 0.1); cdf_edges = np.arange(0.1, 12.0001, 0.2)
    smooth_centers = np.arange(0.1, 12.0001, 0.15)
    for a, b in PAIR_TYPES:
        mask = (np.asarray(cache.symbols)[cache.center] == a) & (np.asarray(cache.symbols)[cache.neighbor] == b)
        d = cache.distances[mask]
        nsrc = max(cache.symbols.count(a), 1); ntgt = cache.symbols.count(b); density = ntgt / cache.volume
        hist, _ = np.histogram(d, bins=rdf_edges)
        shell = (4*math.pi/3) * (rdf_edges[1:]**3-rdf_edges[:-1]**3)
        g = hist / np.maximum(nsrc*density*shell, 1e-12) if ntgt else np.full(len(shell), np.nan)
        for k, value in enumerate(g):
            name=f"atlas_pair_{a}_{b}_rdf_{k:03d}"; out[name]=float(value); defs.append(_definition(name,"pair",f"N(r,r+dr)/(N_aρ_b4πr²dr)","1","12 Å exact PBC","density normalized","radial distribution"))
        cumulative = np.cumsum(np.histogram(d, bins=np.r_[0,cdf_edges])[0]) / nsrc
        for k, value in enumerate(cumulative):
            name=f"atlas_pair_{a}_{b}_cdf_{k:03d}"; out[name]=float(value) if ntgt else math.nan; defs.append(_definition(name,"pair",f"N_{a}_to_{b}(r≤{cdf_edges[k]:.2f})/N_a","count/site","12 Å exact PBC","per source atom","coordination accumulation"))
        for width in (0.20, 0.45):
            for k, center in enumerate(smooth_centers):
                value=float(np.exp(-0.5*((d-center)/width)**2).sum()/nsrc) if d.size else math.nan
                name=f"atlas_pair_{a}_{b}_smooth_w{int(width*100):03d}_{k:03d}"; out[name]=value; defs.append(_definition(name,f"pair","Σ exp(-(r-c)²/2σ²)/N_a","count/site","12 Å exact PBC","per source atom","smooth radial integral"))
        for p in range(1,9):
            name=f"atlas_pair_{a}_{b}_inverse_moment_{p:02d}"; out[name]=float(np.mean(d**(-p))) if d.size else math.nan; defs.append(_definition(name,"pair",f"mean(r^-{p})","Å^-p","12 Å exact PBC","per pair","short-range interaction"))
        for k, cutoff in enumerate(np.arange(1.0,9.0,0.5)):
            name=f"atlas_pair_{a}_{b}_screened_{k:02d}"; out[name]=float(np.sum(np.exp(-d/2.0)/np.maximum(d,1e-6)*(d<=cutoff))/nsrc) if d.size else math.nan; defs.append(_definition(name,"pair","Σ exp(-r/2)/r for r≤cutoff","Å^-1/site","12 Å exact PBC","per source atom","screened interaction"))
        order=np.sort(d)
        for k in range(16):
            name=f"atlas_pair_{a}_{b}_neighbor_{k+1:02d}"; out[name]=float(order[k]) if len(order)>k else math.nan; defs.append(_definition(name,"pair",f"{k+1}th ordered neighbour distance","Å","12 Å exact PBC","per source atom","local shell"))
    return out, defs


def _triplet_features(cache: NeighborCache) -> tuple[dict[str, float], list[FeatureDefinition]]:
    out: dict[str,float]={}; defs=[]; symbols=np.asarray(cache.symbols); hists={t:np.zeros(36) for t in TRIPLET_TYPES}; leg={t:np.zeros(12) for t in TRIPLET_TYPES}; quant={t:[] for t in TRIPLET_TYPES}; motif={t:np.zeros(4) for t in TRIPLET_TYPES}; total_sites=max(len(symbols),1)
    for center in range(len(symbols)):
        take=np.flatnonzero(cache.center==center); take=take[np.argsort(cache.distances[take])[:16]]
        for u,v in combinations_with_replacement(range(len(take)),2):
            if u==v: continue
            x,y=take[u],take[v]; va,vb=cache.vectors[x],cache.vectors[y]; den=np.linalg.norm(va)*np.linalg.norm(vb)
            if den==0: continue
            angle=float(np.degrees(np.arccos(np.clip(np.dot(va,vb)/den,-1,1)))); a,b=sorted((symbols[cache.neighbor[x]],symbols[cache.neighbor[y]])); t=(symbols[center],a,b); w=angle/5.; hists[t][min(35,int(w))]+=1; z=np.cos(np.radians(angle)); leg[t]+=np.array([np.polynomial.legendre.legval(z,[0]*l+[1]) for l in range(12)]); quant[t].append(angle)
            motif[t][0]+=angle<60; motif[t][1]+=angle<90; motif[t][2]+=angle>120; motif[t][3]+=np.linalg.norm(va-vb)<3.0
    for t in TRIPLET_TYPES:
        label="_".join(t); denom=max(sum(hists[t]),1.0)
        for k,v in enumerate(hists[t]):
            n=f"atlas_triplet_{label}_angle_bin_{k:02d}"; out[n]=float(v/denom); defs.append(_definition(n,"triplet",f"fraction angle in [{5*k},{5*(k+1)})°","1","16 nearest cached neighbours","triplet normalized","bond-angle distribution"))
        vals=np.asarray(quant[t],dtype=float)
        for k,q in enumerate((0.1,0.25,0.5,0.75,0.9)):
            n=f"atlas_triplet_{label}_angle_q{k:02d}"; out[n]=float(np.quantile(vals,q)) if vals.size else math.nan; defs.append(_definition(n,"triplet",f"quantile {q} of angle","degree","16 nearest cached neighbours","per triplet","angular disorder"))
        for l,v in enumerate(leg[t]):
            n=f"atlas_triplet_{label}_legendre_{l:02d}"; out[n]=float(v/denom); defs.append(_definition(n,"triplet",f"mean P_{l}(cos θ)","1","16 nearest cached neighbours","triplet normalized","angular order"))
        for k,v in enumerate(motif[t]):
            n=f"atlas_triplet_{label}_motif_{k:02d}"; out[n]=float(v/denom); defs.append(_definition(n,"triplet",f"motif fraction {k}","1","16 nearest cached neighbours","triplet normalized","local motif"))
    return out, defs


def _reciprocal_features(structure: Structure) -> tuple[dict[str,float], list[FeatureDefinition]]:
    out={}; defs=[]
    reduced=structure.get_reduced_structure(reduction_algo="niggli"); frac=np.asarray(reduced.frac_coords); z=np.asarray([float(s.specie.Z) for s in reduced]); rec=np.asarray(reduced.lattice.reciprocal_lattice_crystallographic.matrix); qedges=np.linspace(0,24,1201); intensity=np.zeros(1200); counts=np.zeros(400); dvals=[]
    for h in range(-8,9):
        for k in range(-8,9):
            for l in range(-8,9):
                if (h,k,l)==(0,0,0): continue
                g=np.array([h,k,l],dtype=float)@rec; q=float(np.linalg.norm(g));
                if q==0 or q>=24: continue
                amp=np.sum(z*np.exp(2j*np.pi*(frac@np.array([h,k,l],dtype=float)))); val=float((abs(amp)**2)/(np.sum(z)**2)); idx=min(1199,int(q/24*1200)); intensity[idx]+=val; counts[min(399,int(q/24*400))]+=1; dvals.append(1/q)
    for k,v in enumerate(intensity):
        n=f"atlas_reciprocal_structure_factor_{k:04d}"; out[n]=float(np.log1p(v)); defs.append(_definition(n,"reciprocal","log(1+Σ|F(q)|²)","1","Niggli-reduced reciprocal shells","Z² normalized","diffraction intensity"))
    for k,v in enumerate(counts):
        n=f"atlas_reciprocal_shell_count_{k:03d}"; out[n]=float(v); defs.append(_definition(n,"reciprocal","reflection count in q bin","count","Niggli-reduced reciprocal shells","per cell","reciprocal density"))
    dvals=np.sort(np.asarray(dvals,dtype=float));
    for k,q in enumerate(np.linspace(.05,.95,256)):
        n=f"atlas_reciprocal_dspacing_quantile_{k:03d}"; out[n]=float(np.quantile(dvals,q)) if dvals.size else math.nan; defs.append(_definition(n,"reciprocal",f"d-spacing quantile {q:.3f}","Å","Niggli-reduced low-index shells","per reflection","low-index spacing"))
    return out,defs


def _topology_features(cache: NeighborCache) -> tuple[dict[str,float], list[FeatureDefinition]]:
    out={}; defs=[]; symbols=np.asarray(cache.symbols)
    for a,b in PAIR_TYPES:
        mask=(symbols[cache.center]==a)&(symbols[cache.neighbor]==b); d=cache.distances[mask]; n=max(cache.symbols.count(a),1)
        for k,r in enumerate(np.arange(1.0,9.0,.125)):
            deg=np.bincount(cache.center[mask],minlength=len(symbols)); deg=deg[symbols==a]; active=deg if deg.size else np.array([0.])
            value=float(np.sum(d<=r)/n); name=f"atlas_coordination_{a}_{b}_cut_{k:03d}"; out[name]=value; defs.append(_definition(name,"topology","mean pair degree below cutoff","count/site","12 Å exact PBC","per source atom","coordination population"))
        for s,fn in (("mean",np.mean),("std",np.std),("max",np.max),("isolated",lambda x:np.mean(x==0))):
            deg=np.bincount(cache.center[mask],minlength=len(symbols))[symbols==a]; name=f"atlas_coordination_{a}_{b}_{s}"; out[name]=float(fn(deg)) if deg.size else math.nan; defs.append(_definition(name,"topology",f"{s} degree","count/site","12 Å exact PBC","per source atom","quotient-graph summary"))
    return out,defs


def atlas_row(structure: Structure, cache: NeighborCache | None = None) -> tuple[dict[str,float], list[FeatureDefinition]]:
    cache = cache or NeighborCache.from_structure(structure)
    parts = [_composition_features(cache), _pair_features(cache), _triplet_features(cache), _reciprocal_features(structure), _topology_features(cache)]
    values: dict[str,float]={}; definitions: list[FeatureDefinition]=[]
    for vals, defs in parts: values.update(vals); definitions.extend(defs)
    if len(values) != len(definitions) or len(values) != len(set(values)):
        raise AssertionError("Atlas feature registration is not one-to-one")
    return values, definitions


def validate_bank(train: pd.DataFrame, test: pd.DataFrame, baseline: pd.DataFrame, definitions: Iterable[FeatureDefinition]) -> tuple[pd.DataFrame,pd.DataFrame,list[FeatureDefinition],dict[str,Any]]:
    if list(train.columns) != list(test.columns): raise ValueError("Atlas train/test columns differ")
    defs={d.name:d for d in definitions}; baseline_sig={hashlib.sha256(np.asarray(baseline[c],dtype=np.float64).tobytes()).hexdigest() for c in baseline}
    keep=[]; reasons={"constant":[],"duplicate_atlas":[],"duplicate_baseline":[]}; seen=set()
    for c in train.columns:
        x=np.asarray(train[c],dtype=np.float64); finite=x[np.isfinite(x)]
        sig=hashlib.sha256(x.tobytes()).hexdigest()
        reason=None
        if finite.size<2 or np.unique(finite).size<=1: reason="constant"
        elif sig in seen: reason="duplicate_atlas"
        elif sig in baseline_sig: reason="duplicate_baseline"
        if reason: reasons[reason].append(c)
        else: keep.append(c); seen.add(sig)
    if len(keep)<8000: raise ValueError(f"Only {len(keep)} validated Atlas predictors; need at least 8000")
    report={"raw_predictors":len(train.columns),"validated_predictors":len(keep),"rejections":reasons,"passed":True}
    return train[keep].copy(), test[keep].copy(), [defs[c] for c in keep], report


def build_atlas_matrix(structures: list[Structure], n_jobs: int = 1) -> tuple[pd.DataFrame,list[FeatureDefinition]]:
    # The cache is intentionally constructed exactly once per structure.  Parallelism is
    # left to the caller so the same function is usable in a bounded sprint worker.
    rows=[]; definitions=None
    def one(structure: Structure):
        return atlas_row(structure, NeighborCache.from_structure(structure))
    if n_jobs == 1:
        rows = [one(structure) for structure in structures]
    else:
        from joblib import Parallel, delayed
        # Process workers release the GIL held by the angle/reciprocal loops.  The
        # caller controls the worker count; using more workers than physical cores
        # is intentionally allowed for the sprint host.
        rows = Parallel(n_jobs=n_jobs, prefer="processes", batch_size=1)(delayed(one)(s) for s in structures)
    for _, defs in rows:
        definitions = definitions or defs
    rows = [values for values, _ in rows]
    frame=pd.DataFrame(rows, columns=[d.name for d in definitions]).astype(np.float32)
    return frame, definitions or []


def write_definitions(definitions: Iterable[FeatureDefinition], path: Path) -> str:
    payload=[asdict(d) for d in definitions]; raw=json.dumps(payload,sort_keys=True,separators=(",",":"))+"\n"; path.write_text(raw,encoding="utf-8"); return hashlib.sha256(raw.encode()).hexdigest()
