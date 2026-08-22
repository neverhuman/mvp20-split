"""AUDIT_ONLY constraint-relaxation proposal engine for amphora-solver-lab's
P3 (hazard-constrained hardener selection) EMPTY_FEASIBLE_SET demo.

Lives entirely inside amphora-redteam-audit; amphora-solver-lab's own crate
is never modified by this engine, so its authority ceiling (AUDIT_ONLY /
EVIDENCE_ONLY) is provably unchanged by construction, not merely asserted.

Constraint authority classes:
  HAZARD  -- a GHS/CLP hazard-classification gate. Structurally forbidden to
             relax under any authority this loop holds or could fabricate;
             relaxing a hazard gate is a safety claim, not a solver knob.
  RIGHTS  -- a data/IP rights-review gate (e.g. USBR_RIGHTS_REVIEW_REQUIRED,
             eligible_for_derivatives=false). Same treatment as HAZARD.
  SOFT_PREFERENCE -- an applicability-domain or property-window gate chosen
             for statistical/formulation confidence, not safety or legal
             standing. May be PROPOSED for relaxation, at a stated human
             authority class, as an AUDIT_ONLY proposal -- never decided or
             applied by this code.

propose_relaxation() raises RelaxationForbidden for any HAZARD/RIGHTS
constraint_key, unconditionally. The fail-closed check is keyed on the
constraint's REGISTRY class, not on any value the caller passes in, so it
cannot be bypassed by feeding a candidate record with the hazard code
stripped out -- only by mutating the registry itself (which the positive
control in the audit harness demonstrates and flags).
"""

HAZARD = "HAZARD"
RIGHTS = "RIGHTS"
SOFT = "SOFT_PREFERENCE"


class RelaxationForbidden(Exception):
    pass


CONSTRAINT_REGISTRY = {
    "GHS_H317_SKIN_SENSITISER": {
        "class": HAZARD,
        "relaxable": False,
        "authority_class_required": "STRUCTURALLY_FORBIDDEN_NO_AUTHORITY_SUFFICES",
        "source_kpi": "ghs_clp_hazard_prescreen_kpi (amphora-sourceability-ehs)",
    },
    "GHS_H351_SUSPECTED_CARCINOGEN": {
        "class": HAZARD,
        "relaxable": False,
        "authority_class_required": "STRUCTURALLY_FORBIDDEN_NO_AUTHORITY_SUFFICES",
        "source_kpi": "ghs_clp_hazard_prescreen_kpi (amphora-sourceability-ehs)",
    },
    "RIGHTS_USBR_REVIEW_REQUIRED": {
        "class": RIGHTS,
        "relaxable": False,
        "authority_class_required": "STRUCTURALLY_FORBIDDEN_NO_AUTHORITY_SUFFICES",
        "source_kpi": "synthetic -- no live P3 candidate is rights-blocked this fire; "
                       "registered so the RIGHTS class is structurally tested even "
                       "though the current P3 blocking set never exercises it live",
    },
    "AD_TANIMOTO_MIN": {
        "class": SOFT,
        "relaxable": True,
        "authority_class_required": "FORMULATION_TECHNICAL_LEAD_SIGNOFF",
        "source_kpi": "coating_candidate_design_card_kpi (amphora-molecule-property)",
    },
    "CHI_WATER_MIN": {
        "class": SOFT,
        "relaxable": True,
        "authority_class_required": "FORMULATION_TECHNICAL_LEAD_SIGNOFF",
        "source_kpi": "coating_candidate_design_card_kpi (amphora-molecule-property)",
    },
}


def propose_relaxation(constraint_key, candidate_name, pre_relaxation_infeasibility_proof,
                        threshold, actual_value, registry=None):
    """Return an AUDIT_ONLY relaxation proposal dict for a SOFT_PREFERENCE
    constraint, or raise RelaxationForbidden for HAZARD/RIGHTS.

    `registry` defaults to the real module-level CONSTRAINT_REGISTRY; the
    audit harness's positive control passes a deliberately mutated COPY to
    prove this function's fail-closed behaviour is actually load-bearing
    (i.e. it can distinguish a correctly- from an incorrectly-configured
    registry), never the real object.
    """
    reg = registry if registry is not None else CONSTRAINT_REGISTRY
    if constraint_key not in reg:
        raise KeyError(f"unregistered constraint {constraint_key!r} -- fail closed, refuse to propose")
    entry = reg[constraint_key]
    if entry["class"] in (HAZARD, RIGHTS) or not entry["relaxable"]:
        raise RelaxationForbidden(
            f"constraint {constraint_key!r} is class={entry['class']} -- structurally "
            "un-relaxable; no authority this engine recognizes can grant this relaxation"
        )
    cost_to_move = None
    if threshold is not None and actual_value is not None:
        cost_to_move = round(threshold - actual_value, 6)
    return {
        "constraint": constraint_key,
        "constraint_class": entry["class"],
        "candidate": candidate_name,
        "pre_relaxation_infeasibility_proof": pre_relaxation_infeasibility_proof,
        "authority_class_required": entry["authority_class_required"],
        "cost_to_move": cost_to_move,
        "cost_to_move_units": "threshold_minus_actual (constraint-native units)",
        "proposal_marker": "AUDIT_ONLY_PROPOSAL_NOT_DECISION",
        "decision": None,
        "decided_by": None,
        "applied": False,
        "source_kpi": entry["source_kpi"],
    }
