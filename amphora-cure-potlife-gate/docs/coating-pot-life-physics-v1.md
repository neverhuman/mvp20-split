# Coating pot-life physics v1

`coating-pot-life-physics-v1` predicts one endpoint only: the first failure of
the locked airless-spray checklist. Stable pumping and pressure, a full stable
fan for 30 seconds, 7–9 mil wet-film thickness in the locked pass count, and no
blockage, gel, seed, phase split, or thinner are all required for a pass. The
observed life is the interval from the last pass to the first failure.

Supplier gel time, dry-hard time, through-cure, DSC conversion, and viscosity
doubling are not aliases for this endpoint. The existing `CureObservationV1`
and gel-time command behavior are unchanged.

## Identifiable v1 model

The fitted clock is

\[
\xi(t)=\int_0^t \exp\left[-\frac{E_a}{R}
\left(\frac{1}{T(s)}-\frac{1}{T_\mathrm{ref}}\right)\right]ds,
\]

where `T(s)` is the recorded material temperature, not ambient temperature.
The pre-gel contribution is positive and monotone:

\[
\Phi(\xi)=c_f\left(\frac{\xi}{\xi_g-\xi}\right)^p,
\quad 0\leq\xi<\xi_g.
\]

The initial Stormer response remains on its declared measurement basis. The
clock is an effective cure clock, not chemical conversion. Commercial-grade
formulation scales and formulation/geometry/spray critical clocks are latent
parameters. Primary/secondary reaction constants, hydroxyl-autocatalysis
constants, etherification, diffusion/vitrification, heat transfer, and
evaporation remain unset in v1. Flory–Stockmayer bounds are produced only when
the epoxy and both amine functionality distributions are declared.

The thermal/mass balance remains the extension point for future multi-geometry
and solvent-loss evidence:

\[
\rho C_p V\frac{dT}{dt}=(-\Delta H_r)V\frac{d\alpha}{dt}
-hA(T-T_\mathrm{amb})-\Delta H_v\frac{dm_s}{dt}.
\]

No `h`, evaporation, or molecular kinetic parameter is estimated from the
initial Stormer program.

## Evidence and authority

Only independently mixed, owned, hash-bound runs can enter the v1 fit. Public
patents and papers are context. Supplier material is quarantined. Sandia
828/DEA data is a solver fixture unless a SHA-bound derivative-use review
accepts it.

The model artifact is always `SHADOW`. It binds the protocol, source ledger,
24 fit runs, twelve sealed holdouts, exact formulation hashes, exact geometry
hashes, and exact spray-setup hashes. An out-of-domain configuration abstains.
A prediction remains null until the locked benchmark and packet-bound
independent review both pass.

The benchmark includes overall and formulation medians, direct Arrhenius
time-to-event, a monotone temperature interpolation, the current null, and six
hostile nulls. It reports interval-censored log error, factor-1.5 accuracy,
absolute timing error, proper interval score, 90% interval coverage, paired
block-bootstrap lift, viscosity-proxy error, deterministic replay, and
leave-one-formulation-out diagnostics.

The source landscape is saturation-searched, not exhaustive. The generic
integration of cure kinetics to a critical state is treated as prior art.
`FTO NOT PERFORMED`.
